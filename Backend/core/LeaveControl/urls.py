from django.urls import path
from .views import *

urlpatterns = [
    path('leave-types/<uuid:admin_id>', LeaveTypeAPIView.as_view(), name='leave-type-list-create'),
    path('leave-types/<uuid:admin_id>/<int:pk>', LeaveTypeAPIView.as_view(), name='leave-type-detail'),
    path('leave-balances/<uuid:user_id>', EmployeeLeaveBalanceAPIView.as_view(), name='leave-balance-list-create'),
    path('leave-balances/<uuid:user_id>/<int:pk>', EmployeeLeaveBalanceAPIView.as_view(), name='leave-balance-detail'),
    path('leave-applications/<uuid:user_id>', LeaveApplicationAPIView.as_view(), name='leave-application-list-create'),
    path('leave-applications/<uuid:user_id>/<str:pk>', LeaveApplicationAPIView.as_view(), name='leave-application-detail'),
]
