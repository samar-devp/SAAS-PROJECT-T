from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import CustomUser, SystemOwnerProfile, OrganizationProfile, AdminProfile, UserProfile
from .serializers import SystemOwnerProfileSerializer, OrganizationProfileSerializer, AdminProfileSerializer, UserProfileSerializer
from .permissions import IsSystemOwner, IsOrganization, IsAdmin
from rest_framework_simplejwt.tokens import RefreshToken


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
        print(f"==>> user: {user}")

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
        user = request.user  # ✅ Get logged-in SystemOwner

        # ✅ Add system_owner to request data
        mutable_data = request.data.copy()
        mutable_data["admin"] = user.id

        serializer = self.get_serializer(data=mutable_data)
        if serializer.is_valid():
            profile = serializer.save()
            return Response(generate_tokens(profile.user), status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = CustomUser.objects.get(email=email)
            if user.check_password(password):
                return Response(generate_tokens(user), status=status.HTTP_200_OK)
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
