from django.urls import path
from .views import (
    LocationHistoryAPIView,
    LiveLocationAPIView,
    LocationUpdateAPIView
)

urlpatterns = [
    path('location-history/<uuid:user_id>/', LocationHistoryAPIView.as_view(), name='location-history'),
    path('live-location/', LiveLocationAPIView.as_view(), name='live-location'),
    path('location-update/', LocationUpdateAPIView.as_view(), name='location-update'),
]

