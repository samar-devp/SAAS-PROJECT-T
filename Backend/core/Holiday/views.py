from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Holiday
from .serializers import *
from AuthN.models import *


class HolidayAPIView(APIView):
    def get(self, request, admin_id, pk=None):
        if pk:
            holiday = get_object_or_404(Holiday, admin__id=admin_id, id=pk, is_active=True)
            serializer = HolidaySerializer(holiday)
            return Response(serializer.data)
        holidays = Holiday.objects.filter(admin__id=admin_id, is_active=True)
        serializer = HolidaySerializer(holidays, many=True)
        return Response(serializer.data)

    def post(self, request, admin_id, pk=None):
        admin = get_object_or_404(AdminProfile, user_id=admin_id)
        print(f"==>> admin: {admin}")
        data = request.data.copy()
        data['admin'] = admin.user_id
        print(f"==>> admin.organization.id: {admin.organization.id}")
        data['organization'] = admin.organization.id

        serializer = HolidaySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, admin_id, pk):
        holiday = get_object_or_404(Holiday, admin__id=admin_id, id=pk)
        serializer = HolidayUpdateSerializer(holiday, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, admin_id, pk):
        holiday = get_object_or_404(Holiday, admin__id=admin_id, id=pk)
        serializer = HolidaySerializer(holiday, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, admin_id, pk):
        holiday = get_object_or_404(Holiday, admin__id=admin_id, id=pk)
        holiday.is_active = False
        holiday.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
