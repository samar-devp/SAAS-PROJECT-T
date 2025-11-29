"""
Organization Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal

from .models import (
    SubscriptionPlan, OrganizationSubscription, OrganizationModule,
    OrganizationUsage, OrganizationDeactivationLog, SuperAdminAction
)
from .serializers import (
    SubscriptionPlanSerializer, OrganizationSubscriptionSerializer,
    OrganizationModuleSerializer, OrganizationUsageSerializer,
    OrganizationDeactivationLogSerializer, SuperAdminActionSerializer
)
from AuthN.models import BaseUserModel, OrganizationSettings
from utils.pagination_utils import CustomPagination


class SubscriptionPlanAPIView(APIView):
    """Subscription Plan CRUD (Super Admin Only)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk=None):
        try:
            if pk:
                plan = get_object_or_404(SubscriptionPlan, id=pk)
                serializer = SubscriptionPlanSerializer(plan)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Plan fetched successfully",
                    "data": serializer.data
                })
            else:
                plans = SubscriptionPlan.objects.filter(is_active=True)
                serializer = SubscriptionPlanSerializer(plans, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Plans fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        try:
            serializer = SubscriptionPlanSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Plan created successfully",
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


class OrganizationSubscriptionAPIView(APIView):
    """Organization Subscription Management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                subscription = get_object_or_404(OrganizationSubscription, id=pk, organization=organization)
                serializer = OrganizationSubscriptionSerializer(subscription)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Subscription fetched successfully",
                    "data": serializer.data
                })
            else:
                subscription = OrganizationSubscription.objects.filter(organization=organization).first()
                if subscription:
                    serializer = OrganizationSubscriptionSerializer(subscription)
                    return Response({
                        "status": status.HTTP_200_OK,
                        "message": "Subscription fetched successfully",
                        "data": serializer.data
                    })
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "No subscription found",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        """Assign/Update Subscription"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            plan = get_object_or_404(SubscriptionPlan, id=request.data.get('plan_id'))
            
            start_date = date.fromisoformat(str(request.data.get('start_date', date.today())))
            billing_cycle = plan.billing_cycle
            
            # Calculate expiry date
            if billing_cycle == 'monthly':
                expiry_date = start_date + timedelta(days=30)
            elif billing_cycle == 'quarterly':
                expiry_date = start_date + timedelta(days=90)
            else:  # yearly
                expiry_date = start_date + timedelta(days=365)
            
            grace_period_end = expiry_date + timedelta(days=plan.grace_period_days)
            
            subscription, created = OrganizationSubscription.objects.get_or_create(
                organization=organization,
                defaults={
                    'plan': plan,
                    'start_date': start_date,
                    'expiry_date': expiry_date,
                    'grace_period_end': grace_period_end,
                    'status': 'active'
                }
            )
            
            if not created:
                # Update existing
                subscription.plan = plan
                subscription.start_date = start_date
                subscription.expiry_date = expiry_date
                subscription.grace_period_end = grace_period_end
                subscription.status = 'active'
                subscription.save()
            
            serializer = OrganizationSubscriptionSerializer(subscription)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Subscription assigned successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrganizationModuleAPIView(APIView):
    """Organization Module Management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                module = get_object_or_404(OrganizationModule, id=pk, organization=organization)
                serializer = OrganizationModuleSerializer(module)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Module fetched successfully",
                    "data": serializer.data
                })
            else:
                modules = OrganizationModule.objects.filter(organization=organization)
                serializer = OrganizationModuleSerializer(modules, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Modules fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        """Enable/Disable Module"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            module_code = request.data.get('module_code')
            module_name = request.data.get('module_name')
            is_enabled = request.data.get('is_enabled', True)
            
            module, created = OrganizationModule.objects.get_or_create(
                organization=organization,
                module_code=module_code,
                defaults={
                    'module_name': module_name,
                    'is_enabled': is_enabled,
                    'enabled_at': timezone.now() if is_enabled else None
                }
            )
            
            if not created:
                module.is_enabled = is_enabled
                if is_enabled:
                    module.enabled_at = timezone.now()
                    module.disabled_at = None
                else:
                    module.disabled_at = timezone.now()
                module.save()
            
            serializer = OrganizationModuleSerializer(module)
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Module {'enabled' if is_enabled else 'disabled'} successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrganizationUsageAPIView(APIView):
    """Organization Usage Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            period_type = request.query_params.get('period_type', 'monthly')
            period_start = request.query_params.get('period_start')
            
            if not period_start:
                today = date.today()
                period_start = date(today.year, today.month, 1)
            
            usage = OrganizationUsage.objects.filter(
                organization=organization,
                period_type=period_type,
                period_start=period_start
            ).first()
            
            if usage:
                serializer = OrganizationUsageSerializer(usage)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Usage statistics fetched successfully",
                    "data": serializer.data
                })
            
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Usage statistics not found for the period",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrganizationDeactivationAPIView(APIView):
    """Organization Deactivation (Super Admin)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org_id):
        """Deactivate Organization"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            super_admin = request.user
            
            reason = request.data.get('reason', 'manual_suspend')
            reason_description = request.data.get('reason_description', '')
            
            # Deactivate organization
            organization.is_active = False
            organization.save()
            
            # Update subscription status
            subscription = OrganizationSubscription.objects.filter(organization=organization).first()
            if subscription:
                subscription.status = 'suspended'
                subscription.save()
            
            # Log deactivation
            log = OrganizationDeactivationLog.objects.create(
                organization=organization,
                reason=reason,
                reason_description=reason_description,
                deactivated_by=super_admin
            )
            
            # Log super admin action
            SuperAdminAction.objects.create(
                super_admin=super_admin,
                organization=organization,
                action_type='org_deactivate',
                description=f"Deactivated organization {organization.email}",
                details={'reason': reason, 'reason_description': reason_description}
            )
            
            serializer = OrganizationDeactivationLogSerializer(log)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Organization deactivated successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, org_id):
        """Reactivate Organization"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            super_admin = request.user
            
            # Reactivate organization
            organization.is_active = True
            organization.save()
            
            # Update subscription status
            subscription = OrganizationSubscription.objects.filter(organization=organization).first()
            if subscription:
                subscription.status = 'active'
                subscription.save()
            
            # Update deactivation log
            log = OrganizationDeactivationLog.objects.filter(
                organization=organization,
                reactivated_at__isnull=True
            ).order_by('-deactivated_at').first()
            
            if log:
                log.reactivated_at = timezone.now()
                log.reactivated_by = super_admin
                log.save()
            
            # Log super admin action
            SuperAdminAction.objects.create(
                super_admin=super_admin,
                organization=organization,
                action_type='org_activate',
                description=f"Reactivated organization {organization.email}"
            )
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Organization reactivated successfully"
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

