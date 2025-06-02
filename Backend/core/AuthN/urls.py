from django.urls import path
from .views import *
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *

urlpatterns = [
    path("register/systemowner", SystemOwnerRegisterView.as_view(), name="systemowner-register"),
    path("register/organization", OrganizationRegisterView.as_view(), name="organization-register"),
    path("register/admin", AdminRegisterView.as_view(), name="admin-register"),
    path("register/user", UserRegisterView.as_view(), name="user-register"),
    path('login', LoginView.as_view(), name='login'),

    
]
