# urls.py

from django.urls import path
from .views import LocationAPIView

urlpatterns = [
    path('locations/<uuid:admin_id>', LocationAPIView.as_view(), name='location-list-create'),
    path('locations/<uuid:admin_id>/<int:pk>', LocationAPIView.as_view(), name='location-detail'),
]