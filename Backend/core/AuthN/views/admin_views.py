from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password
from ..models import *
from ..serializers import *
from ..tokens import *
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken

# ---ADMIN-REGISTRATION-AND-LOGIN-API---
class AdminRegisterView(APIView):

    def post(self, request):
        # Extract the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({"error": "Authorization header missing or invalid."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Decode the token and get the SystemOwner user object
            user = decode_jwt_token(auth_header, ["Organization"])

            if not isinstance(user, Organization):
                return Response({"error": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user has permission (SystemOwner should be able to register Admin)
            data = request.data
            data['organization'] = user.id  # Assuming SystemOwner has an organization field

            if Admin.objects.filter(email=data.get('email')).exists():
                return Response({"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)
            if Admin.objects.filter(username=data.get('username')).exists():
                return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

            # Create an Admin using the provided data
            serializer = AdminSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Admin registered successfully."}, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class AdminLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        try:
            admin = Admin.objects.get(username=username)
            
            # Check if the password is correct
            if admin.is_active and check_password(password, admin.password):
                refresh = RefreshToken.for_user(admin)
                refresh.payload
                return Response({
                    'message': 'Login successful.',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=status.HTTP_200_OK)
                
            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)

        except Admin.DoesNotExist:
            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)