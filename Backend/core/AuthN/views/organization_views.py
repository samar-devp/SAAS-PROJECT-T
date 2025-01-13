from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from ..models import SystemOwner, Organization
from ..serializers import OrganizationSerializer
from rest_framework.exceptions import AuthenticationFailed
from ..tokens import *
# from rest_framework_simplejwt.authentication import JWTAuthentication


# ---ORGANIZATION-REGISTRATION-AND-LOGIN-API---
class OrganizationRegisterView(APIView):
    def post(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({"error": "Authorization header missing or invalid."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = decode_jwt_token(auth_header, ["SystemOwner"])

            if not isinstance(user, SystemOwner):
                return Response({"error": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user has permission (SystemOwner should be able to register an Organization)
            data = request.data
            data['owner'] = user.id
            if Organization.objects.filter(email=data.get('email')).exists():
                return Response({"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)
            if Organization.objects.filter(username=data.get('username')).exists():
                return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

            # Add the owner automatically from the authenticated SystemOwner
            data['owner'] = user.id

            serializer = OrganizationSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Organization registered successfully."}, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class OrganizationLoginView(APIView):
    """
    This view handles the login of an Organization by verifying its username and password.
    If successful, a JWT token is generated for the organization.
    """
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Check if username and password are provided
        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the Organization by username
            organization = Organization.objects.get(username=username)

            # Check if password is correct
            if check_password(password, organization.password):
                # Generate JWT tokens for the authenticated organization
                refresh = RefreshToken.for_user(organization)  # Assuming owner is a SystemOwner
                return Response({
                    'message': 'Organization login successful.',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'organization': {
                        'name': organization.organization_name,
                        'email': organization.email
                    }
                }, status=status.HTTP_200_OK)

            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Organization.DoesNotExist:
            # If the organization does not exist, return an error
            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)