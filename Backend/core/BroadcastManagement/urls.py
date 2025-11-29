"""
Broadcast Management URLs
"""

from django.urls import path
from .views import BroadcastAPIView, BroadcastRecipientAPIView
from .additional_utility_views import *

urlpatterns = [
    path('broadcasts/<uuid:org_id>', BroadcastAPIView.as_view(), name='broadcast-list-create'),
    path('broadcasts/<uuid:org_id>/<uuid:pk>', BroadcastAPIView.as_view(), name='broadcast-detail'),
    path('broadcast-recipients/<uuid:broadcast_id>', BroadcastRecipientAPIView.as_view(), name='broadcast-recipients'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', BroadcastDashboardAPIView.as_view(), name='broadcast-dashboard'),
    path('broadcasts-list/<str:org_id>', BroadcastListAPIView.as_view(), name='broadcasts-list'),
]

