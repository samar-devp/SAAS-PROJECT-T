from rest_framework import serializers
from .models import ExpenseCategory

class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ExpenseCategoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'
        read_only_fields = ['id', 'admin', 'organization', 'created_at', 'updated_at']
