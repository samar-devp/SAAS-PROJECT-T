# urls.py
from django.urls import path
from .views import *
from .additional_utility_views import *

urlpatterns = [
    path('attendance-check/<uuid:userid>', AttendanceCheckInOutAPIView.as_view(), name='attendance-checks'),
    path('employee-attendance/<uuid:admin_id>', FetchEmployeeAttendanceAPIView.as_view(), name='fetch-employee-attendance'),
    path('edit-attendance/<uuid:userid>/<int:attendance_id>', EditAttendanceAPIView.as_view(), name='edit-attendance'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', AttendanceDashboardAPIView.as_view(), name='attendance-dashboard'),
    path('employee-history/<str:org_id>/<str:employee_id>', EmployeeAttendanceHistoryAPIView.as_view(), name='employee-attendance-history'),
    path('summary/<str:org_id>', AttendanceSummaryAPIView.as_view(), name='attendance-summary'),
]
