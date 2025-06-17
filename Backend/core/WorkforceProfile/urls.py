# urls.py
from django.urls import path
from .views import AttendanceCheckInOutAPIView

urlpatterns = [
    path('attendance-check/<uuid:user_id>', AttendanceCheckInOutAPIView.as_view(), name='attendance-check'),
]
