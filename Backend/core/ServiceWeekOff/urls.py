from django.urls import path
from .views import WeekOffPolicyAPIView, AssignWeekOffToUserAPIView

urlpatterns = [
    path('week-off-policies/<uuid:admin_id>', WeekOffPolicyAPIView.as_view()),
    path('week-off-policies/<uuid:admin_id>/<int:pk>', WeekOffPolicyAPIView.as_view()),
    path('assign-week-offs/<uuid:admin_id>/<uuid:user_id>', AssignWeekOffToUserAPIView.as_view()),
    path('assign-week-offs/<uuid:admin_id>/<uuid:user_id>/<int:week_off_id>', AssignWeekOffToUserAPIView.as_view()),
]
    