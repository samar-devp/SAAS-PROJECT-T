from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from ..models import SystemOwner, Organization
from ..serializers import OrganizationSerializer
# from rest_framework_simplejwt.authentication import JWTAuthentication

# Organization Registration API (Only SystemOwner can register)
class OrganizationRegisterView(APIView):
    permission_classes = [IsAuthenticated]
    # authentication_classes = [JWTAuthentication]

    def post(self, request):
        user = request.user  # Extract the SystemOwner from the token

        if not isinstance(user, SystemOwner):
            return Response({"error": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user has permission (SystemOwner should be able to register an Organization)
        data = request.data
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


# Organization Login API (Only SystemOwner can authenticate the Organization)
class OrganizationLoginView(APIView):
    permission_classes = [IsAuthenticated]
    # authentication_classes = [JWTAuthentication]

    def post(self, request):
        # The SystemOwner token is used to authenticate and then access the Organization
        user = request.user  # This will be a valid SystemOwner after authentication
        
        if not isinstance(user, SystemOwner):
            return Response({"error": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data
        try:
            # Ensure the owner is the one logged in before returning Organization data
            organization = Organization.objects.get(username=data.get('username'), owner=user)
            
            # Check password for the organization (assuming the password is hashed in the same way as SystemOwner)
            if check_password(data.get('password'), organization.password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Organization login successful.',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'organization': {
                        'name': organization.organization_name,
                        'email': organization.email
                    }
                }, status=status.HTTP_200_OK)

            return Response({"error": "Invalid username or password for Organization."}, status=status.HTTP_401_UNAUTHORIZED)

        except Organization.DoesNotExist:
            return Response({"error": "Organization does not exist or incorrect username."}, status=status.HTTP_401_UNAUTHORIZED)
