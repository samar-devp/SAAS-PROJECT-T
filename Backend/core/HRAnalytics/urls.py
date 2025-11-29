"""
HR Analytics URLs
"""

from django.urls import path
from .views import (
    CostCenterAPIView, AttendanceAnalyticsAPIView,
    AttritionRecordAPIView, SalaryDistributionAPIView
)
from .additional_utility_views import *

urlpatterns = [
    # Cost Centers
    path('cost-centers/<uuid:org_id>', CostCenterAPIView.as_view(), name='cost-centers'),
    path('cost-centers/<uuid:org_id>/<uuid:pk>', CostCenterAPIView.as_view(), name='cost-center-detail'),
    
    # Attendance Analytics
    path('attendance/<uuid:org_id>', AttendanceAnalyticsAPIView.as_view(), name='attendance-analytics'),
    
    # Attrition Records
    path('attrition/<uuid:org_id>', AttritionRecordAPIView.as_view(), name='attrition-records'),
    path('attrition/<uuid:org_id>/<uuid:pk>', AttritionRecordAPIView.as_view(), name='attrition-record-detail'),
    
    # Salary Distribution
    path('salary-distribution/<uuid:org_id>', SalaryDistributionAPIView.as_view(), name='salary-distribution'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', AnalyticsDashboardAPIView.as_view(), name='analytics-dashboard'),
]

