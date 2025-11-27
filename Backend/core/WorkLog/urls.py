# urls.py
from django.urls import path
from .views import (
    AttendanceCheckInOutAPIView,
    FetchEmployeeAttendanceAPIView,
    EditAttendanceAPIView
)

urlpatterns = [
    path('attendance-check/<uuid:userid>', AttendanceCheckInOutAPIView.as_view(), name='attendance-checks'),
    path('employee-attendance/<uuid:admin_id>', FetchEmployeeAttendanceAPIView.as_view(), name='fetch-employee-attendance'),
    path('edit-attendance/<uuid:userid>/<int:attendance_id>', EditAttendanceAPIView.as_view(), name='edit-attendance'),
]
