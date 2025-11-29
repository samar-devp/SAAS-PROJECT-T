"""
Notification Management URLs
"""

from django.urls import path
from .views import (
    NotificationAPIView, NotificationPreferenceAPIView,
    NotificationMarkAllReadAPIView
)
from .additional_utility_views import *

urlpatterns = [
    path('notifications/<uuid:user_id>', NotificationAPIView.as_view(), name='notification-list-create'),
    path('notifications/<uuid:user_id>/<uuid:pk>', NotificationAPIView.as_view(), name='notification-detail'),
    path('notification-preferences/<uuid:user_id>', NotificationPreferenceAPIView.as_view(), name='notification-preferences'),
    path('notifications-mark-all-read/<uuid:user_id>', NotificationMarkAllReadAPIView.as_view(), name='notifications-mark-all-read'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', NotificationDashboardAPIView.as_view(), name='notification-dashboard'),
    path('user-notifications/<str:user_id>', UserNotificationsAPIView.as_view(), name='user-notifications'),
    path('user-notifications/<str:user_id>/<str:notification_id>', UserNotificationsAPIView.as_view(), name='mark-notification-read'),
]

