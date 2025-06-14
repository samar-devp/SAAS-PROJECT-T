from django.urls import path
from .views import TaskTypeAPIView

urlpatterns = [
    path('task-types/<uuid:admin_id>', TaskTypeAPIView.as_view(), name='tasktype-list-create'),
    path('task-types/<uuid:admin_id>/<int:pk>', TaskTypeAPIView.as_view(), name='tasktype-detail'),
]