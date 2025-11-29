from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import TaskType
from .serializers import TaskTypeSerializer, TaskTypeUpdateSerializer
from AuthN.models import BaseUserModel

class TaskTypeAPIView(APIView):
    def get(self, request, admin_id, pk=None):
        try:
            if pk:
                obj = get_object_or_404(TaskType, admin__id=admin_id, id=pk, is_active=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Task type fetched successfully",
                    "data": TaskTypeSerializer(obj).data
                })
            queryset = TaskType.objects.filter(admin__id=admin_id, is_active=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Task types fetched successfully",
                "data": TaskTypeSerializer(queryset, many=True).data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, admin_id):
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            data = request.data.copy()
            data['admin'] = str(admin.id)
            data['organization'] = str(admin.own_admin_profile.organization.id)

            serializer = TaskTypeSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Task type created successfully",
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

    def put(self, request, admin_id, pk):
        try:
            obj = get_object_or_404(TaskType, admin__id=admin_id, id=pk)
            serializer = TaskTypeUpdateSerializer(obj, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Task type updated successfully",
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

    def delete(self, request, admin_id, pk):
        try:
            obj = get_object_or_404(TaskType, admin__id=admin_id, id=pk)
            obj.is_active = False
            obj.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Task type deleted successfully"
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
