from django.urls import path
from .views import *

urlpatterns = [
    path('service-shifts/<uuid:admin_id>', ServiceShiftAPIView.as_view(), name='service-shift-list-create'),
    path('service-shifts/<uuid:admin_id>/<int:pk>', ServiceShiftAPIView.as_view(), name='service-shift-detail'),
]
