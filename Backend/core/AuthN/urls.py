from django.urls import path
from .views.system_views import *
from .views.organization_views import *
from .views.admin_views import *
from .views.supervisor_views import *
from .views.employee_views import *

urlpatterns = [
    # ---SYSTEM-OWNER-REGISTRATION-AND-LOGIN-API---
    path('system-register', SystemOwnerRegisterView.as_view(), name='systemowner-register'),
    path('system-login', SystemOwnerLoginView.as_view(), name='systemowner-login'),

    # ---ORGANIZATION-REGISTRATION-AND-LOGIN-API---
    path('organization-register', OrganizationRegisterView.as_view(), name='organization-register'),
    path('organization-login', OrganizationLoginView.as_view(), name='organization-login'),

    # ---ADMIN-REGISTRATION-AND-LOGIN-API---
    path('admin-register', AdminRegisterView.as_view(), name='organization-register'),
    path('admin-login', AdminLoginView.as_view(), name='organization-register'),

    # ---SUPERVISOR-REGISTER-AND-LOGIN---
    path('supervisor-register', SupervisorRegisterView.as_view(), name='supervisor-register'),
    path('supervisor-login', SupervisorLoginView.as_view(), name='supervisor-login'),

    # ---EMPLOYEE-REGISTER-AND-LOGIN---
    path('employee-register', EmployeeRegisterView.as_view(), name='employee-register'),
    path('employee-login', EmployeeLoginView.as_view(), name='employee-login'),
]