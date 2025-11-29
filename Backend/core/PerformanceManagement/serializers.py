"""
Performance Management Serializers
"""

from rest_framework import serializers
from .models import (
    GoalLibrary, OKR, KPI, ReviewCycle, RatingMatrix,
    PerformanceReview, Review360
)
from AuthN.models import BaseUserModel


class GoalLibrarySerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True, allow_null=True)
    
    class Meta:
        model = GoalLibrary
        fields = '__all__'
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class OKRSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True, allow_null=True)
    reviewed_by_email = serializers.EmailField(source='reviewed_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = OKR
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class KPISerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True, allow_null=True)
    
    class Meta:
        model = KPI
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReviewCycleSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True, allow_null=True)
    
    class Meta:
        model = ReviewCycle
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class RatingMatrixSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    
    class Meta:
        model = RatingMatrix
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PerformanceReviewSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True, allow_null=True)
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.own_user_profile.user_name', read_only=True, allow_null=True)
    review_cycle_name = serializers.CharField(source='review_cycle.name', read_only=True)
    
    class Meta:
        model = PerformanceReview
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class Review360Serializer(serializers.ModelSerializer):
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True, allow_null=True)
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.own_user_profile.user_name', read_only=True, allow_null=True)
    review_cycle_name = serializers.CharField(source='review_cycle.name', read_only=True)
    
    class Meta:
        model = Review360
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

