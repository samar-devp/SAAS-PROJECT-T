from datetime import datetime, timedelta, date
from ServiceShift.models import ServiceShift


def get_nearest_shift_with_late_minutes(checkin_time, assigned_shifts_queryset):
    """
    Finds the nearest shift based on check-in time and calculates late minutes (if any).
    Returns: (nearest_shift_object, late_minutes)
    """
    print(f"==>> employee_assign_shifts: {assigned_shifts_queryset}")

    nearest_shift = None
    min_diff = timedelta.max

    for shift in assigned_shifts_queryset:
        shift_start = datetime.combine(checkin_time.date(), shift.start_time)
        diff = abs(shift_start - checkin_time)

        if diff < min_diff:
            min_diff = diff
            nearest_shift = shift

    if nearest_shift:
        shift_start = datetime.combine(checkin_time.date(), nearest_shift.start_time)
        if checkin_time > shift_start:
            late_diff = (checkin_time - shift_start).total_seconds()
            late_minutes = int(late_diff // 60)
        else:
            late_minutes = 0
    else:
        late_minutes = None

    return nearest_shift, late_minutes



def calculate_total_working_minutes(check_in, check_out):
    total_seconds = (check_out - check_in).total_seconds()
    if total_seconds < 60:
        return None  
    return int(total_seconds // 60)


def calculate_early_exit_minutes(check_out, shift_end_time):
    shift_end = datetime.combine(check_out.date(), shift_end_time)

    if check_out < shift_end:
        early_seconds = (shift_end - check_out).total_seconds()
        return int(early_seconds // 60)

    return 0


def calculate_overtime_minutes(total_minutes, expected_hours=8):
    expected_minutes = expected_hours * 60
    extra = total_minutes - expected_minutes

    return int(extra) if extra > 0 else 0

def format_datetime(dt):
    """Format datetime to 'YYYY-MM-DD HH:MM:SS' """
    if not dt:
        return None
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)


def format_date(d):
    """Format date to 'YYYY-MM-DD' """
    if not d:
        return None
    if isinstance(d, date):
        return d.strftime('%Y-%m-%d')
    return str(d)


def format_minutes(minutes):
    """Convert minutes → 'Xh Ym' """
    if not minutes or minutes <= 0:
        return "0h 0m"
    return f"{minutes // 60}h {minutes % 60}m"


def format_break(obj):
    """Break duration formatter"""
    break_minutes = obj.get('total_break_minutes', 0) if isinstance(obj, dict) else getattr(obj, 'break_duration_minutes', 0)
    return format_minutes(break_minutes)


def format_production_hours(obj):
    """Working duration formatter"""
    total_minutes = obj.get('total_working_minutes', 0) if isinstance(obj, dict) else getattr(obj, 'total_working_minutes', 0)
    return format_minutes(total_minutes)


def format_late_minutes(obj):
    """Late minutes formatted"""
    late_minutes = obj.get('late_minutes', 0) if isinstance(obj, dict) else getattr(obj, 'late_minutes', 0)
    return format_minutes(late_minutes)


def get_check_in_time(obj):
    """Unified check-in formatter"""
    time = obj.get('first_check_in') if isinstance(obj, dict) else getattr(obj, 'check_in_time', None)
    return format_datetime(time)


def get_check_out_time(obj):
    """Unified check-out formatter"""
    time = obj.get('last_check_out') if isinstance(obj, dict) else getattr(obj, 'check_out_time', None)
    return format_datetime(time)



class AttendanceService:

    @staticmethod
    def build_employee_structure(employees, attendance_date):
        data = {}

        for e in employees:
            data[e.user_id] = {
                "id": None,
                "user_id": str(e.user_id),  # Add user_id UUID for edit API
                "employee_name": e.user.own_user_profile.user_name,
                "employee_id": e.user.own_user_profile.user_id,
                "employee_email": e.user.email,

                "attendance_status": "absent",
                "first_check_in": None,
                "last_check_out": None,
                "first_check_in_time": None,
                "shift_name": None,
                "last_check_out_time": None,

                "total_working_minutes": 0,
                "total_break_minutes": 0,

                "is_late": False,
                "late_minutes": 0,
                "is_early_exit": False,
                "early_exit_minutes": 0,

                "assign_shift": None,
                "last_login_status": None,

                "attendance_date": attendance_date,
                "multiple_entries": [],
                "remarks": None
            }

        return data

    @staticmethod
    def aggregate_records(records, data):
        for r in records:
            d = data[r.user_id]

            d["multiple_entries"].append({
                "id": r.id,
                "check_in_time": format_datetime(r.check_in_time),
                "check_out_time": format_datetime(r.check_out_time),
                "total_working_minutes": r.total_working_minutes,
                "remarks": r.remarks,
            })

            # First check-in
            if r.check_in_time:
                if not d["first_check_in_time"] or r.check_in_time < d["first_check_in_time"]:
                    d["first_check_in_time"] = r.check_in_time
                    d['shift_name'] = r.assign_shift.shift_name if r.assign_shift else None
                    d["first_check_in"] = r.check_in_time
                    d["attendance_status"] = r.attendance_status
                    d["assign_shift"] = r.assign_shift
                    d["is_late"] = r.is_late
                    d["late_minutes"] = r.late_minutes
                    d["id"] = r.id

            # Last checkout
            if r.check_out_time:
                if not d["last_check_out_time"] or r.check_out_time > d["last_check_out_time"]:
                    d["last_check_out_time"] = r.check_out_time
                    d["last_check_out"] = r.check_out_time

            d["total_working_minutes"] += (r.total_working_minutes or 0)
            d["total_break_minutes"] += (r.break_duration_minutes or 0)

        return data

    @staticmethod
    def finalize_status(data):
        final = []

        for d in data.values():
            # Last login status
            if d["last_check_out_time"]:
                d["last_login_status"] = "checkout"
            elif d["first_check_in_time"]:
                d["last_login_status"] = "checkin"
            else:
                d["last_login_status"] = None

            # Time formatting for serializer
            d["check_in"] = (
                format_datetime(d["first_check_in_time"]) if d["first_check_in_time"] else None
            )

            d["shift_name"] = d['shift_name']
            
            d["check_out"] = (
                format_datetime(d["last_check_out_time"]) if d["last_check_out_time"] else None
            )

            d["production_hours"] = format_minutes(d["total_working_minutes"])
            d["break_duration"] = format_minutes(d["total_break_minutes"])
            d["late_minutes_display"] = format_minutes(d["late_minutes"])

            # Early exit
            if d["last_check_out_time"] and d["assign_shift"] and d["assign_shift"].end_time:
                d["is_early_exit"] = d["last_check_out_time"] < datetime.combine(
                    d["last_check_out_time"].date(), d["assign_shift"].end_time
                )
                d["early_exit_minutes"] = calculate_early_exit_minutes(
                    d["last_check_out_time"],
                    d["assign_shift"].end_time
                )

            d["attendance_date"] = format_date(d["attendance_date"])

            final.append(d)

        return final