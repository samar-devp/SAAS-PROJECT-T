from django.urls import path
from .views import *
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *

urlpatterns = [
    # ---AUTH---
    path("register/systemowner", SystemOwnerRegisterView.as_view(), name="systemowner-register"),
    path("register/organization", OrganizationRegisterView.as_view(), name="organization-register"),
    path("register/admin", AdminRegisterView.as_view(), name="admin-register"),
    path("register/user", UserRegisterView.as_view(), name="user-register"),
    path('login', LoginView.as_view(), name='login'),
    # ---COMMON CHANGE PASSWORD--- 
    path('change-password', ChangePasswordView.as_view(), name='change-password'),

    # ---ORGANIZATION SETTING----
    path('organization-settings', OrganizationSettingsAPIView.as_view(), name='org-settings'),
    path('organization-settings/<uuid:org_id>', OrganizationSettingsAPIView.as_view(), name='org-settings-detail'),

    # ---ORGANIZATION UNDER OWNER----
    path("organizations", OrganizationsUnderSystemOwnerAPIView.as_view(), name="organizations-under-owner"),

    # ---SESSION INFO----
    path('session-info', SessionInfoAPIView.as_view(), name='session-info'),

    # ---FCM TOKEN UPDATE----
    path("fcm-token/<uuid:user_id>", UserFcmTokenUpdate.as_view(), name="update-fcm-token"),


]
