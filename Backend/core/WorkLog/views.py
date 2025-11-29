from typing import Any
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, date, timedelta
from calendar import monthrange
from .models import Attendance
from AuthN.models import BaseUserModel, UserProfile, AdminProfile
from .serializers import *
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Case, When, IntegerField
from django.http import HttpResponse
from django.core.cache import cache
from django.db import transaction
from utils.Attendance.attendance_utils import *
from utils.pagination_utils import CustomPagination
from utils.helpers.image_utils import save_multiple_base64_images, save_base64_image
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
from utils.Attendance.attendance_excel_export_service import ExcelExportService
from utils.Attendance.attendance_edit_service import AttendanceEditService
import traceback



class AttendanceCheckInOutAPIView(APIView):
    """
    Optimized Check-In/Check-Out API for high traffic (100k+ calls/day)
    - Uses select_related to avoid N+1 queries
    - Caches user profile data
    - Uses update() for faster database writes
    - Optimized shift lookup
    """

    @transaction.atomic
    def post(self, request, userid):
        try:
            today = date.today()
            check_time = datetime.now()
            
            # Optimized: Fetch user with related profile in single query
            user = BaseUserModel.objects.select_related(
                'own_user_profile',
                'own_user_profile__admin',
                'own_user_profile__organization'
            ).only(
                'id',
                'own_user_profile__admin_id',
                'own_user_profile__organization_id',
                'own_user_profile__profile_photo'
            ).get(id=userid)
            
            user_profile = user.own_user_profile

            # 🟦 CHECKOUT FLOW - Optimized query with select_related
            open_attendance = Attendance.objects.select_related(
                'assign_shift'
            ).only(
                'id', 'check_in_time', 'assign_shift__end_time', 
                'assign_shift__duration_minutes'
            ).filter(
                user_id=userid,
                attendance_date=today,
                check_out_time__isnull=True
            ).first()

            if open_attendance:
                # 1️⃣ Total working minutes
                total_minutes = calculate_total_working_minutes(
                    open_attendance.check_in_time,
                    check_time
                )
                # Check if time is at least 10 seconds
                if total_minutes is None:
                    # Calculate seconds to check minimum requirement
                    total_seconds = (check_time - open_attendance.check_in_time).total_seconds()
                    if total_seconds < 10:
                        remaining_seconds = int(10 - total_seconds)
                        return Response({
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": f"Working time too short. Please wait {remaining_seconds} more second(s). Minimum 10 seconds required.",
                            "remaining_seconds": remaining_seconds,
                            "elapsed_seconds": int(total_seconds),
                            "data": []
                        }, status=status.HTTP_400_BAD_REQUEST)
                    # If >= 10 seconds but < 1 minute, set to 0 minutes (will be stored as 0)
                    total_minutes = 0

                # 2️⃣ Early exit minutes
                early_exit = 0
                if open_attendance.assign_shift and open_attendance.assign_shift.end_time:
                    early_exit = calculate_early_exit_minutes(
                        check_time,
                        open_attendance.assign_shift.end_time
                    )

                # 3️⃣ Overtime minutes
                expected_hours = 8
                if open_attendance.assign_shift and open_attendance.assign_shift.duration_minutes:
                    expected_hours = open_attendance.assign_shift.duration_minutes / 60
                overtime = calculate_overtime_minutes(total_minutes, expected_hours=expected_hours)

                # Prepare update data
                update_data = {
                    'check_out_time': check_time,
                    'total_working_minutes': total_minutes,
                    'early_exit_minutes': early_exit,
                    'overtime_minutes': overtime
                }
                
                # Update profile photo from selfie if provided (update on every checkout)
                base64_images = request.data.get("base64_images")
                if base64_images:
                    # Normalize to list if single string
                    if isinstance(base64_images, str):
                        base64_images = [base64_images]
                    
                    # Update profile photo on every checkout
                    if base64_images and len(base64_images) > 0:
                        try:
                            saved_image = save_base64_image(
                                base64_images[0],
                                folder_name='profile_photos',
                                attendance_type='profile',
                                captured_at=check_time
                            )
                            # Update user profile photo
                            user_profile.profile_photo = saved_image.get('file_path', '')
                            user_profile.save(update_fields=['profile_photo'])
                        except Exception as e:
                            # Log error but don't fail checkout
                            print(f"Error updating profile photo: {str(e)}")
                
                # Optimized: Use update() instead of save() for better performance
                Attendance.objects.filter(id=open_attendance.id).update(**update_data)

                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Checked out successfully.",
                    "data": []
                }, status=status.HTTP_200_OK)

            # 🟩 CHECK-IN FLOW
            # Optimized: Cache shifts lookup per user (5 min cache)
            cache_key = f"user_shifts_{userid}"
            shifts = cache.get(cache_key)
            
            if shifts is None:
                shifts = list(user_profile.shifts.all().only('id', 'start_time', 'end_time', 'duration_minutes'))
                cache.set(cache_key, shifts, 300)  # Cache for 5 minutes
            
            nearest_shift, late_minutes = get_nearest_shift_with_late_minutes(
                check_time,
                shifts
            )

            # Prepare payload with minimal data
            payload = {
                "user": str(user.id),
                "admin": str(user_profile.admin_id),
                "organization": str(user_profile.organization_id),
                "attendance_date": today,
                "check_in_time": check_time,
                "attendance_status": "present",
                "marked_by": request.data.get("marked_by", "mobile"),
                "assign_shift": str(nearest_shift.id) if nearest_shift else None,
                "late_minutes": late_minutes or 0
            }
            
            serializer = AttendanceSerializer(data=payload)
            if serializer.is_valid():
                serializer.save()
                
                # Update profile photo from selfie if provided (update on every check-in)
                base64_images = request.data.get("base64_images")
                if base64_images:
                    # Normalize to list if single string
                    if isinstance(base64_images, list) and len(base64_images) > 0:
                        base64_image = base64_images[0]
                    elif isinstance(base64_images, str):
                        base64_image = base64_images
                    else:
                        base64_image = None
                    
                    # Update profile photo on every check-in
                    if base64_image:
                        try:
                            saved_image = save_base64_image(
                                base64_image,
                                folder_name='profile_photos',
                                attendance_type='profile',
                                captured_at=check_time
                            )
                            # Update user profile photo
                            user_profile.profile_photo = saved_image.get('file_path', '')
                            user_profile.save(update_fields=['profile_photo'])
                        except Exception as e:
                            # Log error but don't fail check-in
                            print(f"Error updating profile photo: {str(e)}")
                
                # Invalidate cache after check-in
                cache.delete(cache_key)
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Checked in successfully.",
                    "data": []
                }, status=status.HTTP_201_CREATED)

            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except BaseUserModel.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found.",
                "data": []
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FetchEmployeeAttendanceAPIView(APIView):
    pagination_class = CustomPagination

    def get(self, request, admin_id=None, user_id=None):
        try:
            q_date = request.query_params.get("date")
            export = request.query_params.get("export") == "true"
            status_param = request.query_params.get("status", None)

            if not q_date:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "date parameter is required",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            attendance_date = datetime.strptime(q_date, "%Y-%m-%d").date()

            # If user_id is provided in URL path, filter by single employee
            if user_id:
                try:
                    # Verify employee belongs to the admin
                    employee = UserProfile.objects.select_related("user").get(
                        user_id=user_id,
                        admin_id=admin_id
                    )
                    employees = [employee]
                except UserProfile.DoesNotExist:
                    return Response({
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "Employee not found or does not belong to this admin",
                        "data": []
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Filter by admin_id (all employees under admin)
                if not admin_id:
                    return Response({
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "admin_id is required",
                        "data": []
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                employees = UserProfile.objects.filter(
                    admin_id=admin_id
                ).select_related("user", "user__own_user_profile")

            data = AttendanceService.build_employee_structure(employees, attendance_date)

            records = Attendance.objects.filter(
                user_id__in=list(data.keys()),
                attendance_date=attendance_date
            ).select_related("user", "assign_shift", "user__own_user_profile").order_by('-id')

            
            data = AttendanceService.aggregate_records(records, data)
            print(data, "--------------")
            final_data = AttendanceService.finalize_status(data)

            # Filter by status_param if provided
            if status_param:
                status_param = status_param.lower()
                if status_param == "late":
                    final_data = [x for x in final_data if x.get("is_late")]
                elif status_param == "present":
                    final_data = [x for x in final_data if x.get("attendance_status") == "present"]
                elif status_param == "absent":
                    final_data = [x for x in final_data if x.get("attendance_status") == "absent"]
                print(final_data, "--------------")

            if export:
                return ExcelExportService.generate(final_data, attendance_date)

            # Paginate
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 20))
            start = (page - 1) * page_size


            serializer = AttendanceOutputSerializer(final_data[start:start + page_size], many=True)

            # ------------------- Summary -------------------
            total_emp = len(employees) if user_id else employees.count()
            present = records.filter(attendance_status="present").values("user_id").distinct().count()
            late = records.filter(is_late=True).values("user_id").distinct().count()
            absent = total_emp - records.values("user_id").distinct().count()

            summary = {
                "total_employees": total_emp,
                "present": present,
                "late_login": late,
                "absent": absent,
                "attendance_date": attendance_date.strftime("%Y-%m-%d")
            }

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Attendance fetched successfully",
                "data": serializer.data,
                "summary": summary,
                "total_objects": len(final_data),
                "current_page_number": page
            }, status=status.HTTP_200_OK)

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            # Get last line in traceback (where exception occurred)
            line_number = tb[-1].lineno if tb else None
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "line_number": line_number,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FetchEmployeeMonthlyAttendanceAPIView(APIView):
    """
    Optimized API to fetch monthly present/absent count for employee
    Returns detailed attendance data with dates and summary
    """
    
    def get(self, request, admin_id, user_id, month, year):
        try:
            # Validate month and year
            if month < 1 or month > 12:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid month. Month must be between 1 and 12",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if year < 2000 or year > 2100:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid year",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get employee with related user data
            try:
                employee = UserProfile.objects.select_related("user").get(
                    user_id=user_id,
                    admin_id=admin_id
                )
            except UserProfile.DoesNotExist:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Employee not found or does not belong to this admin",
                    "data": []
                }, status=status.HTTP_404_NOT_FOUND)

            # Calculate first and last day of month
            first_day = date(year, month, 1)
            last_day = date(year, month, monthrange(year, month)[1])
            total_days = (last_day - first_day).days + 1

            # Get all present dates (distinct dates where attendance_status is "present")
            present_dates_list = list(
                Attendance.objects.filter(
                    user_id=user_id,
                    attendance_date__gte=first_day,
                    attendance_date__lte=last_day,
                    attendance_status="present"
                ).values_list('attendance_date', flat=True).distinct().order_by('attendance_date')
            )
            
            # Convert dates to string format (YYYY-MM-DD)
            present_dates_str = [str(d) for d in present_dates_list]
            present_days_count = len(present_dates_str)

            # Generate all dates in the month
            all_dates_in_month = [
                first_day + timedelta(days=x) 
                for x in range(total_days)
            ]
            
            # Find absent dates (dates that are not in present_dates_list)
            present_dates_set = set(present_dates_list)
            absent_dates_list = [
                d for d in all_dates_in_month 
                if d not in present_dates_set
            ]
            
            # Convert absent dates to string format
            absent_dates_str = [str(d) for d in absent_dates_list]
            absent_days_count = len(absent_dates_str)

            # Prepare response data
            response_data = {
                "present": {
                    "count": present_days_count,
                    "dates": present_dates_str
                },
                "absent": {
                    "count": absent_days_count,
                    "dates": absent_dates_str
                }
            }

            # Prepare summary
            summary = {
                "employee_id": str(employee.user_id),
                "employee_name": employee.user_name,
                "month": month,
                "year": year,
                "total_days": total_days,
                "present_days": present_days_count,
                "absent_days": absent_days_count
            }

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Monthly attendance status fetched successfully",
                "data": response_data,
                "summary": summary
            }, status=status.HTTP_200_OK)

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            line_number = tb[-1].lineno if tb else None
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "line_number": line_number,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditAttendanceAPIView(APIView):
    """Clean API to edit attendance check-in & check-out"""

    def put(self, request, userid, attendance_id):
        # Fetch attendance or 404 automatically
        attendance = get_object_or_404(
            Attendance,
            id=attendance_id,
            user_id=userid
        )

        serializer = EditAttendanceSerializer(
            attendance, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        # Update attendance via service
        AttendanceEditService.update_checkin_checkout(
            attendance, serializer.validated_data
        )

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Attendance updated successfully",
            "data": []
        }, status=status.HTTP_200_OK)