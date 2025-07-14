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
        print(f"==>> user: {user}")

        # # ✅ Check if the user is a system owner
        # if user.role != 'system_owner':
        #     return Response({"detail": "You are not authorized to access this data."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ Get all organizations under this system owner
        organizations = OrganizationProfile.objects.filter(system_owner=user)

        # ✅ Serialize and return
        serializer = AllOrganizationProfileSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)