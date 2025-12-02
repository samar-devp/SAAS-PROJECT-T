"""
Leave Management URLs
Comprehensive leave management endpoints
"""

from django.urls import path
from .views import (
    LeaveTypeAPIView, EmployeeLeaveBalanceAPIView, LeaveApplicationAPIView
)
from .advanced_views import (
    LeavePolicyAPIView, AdvancedLeaveApplicationAPIView,
    LeaveApprovalAPIView, LeaveCancellationAPIView,
    CompensatoryOffAPIView, LeaveEncashmentAPIView,
    LeaveBalanceAdjustmentAPIView, LeaveAccrualProcessAPIView,
    LeaveCalendarAPIView, LeaveReportAPIView,
    LeaveExcelExportAPIView, LeaveSummaryDashboardAPIView
)
from .additional_utility_views import *

urlpatterns = [
    # LEAVE TYPES
    path('leave-types/<uuid:admin_id>', LeaveTypeAPIView.as_view(), name='leave-type-list-create'),
    path('leave-types/<uuid:admin_id>/<int:pk>', LeaveTypeAPIView.as_view(), name='leave-type-detail'),
    
    # LEAVE POLICIES (uses admin_id to get organization)
    path('leave-policies/<uuid:admin_id>', LeavePolicyAPIView.as_view(), name='leave-policy-list-create'),
    path('leave-policies/<uuid:admin_id>/<uuid:pk>', LeavePolicyAPIView.as_view(), name='leave-policy-detail'),
    
    # LEAVE BALANCES
    path('leave-balances/<uuid:user_id>', EmployeeLeaveBalanceAPIView.as_view(), name='leave-balance-list-create'),
    path('leave-balances/<uuid:user_id>/<int:pk>', EmployeeLeaveBalanceAPIView.as_view(), name='leave-balance-detail'),
    
    # LEAVE APPLICATIONS (Basic)
    path('leave-applications/<uuid:user_id>', LeaveApplicationAPIView.as_view(), name='leave-application-list-create'),
    path('leave-applications/<uuid:user_id>/<str:pk>', LeaveApplicationAPIView.as_view(), name='leave-application-detail'),
    
    # ADVANCED LEAVE APPLICATIONS
    path('advanced-leave-applications/<uuid:user_id>', AdvancedLeaveApplicationAPIView.as_view(), name='advanced-leave-application-create'),
    
    # LEAVE APPROVAL
    path('leave-approval/<uuid:application_id>', LeaveApprovalAPIView.as_view(), name='leave-approval'),
    
    # LEAVE CANCELLATION
    path('leave-cancellation/<uuid:application_id>', LeaveCancellationAPIView.as_view(), name='leave-cancellation'),
    
    # COMPENSATORY OFF
    path('compensatory-off/<uuid:admin_id>', CompensatoryOffAPIView.as_view(), name='comp-off-list-create'),
    path('compensatory-off/<uuid:admin_id>/<uuid:user_id>', CompensatoryOffAPIView.as_view(), name='comp-off-by-user'),
    path('compensatory-off/<uuid:admin_id>/<uuid:pk>', CompensatoryOffAPIView.as_view(), name='comp-off-detail'),
    
    # LEAVE ENCASHMENT
    path('leave-encashment/<uuid:admin_id>', LeaveEncashmentAPIView.as_view(), name='leave-encashment-list-create'),
    path('leave-encashment/<uuid:admin_id>/<uuid:user_id>', LeaveEncashmentAPIView.as_view(), name='leave-encashment-by-user'),
    path('leave-encashment/<uuid:admin_id>/<uuid:pk>', LeaveEncashmentAPIView.as_view(), name='leave-encashment-detail'),
    
    # LEAVE BALANCE ADJUSTMENT
    path('leave-balance-adjustment/<uuid:admin_id>', LeaveBalanceAdjustmentAPIView.as_view(), name='leave-balance-adjustment'),
    
    # LEAVE ACCRUAL PROCESSING
    path('leave-accrual-process/<uuid:admin_id>', LeaveAccrualProcessAPIView.as_view(), name='leave-accrual-process'),
    
    # LEAVE CALENDAR
    path('leave-calendar/<uuid:admin_id>', LeaveCalendarAPIView.as_view(), name='leave-calendar'),
    path('leave-calendar/<uuid:admin_id>/<int:month>/<int:year>', LeaveCalendarAPIView.as_view(), name='leave-calendar-month'),
    
    # LEAVE REPORTS
    path('leave-reports/<uuid:admin_id>', LeaveReportAPIView.as_view(), name='leave-reports'),
    
    # LEAVE EXCEL EXPORT
    path('leave-excel-export/<uuid:admin_id>', LeaveExcelExportAPIView.as_view(), name='leave-excel-export'),
    
    # LEAVE SUMMARY DASHBOARD
    path('leave-dashboard/<uuid:admin_id>', LeaveSummaryDashboardAPIView.as_view(), name='leave-dashboard'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', LeaveDashboardAPIView.as_view(), name='leave-dashboard-org'),
    path('leave-balances-list/<str:org_id>', EmployeeLeaveBalanceListAPIView.as_view(), name='leave-balances-list'),
    path('leave-balances-list/<str:org_id>/<str:employee_id>', EmployeeLeaveBalanceListAPIView.as_view(), name='leave-balances-list-by-employee'),
    path('applications-list/<str:org_id>', LeaveApplicationListAPIView.as_view(), name='leave-applications-list'),
]
