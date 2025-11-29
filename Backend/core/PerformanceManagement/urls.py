"""
Performance Management URLs
"""

from django.urls import path
from .views import (
    GoalLibraryAPIView, OKRAPIView, KPIAPIView,
    ReviewCycleAPIView, PerformanceReviewAPIView
)
from .additional_utility_views import *

urlpatterns = [
    # Goal Library
    path('goals/<uuid:org_id>', GoalLibraryAPIView.as_view(), name='goal-library'),
    path('goals/<uuid:org_id>/<uuid:pk>', GoalLibraryAPIView.as_view(), name='goal-library-detail'),
    
    # OKRs
    path('okrs/<uuid:org_id>', OKRAPIView.as_view(), name='okrs'),
    path('okrs/<uuid:org_id>/<uuid:pk>', OKRAPIView.as_view(), name='okr-detail'),
    
    # KPIs
    path('kpis/<uuid:org_id>', KPIAPIView.as_view(), name='kpis'),
    path('kpis/<uuid:org_id>/<uuid:pk>', KPIAPIView.as_view(), name='kpi-detail'),
    
    # Review Cycles
    path('review-cycles/<uuid:org_id>', ReviewCycleAPIView.as_view(), name='review-cycles'),
    path('review-cycles/<uuid:org_id>/<uuid:pk>', ReviewCycleAPIView.as_view(), name='review-cycle-detail'),
    
    # Performance Reviews
    path('reviews/<uuid:org_id>', PerformanceReviewAPIView.as_view(), name='performance-reviews'),
    path('reviews/<uuid:org_id>/<uuid:pk>', PerformanceReviewAPIView.as_view(), name='performance-review-detail'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', PerformanceDashboardAPIView.as_view(), name='performance-dashboard'),
]

