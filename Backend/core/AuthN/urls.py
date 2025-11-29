from django.urls import path
from .views import *
from .bulk_views import *
from .additional_views import *
from .dashboard_views import *
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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

    # ---BULK REGISTRATION----
    path("bulk-register/employees/<uuid:admin_id>", BulkEmployeeRegistrationAPIView.as_view(), name="bulk-employee-register"),
    path("bulk-register/admins/<uuid:org_id>", BulkAdminRegistrationAPIView.as_view(), name="bulk-admin-register"),
    path("bulk-register/download/employee-sample", DownloadEmployeeSampleCSVAPIView.as_view(), name="download-employee-sample"),
    path("bulk-register/download/admin-sample", DownloadAdminSampleCSVAPIView.as_view(), name="download-admin-sample"),

    # ---ADDITIONAL UTILITY APIS----
    # Change Password for All Roles
    path('change-password/<uuid:user_id>', ChangePasswordAllRolesAPIView.as_view(), name='change-password-all-roles'),
    
    # Employee Lists
    path('employee/<str:org_id>', EmployeeListUnderAdminAPIView.as_view(), name='employee-list-under-admin'),
    path('employee/<str:org_id>/<str:unqID>', EmployeeProfileUpdateAPIView.as_view(), name='employee-update'),
    
    # Employee Deactivate/Activate
    path('user_deactivate/<str:org_id>/<str:unqID>', EmployeeDeactivateAPIView.as_view(), name='user_deactivate_api'),
    path('employee_deactivate/<str:org_id>/<str:unqID>', EmployeeDeactivateAPIView.as_view(), name='employee_deactivate_api'),
    
    # Employee Profile Update
    path('employee_profile_update/<str:org_id>/<str:unqID>', EmployeeProfileUpdateAPIView.as_view(), name='employee_profile_update_api'),
    
    # Employee Transfer
    path('emp_transfer/<str:org_id>', EmployeeTransferAPIView.as_view(), name='empTransfer'),
    
    # Admin Details CSV
    path('admin_detail_csv/<str:org_id>', AdminDetailCSVAPIView.as_view(), name='adminDetailCsv'),
    
    # Deactivate List
    path('deactivate_list/<str:org_id>/<str:clnID>', DeactivateUserListAPIView.as_view(), name='DeactivateUserApi'),
    path('deactivate_list/<str:org_id>', DeactivateUserListAPIView.as_view(), name='DeactivateUserApi'),
    path('deactivate_list_update/<str:clnID>', DeactivateUserListAPIView.as_view(), name='DeactivateUserApi'),
    
    # All User List Info
    path('all_user_list_info/<str:userID>', AllUserListInfoAPIView.as_view(), name='all_user_list_info'),
    path('all_user_device_info/<str:userID>', AllUserDeviceInfoAPIView.as_view(), name='all_user_device_info'),
    
    # Organization All Admin
    path('organization_all_admin/<str:orgID>', AllAdminsUnderOrganizationAPIView.as_view(), name='organization_all_admin'),
    
    # Employee Status Update
    path('employee_status_update/<str:clnID>/<str:date>', EmployeeStatusUpdateAPIView.as_view(), name='EmployeeDailyUpdate'),
    path('employee_fencing_update/<str:clnID>/<str:unqID>', UpdateAllowFencingAPIView.as_view(), name='EmployeeFencingUpdate'),
    
    # All Employee Profile
    path('employee_profile/<str:clnID>', AllEmployeeProfileAPIView.as_view(), name='AllEmployeeProfile'),
    
    # Employee Bulk Deactivate
    path('employee_bulk_deactivate/<str:clnID>', EmployeeBulkDeactivateAPIView.as_view(), name='employee_bulk_deactivate'),
    
    # Employee Global Search
    path('search_employee/<str:orgID>', EmployeeGlobalSearchAPIView.as_view(), name='EmployeeGlobalSearch'),
    
    # All Employees Under Organization
    path('all_employees/<str:org_id>', AllEmployeesUnderOrganizationAPIView.as_view(), name='all-employees-org'),
    
    # Dashboard APIs
    path('dashboard/organization/<str:org_id>', OrganizationDashboardAPIView.as_view(), name='organization-dashboard'),
    path('dashboard/admin/<str:admin_id>', AdminDashboardAPIView.as_view(), name='admin-dashboard'),

]
