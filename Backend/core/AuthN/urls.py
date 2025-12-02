from django.urls import path
from .views import *
from .bulk_views import *
from .additional_views import *
from django.urls import path
from rest_framework_simplejwt.views import *

urlpatterns = [
    # ---AUTH---
    path("register/systemowner", SystemOwnerRegisterView.as_view(), name="systemowner-register"),
    path("register/organization", OrganizationRegisterView.as_view(), name="organization-register"),
    path("register/admin", AdminRegisterView.as_view(), name="admin-register"),
    path("register/user", UserRegisterView.as_view(), name="user-register"),
    path('login', LoginView.as_view(), name='login'),
    # ---COMMON CHANGE PASSWORD--- 
    path('change-password', ChangePasswordView.as_view(), name='change-password'),


    # ---ORGANIZATION UNDER OWNER----
    path("organizations", OrganizationsUnderSystemOwnerAPIView.as_view(), name="organizations-under-owner"),
    path("organizations/<uuid:org_id>", OrganizationsUnderSystemOwnerAPIView.as_view(), name="organizations-under-owner-detail"),
    path("organizations/<uuid:org_id>/upload-logo", OrganizationLogoUploadAPIView.as_view(), name="organization-upload-logo"),

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
    path('employee/<uuid:admin_id>', EmployeeListUnderAdminAPIView.as_view(), name='employee-list-under-admin'),
    path('employee/<uuid:admin_id>/<uuid:user_id>', EmployeeProfileUpdateAPIView.as_view(), name='employee-update'),
    
    # Employee Deactivate/Activate
    path('user_deactivate/<uuid:admin_id>/<uuid:user_id>', EmployeeDeactivateAPIView.as_view(), name='user_deactivate_api'),
    path('employee_deactivate/<uuid:admin_id>/<uuid:user_id>', EmployeeDeactivateAPIView.as_view(), name='employee_deactivate_api'),
    
    # Employee Profile Update
    path('employee_profile_update/<uuid:admin_id>/<uuid:user_id>', EmployeeProfileUpdateAPIView.as_view(), name='employee_profile_update_api'),
    
    # Employee Transfer
    path('emp_transfer/<str:org_id>', EmployeeTransferAPIView.as_view(), name='empTransfer'),
    
    
    # Deactivate List
    path('deactivate_list/<str:admin_id>', DeactivateUserListAPIView.as_view(), name='DeactivateUserApi'),
    path('deactivate_list_update/<str:admin_id>', DeactivateUserListAPIView.as_view(), name='DeactivateUserApi'),
    
    
    # Organization All Admin
    path('organization_all_admin/<str:orgID>', AllAdminsUnderOrganizationAPIView.as_view(), name='organization_all_admin'),
    
    # Organization's Own Admins (using logged-in organization)
    path('organization/admins', OrganizationOwnAdminsAPIView.as_view(), name='organization-own-admins'),
    path('organization/admins/<uuid:admin_id>', OrganizationOwnAdminsAPIView.as_view(), name='organization-own-admins-edit'),
    
    # Single Admin Details
    path('admin/<uuid:admin_id>', AdminDetailsAPIView.as_view(), name='admin-details'),
    
    
    # Employee Bulk Deactivate
    path('employee_bulk_deactivate/<str:clnID>', EmployeeBulkDeactivateAPIView.as_view(), name='employee_bulk_deactivate'),
    
    # Employee Global Search
    path('search_employee/<str:orgID>', EmployeeGlobalSearchAPIView.as_view(), name='EmployeeGlobalSearch'),
    
    # All Employees Under Organization
    

]
