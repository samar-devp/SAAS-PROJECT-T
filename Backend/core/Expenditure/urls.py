"""
Expense Management URLs
"""

from django.urls import path
from .views import (
    ExpenseCategoryAPIView, ExpenseAPIView,
    ExpenseApprovalAPIView, ExpenseReimbursementAPIView,
    ExpenseBudgetAPIView, ExpenseDashboardAPIView
)
from .additional_utility_views import *

urlpatterns = [
    path('expense-categories/<uuid:admin_id>', ExpenseCategoryAPIView.as_view(), name='expense-category-list-create'),
    path('expense-categories/<uuid:admin_id>/<int:pk>', ExpenseCategoryAPIView.as_view(), name='expense-category-detail'),
    path('expenses/<uuid:admin_id>', ExpenseAPIView.as_view(), name='expense-list-create'),
    path('expenses/<uuid:admin_id>/<uuid:pk>', ExpenseAPIView.as_view(), name='expense-detail'),
    path('expense-approval/<uuid:expense_id>', ExpenseApprovalAPIView.as_view(), name='expense-approval'),
    path('expense-reimbursement/<uuid:admin_id>', ExpenseReimbursementAPIView.as_view(), name='expense-reimbursement'),
    path('expense-budget/<uuid:admin_id>', ExpenseBudgetAPIView.as_view(), name='expense-budget'),
    path('expense-dashboard/<uuid:admin_id>', ExpenseDashboardAPIView.as_view(), name='expense-dashboard'),
    
    # Additional Utility APIs
    path('expenses-list/<str:org_id>', ExpenseListAPIView.as_view(), name='expenses-list'),
    path('employee-expenses/<str:org_id>/<str:employee_id>', EmployeeExpenseListAPIView.as_view(), name='employee-expenses'),
    path('reimbursements-list/<str:org_id>', ExpenseReimbursementListAPIView.as_view(), name='reimbursements-list'),
]
