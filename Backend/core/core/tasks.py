"""
Celery Tasks for Core Application
"""

from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta, date, time
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task(name='general_auto_checkout_task')
def general_auto_checkout_task():
    """
    Handles general auto-checkout for organizations.
    This checks out all pending users at a fixed time defined by the organization.
    This task should be run periodically (e.g., every 5-10 minutes) by a scheduler.
    """
    from AuthN.models import OrganizationSettings
    from WorkLog.models import Attendance
    
    now = timezone.now()
    current_date = now.date()
    logger.info(f"--- Running General Auto-Checkout Task at {now} ---")
    
    try:
        # Get organizations with general auto-checkout enabled (and shift-wise disabled to avoid conflict).
        general_settings = OrganizationSettings.objects.filter(
            auto_checkout_enabled=True,
            auto_shiftwise_checkout_enabled=False,  # Ensure shift-wise is off to prevent conflicts.
            auto_checkout_time__isnull=False,
        )
        
        for setting in general_settings:
            # Proceed only if the current time is past the organization's auto-checkout time.
            if now.time() >= setting.auto_checkout_time:
                attendances_to_checkout = Attendance.objects.filter(
                    user__organization=setting.organization,
                    attendance_date=current_date,
                    check_in_time__isnull=False,
                    check_out_time__isnull=True
                )
                
                checkout_datetime = datetime.combine(current_date, setting.auto_checkout_time)
                checkout_datetime_aware = timezone.make_aware(checkout_datetime, timezone.get_current_timezone())
                
                updates_to_perform = []
                for attendance in attendances_to_checkout:
                    attendance.check_out_time = checkout_datetime_aware
                    attendance.remarks = (attendance.remarks or "") + "\nAuto checked-out by system (General)."
                    if attendance.check_in_time:
                        total_seconds = (attendance.check_out_time - attendance.check_in_time).total_seconds()
                        attendance.total_working_minutes = int(total_seconds // 60)
                    updates_to_perform.append(attendance)
                
                if updates_to_perform:
                    Attendance.objects.bulk_update(updates_to_perform, ['check_out_time', 'remarks', 'total_working_minutes'])
                    logger.info(f"[General] Auto-checked out {len(updates_to_perform)} users for organization: {setting.organization.email}")
        
        logger.info("--- General Auto-Checkout Task Finished ---")
        return {"status": "success", "message": "General auto-checkout completed"}
    except Exception as e:
        logger.error(f"Error in general_auto_checkout_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='shiftwise_auto_checkout_task')
def shiftwise_auto_checkout_task():
    """
    Handles shift-wise auto-checkout for organizations.
    This checks out users based on their assigned shift's end time plus a grace period.
    This task should be run periodically (e.g., every 5-10 minutes) by a scheduler.
    """
    from AuthN.models import OrganizationSettings
    from WorkLog.models import Attendance
    
    now = timezone.now()
    current_date = now.date()
    logger.info(f"--- Running Shift-Wise Auto-Checkout Task at {now} ---")
    
    try:
        shiftwise_settings = OrganizationSettings.objects.filter(
            auto_shiftwise_checkout_enabled=True,
            auto_shiftwise_checkout_time__isnull=False
        )
        
        for setting in shiftwise_settings:
            # Find pending checkouts from today AND yesterday to handle night shifts.
            # A shift starting late yesterday might end today.
            yesterday = current_date - timedelta(days=1)
            
            pending_attendances = Attendance.objects.filter(
                user__organization=setting.organization,
                attendance_date__in=[current_date, yesterday],
                check_in_time__isnull=False,
                check_out_time__isnull=True,
                assign_shift__isnull=False,
                assign_shift__end_time__isnull=False,
                assign_shift__start_time__isnull=False,
            ).select_related('assign_shift')  # Use select_related for performance
            
            updates_to_perform = []
            
            for attendance in pending_attendances:
                shift_end_time = attendance.assign_shift.end_time
                grace_period_minutes = setting.auto_shiftwise_checkout_in_minutes or 30  # Use configured grace period or default 30 minutes
                
                # Determine if it's a night shift (ends on the next day)
                is_night_shift = attendance.assign_shift.end_time < attendance.assign_shift.start_time
                
                # The checkout date is the next day if it's a night shift
                checkout_date = attendance.attendance_date
                if is_night_shift:
                    checkout_date += timedelta(days=1)
                
                # Create a timedelta object for the grace period.
                grace_delta = timedelta(minutes=grace_period_minutes)
                
                # Calculate the exact time when auto-checkout should be triggered.
                # This is based on the calculated checkout_date.
                trigger_datetime = datetime.combine(checkout_date, shift_end_time) + grace_delta
                trigger_datetime_aware = timezone.make_aware(trigger_datetime, timezone.get_current_timezone())
                
                # Check if the current time has passed the trigger time.
                if now >= trigger_datetime_aware:
                    # As requested, the checkout time should be the shift's end time.
                    checkout_datetime = datetime.combine(checkout_date, shift_end_time)
                    checkout_datetime_aware = timezone.make_aware(checkout_datetime, timezone.get_current_timezone())
                    
                    attendance.check_out_time = checkout_datetime_aware
                    attendance.remarks = (attendance.remarks or "") + "\nAuto checked-out by system (Shift-wise)."
                    if attendance.check_in_time:
                        total_seconds = (attendance.check_out_time - attendance.check_in_time).total_seconds()
                        attendance.total_working_minutes = int(total_seconds // 60)
                    
                    updates_to_perform.append(attendance)
            
            if updates_to_perform:
                Attendance.objects.bulk_update(updates_to_perform, ['check_out_time', 'remarks', 'total_working_minutes'])
                logger.info(f"[Shift-Wise] Auto-checked out {len(updates_to_perform)} users for organization: {setting.organization.email}")
        
        logger.info("--- Shift-Wise Auto-Checkout Task Finished ---")
        return {"status": "success", "message": "Shift-wise auto-checkout completed"}
    except Exception as e:
        logger.error(f"Error in shiftwise_auto_checkout_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='process_monthly_payroll_task')
def process_monthly_payroll_task(org_id, month, year):
    """
    Process monthly payroll for an organization.
    This task should be run at the end of each month.
    """
    from PayrollSystem.payroll_calculator import PayrollCalculator
    from AuthN.models import BaseUserModel
    
    logger.info(f"--- Processing Monthly Payroll for Org: {org_id}, Month: {month}, Year: {year} ---")
    
    try:
        organization = BaseUserModel.objects.get(id=org_id, role='organization')
        calculator = PayrollCalculator(organization, month, year)
        
        # Get all active employees
        employees = BaseUserModel.objects.filter(
            role='user',
            organization=organization,
            is_active=True
        )
        
        processed_count = 0
        for employee in employees:
            try:
                calculator.calculate_payroll(employee)
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing payroll for employee {employee.id}: {str(e)}")
        
        logger.info(f"--- Payroll Processing Completed: {processed_count} employees processed ---")
        return {"status": "success", "message": f"Payroll processed for {processed_count} employees"}
    except Exception as e:
        logger.error(f"Error in process_monthly_payroll_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='process_leave_accrual_task')
def process_leave_accrual_task(org_id=None):
    """
    Process leave accrual for employees.
    This task should be run monthly or as per organization policy.
    """
    from LeaveControl.leave_calculator import LeaveCalculator
    from AuthN.models import BaseUserModel
    
    logger.info(f"--- Processing Leave Accrual ---")
    
    try:
        if org_id:
            organizations = [BaseUserModel.objects.get(id=org_id, role='organization')]
        else:
            organizations = BaseUserModel.objects.filter(role='organization', is_active=True)
        
        total_accrued = 0
        for organization in organizations:
            calculator = LeaveCalculator(organization)
            employees = BaseUserModel.objects.filter(
                role='user',
                organization=organization,
                is_active=True
            )
            
            for employee in employees:
                try:
                    from LeaveControl.models import LeaveType, EmployeeLeaveBalance
                    from LeaveControl.leave_calculator import LeaveCalculator
                    
                    # Get all active leave types with accrual enabled
                    leave_types = LeaveType.objects.filter(
                        admin=organization.own_organization_profile_setting.organization,
                        accrual_enabled=True,
                        is_active=True
                    )
                    
                    for leave_type in leave_types:
                        try:
                            # Get or create leave balance
                            balance, created = EmployeeLeaveBalance.objects.get_or_create(
                                user=employee,
                                leave_type=leave_type,
                                defaults={
                                    'accrued': Decimal('0.00'),
                                    'assigned': Decimal('0.00'),
                                    'used': Decimal('0.00'),
                                    'pending': Decimal('0.00'),
                                    'carried_forward': Decimal('0.00')
                                }
                            )
                            
                            # Create calculator and process accrual
                            calculator = LeaveCalculator(employee, leave_type, date.today().year)
                            accrual_log = calculator.process_leave_accrual(date.today())
                            
                            if accrual_log:
                                total_accrued += 1
                                logger.info(f"Accrued {accrual_log.days_accrued} days of {leave_type.code} for {employee.email}")
                        except Exception as e:
                            logger.error(f"Error processing leave accrual for {employee.id} - {leave_type.code}: {str(e)}")
                            
                except Exception as e:
                    logger.error(f"Error processing leave accrual for employee {employee.id}: {str(e)}")
        
        logger.info(f"--- Leave Accrual Processing Completed: {total_accrued} employees processed ---")
        return {"status": "success", "message": f"Leave accrual processed for {total_accrued} employees"}
    except Exception as e:
        logger.error(f"Error in process_leave_accrual_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='send_scheduled_notifications_task')
def send_scheduled_notifications_task():
    """
    Send scheduled notifications.
    This task should be run periodically (e.g., every minute).
    """
    from NotificationControl.models import Notification
    
    logger.info(f"--- Processing Scheduled Notifications ---")
    
    try:
        now = timezone.now()
        pending_notifications = Notification.objects.filter(
            scheduled_at__lte=now,
            status='scheduled'
        )
        
        sent_count = 0
        for notification in pending_notifications:
            try:
                # Send notification logic here
                notification.status = 'sent'
                notification.sent_at = now
                notification.save()
                sent_count += 1
            except Exception as e:
                logger.error(f"Error sending notification {notification.id}: {str(e)}")
                notification.status = 'failed'
                notification.save()
        
        logger.info(f"--- Scheduled Notifications Processing Completed: {sent_count} notifications sent ---")
        return {"status": "success", "message": f"{sent_count} notifications sent"}
    except Exception as e:
        logger.error(f"Error in send_scheduled_notifications_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='process_expense_reimbursements_task')
def process_expense_reimbursements_task(org_id=None):
    """
    Process expense reimbursements based on reimbursement cycle.
    This task should be run weekly/monthly based on organization policy.
    """
    from Expenditure.models import ExpenseReimbursement, ExpensePolicy
    from AuthN.models import BaseUserModel
    
    logger.info(f"--- Processing Expense Reimbursements ---")
    
    try:
        if org_id:
            organizations = [BaseUserModel.objects.get(id=org_id, role='organization')]
        else:
            organizations = BaseUserModel.objects.filter(role='organization', is_active=True)
        
        processed_count = 0
        for organization in organizations:
            # Get organization's expense policy
            policy = ExpensePolicy.objects.filter(
                organization=organization,
                is_active=True
            ).first()
            
            if not policy:
                continue
            
            # Get pending reimbursements
            pending_reimbursements = ExpenseReimbursement.objects.filter(
                organization=organization,
                status='pending'
            )
            
            for reimbursement in pending_reimbursements:
                try:
                    # Process reimbursement logic here
                    reimbursement.status = 'processing'
                    reimbursement.save()
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing reimbursement {reimbursement.id}: {str(e)}")
        
        logger.info(f"--- Expense Reimbursements Processing Completed: {processed_count} reimbursements processed ---")
        return {"status": "success", "message": f"{processed_count} reimbursements processed"}
    except Exception as e:
        logger.error(f"Error in process_expense_reimbursements_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='send_broadcast_notifications_task')
def send_broadcast_notifications_task():
    """
    Send scheduled broadcast notifications.
    This task should be run periodically (e.g., every minute).
    """
    from BroadcastManagement.models import Broadcast
    
    logger.info(f"--- Processing Scheduled Broadcasts ---")
    
    try:
        now = timezone.now()
        pending_broadcasts = Broadcast.objects.filter(
            scheduled_at__lte=now,
            status='scheduled'
        )
        
        sent_count = 0
        for broadcast in pending_broadcasts:
            try:
                # Send broadcast logic here
                broadcast.status = 'sent'
                broadcast.sent_at = now
                broadcast.save()
                sent_count += 1
            except Exception as e:
                logger.error(f"Error sending broadcast {broadcast.id}: {str(e)}")
                broadcast.status = 'failed'
                broadcast.save()
        
        logger.info(f"--- Scheduled Broadcasts Processing Completed: {sent_count} broadcasts sent ---")
        return {"status": "success", "message": f"{sent_count} broadcasts sent"}
    except Exception as e:
        logger.error(f"Error in send_broadcast_notifications_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='update_asset_depreciation_task')
def update_asset_depreciation_task(org_id=None):
    """
    Update asset depreciation monthly.
    This task should be run monthly.
    """
    from AssetManagement.models import Asset, AssetDepreciation
    from AuthN.models import BaseUserModel
    from datetime import date
    
    logger.info(f"--- Updating Asset Depreciation ---")
    
    try:
        if org_id:
            organizations = [BaseUserModel.objects.get(id=org_id, role='organization')]
        else:
            organizations = BaseUserModel.objects.filter(role='organization', is_active=True)
        
        updated_count = 0
        for organization in organizations:
            assets = Asset.objects.filter(
                organization=organization,
                status='active'
            )
            
            for asset in assets:
                try:
                    from AssetManagement.depreciation_service import AssetDepreciationService
                    
                    # Skip if asset doesn't have required fields
                    if not asset.purchase_price or not asset.purchase_date:
                        continue
                    
                    # Skip if asset is disposed/retired
                    if asset.status in ['disposed', 'retired']:
                        continue
                    
                    # Create depreciation service
                    depreciation_service = AssetDepreciationService(asset)
                    
                    # Process all pending depreciation (default: straight-line method)
                    # You can change method to 'wdv' for Written Down Value method
                    records = depreciation_service.process_all_pending_depreciation(
                        end_date=date.today(),
                        method='straight_line'  # or 'wdv' for WDV method
                    )
                    
                    if records:
                        updated_count += 1
                        logger.info(f"Processed {len(records)} depreciation records for asset {asset.id}")
                    
                except Exception as e:
                    logger.error(f"Error updating depreciation for asset {asset.id}: {str(e)}")
        
        logger.info(f"--- Asset Depreciation Update Completed: {updated_count} assets updated ---")
        return {"status": "success", "message": f"{updated_count} assets updated"}
    except Exception as e:
        logger.error(f"Error in update_asset_depreciation_task: {str(e)}")
        return {"status": "error", "message": str(e)}


# ==================== DAILY TASKS ====================

@shared_task(name='attendance_auto_close_task')
def attendance_auto_close_task():
    """Auto-close attendance for previous day if not closed"""
    from WorkLog.models import Attendance
    from AuthN.models import BaseUserModel
    
    logger.info("--- Running Attendance Auto-Close Task ---")
    try:
        yesterday = date.today() - timedelta(days=1)
        
        # Close all open attendances from yesterday
        open_attendances = Attendance.objects.filter(
            attendance_date=yesterday,
            check_in_time__isnull=False,
            check_out_time__isnull=True
        )
        
        closed_count = 0
        for attendance in open_attendances:
            # Auto-checkout at end of day (23:59:59)
            checkout_time = datetime.combine(yesterday, time(23, 59, 59))
            checkout_time_aware = timezone.make_aware(checkout_time, timezone.get_current_timezone())
            
            attendance.check_out_time = checkout_time_aware
            attendance.remarks = (attendance.remarks or "") + "\nAuto closed by system."
            
            if attendance.check_in_time:
                total_seconds = (checkout_time_aware - attendance.check_in_time).total_seconds()
                attendance.total_working_minutes = int(total_seconds // 60)
            
            attendance.save()
            closed_count += 1
        
        logger.info(f"--- Attendance Auto-Close Completed: {closed_count} attendances closed ---")
        return {"status": "success", "message": f"{closed_count} attendances closed"}
    except Exception as e:
        logger.error(f"Error in attendance_auto_close_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='late_early_detection_task')
def late_early_detection_task():
    """Detect late check-ins and early check-outs"""
    from WorkLog.models import Attendance
    from ServiceShift.models import ServiceShift
    from AuthN.models import UserProfile
    
    logger.info("--- Running Late/Early Detection Task ---")
    try:
        today = date.today()
        attendances = Attendance.objects.filter(
            attendance_date=today,
            check_in_time__isnull=False
        ).select_related('user', 'assign_shift')
        
        detected_count = 0
        for attendance in attendances:
            try:
                user_profile = UserProfile.objects.get(user=attendance.user)
                shift = attendance.assign_shift
                
                if not shift:
                    continue
                
                # Check late check-in
                if attendance.check_in_time:
                    check_in_time = attendance.check_in_time.time()
                    if check_in_time > shift.start_time:
                        late_minutes = int((datetime.combine(today, check_in_time) - 
                                          datetime.combine(today, shift.start_time)).total_seconds() / 60)
                        attendance.remarks = (attendance.remarks or "") + f"\nLate by {late_minutes} minutes."
                        attendance.save()
                        detected_count += 1
                
                # Check early check-out
                if attendance.check_out_time and shift.end_time:
                    check_out_time = attendance.check_out_time.time()
                    if check_out_time < shift.end_time:
                        early_minutes = int((datetime.combine(today, shift.end_time) - 
                                           datetime.combine(today, check_out_time)).total_seconds() / 60)
                        attendance.remarks = (attendance.remarks or "") + f"\nEarly exit by {early_minutes} minutes."
                        attendance.save()
                        detected_count += 1
                        
            except UserProfile.DoesNotExist:
                continue
        
        logger.info(f"--- Late/Early Detection Completed: {detected_count} records updated ---")
        return {"status": "success", "message": f"{detected_count} records updated"}
    except Exception as e:
        logger.error(f"Error in late_early_detection_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='birthday_anniversary_alerts_task')
def birthday_anniversary_alerts_task():
    """Send birthday and anniversary alerts"""
    from AuthN.models import UserProfile, BaseUserModel
    from NotificationControl.models import Notification
    
    logger.info("--- Running Birthday/Anniversary Alerts Task ---")
    try:
        today = date.today()
        alerts_sent = 0
        
        # Birthday alerts
        birthdays = UserProfile.objects.filter(
            date_of_birth__month=today.month,
            date_of_birth__day=today.day
        ).select_related('user', 'organization')
        
        for profile in birthdays:
            try:
                Notification.objects.create(
                    user=profile.user,
                    organization=profile.organization,
                    title="🎉 Happy Birthday!",
                    message=f"Wishing {profile.user_name} a very happy birthday!",
                    notification_type='system',
                    priority='normal'
                )
                alerts_sent += 1
            except Exception as e:
                logger.error(f"Error sending birthday alert for {profile.user.email}: {str(e)}")
        
        # Anniversary alerts (date of joining)
        anniversaries = UserProfile.objects.filter(
            date_of_joining__month=today.month,
            date_of_joining__day=today.day
        ).select_related('user', 'organization')
        
        for profile in anniversaries:
            try:
                years = today.year - profile.date_of_joining.year
                Notification.objects.create(
                    user=profile.user,
                    organization=profile.organization,
                    title="🎊 Work Anniversary!",
                    message=f"Congratulations {profile.user_name} on completing {years} year(s)!",
                    notification_type='system',
                    priority='normal'
                )
                alerts_sent += 1
            except Exception as e:
                logger.error(f"Error sending anniversary alert for {profile.user.email}: {str(e)}")
        
        logger.info(f"--- Birthday/Anniversary Alerts Completed: {alerts_sent} alerts sent ---")
        return {"status": "success", "message": f"{alerts_sent} alerts sent"}
    except Exception as e:
        logger.error(f"Error in birthday_anniversary_alerts_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='data_backup_task')
def data_backup_task():
    """Daily data backup task"""
    logger.info("--- Running Data Backup Task ---")
    try:
        # Backup logic here (database dump, file backup, etc.)
        # This is a placeholder - implement actual backup logic
        logger.info("--- Data Backup Completed ---")
        return {"status": "success", "message": "Backup completed"}
    except Exception as e:
        logger.error(f"Error in data_backup_task: {str(e)}")
        return {"status": "error", "message": str(e)}


# ==================== MONTHLY TASKS ====================

@shared_task(name='leave_carry_forward_task')
def leave_carry_forward_task():
    """Process leave carry-forward at year end"""
    from LeaveControl.models import LeavePolicy, EmployeeLeaveBalance
    from LeaveControl.leave_calculator import LeaveCalculator
    from AuthN.models import BaseUserModel
    
    logger.info("--- Running Leave Carry-Forward Task ---")
    try:
        today = date.today()
        
        # Run only at year end (December 31st or January 1st)
        if today.month != 12 and today.month != 1:
            return {"status": "skipped", "message": "Not year end"}
        
        organizations = BaseUserModel.objects.filter(role='organization', is_active=True)
        processed_count = 0
        
        for org in organizations:
            try:
                calculator = LeaveCalculator(org.id)
                policies = LeavePolicy.objects.filter(organization=org, is_active=True)
                
                for policy in policies:
                    if policy.carry_forward_enabled:
                        # Process carry-forward for all employees
                        balances = EmployeeLeaveBalance.objects.filter(
                            leave_type=policy.leave_type,
                            year=today.year - 1 if today.month == 1 else today.year,
                            is_active=True
                        )
                        
                        for balance in balances:
                            calculator.carry_forward_leaves(
                                user_id=balance.user_id,
                                leave_type_id=policy.leave_type.id,
                                from_year=balance.year,
                                to_year=today.year
                            )
                            processed_count += 1
                            
            except Exception as e:
                logger.error(f"Error processing carry-forward for org {org.id}: {str(e)}")
        
        logger.info(f"--- Leave Carry-Forward Completed: {processed_count} balances processed ---")
        return {"status": "success", "message": f"{processed_count} balances processed"}
    except Exception as e:
        logger.error(f"Error in leave_carry_forward_task: {str(e)}")
        return {"status": "error", "message": str(e)}


# ==================== ORGANIZATION TASKS ====================

@shared_task(name='check_organization_expiry_task')
def check_organization_expiry_task():
    """Check and handle organization expiry"""
    from OrganizationManagement.models import OrganizationSubscription, OrganizationDeactivationLog
    from AuthN.models import BaseUserModel, OrganizationSettings
    
    logger.info("--- Running Organization Expiry Check Task ---")
    try:
        today = date.today()
        expired_count = 0
        grace_period_count = 0
        
        subscriptions = OrganizationSubscription.objects.filter(
            status__in=['active', 'trial'],
            expiry_date__lte=today
        )
        
        for subscription in subscriptions:
            try:
                org = subscription.organization
                
                # Check if in grace period
                if subscription.grace_period_end and today <= subscription.grace_period_end:
                    if subscription.status == 'active':
                        # Send grace period reminder
                        grace_period_count += 1
                        logger.info(f"Organization {org.email} in grace period until {subscription.grace_period_end}")
                else:
                    # Expired - deactivate
                    subscription.status = 'expired'
                    subscription.save()
                    
                    # Deactivate organization
                    org.is_active = False
                    org.save()
                    
                    # Log deactivation
                    OrganizationDeactivationLog.objects.create(
                        organization=org,
                        reason='plan_expired',
                        reason_description=f"Plan expired on {subscription.expiry_date}"
                    )
                    
                    expired_count += 1
                    logger.info(f"Organization {org.email} expired and deactivated")
                    
            except Exception as e:
                logger.error(f"Error processing expiry for subscription {subscription.id}: {str(e)}")
        
        logger.info(f"--- Organization Expiry Check Completed: {expired_count} expired, {grace_period_count} in grace ---")
        return {"status": "success", "message": f"{expired_count} expired, {grace_period_count} in grace"}
    except Exception as e:
        logger.error(f"Error in check_organization_expiry_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='send_renewal_reminders_task')
def send_renewal_reminders_task():
    """Send renewal reminders to organizations"""
    from OrganizationManagement.models import OrganizationSubscription
    from NotificationControl.models import Notification
    
    logger.info("--- Running Renewal Reminders Task ---")
    try:
        today = date.today()
        reminders_sent = 0
        
        # Remind 7, 3, 1 days before expiry
        reminder_days = [7, 3, 1]
        
        for days in reminder_days:
            reminder_date = today + timedelta(days=days)
            subscriptions = OrganizationSubscription.objects.filter(
                status='active',
                expiry_date=reminder_date,
                renewal_reminder_sent=False
            )
            
            for subscription in subscriptions:
                try:
                    # Send notification
                    Notification.objects.create(
                        user=subscription.organization,
                        organization=subscription.organization,
                        title="Subscription Renewal Reminder",
                        message=f"Your subscription expires in {days} day(s). Please renew to continue using our services.",
                        notification_type='system',
                        priority='high'
                    )
                    
                    subscription.renewal_reminder_sent = True
                    subscription.save()
                    reminders_sent += 1
                    
                except Exception as e:
                    logger.error(f"Error sending reminder for subscription {subscription.id}: {str(e)}")
        
        logger.info(f"--- Renewal Reminders Completed: {reminders_sent} reminders sent ---")
        return {"status": "success", "message": f"{reminders_sent} reminders sent"}
    except Exception as e:
        logger.error(f"Error in send_renewal_reminders_task: {str(e)}")
        return {"status": "error", "message": str(e)}


# ==================== SECURITY TASKS ====================

@shared_task(name='token_cleanup_task')
def token_cleanup_task():
    """Clean up expired tokens"""
    from rest_framework.authtoken.models import Token
    from django.utils import timezone
    from datetime import timedelta
    
    logger.info("--- Running Token Cleanup Task ---")
    try:
        # Delete tokens older than 30 days (adjust as needed)
        cutoff_date = timezone.now() - timedelta(days=30)
        
        # Note: Token model doesn't have created date by default
        # You may need to extend it or use a custom token model
        # This is a placeholder
        deleted_count = 0
        
        logger.info(f"--- Token Cleanup Completed: {deleted_count} tokens deleted ---")
        return {"status": "success", "message": f"{deleted_count} tokens deleted"}
    except Exception as e:
        logger.error(f"Error in token_cleanup_task: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(name='suspicious_login_detection_task')
def suspicious_login_detection_task():
    """Detect suspicious login patterns"""
    from UserActivity.models import UserActivity
    from NotificationControl.models import Notification
    from django.db.models import Count
    from datetime import timedelta
    
    logger.info("--- Running Suspicious Login Detection Task ---")
    try:
        # Check for multiple failed logins from same IP
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        suspicious_activities = UserActivity.objects.filter(
            activity_type='login_failed',
            created_at__gte=one_hour_ago
        ).values('ip_address', 'user').annotate(
            failed_count=Count('id')
        ).filter(failed_count__gte=5)  # 5+ failed attempts
        
        detected_count = 0
        for activity in suspicious_activities:
            try:
                # Send alert
                Notification.objects.create(
                    user_id=activity['user'],
                    title="Suspicious Login Activity Detected",
                    message=f"Multiple failed login attempts detected from IP {activity['ip_address']}",
                    notification_type='security',
                    priority='high'
                )
                detected_count += 1
            except Exception as e:
                logger.error(f"Error processing suspicious activity: {str(e)}")
        
        logger.info(f"--- Suspicious Login Detection Completed: {detected_count} activities detected ---")
        return {"status": "success", "message": f"{detected_count} activities detected"}
    except Exception as e:
        logger.error(f"Error in suspicious_login_detection_task: {str(e)}")
        return {"status": "error", "message": str(e)}

