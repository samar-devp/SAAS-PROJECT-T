from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from AuthN.models import AdminProfile

class LeaveTypeAPIView(APIView):
    def get(self, request, admin_id, pk=None):
        if pk:
            leave = get_object_or_404(LeaveType, admin__id=admin_id, id=pk, is_active=True)
            serializer = LeaveTypeSerializer(leave)
            return Response(serializer.data)
        leaves = LeaveType.objects.filter(admin__id=admin_id, is_active=True)
        serializer = LeaveTypeSerializer(leaves, many=True)
        return Response(serializer.data)

    def post(self, request, admin_id, pk=None):
        admin = get_object_or_404(AdminProfile, user_id=admin_id)
        print(f"==>> admin: {admin}")
        data = request.data.copy()
        data['admin'] = admin.user_id
        data['organization'] = admin.organization.id

        serializer = LeaveTypeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, admin_id, pk):
        leave = get_object_or_404(LeaveType, admin__id=admin_id, id=pk)
        serializer = LeaveTypeUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, admin_id, pk):
        leave = get_object_or_404(LeaveType, admin__id=admin_id, id=pk)
        serializer = LeaveTypeSerializer(leave, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, admin_id, pk):
        leave = get_object_or_404(LeaveType, admin__id=admin_id, id=pk)
        leave.is_active = False
        leave.save()
        return Response(status=status.HTTP_204_NO_CONTENT)



class EmployeeLeaveBalanceAPIView(APIView):
    def get(self, request, user_id, pk=None):
        if pk:
            balance = get_object_or_404(EmployeeLeaveBalance, user__id=user_id, id=pk, is_active=True)
            serializer = EmployeeLeaveBalanceSerializer(balance)
            return Response(serializer.data)
        balances = EmployeeLeaveBalance.objects.filter(user__id=user_id, is_active=True)
        serializer = EmployeeLeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)

    def post(self, request, user_id, pk=None):
        print(f"==>> user_id: {user_id}")
        # user = get_object_or_404(BaseUserModel, id=user_id, role='user')
        user = get_object_or_404(UserProfile, user_id=user_id)
        print(f"==>> user: {user.user_id}")
        print(f"==>> user: {user.admin_id}")
        data = request.data.copy()
        data['user'] = user.user_id
        data['admin'] = user.admin_id

        serializer = EmployeeLeaveBalanceSerializer(data=data)
        assigned = LeaveType.objects.get(id=data['leave_type']).default_count
        if int(data.get('used', 0)) > assigned:
            return Response(
                {"error": f"You cannot apply more than {assigned} leaves for this leave type."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, user_id, pk):
        leave_balance = get_object_or_404(EmployeeLeaveBalance, user__id=user_id, id=pk)
        serializer = EmployeeLeaveBalanceUpdateSerializer(leave_balance, data=request.data)
        if serializer.is_valid():
            assigned = LeaveType.objects.get(id=request.data['leave_type']).default_count
            if int(request.data.get('used', 0)) > assigned:
                return Response(
                    {"error": f"You cannot apply more than {assigned} leaves for this leave type."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id, pk):
        leave_balance = get_object_or_404(EmployeeLeaveBalance, user__id=user_id, id=pk)
        leave_balance.is_active = False
        leave_balance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LeaveApplicationAPIView(APIView):
    def get(self, request, user_id, pk=None):
        if pk:
            leave = get_object_or_404(LeaveApplication, user__id=user_id, id=pk)
            serializer = LeaveApplicationSerializer(leave)
            return Response(serializer.data)
        leaves = LeaveApplication.objects.filter(user__id=user_id)
        serializer = LeaveApplicationSerializer(leaves, many=True)
        return Response(serializer.data)

    def post(self, request, user_id, pk=None):
        user = get_object_or_404(UserProfile, user_id=user_id)
        data = request.data.copy()
        data['user'] = user.user_id
        data['admin'] = user.admin_id
        data['organization'] = user.organization_id

        from_date = data.get('from_date')
        to_date = data.get('to_date')

        if from_date and to_date:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            total_days = (to_date_obj - from_date_obj).days + 1
            data['total_days'] = total_days

            # Validate and fetch leave balance
            balance = EmployeeLeaveBalance.objects.filter(
                user__id=user_id,
                leave_type_id=data['leave_type'],
                year=from_date_obj.year,
                is_active=True
            ).first()

            if not balance:
                return Response({"error": "Leave balance not found."}, status=status.HTTP_400_BAD_REQUEST)
            
            if balance.balance < total_days:
                return Response({"error": "Not enough leave balance."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LeaveApplicationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            # Update used leave count
            if from_date and to_date and balance:
                balance.used += total_days
                balance.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, user_id, pk):
        leave = get_object_or_404(LeaveApplication, user__id=user_id, id=pk)
        serializer = LeaveApplicationUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
