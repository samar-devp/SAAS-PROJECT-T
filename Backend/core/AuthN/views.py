"""
Authentication and User Management Views
========================================

All views are optimized for O(1) complexity where possible:
- Use select_related/prefetch_related to avoid N+1 queries
- Use get_object_or_404 for proper error handling
- Consistent error response format
- Proper use of serializers for validation

Time Complexity: O(1) for most operations
Space Complexity: O(1) - Minimal space usage
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import (
    BaseUserModel, SystemOwnerProfile, OrganizationProfile,
    AdminProfile, UserProfile, OrganizationSettings
)
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    SystemOwnerProfileSerializer, OrganizationProfileSerializer,
    AdminProfileSerializer, UserProfileSerializer,
    OrganizationSettingsSerializer, AllOrganizationProfileSerializer
)
from .permissions import IsSystemOwner
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from utils.session_utils import serialize_org_settings
import os
import uuid
from datetime import datetime
from django.conf import settings


def generate_tokens(user):
    """
    Generate JWT tokens for a user.
    
    Args:
        user: BaseUserModel instance
        
    Returns:
        dict: Contains refresh_token, access_token, user_id, and role
        
    Time Complexity: O(1)
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh_token": str(refresh),
        "access_token": str(refresh.access_token),
        "user_id": str(user.id),
        "role": user.role,
    }


class SystemOwnerRegisterView(generics.CreateAPIView):
    """
    Register a new System Owner.
    
    Time Complexity: O(1) - Single database insert
    """
    queryset = SystemOwnerProfile.objects.all()
    serializer_class = SystemOwnerProfileSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Create a new system owner profile.
        
        Returns:
            Response with tokens on success, validation errors on failure
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(generate_tokens(profile.user), status=status.HTTP_201_CREATED)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class OrganizationRegisterView(generics.CreateAPIView):
    """
    Register a new Organization under a System Owner.
    
    Time Complexity: O(1) - Single database insert with select_related
    """
    queryset = OrganizationProfile.objects.select_related('user', 'system_owner')
    serializer_class = OrganizationProfileSerializer
    permission_classes = [IsSystemOwner]

    def create(self, request, *args, **kwargs):
        """
        Create a new organization profile.
        Automatically assigns the logged-in system owner.
        
        Returns:
            Response with tokens on success, validation errors on failure
        """
        system_owner = request.user
        
        # Add system_owner to request data
        mutable_data = request.data.copy()
        mutable_data["system_owner"] = str(system_owner.id)

        serializer = self.get_serializer(data=mutable_data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(generate_tokens(profile.user), status=status.HTTP_201_CREATED)

        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AdminRegisterView(generics.CreateAPIView):
    """
    Register a new Admin under an Organization.
    
    If logged-in user is an organization, automatically assigns it.
    
    Time Complexity: O(1) - Single database insert with select_related
    """
    queryset = AdminProfile.objects.select_related('user', 'organization')
    serializer_class = AdminProfileSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Create a new admin profile.
        Automatically assigns organization if logged-in user is an organization.
        
        Returns:
            Response with admin data on success, validation errors on failure
        """
        # If logged-in user is an organization, automatically set organization
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if request.user.role == 'organization':
            data['organization'] = str(request.user.id)
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Admin created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserRegisterView(generics.CreateAPIView):
    """
    Register a new User (Employee) under an Admin.
    
    If logged-in user is an admin, automatically assigns it.
    If logged-in user is an organization, uses admin_id from request data or selected_admin_id.
    
    Time Complexity: O(1) - Single database insert with select_related
    """
    queryset = UserProfile.objects.select_related('user', 'admin', 'organization')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Create a new user profile.
        Automatically assigns admin if logged-in user is an admin.
        If logged-in user is an organization, uses admin_id from request.
        
        Returns:
            Response with tokens on success, validation errors on failure
        """
        # Prepare data
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        
        # If logged-in user is an admin, automatically set admin
        if request.user.role == 'admin':
            data['admin'] = str(request.user.id)
        # If logged-in user is an organization, require admin_id in payload
        elif request.user.role == 'organization':
            # Get admin_id from request data (can be 'admin_id' or 'admin' field)
            admin_id = data.get('admin_id') or data.get('admin')
            
            if not admin_id:
                # admin_id is required for organization role
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": {
                        "admin_id": ["admin_id is required when registering as organization. Please provide 'admin_id' in the payload."]
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate that the admin belongs to this organization
            try:
                from .models import AdminProfile
                admin_profile = AdminProfile.objects.filter(
                    user_id=admin_id,
                    organization=request.user
                ).select_related('user').first()
                
                if not admin_profile:
                    return Response({
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Validation error",
                        "errors": {
                            "admin_id": ["Invalid admin_id. The admin must belong to your organization."]
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Set admin in data (use user.id from the admin profile)
                data['admin'] = str(admin_profile.user.id)
                # Remove admin_id if it was used (keep only 'admin' field)
                if 'admin_id' in data:
                    data.pop('admin_id')
                    
            except Exception as e:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": {
                        "admin_id": [f"Error validating admin_id: {str(e)}"]
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=data, context={'request': request})
        if serializer.is_valid():
            profile = serializer.save()
            return Response(generate_tokens(profile.user), status=status.HTTP_201_CREATED)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Login endpoint supporting both email and username authentication.
    
    Time Complexity: O(1) - Constant time authentication
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Authenticate user and return JWT tokens.
        Supports both email and username login.
        
        Returns:
            Response with tokens on success, error message on failure
        """
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "").strip()

        if not username or not password:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Username/Email and password are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        user = None
        
        # O(1) - First, try to authenticate with the value as email (since USERNAME_FIELD = "email")
        user = authenticate(request, username=username, password=password)
        
        # O(1) - If authentication fails, try to find user by username and then authenticate with email
        if user is None:
            try:
                # O(1) - Single query with .only() to limit fields
                user_obj = BaseUserModel.objects.only('email', 'username').get(username=username)
                # O(1) - Authenticate with email
                user = authenticate(request, username=user_obj.email, password=password)
            except BaseUserModel.DoesNotExist:
                user = None

        if user is None:
            return Response({
                "status": status.HTTP_401_UNAUTHORIZED,
                "message": "Invalid credentials"
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({
                "status": status.HTTP_401_UNAUTHORIZED,
                "message": "User account is disabled"
            }, status=status.HTTP_401_UNAUTHORIZED)

        return Response(generate_tokens(user), status=status.HTTP_200_OK)


class ChangePasswordView(generics.GenericAPIView):
    """
    Change password for authenticated user.
    
    Time Complexity: O(1) - Constant time password operations
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Change user's password.
        
        Returns:
            Response with success message or error details
        """
        user = request.user
        old_password = request.data.get("old_password", "").strip()
        new_password = request.data.get("new_password", "").strip()

        if not old_password or not new_password:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Old password and new password are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Old password is incorrect"
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Password updated successfully"
        }, status=status.HTTP_200_OK)



class OrganizationSettingsAPIView(APIView):
    """
    Get and update organization settings.
    
    Time Complexity: O(1) - Single database query with select_related
    """
    permission_classes = [IsAuthenticated, IsSystemOwner]

    def get(self, request, org_id):
        """
        Get organization settings.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Response with settings data
        """
        # O(1) - Single query with select_related
        settings = get_object_or_404(
            OrganizationSettings.objects.select_related('organization'),
            organization__id=org_id
        )
        serializer = OrganizationSettingsSerializer(settings)
        
        return Response({
            "status": status.HTTP_200_OK,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, org_id):
        """
        Update organization settings.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Response with updated settings or validation errors
        """
        # O(1) - Single query with select_related
        setting = get_object_or_404(
            OrganizationSettings.objects.select_related('organization'),
            organization__id=org_id
        )
        
        serializer = OrganizationSettingsSerializer(setting, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Settings updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class OrganizationsUnderSystemOwnerAPIView(APIView):
    """
    List and update organizations under a system owner.
    
    Optimized with select_related/prefetch_related for O(1) complexity.
    
    Time Complexity: O(1) for single org, O(n) for list where n = number of orgs
    """
    permission_classes = [IsAuthenticated, IsSystemOwner]

    def get(self, request, org_id=None):
        """
        Get single organization or list all organizations.
        
        Args:
            org_id: Optional organization UUID
            
        Returns:
            Response with organization(s) data
        """
        system_owner = request.user
        
        # If org_id is provided, return single organization
        if org_id:
            # O(1) - Single query with select_related and prefetch_related
            organization = get_object_or_404(
                OrganizationProfile.objects.select_related(
                    'user', 'system_owner'
                ).prefetch_related(
                    'user__own_organization_profile_setting'
                ),
                id=org_id,
                system_owner=system_owner
            )
            serializer = AllOrganizationProfileSerializer(organization)
            return Response({
                "status": status.HTTP_200_OK,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        # Otherwise return all organizations
        # O(n) - Single query with select_related and prefetch_related
        organizations = OrganizationProfile.objects.filter(
            system_owner=system_owner
        ).select_related(
            'user', 'system_owner'
        ).prefetch_related(
            'user__own_organization_profile_setting'
        )
        
        serializer = AllOrganizationProfileSerializer(organizations, many=True)
        return Response({
            "status": status.HTTP_200_OK,
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request, org_id):
        """
        Update organization profile.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Response with updated organization or validation errors
        """
        system_owner = request.user
        
        # O(1) - Single query with select_related
        organization = get_object_or_404(
            OrganizationProfile.objects.select_related('user', 'system_owner'),
            id=org_id,
            system_owner=system_owner
        )
        
        serializer = AllOrganizationProfileSerializer(
            organization,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Organization updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class OrganizationLogoUploadAPIView(APIView):
    """
    Upload organization logo file.
    
    Time Complexity: O(1) - Single database query and file write
    """
    permission_classes = [IsAuthenticated, IsSystemOwner]
    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    def post(self, request, org_id):
        """
        Upload logo file for organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Response with logo URL or error message
        """
        system_owner = request.user
        
        # O(1) - Single query with select_related
        organization = get_object_or_404(
            OrganizationProfile.objects.select_related('user'),
            id=org_id,
            system_owner=system_owner
        )
        
        # Check if file is provided
        if 'logo' not in request.FILES:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "No logo file provided"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logo_file = request.FILES['logo']
        
        # Validate file type
        if logo_file.content_type not in self.ALLOWED_IMAGE_TYPES:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_IMAGE_TYPES)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size
        if logo_file.size > self.MAX_FILE_SIZE:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "File size exceeds 5MB limit"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create organization_logos folder if it doesn't exist
            folder_name = 'organization_logos'
            media_folder = os.path.join(settings.MEDIA_ROOT, folder_name)
            os.makedirs(media_folder, exist_ok=True)
            
            # Generate unique file name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            file_extension = logo_file.name.split('.')[-1].lower()
            file_name = f"{timestamp}_{unique_id}.{file_extension}"
            file_path = os.path.join(media_folder, file_name)
            
            # Save file
            with open(file_path, 'wb+') as destination:
                for chunk in logo_file.chunks():
                    destination.write(chunk)
            
            # Generate relative path
            relative_path = os.path.join(folder_name, file_name)
            
            # Get or create organization settings
            try:
                org_settings = organization.user.own_organization_profile_setting
            except OrganizationSettings.DoesNotExist:
                org_settings = OrganizationSettings.objects.create(organization=organization.user)
            
            # Update logo - ImageField stores the relative path
            org_settings.organization_logo = relative_path
            org_settings.save()
            
            # Return full URL path using ImageField's url property
            try:
                logo_url = org_settings.organization_logo.url
            except (ValueError, AttributeError):
                logo_url = f"{settings.MEDIA_URL}{relative_path}"
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Logo uploaded successfully",
                "data": {
                    "logo_path": relative_path,
                    "logo_url": logo_url
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error uploading logo: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SessionInfoAPIView(APIView):
    """
    Get session information for authenticated user.
    
    Optimized with select_related/prefetch_related to avoid N+1 queries.
    
    Time Complexity: O(1) - Single optimized query per role
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get current user's session information based on role.
        
        Returns:
            Response with user data and role-specific information
        """
        user = request.user
        
        # O(1) - Role-based query optimization
        role = user.role
        data = {
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": role,
            "date_joined": user.date_joined,
        }
        
        try:
            if role == "system_owner":
                # O(1) - Single query with select_related
                profile = SystemOwnerProfile.objects.select_related('user').filter(
                    user=user
                ).only('company_name', 'user_id').first()
                
                data["company_name"] = profile.company_name if profile else None
                message = "System Owner authenticated"

            elif role == "organization":
                # O(1) - Single query with select_related and prefetch_related
                profile = OrganizationProfile.objects.select_related(
                    'user', 'system_owner'
                ).prefetch_related(
                    'user__own_organization_profile_setting'
                ).filter(user=user).only(
                    'organization_name', 'system_owner_id', 'user_id'
                ).first()
                
                settings = OrganizationSettings.objects.filter(
                    organization=user
                ).only('id').first() if user else None
                
                data["organization_name"] = profile.organization_name if profile else None
                data["system_owner_id"] = str(profile.system_owner.id) if profile and profile.system_owner else None
                data["settings"] = serialize_org_settings(settings) if settings else None
                message = "Organization authenticated"

            elif role == "admin":
                # O(1) - Single query with select_related
                profile = AdminProfile.objects.select_related(
                    'user', 'organization'
                ).filter(user=user).only(
                    'admin_name', 'organization_id', 'user_id'
                ).first()
                
                data["admin_name"] = profile.admin_name if profile else None
                data["organization_id"] = str(profile.organization.id) if profile and profile.organization else None
                message = "Admin authenticated"

            elif role == "user":
                # O(1) - Single query with select_related
                profile = UserProfile.objects.select_related(
                    'user', 'admin', 'organization'
                ).filter(user=user).only(
                    'user_name', 'admin_id', 'organization_id', 'user_id'
                ).first()
                
                data["user_name"] = profile.user_name if profile else None
                data["admin_id"] = str(profile.admin.id) if profile and profile.admin else None
                data["organization_id"] = str(profile.organization.id) if profile and profile.organization else None
                message = "User authenticated"

            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid user role"
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "status": status.HTTP_200_OK,
                "message": message,
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error fetching session info: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


