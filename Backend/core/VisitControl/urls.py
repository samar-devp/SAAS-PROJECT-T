"""
Visit Management URLs
"""

from django.urls import path
from .views import (
    VisitAssignmentAPIView, VisitStartEndAPIView,
    VisitTemplateAPIView, VisitReportAPIView
)
from .additional_utility_views import *

urlpatterns = [
    path('visits/<uuid:admin_id>', VisitAssignmentAPIView.as_view(), name='visit-list-create'),
    path('visits/<uuid:admin_id>/<uuid:pk>', VisitAssignmentAPIView.as_view(), name='visit-detail'),
    path('visit-start-end/<uuid:visit_id>', VisitStartEndAPIView.as_view(), name='visit-start-end'),
    path('visit-templates/<uuid:admin_id>', VisitTemplateAPIView.as_view(), name='visit-template-list-create'),
    path('visit-templates/<uuid:admin_id>/<uuid:pk>', VisitTemplateAPIView.as_view(), name='visit-template-detail'),
    path('visit-reports/<uuid:admin_id>', VisitReportAPIView.as_view(), name='visit-reports'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', VisitDashboardAPIView.as_view(), name='visit-dashboard'),
    path('employee-visits/<str:org_id>/<str:employee_id>', EmployeeVisitListAPIView.as_view(), name='employee-visits'),
]

