"""
Performance Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal

from .models import GoalLibrary, OKR, KPI, ReviewCycle, RatingMatrix, PerformanceReview, Review360
from .serializers import (
    GoalLibrarySerializer, OKRSerializer, KPISerializer, ReviewCycleSerializer,
    RatingMatrixSerializer, PerformanceReviewSerializer, Review360Serializer
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class GoalLibraryAPIView(APIView):
    """Goal Library CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                goal = get_object_or_404(GoalLibrary, id=pk, organization=organization)
                serializer = GoalLibrarySerializer(goal)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Goal fetched successfully",
                    "data": serializer.data
                })
            else:
                goals = GoalLibrary.objects.filter(organization=organization, is_active=True)
                
                # Filters
                category = request.query_params.get('category')
                department = request.query_params.get('department')
                
                if category:
                    goals = goals.filter(category=category)
                if department:
                    goals = goals.filter(department=department)
                
                serializer = GoalLibrarySerializer(goals, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Goals fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admin_id = request.data.get('admin_id')
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin') if admin_id else None
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            if admin:
                data['admin'] = str(admin.id)
            
            serializer = GoalLibrarySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Goal created successfully",
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


class OKRAPIView(APIView):
    """OKR CRUD"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                okr = get_object_or_404(OKR, id=pk, organization=organization)
                serializer = OKRSerializer(okr)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "OKR fetched successfully",
                    "data": serializer.data
                })
            else:
                okrs = OKR.objects.filter(organization=organization)
                
                # Filters
                employee_id = request.query_params.get('employee_id')
                status_filter = request.query_params.get('status')
                period_type = request.query_params.get('period_type')
                
                if employee_id:
                    okrs = okrs.filter(employee_id=employee_id)
                if status_filter:
                    okrs = okrs.filter(status=status_filter)
                if period_type:
                    okrs = okrs.filter(period_type=period_type)
                
                serializer = OKRSerializer(okrs.order_by('-period_start'), many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "OKRs fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=request.data.get('employee_id'), role='user')
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            data['employee'] = str(employee.id)
            
            serializer = OKRSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "OKR created successfully",
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
    
    def put(self, request, org_id, pk):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            okr = get_object_or_404(OKR, id=pk, organization=organization)
            
            data = request.data.copy()
            serializer = OKRSerializer(okr, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "OKR updated successfully",
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


class KPIAPIView(APIView):
    """KPI CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                kpi = get_object_or_404(KPI, id=pk, organization=organization)
                serializer = KPISerializer(kpi)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "KPI fetched successfully",
                    "data": serializer.data
                })
            else:
                kpis = KPI.objects.filter(organization=organization)
                
                employee_id = request.query_params.get('employee_id')
                if employee_id:
                    kpis = kpis.filter(employee_id=employee_id)
                
                serializer = KPISerializer(kpis.order_by('-period_start'), many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "KPIs fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=request.data.get('employee_id'), role='user')
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            data['employee'] = str(employee.id)
            
            # Calculate status based on current vs target
            current = Decimal(str(data.get('current_value', 0)))
            target = Decimal(str(data.get('target_value', 0)))
            
            if current >= target:
                data['status'] = 'above_target'
            elif current >= target * Decimal('0.8'):  # 80% of target
                data['status'] = 'on_target'
            else:
                data['status'] = 'below_target'
            
            serializer = KPISerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "KPI created successfully",
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


class ReviewCycleAPIView(APIView):
    """Review Cycle CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                cycle = get_object_or_404(ReviewCycle, id=pk, organization=organization)
                serializer = ReviewCycleSerializer(cycle)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Review cycle fetched successfully",
                    "data": serializer.data
                })
            else:
                cycles = ReviewCycle.objects.filter(organization=organization)
                serializer = ReviewCycleSerializer(cycles.order_by('-start_date'), many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Review cycles fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admin_id = request.data.get('admin_id')
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin') if admin_id else None
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            if admin:
                data['admin'] = str(admin.id)
            
            serializer = ReviewCycleSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Review cycle created successfully",
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


class PerformanceReviewAPIView(APIView):
    """Performance Review CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                review = get_object_or_404(PerformanceReview, id=pk, organization=organization)
                serializer = PerformanceReviewSerializer(review)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Review fetched successfully",
                    "data": serializer.data
                })
            else:
                reviews = PerformanceReview.objects.filter(organization=organization)
                
                # Filters
                employee_id = request.query_params.get('employee_id')
                reviewer_id = request.query_params.get('reviewer_id')
                review_type = request.query_params.get('review_type')
                status_filter = request.query_params.get('status')
                
                if employee_id:
                    reviews = reviews.filter(employee_id=employee_id)
                if reviewer_id:
                    reviews = reviews.filter(reviewer_id=reviewer_id)
                if review_type:
                    reviews = reviews.filter(review_type=review_type)
                if status_filter:
                    reviews = reviews.filter(status=status_filter)
                
                serializer = PerformanceReviewSerializer(reviews.order_by('-created_at'), many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Reviews fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=request.data.get('employee_id'), role='user')
            reviewer = get_object_or_404(BaseUserModel, id=request.data.get('reviewer_id'))
            review_cycle = get_object_or_404(ReviewCycle, id=request.data.get('review_cycle_id'))
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            data['employee'] = str(employee.id)
            data['reviewer'] = str(reviewer.id)
            data['review_cycle'] = str(review_cycle.id)
            
            serializer = PerformanceReviewSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Performance review created successfully",
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

