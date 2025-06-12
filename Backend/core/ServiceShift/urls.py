from django.urls import path
from .views import ServiceShiftListCreateAPIView, ServiceShiftDetailAPIView

urlpatterns = [
    path('shifts/', ServiceShiftListCreateAPIView.as_view(), name='shift-list-create'),
    path('shifts/<uuid:pk>/', ServiceShiftDetailAPIView.as_view(), name='shift-detail'),
]
