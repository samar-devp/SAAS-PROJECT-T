"""
Advanced Expense Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
import traceback

from .models import (
    ExpenseCategory, Expense, ExpensePolicy,
    ExpenseApprovalWorkflow, ExpenseReimbursement,
    ExpenseBudget, ExpenseReport
)
from .serializers import (
    ExpenseCategorySerializer, ExpenseCategoryUpdateSerializer,
    ExpenseSerializer, ExpensePolicySerializer,
    ExpenseApprovalWorkflowSerializer, ExpenseReimbursementSerializer,
    ExpenseBudgetSerializer, ExpenseReportSerializer
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class ExpenseCategoryAPIView(APIView):
    """Expense Category CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id, pk=None):
        """Get categories"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if pk:
                category = get_object_or_404(ExpenseCategory, id=pk, admin=admin, is_active=True)
                serializer = ExpenseCategorySerializer(category)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Category fetched successfully",
                    "data": serializer.data
                })
            else:
                categories = ExpenseCategory.objects.filter(admin=admin, is_active=True)
                serializer = ExpenseCategorySerializer(categories, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Categories fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, admin_id):
        """Create category"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            data = request.data.copy()
            data['admin'] = str(admin.id)
            data['organization'] = str(admin.own_admin_profile.organization.id)
            
            serializer = ExpenseCategorySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Category created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, admin_id, pk):
        """Update category"""
        try:
            category = get_object_or_404(ExpenseCategory, id=pk, admin_id=admin_id)
            serializer = ExpenseCategoryUpdateSerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Category updated successfully",
                    "data": serializer.data
                })
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, admin_id, pk):
        """Delete category"""
        try:
            category = get_object_or_404(ExpenseCategory, id=pk, admin_id=admin_id)
            category.is_active = False
            category.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Category deleted successfully"
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExpenseAPIView(APIView):
    """Expense CRUD"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id, pk=None):
        """Get expenses"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if pk:
                expense = get_object_or_404(Expense, id=pk, admin=admin)
                serializer = ExpenseSerializer(expense)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Expense fetched successfully",
                    "data": serializer.data
                })
            else:
                queryset = Expense.objects.filter(admin=admin)
                
                # Filters
                status_filter = request.query_params.get('status')
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                
                employee_id = request.query_params.get('employee_id')
                if employee_id:
                    queryset = queryset.filter(employee_id=employee_id)
                
                category_id = request.query_params.get('category_id')
                if category_id:
                    queryset = queryset.filter(category_id=category_id)
                
                date_from = request.query_params.get('date_from')
                if date_from:
                    queryset = queryset.filter(expense_date__gte=date_from)
                
                date_to = request.query_params.get('date_to')
                if date_to:
                    queryset = queryset.filter(expense_date__lte=date_to)
                
                # Pagination
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = ExpenseSerializer(paginated_qs, many=True)
                pagination_data = paginator.get_paginated_response(serializer.data)
                pagination_data["results"] = serializer.data
                pagination_data["message"] = "Expenses fetched successfully"
                
                return Response(pagination_data)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, admin_id):
        """Create expense"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            data = request.data.copy()
            data['admin'] = str(admin.id)
            data['organization'] = str(admin.own_admin_profile.organization.id)
            data['created_by'] = str(request.user.id)
            
            # Calculate tax amounts
            amount = Decimal(str(data.get('amount', 0)))
            category = get_object_or_404(ExpenseCategory, id=data.get('category'))
            
            amount_before_tax = amount
            gst_amount = Decimal('0.00')
            tds_amount = Decimal('0.00')
            
            if category.gst_applicable:
                gst_amount = (amount * category.gst_rate) / 100
                amount_before_tax = amount / (1 + category.gst_rate / 100)
            
            if category.tds_applicable:
                tds_amount = (amount * category.tds_rate) / 100
            
            total_amount = amount - tds_amount
            
            data['amount_before_tax'] = float(amount_before_tax)
            data['gst_amount'] = float(gst_amount)
            data['tds_amount'] = float(tds_amount)
            data['tax_amount'] = float(gst_amount)
            data['total_amount'] = float(total_amount)
            
            serializer = ExpenseSerializer(data=data)
            if serializer.is_valid():
                expense = serializer.save()
                
                # Create approval workflow if needed
                if category.requires_approval:
                    from .models import ExpenseApprovalWorkflow
                    from AuthN.models import BaseUserModel
                    
                    # Get approval policy
                    policy = ExpensePolicy.objects.filter(
                        organization=expense.organization,
                        is_active=True,
                        effective_from__lte=expense.expense_date
                    ).order_by('-effective_from').first()
                    
                    if policy:
                        # Determine approval levels based on amount
                        approval_levels = []
                        
                        if expense.total_amount > (policy.requires_finance_approval_above or Decimal('999999')):
                            # Need finance approval
                            # Get finance team members (you can customize this logic)
                            finance_users = BaseUserModel.objects.filter(
                                role='admin',
                                organization=expense.organization
                            )[:1]  # Get first admin as finance approver
                            for user in finance_users:
                                approval_levels.append({'level': 3, 'approver': user})
                        
                        elif expense.total_amount > (policy.requires_manager_approval_above or Decimal('999999')):
                            # Need manager approval
                            # Get employee's manager (you can customize this logic)
                            manager = expense.employee.own_user_profile.manager if hasattr(expense.employee.own_user_profile, 'manager') else None
                            if manager:
                                approval_levels.append({'level': 2, 'approver': manager})
                        
                        else:
                            # Default approval - direct manager or admin
                            manager = expense.employee.own_user_profile.manager if hasattr(expense.employee.own_user_profile, 'manager') else None
                            if manager:
                                approval_levels.append({'level': 1, 'approver': manager})
                            else:
                                # Fallback to admin
                                admin_users = BaseUserModel.objects.filter(
                                    role='admin',
                                    organization=expense.organization
                                )[:1]
                                for user in admin_users:
                                    approval_levels.append({'level': 1, 'approver': user})
                        
                        # Create approval workflow entries
                        for approval_info in approval_levels:
                            ExpenseApprovalWorkflow.objects.create(
                                expense=expense,
                                approver=approval_info['approver'],
                                level=approval_info['level'],
                                status='pending'
                            )
                        
                        expense.status = 'pending'
                        expense.save()
                    else:
                        # No policy, default to pending
                        expense.status = 'pending'
                        expense.save()
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Expense created successfully",
                    "data": ExpenseSerializer(expense).data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def put(self, request, admin_id, pk):
        """Update expense"""
        try:
            expense = get_object_or_404(Expense, id=pk, admin_id=admin_id)
            serializer = ExpenseSerializer(expense, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Expense updated successfully",
                    "data": serializer.data
                })
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExpenseApprovalAPIView(APIView):
    """Expense Approval"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, expense_id):
        """Approve or reject expense"""
        try:
            expense = get_object_or_404(Expense, id=expense_id)
            action = request.data.get('action')  # 'approve' or 'reject'
            comments = request.data.get('comments', '')
            
            if action == 'approve':
                expense.status = 'approved'
                expense.approved_by = request.user
                expense.approved_at = timezone.now()
                expense.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Expense approved successfully",
                    "data": ExpenseSerializer(expense).data
                })
            
            elif action == 'reject':
                expense.status = 'rejected'
                expense.rejected_by = request.user
                expense.rejected_at = timezone.now()
                expense.rejection_reason = comments
                expense.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Expense rejected",
                    "data": ExpenseSerializer(expense).data
                })
            
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid action"
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExpenseReimbursementAPIView(APIView):
    """Expense Reimbursement"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, admin_id):
        """Create reimbursement"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            employee_id = request.data.get('employee_id')
            expense_ids = request.data.get('expense_ids', [])
            reimbursement_date = request.data.get('reimbursement_date', date.today().isoformat())
            
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            expenses = Expense.objects.filter(
                id__in=expense_ids,
                employee=employee,
                status='approved'
            )
            
            total_amount = sum([exp.total_amount for exp in expenses])
            
            reimbursement = ExpenseReimbursement.objects.create(
                organization=admin.own_admin_profile.organization,
                employee=employee,
                reimbursement_date=reimbursement_date,
                total_amount=total_amount,
                status='pending'
            )
            
            reimbursement.expenses.set(expenses)
            
            # Update expense status
            expenses.update(status='reimbursed', reimbursement_amount=total_amount)
            
            serializer = ExpenseReimbursementSerializer(reimbursement)
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Reimbursement created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExpenseBudgetAPIView(APIView):
    """Expense Budget Management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id):
        """Get budgets"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            year = request.query_params.get('year', date.today().year)
            month = request.query_params.get('month')
            
            queryset = ExpenseBudget.objects.filter(
                organization=admin.own_admin_profile.organization,
                year=year
            )
            
            if month:
                queryset = queryset.filter(month=month)
            
            serializer = ExpenseBudgetSerializer(queryset, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Budgets fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, admin_id):
        """Create budget"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            data = request.data.copy()
            data['organization'] = str(admin.own_admin_profile.organization.id)
            
            serializer = ExpenseBudgetSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Budget created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExpenseDashboardAPIView(APIView):
    """Expense Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id):
        """Get dashboard stats"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            organization = admin.own_admin_profile.organization
            
            # Date filters
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to', date.today().isoformat())
            
            queryset = Expense.objects.filter(organization=organization)
            
            if date_from:
                queryset = queryset.filter(expense_date__gte=date_from)
            if date_to:
                queryset = queryset.filter(expense_date__lte=date_to)
            
            # Statistics
            total_expenses = queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            pending_expenses = queryset.filter(status='pending').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            approved_expenses = queryset.filter(status='approved').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            reimbursed_expenses = queryset.filter(status='reimbursed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            
            # By category
            category_stats = queryset.values('category__name').annotate(
                total=Sum('total_amount'),
                count=Count('id')
            ).order_by('-total')
            
            # By status
            status_stats = queryset.values('status').annotate(
                total=Sum('total_amount'),
                count=Count('id')
            )
            
            # By employee
            employee_stats = queryset.values('employee__own_user_profile__user_name').annotate(
                total=Sum('total_amount'),
                count=Count('id')
            ).order_by('-total')[:10]
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Dashboard stats fetched successfully",
                "data": {
                    "summary": {
                        "total_expenses": float(total_expenses),
                        "pending_expenses": float(pending_expenses),
                        "approved_expenses": float(approved_expenses),
                        "reimbursed_expenses": float(reimbursed_expenses)
                    },
                    "by_category": list(category_stats),
                    "by_status": list(status_stats),
                    "top_employees": list(employee_stats)
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
