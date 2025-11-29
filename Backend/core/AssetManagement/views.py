"""
Asset Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
import traceback

from .models import AssetCategory, Asset, AssetMaintenance, AssetTransfer, AssetDepreciation
from .serializers import (
    AssetCategorySerializer, AssetSerializer, AssetMaintenanceSerializer,
    AssetTransferSerializer, AssetDepreciationSerializer
)
from AuthN.models import BaseUserModel
from utils.pagination_utils import CustomPagination


class AssetCategoryAPIView(APIView):
    """Asset Category CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        """Get categories"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                category = get_object_or_404(AssetCategory, id=pk, organization=organization)
                serializer = AssetCategorySerializer(category)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Category fetched successfully",
                    "data": serializer.data
                })
            else:
                categories = AssetCategory.objects.filter(organization=organization, is_active=True)
                serializer = AssetCategorySerializer(categories, many=True)
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
    
    def post(self, request, org_id):
        """Create category"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admin = get_object_or_404(BaseUserModel, id=request.data.get('admin_id'), role='admin')
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            data['admin'] = str(admin.id)
            
            serializer = AssetCategorySerializer(data=data)
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


class AssetAPIView(APIView):
    """Asset CRUD"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, pk=None):
        """Get assets"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                asset = get_object_or_404(Asset, id=pk, organization=organization)
                serializer = AssetSerializer(asset)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Asset fetched successfully",
                    "data": serializer.data
                })
            else:
                queryset = Asset.objects.filter(organization=organization, is_active=True)
                
                # Filters
                status_filter = request.query_params.get('status')
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                
                category_id = request.query_params.get('category_id')
                if category_id:
                    queryset = queryset.filter(category_id=category_id)
                
                assigned_to = request.query_params.get('assigned_to')
                if assigned_to:
                    queryset = queryset.filter(assigned_to_id=assigned_to)
                
                # Pagination
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = AssetSerializer(paginated_qs, many=True)
                pagination_data = paginator.get_paginated_response(serializer.data)
                pagination_data["results"] = serializer.data
                pagination_data["message"] = "Assets fetched successfully"
                
                return Response(pagination_data)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, org_id):
        """Create asset"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admin = get_object_or_404(BaseUserModel, id=request.data.get('admin_id'), role='admin')
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            data['admin'] = str(admin.id)
            data['created_by'] = str(request.user.id)
            
            serializer = AssetSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Asset created successfully",
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
    
    @transaction.atomic
    def put(self, request, org_id, pk):
        """Update asset"""
        try:
            asset = get_object_or_404(Asset, id=pk, organization_id=org_id)
            serializer = AssetSerializer(asset, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Asset updated successfully",
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


class AssetMaintenanceAPIView(APIView):
    """Asset Maintenance"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, asset_id):
        """Get maintenance records"""
        try:
            asset = get_object_or_404(Asset, id=asset_id)
            maintenance_records = AssetMaintenance.objects.filter(asset=asset)
            serializer = AssetMaintenanceSerializer(maintenance_records, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Maintenance records fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, asset_id):
        """Create maintenance record"""
        try:
            asset = get_object_or_404(Asset, id=asset_id)
            data = request.data.copy()
            data['asset'] = str(asset.id)
            data['organization'] = str(asset.organization.id)
            data['created_by'] = str(request.user.id)
            
            serializer = AssetMaintenanceSerializer(data=data)
            if serializer.is_valid():
                maintenance = serializer.save()
                
                # Update asset status if needed
                if maintenance.status == 'in_progress':
                    asset.status = 'maintenance'
                    asset.save()
                elif maintenance.status == 'completed':
                    asset.status = 'available'
                    asset.save()
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Maintenance record created successfully",
                    "data": AssetMaintenanceSerializer(maintenance).data
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


class AssetTransferAPIView(APIView):
    """Asset Transfer"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, asset_id):
        """Transfer asset"""
        try:
            asset = get_object_or_404(Asset, id=asset_id)
            data = request.data.copy()
            data['asset'] = str(asset.id)
            data['organization'] = str(asset.organization.id)
            data['created_by'] = str(request.user.id)
            data['from_user'] = str(asset.assigned_to.id) if asset.assigned_to else None
            data['from_location'] = asset.location
            
            serializer = AssetTransferSerializer(data=data)
            if serializer.is_valid():
                transfer = serializer.save()
                
                # Update asset assignment
                asset.assigned_to_id = data.get('to_user')
                asset.location = data.get('to_location', asset.location)
                asset.assigned_date = date.today()
                asset.assigned_by = request.user
                asset.save()
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Asset transferred successfully",
                    "data": AssetTransferSerializer(transfer).data
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

