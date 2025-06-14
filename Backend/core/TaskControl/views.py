from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import TaskType
from .serializers import TaskTypeSerializer, TaskTypeUpdateSerializer
from AuthN.models import AdminProfile

class TaskTypeAPIView(APIView):
    def get(self, request, admin_id, pk=None):
        if pk:
            obj = get_object_or_404(TaskType, admin__user_id=admin_id, id=pk, is_active=True)
            return Response(TaskTypeSerializer(obj).data)
        queryset = TaskType.objects.filter(admin__id=admin_id, is_active=True)
        return Response(TaskTypeSerializer(queryset, many=True).data)

    def post(self, request, admin_id):
        admin = get_object_or_404(AdminProfile, user_id=admin_id)
        data = request.data.copy()
        data['admin'] = str(admin.user_id)
        data['organization'] = str(admin.organization.id)

        serializer = TaskTypeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, admin_id, pk):
        obj = get_object_or_404(TaskType, admin__id=admin_id, id=pk)
        serializer = TaskTypeUpdateSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, admin_id, pk):
        obj = get_object_or_404(TaskType, admin__id=admin_id, id=pk)
        obj.is_active = False
        obj.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
