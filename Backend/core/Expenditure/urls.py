from django.urls import path
from .views import ExpenseCategoryAPIView

urlpatterns = [
    path('expense-categories/<uuid:admin_id>', ExpenseCategoryAPIView.as_view(), name='expense-category-list'),
    path('expense-categories/<uuid:admin_id>/<int:pk>', ExpenseCategoryAPIView.as_view(), name='expense-category-detail'),
]