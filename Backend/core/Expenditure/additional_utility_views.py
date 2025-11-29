"""
Additional Utility APIs for Expense Management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal

from .models import Expense, ExpenseCategory, ExpenseReimbursement, ExpenseBudget
from .serializers import ExpenseSerializer, ExpenseReimbursementSerializer
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class ExpenseListAPIView(APIView):
    """Get expenses list with filters"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            user_profiles = UserProfile.objects.filter(organization=organization)
            employee_ids = [p.user.id for p in user_profiles]
            
            expenses = Expense.objects.filter(employee_id__in=employee_ids)
            
            # Filters
            status_filter = request.query_params.get('status')
            category_id = request.query_params.get('category_id')
            employee_id = request.query_params.get('employee_id')
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            
            if status_filter:
                expenses = expenses.filter(status=status_filter)
            if category_id:
                expenses = expenses.filter(category_id=category_id)
            if employee_id:
                expenses = expenses.filter(employee_id=employee_id)
            if from_date:
                expenses = expenses.filter(expense_date__gte=from_date)
            if to_date:
                expenses = expenses.filter(expense_date__lte=to_date)
            
            expenses = expenses.order_by('-expense_date')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(expenses, request)
            
            serializer = ExpenseSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            # Summary
            total_amount = expenses.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            pending_amount = expenses.filter(status='pending').aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            
            pagination_data["summary"] = {
                "total_amount": float(total_amount),
                "pending_amount": float(pending_amount),
                "total_count": expenses.count()
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Expenses fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeExpenseListAPIView(APIView):
    """Get expenses for a specific employee"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, employee_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            expenses = Expense.objects.filter(employee=employee)
            
            status_filter = request.query_params.get('status')
            if status_filter:
                expenses = expenses.filter(status=status_filter)
            
            expenses = expenses.order_by('-expense_date')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(expenses, request)
            
            serializer = ExpenseSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Employee expenses fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExpenseReimbursementListAPIView(APIView):
    """Get reimbursement list"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            reimbursements = ExpenseReimbursement.objects.filter(organization=organization)
            
            status_filter = request.query_params.get('status')
            if status_filter:
                reimbursements = reimbursements.filter(status=status_filter)
            
            reimbursements = reimbursements.order_by('-created_at')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(reimbursements, request)
            
            serializer = ExpenseReimbursementSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Reimbursements fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

