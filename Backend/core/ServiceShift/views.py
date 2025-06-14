from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .models import ServiceShift
from .serializers import *
from django.shortcuts import get_object_or_404
from AuthN.models import *


class ServiceShiftAPIView(APIView):
    def get(self, request, admin_id, pk=None):
        if pk:
            obj = get_object_or_404(ServiceShift, admin__id=admin_id, id=pk, is_active=True)
            return Response(ServiceShiftSerializer(obj).data)
        shifts = ServiceShift.objects.filter(admin__id=admin_id, is_active=True)
        return Response(ServiceShiftSerializer(shifts, many=True).data)

    def post(self, request, admin_id, pk=None):
        admin = get_object_or_404(AdminProfile, user_id=admin_id)
        print(f"==>> admin: {admin}")
        data = request.data.copy()
        print(f"==>> admin.user_id: {admin.user_id}")
        data['admin'] = str(admin.user_id)
        data['organization'] = str(admin.organization.id)
        print(f"==>> admin.organization.id: {admin.organization.id}")

        serializer = ServiceShiftSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, admin_id, pk):
        obj = get_object_or_404(ServiceShift, admin__id=admin_id, id=pk)
        serializer = ServiceShiftUpdateSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, admin_id, pk):
        obj = get_object_or_404(ServiceShift, admin__id=admin_id, id=pk)
        obj.is_active = False
        obj.save()
        return Response(status=status.HTTP_204_NO_CONTENT)