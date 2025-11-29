"""
Additional Utility APIs for Performance Management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, date

from .models import OKR, KPI, PerformanceReview, ReviewCycle
from .serializers import OKRSerializer, KPISerializer, PerformanceReviewSerializer
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class PerformanceDashboardAPIView(APIView):
    """Performance Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            # OKRs
            okrs = OKR.objects.filter(organization=organization)
            total_okrs = okrs.count()
            completed_okrs = okrs.filter(status='completed').count()
            on_track_okrs = okrs.filter(status='on_track').count()
            at_risk_okrs = okrs.filter(status='at_risk').count()
            
            # KPIs
            kpis = KPI.objects.filter(organization=organization)
            total_kpis = kpis.count()
            on_target = kpis.filter(status='on_target').count()
            above_target = kpis.filter(status='above_target').count()
            below_target = kpis.filter(status='below_target').count()
            
            # Reviews
            reviews = PerformanceReview.objects.filter(organization=organization)
            total_reviews = reviews.count()
            completed_reviews = reviews.filter(status='completed').count()
            
            avg_rating = reviews.filter(overall_rating__isnull=False).aggregate(
                avg=Avg('overall_rating')
            )['avg'] or 0
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Performance dashboard data fetched successfully",
                "data": {
                    "okrs": {
                        "total": total_okrs,
                        "completed": completed_okrs,
                        "on_track": on_track_okrs,
                        "at_risk": at_risk_okrs
                    },
                    "kpis": {
                        "total": total_kpis,
                        "on_target": on_target,
                        "above_target": above_target,
                        "below_target": below_target
                    },
                    "reviews": {
                        "total": total_reviews,
                        "completed": completed_reviews,
                        "average_rating": round(float(avg_rating), 2)
                    }
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

