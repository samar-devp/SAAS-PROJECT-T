"""
Additional Utility APIs for Asset Management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal

from .models import Asset, AssetCategory, AssetMaintenance, AssetTransfer
from .serializers import AssetSerializer, AssetCategorySerializer
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class AssetDashboardAPIView(APIView):
    """Asset Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            assets = Asset.objects.filter(organization=organization)
            
            total_assets = assets.count()
            active = assets.filter(status='active').count()
            assigned = assets.filter(status='assigned').count()
            maintenance = assets.filter(status='maintenance').count()
            disposed = assets.filter(status='disposed').count()
            
            total_value = assets.aggregate(total=Sum('current_value'))['total'] or Decimal('0')
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Asset dashboard data fetched successfully",
                "data": {
                    "total_assets": total_assets,
                    "active": active,
                    "assigned": assigned,
                    "maintenance": maintenance,
                    "disposed": disposed,
                    "total_value": float(total_value)
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeAssetListAPIView(APIView):
    """Get assets assigned to an employee"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, employee_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            assets = Asset.objects.filter(
                organization=organization,
                assigned_to=employee
            )
            
            status_filter = request.query_params.get('status')
            if status_filter:
                assets = assets.filter(status=status_filter)
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(assets, request)
            
            serializer = AssetSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Assets fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

