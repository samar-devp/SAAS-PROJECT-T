from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from ..models import *
from ..serializers import *
from rest_framework.exceptions import AuthenticationFailed
from ..tokens import *


# ---EMPLOYEE-REGISTER-AND-LOGIN---
class EmployeeRegisterView(APIView):
    def post(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({"error": "Authorization header missing or invalid."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Allow both Supervisor and Admin to create employees
            user = decode_jwt_token(auth_header, ["Supervisor", "Admin"])

            if not isinstance(user, (Supervisor, Admin)):
                return Response({"error": "Invalid user type."}, status=status.HTTP_400_BAD_REQUEST)

            data = request.data
            if isinstance(user,Admin):
                data['admin'] = user.id  # Associate employee with the current user (Supervisor/Admin)
            else:
                data['supervisor'] = user.id  # Associate employee with the current user (Supervisor/Admin)

            if Employee.objects.filter(email=data.get('email')).exists():
                return Response({"error": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)
            if Employee.objects.filter(username=data.get('username')).exists():
                return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = EmployeeSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Employee registered successfully."}, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class EmployeeLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            employee = Employee.objects.get(username=username)

            # Check if the password is correct
            if employee.is_active and check_password(password, employee.password):
                refresh = RefreshToken.for_user(employee)
                return Response({
                    'message': 'Login successful.',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=status.HTTP_200_OK)

            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)

        except Employee.DoesNotExist:
            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
