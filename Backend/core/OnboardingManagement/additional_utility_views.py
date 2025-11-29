"""
Additional Utility APIs for Onboarding Management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, date

from .models import OnboardingProcess, OnboardingTask, DocumentType, EmployeeDocument
from .serializers import OnboardingProcessSerializer, OnboardingTaskSerializer
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class OnboardingDashboardAPIView(APIView):
    """Onboarding Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            processes = OnboardingProcess.objects.filter(organization=organization)
            
            total = processes.count()
            pending = processes.filter(status='pending').count()
            in_progress = processes.filter(status='in_progress').count()
            completed = processes.filter(status='completed').count()
            
            # Tasks statistics
            tasks = OnboardingTask.objects.filter(
                onboarding_process__organization=organization
            )
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='completed').count()
            
            # Documents statistics
            user_profiles = UserProfile.objects.filter(organization=organization)
            employee_ids = [p.user.id for p in user_profiles]
            documents = EmployeeDocument.objects.filter(employee_id__in=employee_ids)
            total_documents = documents.count()
            verified_documents = documents.filter(is_verified=True).count()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Onboarding dashboard data fetched successfully",
                "data": {
                    "processes": {
                        "total": total,
                        "pending": pending,
                        "in_progress": in_progress,
                        "completed": completed
                    },
                    "tasks": {
                        "total": total_tasks,
                        "completed": completed_tasks,
                        "completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2)
                    },
                    "documents": {
                        "total": total_documents,
                        "verified": verified_documents,
                        "verification_rate": round((verified_documents / total_documents * 100) if total_documents > 0 else 0, 2)
                    }
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

