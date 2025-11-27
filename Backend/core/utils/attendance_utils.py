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