from datetime import datetime, timedelta
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