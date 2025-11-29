"""
Advanced Attendance Calculation Service for Payroll
Handles complex attendance scenarios: sandwich leave, late/early, shift-based, week-off, holidays
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from calendar import monthrange

from WorkLog.models import Attendance
from LeaveControl.models import LeaveApplication, LeaveType
from ServiceShift.models import ServiceShift
from ServiceWeekOff.models import WeekOffPolicy
from Holiday.models import Holiday
from AuthN.models import BaseUserModel, UserProfile


class AttendanceCalculationService:
    """Service for calculating detailed attendance data for payroll"""
    
    def __init__(self, employee, month, year, organization=None, admin=None):
        self.employee = employee
        self.month = month
        self.year = year
        self.organization = organization
        self.admin = admin
        self.user_profile = None
        self.week_off_policies = []
        self.holidays = []
        self.leave_applications = []
        self.attendance_records = []
        
        # Initialize data
        self._load_employee_data()
        self._load_week_off_policies()
        self._load_holidays()
        self._load_leave_applications()
        self._load_attendance_records()
    
    def _load_employee_data(self):
        """Load employee profile and related data"""
        try:
            self.user_profile = self.employee.own_user_profile
        except UserProfile.DoesNotExist:
            self.user_profile = None
    
    def _load_week_off_policies(self):
        """Load week-off policies for employee"""
        if self.user_profile:
            self.week_off_policies = list(self.user_profile.week_offs.filter(is_active=True))
        elif self.admin:
            # Fallback to admin's week-off policies
            self.week_off_policies = list(
                WeekOffPolicy.objects.filter(admin=self.admin, is_active=True)
            )
        elif self.organization:
            # Fallback to organization's week-off policies
            self.week_off_policies = list(
                WeekOffPolicy.objects.filter(organization=self.organization, is_active=True)
            )
    
    def _load_holidays(self):
        """Load holidays for the month"""
        start_date = date(self.year, self.month, 1)
        _, last_day = monthrange(self.year, self.month)
        end_date = date(self.year, self.month, last_day)
        
        if self.admin:
            self.holidays = list(
                Holiday.objects.filter(
                    admin=self.admin,
                    holiday_date__gte=start_date,
                    holiday_date__lte=end_date,
                    is_active=True
                )
            )
        elif self.organization:
            self.holidays = list(
                Holiday.objects.filter(
                    organization=self.organization,
                    holiday_date__gte=start_date,
                    holiday_date__lte=end_date,
                    is_active=True
                )
            )
    
    def _load_leave_applications(self):
        """Load approved leave applications for the month"""
        start_date = date(self.year, self.month, 1)
        _, last_day = monthrange(self.year, self.month)
        end_date = date(self.year, self.month, last_day)
        
        self.leave_applications = list(
            LeaveApplication.objects.filter(
                user=self.employee,
                status='approved',
                from_date__lte=end_date,
                to_date__gte=start_date
            ).select_related('leave_type')
        )
    
    def _load_attendance_records(self):
        """Load attendance records for the month"""
        self.attendance_records = list(
            Attendance.objects.filter(
                user=self.employee,
                attendance_date__year=self.year,
                attendance_date__month=self.month
            ).select_related('assign_shift')
        )
    
    def _is_week_off(self, check_date):
        """Check if a date is a week-off based on employee's week-off policies"""
        if not self.week_off_policies:
            return False
        
        weekday_name = check_date.strftime('%A')  # Monday, Tuesday, etc.
        
        for policy in self.week_off_policies:
            week_days = policy.week_days if isinstance(policy.week_days, list) else []
            
            if weekday_name in week_days:
                # Check week-off cycle if applicable
                if policy.week_off_cycle:
                    week_number = (check_date.day - 1) // 7 + 1
                    if week_number in policy.week_off_cycle:
                        return True
                else:
                    return True
        
        return False
    
    def _is_holiday(self, check_date):
        """Check if a date is a holiday"""
        return any(holiday.holiday_date == check_date for holiday in self.holidays)
    
    def _get_leave_for_date(self, check_date):
        """Get leave application for a specific date"""
        for leave in self.leave_applications:
            if leave.from_date <= check_date <= leave.to_date:
                # Check if it's a half-day
                if leave.duration_type == 'half_day':
                    # For half-day, check if it's first or second half
                    # This is simplified - can be enhanced based on from_time/to_time
                    return leave, 0.5
                elif leave.duration_type == 'short_leave':
                    # Short leave is typically 2-4 hours, count as 0.25 day
                    return leave, 0.25
                else:
                    return leave, 1.0
        return None, 0.0
    
    def _is_comp_off_leave(self, leave):
        """Check if leave is compensatory off (should not be counted in payroll)"""
        if leave and leave.leave_type:
            return leave.leave_type.category == 'compensatory'
        return False
    
    def _is_lop_leave(self, leave):
        """Check if leave is Loss of Pay (LOP)"""
        if leave and leave.leave_type:
            return leave.leave_type.category == 'lwp' or not leave.leave_type.is_paid
        return False
    
    def _get_attendance_for_date(self, check_date):
        """Get attendance record for a specific date"""
        for att in self.attendance_records:
            if att.attendance_date == check_date:
                return att
        return None
    
    def _calculate_sandwich_days(self, start_date, end_date):
        """Calculate sandwich days (week-offs/holidays between two leave/absent days)"""
        sandwich_days = []
        current_date = start_date + timedelta(days=1)
        
        while current_date < end_date:
            if self._is_week_off(current_date) or self._is_holiday(current_date):
                # Check if there's attendance for this day
                att = self._get_attendance_for_date(current_date)
                if not att or att.attendance_status != 'present':
                    sandwich_days.append(current_date)
            current_date += timedelta(days=1)
        
        return sandwich_days
    
    def calculate_detailed_attendance(self):
        """Calculate comprehensive attendance data for payroll"""
        start_date = date(self.year, self.month, 1)
        _, last_day = monthrange(self.year, self.month)
        end_date = date(self.year, self.month, last_day)
        
        # Get employee joining date
        joining_date = self.user_profile.date_of_joining if self.user_profile else None
        
        # Initialize counters
        total_calendar_days = last_day
        working_days = 0
        present_days = 0
        absent_days = 0
        leave_days = Decimal('0.00')
        lop_days = Decimal('0.00')
        half_day_leaves = Decimal('0.00')
        week_off_days = 0
        holiday_days = 0
        sandwich_absent_days = 0
        payable_days = Decimal('0.00')
        
        # Track late and early exits
        late_days = 0
        early_exit_days = 0
        total_late_minutes = 0
        total_early_exit_minutes = 0
        
        # Track overtime
        total_overtime_hours = Decimal('0.00')
        
        # Day-wise breakdown
        day_wise_data = []
        
        current_date = start_date
        while current_date <= end_date:
            # Skip if before joining date
            if joining_date and current_date < joining_date:
                current_date += timedelta(days=1)
                continue
            
            day_data = {
                'date': current_date,
                'is_week_off': False,
                'is_holiday': False,
                'is_leave': False,
                'is_comp_off': False,
                'is_lop': False,
                'is_present': False,
                'is_absent': False,
                'is_sandwich': False,
                'is_late': False,
                'is_early_exit': False,
                'late_minutes': 0,
                'early_exit_minutes': 0,
                'working_minutes': 0,
                'overtime_hours': Decimal('0.00'),
                'leave_type': None,
                'leave_days': Decimal('0.00')
            }
            
            # Check week-off
            if self._is_week_off(current_date):
                day_data['is_week_off'] = True
                week_off_days += 1
                # Week-off is not a working day, but may be payable if employee worked
                att = self._get_attendance_for_date(current_date)
                if att and att.attendance_status == 'present':
                    working_days += 1
                    present_days += 1
                    payable_days += Decimal('1.00')
                    day_data['is_present'] = True
                    day_data['working_minutes'] = att.total_working_minutes or 0
                    if att.is_late:
                        day_data['is_late'] = True
                        day_data['late_minutes'] = att.late_minutes or 0
                        late_days += 1
                        total_late_minutes += att.late_minutes or 0
                    if att.is_early_exit:
                        day_data['is_early_exit'] = True
                        day_data['early_exit_minutes'] = att.early_exit_minutes or 0
                        early_exit_days += 1
                        total_early_exit_minutes += att.early_exit_minutes or 0
            # Check holiday
            elif self._is_holiday(current_date):
                day_data['is_holiday'] = True
                holiday_days += 1
                # Holiday is not a working day, but may be payable if employee worked
                att = self._get_attendance_for_date(current_date)
                if att and att.attendance_status == 'present':
                    working_days += 1
                    present_days += 1
                    payable_days += Decimal('1.00')
                    day_data['is_present'] = True
                    day_data['working_minutes'] = att.total_working_minutes or 0
            # Regular working day
            else:
                working_days += 1
                
                # Check leave
                leave, leave_days_count = self._get_leave_for_date(current_date)
                if leave:
                    day_data['is_leave'] = True
                    day_data['leave_type'] = leave.leave_type.code if leave.leave_type else None
                    day_data['leave_days'] = Decimal(str(leave_days_count))
                    
                    # Check if comp-off (should not affect payroll)
                    if self._is_comp_off_leave(leave):
                        day_data['is_comp_off'] = True
                        # Comp-off is treated as present for payroll
                        present_days += 1
                        payable_days += Decimal(str(leave_days_count))
                        leave_days += Decimal(str(leave_days_count))
                    # Check if LOP
                    elif self._is_lop_leave(leave):
                        day_data['is_lop'] = True
                        lop_days += Decimal(str(leave_days_count))
                        leave_days += Decimal(str(leave_days_count))
                        # LOP days are not payable
                    else:
                        # Paid leave
                        leave_days += Decimal(str(leave_days_count))
                        if leave_days_count == 0.5:
                            half_day_leaves += Decimal('0.50')
                        payable_days += Decimal(str(leave_days_count))
                
                # Check attendance
                att = self._get_attendance_for_date(current_date)
                if att:
                    if att.attendance_status == 'present':
                        present_days += 1
                        payable_days += Decimal('1.00')
                        day_data['is_present'] = True
                        day_data['working_minutes'] = att.total_working_minutes or 0
                        
                        # Check late
                        if att.is_late:
                            day_data['is_late'] = True
                            day_data['late_minutes'] = att.late_minutes or 0
                            late_days += 1
                            total_late_minutes += att.late_minutes or 0
                        
                        # Check early exit
                        if att.is_early_exit:
                            day_data['is_early_exit'] = True
                            day_data['early_exit_minutes'] = att.early_exit_minutes or 0
                            early_exit_days += 1
                            total_early_exit_minutes += att.early_exit_minutes or 0
                        
                        # Calculate overtime
                        if att.total_working_minutes:
                            shift = att.assign_shift
                            if shift and shift.duration_minutes:
                                expected_minutes = shift.duration_minutes
                                if att.total_working_minutes > expected_minutes:
                                    overtime_minutes = att.total_working_minutes - expected_minutes
                                    overtime_hours = Decimal(str(overtime_minutes)) / Decimal('60')
                                    total_overtime_hours += overtime_hours
                                    day_data['overtime_hours'] = overtime_hours
                    else:
                        # Absent
                        absent_days += 1
                        day_data['is_absent'] = True
                        # Check for sandwich absent
                        # This is simplified - can be enhanced to check previous/next day
                else:
                    # No attendance record - check if it's a leave day
                    if not leave:
                        # No leave and no attendance = absent
                        absent_days += 1
                        day_data['is_absent'] = True
            
            day_wise_data.append(day_data)
            current_date += timedelta(days=1)
        
        # Calculate sandwich absent days (week-offs/holidays between two absent days)
        # This is a simplified version - can be enhanced
        for i, day_data in enumerate(day_wise_data):
            if day_data['is_absent']:
                # Check previous and next days
                if i > 0 and i < len(day_wise_data) - 1:
                    prev_day = day_wise_data[i - 1]
                    next_day = day_wise_data[i + 1]
                    if prev_day['is_absent'] and next_day['is_absent']:
                        # Check if current day is week-off or holiday
                        if day_data['is_week_off'] or day_data['is_holiday']:
                            day_data['is_sandwich'] = True
                            sandwich_absent_days += 1
        
        # Calculate net payable days
        # Payable days = Present days + Paid leave days + Week-off/Holiday worked days
        # This is already calculated above
        
        return {
            'total_calendar_days': total_calendar_days,
            'working_days': working_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'leave_days': leave_days,
            'lop_days': lop_days,
            'half_day_leaves': half_day_leaves,
            'week_off_days': week_off_days,
            'holiday_days': holiday_days,
            'sandwich_absent_days': sandwich_absent_days,
            'payable_days': payable_days,
            'late_days': late_days,
            'early_exit_days': early_exit_days,
            'total_late_minutes': total_late_minutes,
            'total_early_exit_minutes': total_early_exit_minutes,
            'overtime_hours': total_overtime_hours,
            'day_wise_data': day_wise_data
        }

