"""
Visit Management URLs
"""

from django.urls import path
from .views import (
    VisitAPIView, VisitCheckInAPIView, VisitCheckOutAPIView, VisitStatsAPIView
)

urlpatterns = [
    # Visit CRUD Operations
    path('visit-list-create/<uuid:admin_id>', VisitAPIView.as_view(), name='visit-list-create'),
    path('visit-list-create-by-user/<uuid:admin_id>/<uuid:user_id>', VisitAPIView.as_view(), name='visit-list-create-by-user'),
    path('visit-detail-update-delete/<uuid:admin_id>/<uuid:user_id>/<int:pk>', VisitAPIView.as_view(), name='visit-detail-update-delete'),
    
    # Check-in/Check-out Operations
    path('visit-check-in/<uuid:admin_id>/<uuid:user_id>/<int:visit_id>', VisitCheckInAPIView.as_view(), name='visit-check-in'),
    path('visit-check-out/<uuid:admin_id>/<uuid:user_id>/<int:visit_id>', VisitCheckOutAPIView.as_view(), name='visit-check-out'),
    
    # Statistics
    path('visit-stats/<uuid:admin_id>', VisitStatsAPIView.as_view(), name='visit-stats'),
    path('visit-stats-by-user/<uuid:admin_id>/<uuid:user_id>', VisitStatsAPIView.as_view(), name='visit-stats-by-user'),
]
