"""
Asset Management URLs
"""

from django.urls import path
from .views import (
    AssetCategoryAPIView, AssetAPIView,
    AssetMaintenanceAPIView, AssetTransferAPIView
)
from .additional_utility_views import *

urlpatterns = [
    path('asset-categories/<uuid:org_id>', AssetCategoryAPIView.as_view(), name='asset-category-list-create'),
    path('asset-categories/<uuid:org_id>/<uuid:pk>', AssetCategoryAPIView.as_view(), name='asset-category-detail'),
    path('assets/<uuid:org_id>', AssetAPIView.as_view(), name='asset-list-create'),
    path('assets/<uuid:org_id>/<uuid:pk>', AssetAPIView.as_view(), name='asset-detail'),
    path('asset-maintenance/<uuid:asset_id>', AssetMaintenanceAPIView.as_view(), name='asset-maintenance'),
    path('asset-transfer/<uuid:asset_id>', AssetTransferAPIView.as_view(), name='asset-transfer'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', AssetDashboardAPIView.as_view(), name='asset-dashboard'),
    path('employee-assets/<str:org_id>/<str:employee_id>', EmployeeAssetListAPIView.as_view(), name='employee-assets'),
]

