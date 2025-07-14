from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, date, timedelta
from .models import Attendance, BaseUserModel
from .serializers import AttendanceSerializer
from django.shortcuts import get_object_or_404
from utils.attendance_utils import *


class AttendanceCheckInOutAPIView(APIView):
    def post(self, request, user_id):
        try:
            user = get_object_or_404(BaseUserModel, id=user_id)
            today = date.today()

            # Check if any attendance without checkout exists today
            open_attendance = Attendance.objects.filter(
                user=user,
                attendance_date=today,
                check_out_time__isnull=True
            ).first()

            if open_attendance:
                # Do checkout
                check_out_time = datetime.now()
                shift_end = datetime.combine(check_out_time.date(), open_attendance.assign_shift.end_time)

                if check_out_time < shift_end:
                    early_diff = (shift_end - check_out_time).total_seconds()
                    early_exit_minutes = int(early_diff // 60)
                else:
                    early_exit_minutes = 0
                open_attendance.check_out_time = check_out_time

                # Calculate total seconds worked
                print(f"==>> check_out_time: {check_out_time}")
                print(f"==>> open_attendance.check_in_time: {open_attendance.check_in_time}")
                total_seconds = (check_out_time - open_attendance.check_in_time).total_seconds()
                print(f"==>> total_seconds: {total_seconds}")

                if total_seconds < 70:
                    return Response(
                        {"detail": "Working time too short. At least 1 minute required to register checkout."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # open_attendance.total_working_hours = timedelta(seconds=total_seconds)

                rounded_minutes = int(total_seconds // 60)
                open_attendance.total_working_minutes = rounded_minutes  # ✅ Save as integer
                print(f"==>> rounded_second: {rounded_minutes}")
                open_attendance.early_exit_minutes = early_exit_minutes
                open_attendance.save()

                # Optional: Overtime calculation
                expected_work_minutes = 8 * 60
                worked_minutes = total_seconds // 60
                extra = worked_minutes - expected_work_minutes

                if extra > 0:
                    open_attendance.overtime_minutes = int(extra)

                open_attendance.save()
                return Response(
                    {"detail": "Checked out successfully."},
                    status=status.HTTP_200_OK
                )

            else:
                # No open attendance: perform new check-in
                check_in_time = datetime.now()
                print(f"==>> user.own_user_profile.shifts.all(): {user.own_user_profile.shifts.all()}")
                nearest_shift, late_minutes = get_nearest_shift_with_late_minutes(check_in_time, user.own_user_profile.shifts.all())
                print(f"==>> nearest_shift: {nearest_shift}")
                print(f"==>> late_minutes: {late_minutes}")

                payload = {
                    "user": str(user.id),
                    "admin": str(user.own_user_profile.admin.id),
                    "organization": str(user.own_user_profile.organization.id),
                    "attendance_date": today,
                    "check_in_time": check_in_time,
                    "attendance_status": "present",
                    "marked_by": request.data.get("marked_by", "mobile"),
                    "assign_shift": str(nearest_shift.id) if nearest_shift else None,  # ✅ auto shift
                    "late_minutes" : late_minutes
                    
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
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
