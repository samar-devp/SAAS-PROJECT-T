from django.urls import path
from .views.system_views import *
from .views.organization_views import *

urlpatterns = [
    # ---SYSTEM-OWNER-REGISTRATION-AND-LOGIN-API---
    path('system-register', SystemOwnerRegisterView.as_view(), name='systemowner-register'),
    path('system-login', SystemOwnerLoginView.as_view(), name='systemowner-login'),
    # ---ORGANIZATION-REGISTRATION-AND-LOGIN-API---
    path('organization-register', OrganizationRegisterView.as_view(), name='organization-register'),
    path('organization-login', OrganizationLoginView.as_view(), name='organization-login'),
]