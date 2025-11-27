from typing import Any
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, date, timedelta
from .models import Attendance
from AuthN.models import BaseUserModel, UserProfile, AdminProfile
from .serializers import AttendanceSerializer, EmployeeAttendanceListSerializer, EditAttendanceSerializer
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Case, When, IntegerField
from django.http import HttpResponse
from utils.attendance_utils import *
from utils.pagination_utils import CustomPagination
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO


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
            # ------------------- REQUIRED PARAMS -------------------
            q_date = request.query_params.get("date")
            status_filter = request.query_params.get("status")
            export = request.query_params.get("export", "false").lower() == "true"

            # ---- date is compulsory ----
            if not q_date:
                return Response(
                    {"detail": "date parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                attendance_date = datetime.strptime(q_date, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"detail": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ------------------- Admin -------------------
            admin = AdminProfile.objects.filter(user_id=admin_id).select_related("organization").first()
            if not admin:
                return Response({"detail": "Admin not found"}, status=404)

            # ------------------- Employees -------------------
            employees = (
                UserProfile.objects.filter(admin_id=admin_id)
                .select_related("user", "user__own_user_profile")
            )
            employee_ids = list(employees.values_list("user_id", flat=True))

            # ------------------- Attendance Records -------------------
            records = (
                Attendance.objects.filter(
                    user_id__in=employee_ids,
                    attendance_date=attendance_date
                )
                .select_related("user", "assign_shift", "user__own_user_profile")
                .order_by("id")
            )

            # If status filter applied → early filter
            if status_filter and status_filter == 'late':
                records = records.filter(is_late=True)  # ✅
            else:
                records = records.filter(attendance_status__iexact=status_filter)

            # ------------------- Prepare Empty Structure -------------------
            data = {
                e.user_id: {
                    "id": None,
                    "user": e.user,
                    "attendance_status": "absent",
                    "first_check_in": None,
                    "last_check_out": None,
                    "first_check_in_time": None,
                    "last_check_out_time": None,
                    "total_working_minutes": 0,
                    "total_break_minutes": 0,
                    "is_late": False,
                    "late_minutes": 0,
                    "last_login_status": None,
                    "assign_shift": None,
                    "attendance_date": attendance_date,
                    "multiple_entries": [],
                    "is_early_exit": False,
                    "early_exit_minutes": 0,
                    "remarks": None,
                }
                for e in employees
            }

            # ------------------- Aggregate Records -------------------
            for r in records:
                d = data[r.user_id]

                d["multiple_entries"].append({
                    "id": r.id,
                    "check_in_time": format_datetime(r.check_in_time),
                    "check_out_time": format_datetime(r.check_out_time),
                    "total_working_minutes": r.total_working_minutes,
                    "remarks": r.remarks,
                })

                if r.check_in_time:
                    if not d["first_check_in_time"] or r.check_in_time < d["first_check_in_time"]:
                        d["first_check_in"] = r.check_in_time
                        d["first_check_in_time"] = r.check_in_time
                        d["attendance_status"] = r.attendance_status
                        d["assign_shift"] = r.assign_shift
                        d["is_late"] = r.is_late
                        d["late_minutes"] = r.late_minutes
                        d["id"] = r.id

                if r.check_out_time:
                    if not d["last_check_out_time"] or r.check_out_time > d["last_check_out_time"]:
                        d["last_check_out"] = r.check_out_time
                        d["last_check_out_time"] = r.check_out_time

                d["total_working_minutes"] += (r.total_working_minutes or 0)
                d["total_break_minutes"] += (r.break_duration_minutes or 0)

            # ------------------- Determine Last Login -------------------
            for info in data.values():
                last_in = info["first_check_in_time"]
                last_out = info["last_check_out_time"]

                if last_out:
                    info["last_login_status"] = "checkout"
                elif last_in:
                    info["last_login_status"] = "checkin"
                else:
                    info["last_login_status"] = None

            # Convert to list
            result_list = list(data.values())

            # ------------------- Apply status filter to final output -------------------
            if status_filter:
                result_list = [x for x in result_list if x["attendance_status"].lower() == status_filter.lower()]

            # ------------------- Summary -------------------
            present = records.filter(attendance_status="present").values("user_id").distinct().count()
            late = records.filter(is_late=True).values("user_id").distinct().count()
            total_emp = employees.count()
            absent = total_emp - records.values("user_id").distinct().count()

            # Excel export
            if export:
                return self._generate_excel_report(result_list, attendance_date, admin)

            # ------------------- Manual Pagination -------------------
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 20))
            start = (page - 1) * page_size

            serializer = EmployeeAttendanceListSerializer(result_list[start:start + page_size], many=True)

            return Response({
                "total_pages": (len(result_list) + page_size - 1) // page_size,
                "current_page_number": page,
                "page_size": page_size,
                "total_objects": len(result_list),
                "previous_page_number": page - 1 if page > 1 else None,
                "next_page_number": page + 1 if start + page_size < len(result_list) else None,
                "results": serializer.data,
                "summary": {
                    "total_employees": total_emp,
                    "present": present,
                    "late_login": late,
                    "absent": absent,
                    "attendance_date": attendance_date.strftime("%Y-%m-%d")
                }
            })

        except Exception as e:
            return Response({"detail": str(e)}, status=500)
    
    def _generate_excel_report(self, aggregated_list, attendance_date, admin_profile):
        """Generate Excel report for attendance using aggregated data"""
        try:
            # Create workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Attendance Report"
            
            # Header style
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=12)
            
            # Headers
            headers = [
                "Employee Name", "Employee ID", "Email", "Status", "Last Login Status",
                "Check In", "Check Out", "Break Duration", 
                "Late", "Production Hours"
            ]
            
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.value = header
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Data rows
            for row_num, attendance in enumerate(aggregated_list, 2):
                user = attendance.get('user')
                employee_name = user.own_user_profile.user_name if user and hasattr(user, 'own_user_profile') else "N/A"
                employee_id = user.own_user_profile.custom_employee_id if user and hasattr(user, 'own_user_profile') else "N/A"
                email = user.email if user else "N/A"
                status = attendance.get('attendance_status', 'N/A')
                last_login_status = attendance.get('last_login_status', 'N/A')
                
                check_in_time = attendance.get('first_check_in')
                check_in = check_in_time.strftime('%Y-%m-%d %H:%M:%S') if check_in_time else "N/A"
                
                check_out_time = attendance.get('last_check_out')
                check_out = check_out_time.strftime('%Y-%m-%d %H:%M:%S') if check_out_time else "N/A"
                
                # Break duration
                break_minutes = attendance.get('total_break_minutes', 0)
                if break_minutes:
                    hours = break_minutes // 60
                    minutes = break_minutes % 60
                    break_duration = f"{hours}h {minutes}m"
                else:
                    break_duration = "0h 0m"
                
                # Late
                late_minutes = attendance.get('late_minutes', 0)
                if late_minutes and late_minutes > 0:
                    hours = late_minutes // 60
                    minutes = late_minutes % 60
                    late = f"{hours}h {minutes}m"
                else:
                    late = "0h 0m"
                
                # Production hours
                total_minutes = attendance.get('total_working_minutes', 0)
                if total_minutes:
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    production_hours = f"{hours}h {minutes}m"
                else:
                    production_hours = "0h 0m"
                
                row_data = [
                    employee_name, employee_id, email, status, last_login_status,
                    check_in, check_out, break_duration,
                    late, production_hours
                ]
                
                for col_num, value in enumerate(row_data, 1):
                    cell = ws.cell(row=row_num, column=col_num)
                    cell.value = value
                    cell.alignment = Alignment(horizontal="left", vertical="center")
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Save to BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            # Create HTTP response
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            filename = f"attendance_report_{attendance_date.strftime('%Y-%m-%d')}.xlsx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response(
                {"detail": f"Error generating Excel report: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EditAttendanceAPIView(APIView):
    """API to edit attendance check_in and check_out times only"""

    def put(self, request, userid, attendance_id):
        try:
            # Validate that attendance belongs to this employee
            attendance = get_object_or_404(
                Attendance,
                id=attendance_id,
                user=userid
            )

            serializer = EditAttendanceSerializer(attendance, data=request.data, partial=True)

            if serializer.is_valid():
                check_in = serializer.validated_data.get("check_in_time")
                check_out = serializer.validated_data.get("check_out_time")

                # ----------------------------
                # UPDATE CHECK-IN TIME
                # ----------------------------
                if check_in:
                    attendance.check_in_time = check_in

                    # RECALCULATE LATE LOGIN
                    if attendance.assign_shift:
                        shift_start_dt = datetime.combine(
                            attendance.attendance_date,
                            attendance.assign_shift.start_time
                        )
                        if check_in > shift_start_dt:
                            diff = (check_in - shift_start_dt).total_seconds()
                            attendance.late_minutes = int(diff // 60)
                            attendance.is_late = True
                        else:
                            attendance.late_minutes = 0
                            attendance.is_late = False

                # ----------------------------
                # UPDATE CHECK-OUT TIME
                # ----------------------------
                if check_out:
                    attendance.check_out_time = check_out

                # ----------------------------
                # RECALCULATE ALL METRICS
                # ----------------------------
                if attendance.check_in_time and attendance.check_out_time:
                    # 1. Working minutes
                    total_minutes = calculate_total_working_minutes(
                        attendance.check_in_time, attendance.check_out_time
                    )
                    attendance.total_working_minutes = total_minutes or 0

                    # 2. Early exit
                    if attendance.assign_shift:
                        end_dt = datetime.combine(
                            attendance.attendance_date,
                            attendance.assign_shift.end_time
                        )
                        early = calculate_early_exit_minutes(
                            attendance.check_out_time,
                            end_dt.time()
                        )
                        attendance.early_exit_minutes = early
                        attendance.is_early_exit = early > 0

                        # 3. Overtime
                        attendance.overtime_minutes = calculate_overtime_minutes(
                            total_minutes,
                            attendance.assign_shift.duration_minutes / 60
                            if attendance.assign_shift.duration_minutes
                            else 8
                        )

                # ---------------------------------------
                # UPDATE REMARK FIELD AFTER MODIFICATION
                # ---------------------------------------
                attendance.remarks = f"Updated on {datetime.now().strftime('%Y-%m-%d %I:%M %p')}"

                attendance.save()

                # ---------------------------------------
                # PREPARE RESPONSE
                # ---------------------------------------
                aggregated = {
                    "id": attendance.id,
                    "first_check_in": attendance.check_in_time,
                    "last_check_out": attendance.check_out_time,
                    "first_check_in_time": attendance.check_in_time,
                    "last_check_out_time": attendance.check_out_time,
                    "total_working_minutes": attendance.total_working_minutes or 0,
                    "total_break_minutes": attendance.break_duration_minutes or 0,
                    "is_late": attendance.is_late,
                    "late_minutes": attendance.late_minutes,
                    "attendance_status": attendance.attendance_status,
                    "last_login_status": "checkout" if attendance.check_out_time else "checkin",
                    "user": attendance.user,
                    "assign_shift": attendance.assign_shift,
                    "attendance_date": attendance.attendance_date,
                    "remarks": attendance.remarks,
                }

                return Response(
                    {
                        "message": "Attendance updated successfully",
                        "data": EmployeeAttendanceListSerializer(aggregated).data
                    },
                    status=status.HTTP_200_OK
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)