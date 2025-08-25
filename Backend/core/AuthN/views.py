from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import *
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from .permissions import IsSystemOwner, IsOrganization, IsAdmin
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from utils.session_utils import *

def generate_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh_token": str(refresh),
        "access_token": str(refresh.access_token),
        "user_id": user.id,
        "role": user.role,
    }


class SystemOwnerRegisterView(generics.CreateAPIView):
    queryset = SystemOwnerProfile.objects.all()
    serializer_class = SystemOwnerProfileSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(generate_tokens(profile.user), status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationRegisterView(generics.CreateAPIView):
    queryset = OrganizationProfile.objects.all()
    serializer_class = OrganizationProfileSerializer
    permission_classes = [IsSystemOwner]

    def create(self, request, *args, **kwargs):
        user = request.user  # ✅ Get logged-in SystemOwner
        print(f"==>> user: {user.id}")

        # ✅ Add system_owner to request data
        mutable_data = request.data.copy()
        mutable_data["system_owner"] = user.id  

        serializer = self.get_serializer(data=mutable_data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(generate_tokens(profile.user), status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminRegisterView(generics.CreateAPIView):
    queryset = AdminProfile.objects.all()
    serializer_class = AdminProfileSerializer
    permission_classes = [IsOrganization]

    def create(self, request, *args, **kwargs):
        user = request.user  # ✅ Get logged-in SystemOwner

        # ✅ Add system_owner to request data
        mutable_data = request.data.copy()
        mutable_data["organization"] = user.id

        serializer = self.get_serializer(data=mutable_data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(generate_tokens(profile.user), status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegisterView(generics.CreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdmin]
    def create(self, request, *args, **kwargs):
        user = request.user  # Logged-in Admin

        # ✅ Ensure admin profile exists
        try:
            admin_profile = AdminProfile.objects.get(user_id=user.id)
        except AdminProfile.DoesNotExist:
            raise ValidationError({"detail": "Admin profile not found for this user."})

        # ✅ Get related organization
        organization = admin_profile.organization
        if not organization:
            raise ValidationError({"detail": "Admin is not linked to any organization."})

        # ✅ Modify request data
        mutable_data = request.data.copy()
        mutable_data["admin"] = user.id  # FK to BaseUserModel (admin)
        mutable_data["organization"] = organization.id  # FK to BaseUserModel (organization)

        # ✅ Validate and save
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()

        return Response(generate_tokens(profile.user), status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        try:
            user = BaseUserModel.objects.get(username=username)
            if user.check_password(password):
                return Response(generate_tokens(user), status=status.HTTP_200_OK)
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        except BaseUserModel.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        

class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password:
            return Response({"error": "Old password is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password:
            return Response({"error": "New password is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Optional: check old password
        if old_password and not user.check_password(old_password):
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)



# POST, PUT, PATCH, DELETE on specific org_id
class OrganizationSettingsAPIView(APIView):
    # permission_classes = [IsAuthenticated, IsOrganization]

    def get(self, request, org_id):
        settings = OrganizationSettings.objects.get(organization__id=org_id)
        serializer = OrganizationSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request, org_id):
        setting = OrganizationSettings.objects.get(organization__id=org_id)
        print(f"==>> setting: {setting}")
        serializer = OrganizationSettingsSerializer(setting, data=request.data)
        print(f"==>> serializer: {serializer}")
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationsUnderSystemOwnerAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSystemOwner]

    def get(self, request):
        user = request.user
        organizations = OrganizationProfile.objects.filter(system_owner=user)
        serializer = AllOrganizationProfileSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class SessionInfoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        log_user = request.user  

        if not log_user or not log_user.is_authenticated:
            return Response({"message": "Please provide a valid token.", "status": status.HTTP_401_UNAUTHORIZED})

        try:
            if log_user.role == "system_owner":
                profile = SystemOwnerProfile.objects.filter(user=log_user).first()
                data = {
                    "user_id": str(log_user.id),
                    "email": log_user.email,
                    "username": log_user.username,
                    "role": log_user.role,
                    "company_name": profile.company_name if profile else None,
                    "date_joined": log_user.date_joined,
                }
                msg = "System Owner authenticated"

            elif log_user.role == "organization":
                profile = OrganizationProfile.objects.filter(user=log_user).first()
                settings = OrganizationSettings.objects.filter(organization=log_user).first()
                data = {
                    "user_id": str(log_user.id),
                    "email": log_user.email,
                    "username": log_user.username,
                    "role": log_user.role,
                    "organization_name": profile.organization_name if profile else None,
                    "system_owner_id": str(profile.system_owner.id) if profile else None,
                    "settings": serialize_org_settings(settings),
                }
                msg = "Organization authenticated"

            elif log_user.role == "admin":
                profile = AdminProfile.objects.filter(user=log_user).first()
                org_settings = OrganizationSettings.objects.filter(organization=profile.organization).first() if profile else None
                data = {
                    "user_id": str(log_user.id),
                    "email": log_user.email,
                    "username": log_user.username,
                    "role": log_user.role,
                    "admin_name": profile.admin_name if profile else None,
                    "organization_id": str(profile.organization.id) if profile else None,
                    "organization_settings": serialize_org_settings(org_settings),
                }
                msg = "Admin authenticated"

            elif log_user.role == "user":
                profile = UserProfile.objects.filter(user=log_user).first()
                data = {
                    "user_id": str(log_user.id),
                    "email": log_user.email,
                    "username": log_user.username,
                    "role": log_user.role,
                    "user_name": profile.user_name if profile else None,
                    "organization_id": str(profile.organization.id) if profile else None,
                    "admin_id": str(profile.admin.id) if profile else None,
                    "user_type": profile.user_type if profile else None,
                    "designation": profile.designation if profile else None,
                    "job_title": profile.job_title if profile else None,
                }
                msg = "User authenticated"

            else:
                return Response({"message": "Invalid role", "status": status.HTTP_400_BAD_REQUEST})

            return Response({"success": True, "status": status.HTTP_200_OK, "message": msg, "data": data})

        except Exception as e:
            return Response({'message': str(e), 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})



class UserFcmTokenUpdate(APIView):
    """
    API to update User's FCM token
    """

    def put(self, request, user_id):  # <-- yaha user_id URL se aayega
        data = request.data

        # check required fields
        if not data.get("fcm_token"):
            return Response({"message": "Please provide fcm_token.", "status": status.HTTP_422_UNPROCESSABLE_ENTITY})
        try:
            user = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"message": "Invalid user_id", "status": status.HTTP_404_NOT_FOUND})

        # update token
        user.fcm_token = data["fcm_token"]
        user.save()
        return Response({"message": "Successfully updated the FCM token","data": {"user_id": user.id, "fcm_token": user.fcm_token},"status": status.HTTP_200_OK,})