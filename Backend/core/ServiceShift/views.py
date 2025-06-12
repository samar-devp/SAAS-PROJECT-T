from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .models import ServiceShift
from .serializers import ServiceShiftSerializer
from .permissions import IsAdminOrOrganization
from django.shortcuts import get_object_or_404

class ServiceShiftListCreateAPIView(APIView):
    permission_classes = [IsAdminOrOrganization]

    def get(self, request):
        shifts = ServiceShift.objects.all()
        serializer = ServiceShiftSerializer(shifts, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user

        if user.role not in ['admin', 'organization']:
            raise PermissionDenied("Only admin or organization can create shifts.")

        try:
            admin_profile = user.adminprofile
        except Exception:
            return Response({"detail": "Admin profile not found for this user."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ServiceShiftSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(admin=admin_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServiceShiftDetailAPIView(APIView):
    permission_classes = [IsAdminOrOrganization]

    def get_object(self, pk):
        return get_object_or_404(ServiceShift, pk=pk)

    def get(self, request, pk):
        shift = self.get_object(pk)
        serializer = ServiceShiftSerializer(shift)
        return Response(serializer.data)

    def put(self, request, pk):
        shift = self.get_object(pk)
        serializer = ServiceShiftSerializer(shift, data=request.data)
        if serializer.is_valid():
            serializer.save()  # Optional: validate ownership before save
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        shift = self.get_object(pk)
        serializer = ServiceShiftSerializer(shift, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        shift = self.get_object(pk)
        shift.delete()
        return Response({"detail": "Deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
