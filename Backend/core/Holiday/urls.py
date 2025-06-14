from django.urls import path
from .views import HolidayAPIView

urlpatterns = [
    path('holidays/<uuid:admin_id>', HolidayAPIView.as_view(), name='holiday-list-create'),
    path('holidays/<uuid:admin_id>/<str:pk>', HolidayAPIView.as_view(), name='holiday-detail'),
]
