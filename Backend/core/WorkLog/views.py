from typing import Any
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, date, timedelta
from .models import Attendance
from AuthN.models import BaseUserModel, UserProfile, AdminProfile
from .serializers import *
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Case, When, IntegerField
from django.http import HttpResponse
from utils.Attendance.attendance_utils import *
from utils.pagination_utils import CustomPagination
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
from utils.Attendance.attendance_excel_export_service import ExcelExportService
from utils.Attendance.attendance_edit_service import AttendanceEditService
from rest_framework import status
import traceback



class AttendanceCheckInOutAPIView(APIView):
    print(f"==>> AttendanceCheckInOutAPIView")

    def post(self, request, userid):
        print(f"==>> Received userid: {userid}, type: {type(userid)}")
        try:
            user = get_object_or_404(BaseUserModel, id=userid)
            print(f"==>> user: {user}")
            today = date.today()

            # 🟦 CHECKOUT FLOW
            open_attendance = Attendance.objects.filter(
                user=user,
                attendance_date=today,
                check_out_time__isnull=True
            ).first()

            if open_attendance:
                check_out_time = datetime.now()

                # 1️⃣ Total working minutes
                total_minutes = calculate_total_working_minutes(
                    open_attendance.check_in_time,
                    check_out_time
                )

                if total_minutes is None:
                    return Response(
                        {"detail": "Working time too short. At least 1 minute required."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 2️⃣ Early exit minutes
                early_exit = calculate_early_exit_minutes(
                    check_out_time,
                    open_attendance.assign_shift.end_time
                )

                # 3️⃣ Overtime minutes
                if open_attendance.assign_shift.duration_minutes:
                    expected_hours = open_attendance.assign_shift.duration_minutes / 60
                else:
                    expected_hours = 8
                overtime = calculate_overtime_minutes(total_minutes, expected_hours=expected_hours)

                # Save attendance
                open_attendance.check_out_time = check_out_time
                open_attendance.total_working_minutes = total_minutes
                open_attendance.early_exit_minutes = early_exit
                open_attendance.overtime_minutes = overtime
                open_attendance.save()

                return Response(
                    {"detail": "Checked out successfully."},
                    status=status.HTTP_200_OK
                )

            # 🟩 CHECK-IN FLOW
            check_in_time = datetime.now()

            nearest_shift, late_minutes = get_nearest_shift_with_late_minutes(
                check_in_time,
                user.own_user_profile.shifts.all()
            )

            payload = {
                "user": str(user.id),
                "admin": str(user.own_user_profile.admin.id),
                "organization": str(user.own_user_profile.organization.id),
                "attendance_date": today,
                "check_in_time": check_in_time,
                "attendance_status": "present",
                "marked_by": request.data.get("marked_by", "mobile"),
                "assign_shift": str(nearest_shift.id) if nearest_shift else None,
                "late_minutes": late_minutes
            }

            serializer = AttendanceSerializer(data=payload)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"detail": "Checked in successfully."},
                    status=status.HTTP_201_CREATED
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FetchEmployeeAttendanceAPIView(APIView):
    pagination_class = CustomPagination

    def get(self, request, admin_id):
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

            employees = UserProfile.objects.filter(
                admin_id=admin_id
            ).select_related("user", "user__own_user_profile")

            data = AttendanceService.build_employee_structure(employees, attendance_date)

            records = Attendance.objects.filter(
                user_id__in=list(data.keys()),
                attendance_date=attendance_date
            ).select_related("user", "assign_shift", "user__own_user_profile")

            
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
            total_emp = employees.count()
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

        output = AttendanceOutputSerializer(attendance)

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Attendance updated successfully",
            "data": []
        }, status=status.HTTP_200_OK)