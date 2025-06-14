from django.urls import path
from .views import WeekOffPolicyAPIView

urlpatterns = [
    path('week-off-policy/<uuid:admin_id>', WeekOffPolicyAPIView.as_view()),
    path('week-off-policy/<uuid:admin_id>/<int:pk>', WeekOffPolicyAPIView.as_view()),
]
    