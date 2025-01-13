from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import SystemOwner
from ..serializers import SystemOwnerSerializer
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken

# ---SYSTEM-OWNER-REGISTRATION-AND-LOGIN-API---
class SystemOwnerRegisterView(APIView):
    def post(self, request):
        data = request.data
        if SystemOwner.objects.filter(email=data.get('email')).exists():
            return Response({"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)
        if SystemOwner.objects.filter(username=data.get('username')).exists():
            return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SystemOwnerSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Registration successful."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class SystemOwnerLoginView(APIView):
    """
    This view handles the login of a SystemOwner by verifying their username and password.
    If successful, a JWT token is generated for the user.
    """
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Check if username and password are provided
        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the SystemOwner by username
            user = SystemOwner.objects.get(username=username)

            # Check if user is active and password is correct
            if user.is_active and check_password(password, user.password):
                # Generate JWT tokens for the authenticated user
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Login successful.',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=status.HTTP_200_OK)

            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
        
        except SystemOwner.DoesNotExist:
            # If user does not exist, return an error
            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
