"""
Advanced Asset Management System
Comprehensive asset tracking, maintenance, and lifecycle management
"""

from django.db import models
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime
from AuthN.models import *


class AssetCategory(models.Model):
    """Asset Category"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_asset_categories'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_asset_categories'
    )
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    parent_category = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sub_categories'
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'code')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Asset(models.Model):
    """Asset Model"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
        ('disposed', 'Disposed'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged')
    ]
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('critical', 'Critical')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_assets'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_assets'
    )
    category = models.ForeignKey(
        AssetCategory, on_delete=models.PROTECT,
        related_name='assets'
    )
    
    # Asset Identification
    asset_code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    # Asset Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    location = models.CharField(max_length=255, blank=True, null=True)
    
    # Assignment
    assigned_to = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'user'},
        related_name='assigned_assets'
    )
    assigned_date = models.DateField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='asset_assignments',
        limit_choices_to={'role': 'admin'}
    )
    
    # Financial
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    warranty_expiry = models.DateField(null=True, blank=True)
    vendor = models.CharField(max_length=255, blank=True, null=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Specifications
    specifications = models.JSONField(default=dict, blank=True)
    photos = models.JSONField(default=list, blank=True)
    documents = models.JSONField(default=list, blank=True)
    
    # Lifecycle
    installation_date = models.DateField(null=True, blank=True)
    retirement_date = models.DateField(null=True, blank=True)
    disposal_date = models.DateField(null=True, blank=True)
    disposal_reason = models.TextField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_assets'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset_code']),
            models.Index(fields=['status', 'assigned_to']),
            models.Index(fields=['category', 'status']),
        ]
    
    def __str__(self):
        return f"{self.asset_code} - {self.name}"


class AssetMaintenance(models.Model):
    """Asset Maintenance Records"""
    MAINTENANCE_TYPE_CHOICES = [
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('emergency', 'Emergency'),
        ('inspection', 'Inspection')
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE,
        related_name='maintenance_records'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'}
    )
    
    # Maintenance Details
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Schedule
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    # Service Provider
    service_provider = models.CharField(max_length=255, blank=True, null=True)
    technician_name = models.CharField(max_length=255, blank=True, null=True)
    technician_contact = models.CharField(max_length=20, blank=True, null=True)
    
    # Cost
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Results
    work_performed = models.TextField(blank=True, null=True)
    parts_replaced = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, null=True)
    attachments = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_asset_maintenances'
    )
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.asset.name} - {self.title}"


class AssetTransfer(models.Model):
    """Asset Transfer History"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE,
        related_name='transfers'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'}
    )
    
    # Transfer Details
    from_user = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='asset_transfers_from'
    )
    to_user = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='asset_transfers_to'
    )
    from_location = models.CharField(max_length=255, blank=True, null=True)
    to_location = models.CharField(max_length=255, blank=True, null=True)
    
    transfer_date = models.DateField()
    reason = models.TextField()
    condition_before = models.CharField(max_length=20, blank=True, null=True)
    condition_after = models.CharField(max_length=20, blank=True, null=True)
    
    approved_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_asset_transfers',
        limit_choices_to={'role': 'admin'}
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_asset_transfers'
    )
    
    class Meta:
        ordering = ['-transfer_date']
    
    def __str__(self):
        return f"{self.asset.name} - Transfer"


class AssetDepreciation(models.Model):
    """Asset Depreciation Records"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE,
        related_name='depreciation_records'
    )
    
    depreciation_date = models.DateField()
    depreciation_amount = models.DecimalField(max_digits=12, decimal_places=2)
    accumulated_depreciation = models.DecimalField(max_digits=12, decimal_places=2)
    book_value = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-depreciation_date']
    
    def __str__(self):
        return f"{self.asset.name} - Depreciation"

