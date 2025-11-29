"""
Asset Management Serializers
"""

from rest_framework import serializers
from .models import AssetCategory, Asset, AssetMaintenance, AssetTransfer, AssetDepreciation
from AuthN.models import BaseUserModel


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssetSerializer(serializers.ModelSerializer):
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True, allow_null=True)
    assigned_to_name = serializers.CharField(source='assigned_to.own_user_profile.user_name', read_only=True, allow_null=True)
    assigned_by_email = serializers.EmailField(source='assigned_by.email', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = Asset
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssetMaintenanceSerializer(serializers.ModelSerializer):
    asset_detail = AssetSerializer(source='asset', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = AssetMaintenance
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssetTransferSerializer(serializers.ModelSerializer):
    asset_detail = AssetSerializer(source='asset', read_only=True)
    from_user_email = serializers.EmailField(source='from_user.email', read_only=True, allow_null=True)
    to_user_email = serializers.EmailField(source='to_user.email', read_only=True, allow_null=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = AssetTransfer
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class AssetDepreciationSerializer(serializers.ModelSerializer):
    asset_detail = AssetSerializer(source='asset', read_only=True)
    
    class Meta:
        model = AssetDepreciation
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

