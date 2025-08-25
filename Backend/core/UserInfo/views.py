from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from AuthN.models import UserProfile
from AuthN.serializers import UserProfileSerializer
from utils.pagination_utils import CustomPagination
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction
from utils.common_utils import *
class StaffListByAdmin(APIView):
    """
    API to get employees under an organization/admin
    """
    pagination_class = CustomPagination

    def get(self, request, admin_id):
        try:
            search = request.query_params.get("q", None)

            # base queryset
            queryset = UserProfile.objects.filter(admin_id=admin_id)

            # optional search
            if search:
                queryset = queryset.filter(
                    Q(user_name__icontains=search) |
                    Q(custom_employee_id__icontains=search) |
                    Q(designation__icontains=search)
                )

            # counts
            total_employees = queryset.count()
            active_count = queryset.filter(user__is_active=True).count()
            inactive_count = queryset.filter(user__is_active=False).count()

            # pagination
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)

            # serialize
            serializer = UserProfileSerializer(paginated_qs, many=True)

            # ✅ since your CustomPagination returns a dict
            pagination_data = paginator.get_paginated_response(serializer.data)
            pagination_data["results"] = serializer.data   # ✅ employees list add
            # safely add extra keys to dict
            pagination_data["summary"] = {
                "total": total_employees,
                "active": active_count,
                "inactive": inactive_count,
            }
            pagination_data["message"] = "Data fetched"
            pagination_data["status"] = status.HTTP_200_OK

            return Response(pagination_data)

        except Exception as e:
            return Response(
                {"message": str(e), "status": status.HTTP_500_INTERNAL_SERVER_ERROR}
            )


            
    def put(self, request, *args, **kwargs):
        employee_ids = request.data.get("employee_ids", [])
        if not employee_ids:
            return Response({"error": "employee_ids required"}, status=400)

        update_data = request.data.copy()
        update_data.pop("employee_ids", None)

        if not update_data:
            return Response({"error": "No fields to update"}, status=400)

        results = []
        for emp_id in employee_ids:
            employee = get_object_or_404(UserProfile, user_id=emp_id)
            serializer = UserProfileSerializer(employee, data=update_data, partial=True)  # 👈 partial=False
            if serializer.is_valid():
                serializer.save()
                results.append(serializer.data)
            else:
                results.append({"emp_id": emp_id, "errors": serializer.errors})

        return Response(results, status=200)