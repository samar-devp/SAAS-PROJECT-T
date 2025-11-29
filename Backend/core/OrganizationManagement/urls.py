"""
Organization Management URLs
"""

from django.urls import path
from .views import (
    SubscriptionPlanAPIView, OrganizationSubscriptionAPIView,
    OrganizationModuleAPIView, OrganizationUsageAPIView,
    OrganizationDeactivationAPIView
)

urlpatterns = [
    # Subscription Plans
    path('plans', SubscriptionPlanAPIView.as_view(), name='subscription-plans'),
    path('plans/<uuid:pk>', SubscriptionPlanAPIView.as_view(), name='subscription-plan-detail'),
    
    # Organization Subscriptions
    path('subscriptions/<uuid:org_id>', OrganizationSubscriptionAPIView.as_view(), name='org-subscriptions'),
    
    # Organization Modules
    path('modules/<uuid:org_id>', OrganizationModuleAPIView.as_view(), name='org-modules'),
    path('modules/<uuid:org_id>/<uuid:pk>', OrganizationModuleAPIView.as_view(), name='org-module-detail'),
    
    # Organization Usage
    path('usage/<uuid:org_id>', OrganizationUsageAPIView.as_view(), name='org-usage'),
    
    # Organization Deactivation (Super Admin)
    path('deactivate/<uuid:org_id>', OrganizationDeactivationAPIView.as_view(), name='org-deactivate'),
]

