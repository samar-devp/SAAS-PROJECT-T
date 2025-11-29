"""
Notes Management URLs
"""

from django.urls import path
from .views import (
    NoteCategoryAPIView, NoteAPIView, NoteCommentAPIView
)
from .additional_utility_views import *

urlpatterns = [
    path('note-categories/<uuid:org_id>', NoteCategoryAPIView.as_view(), name='note-category-list-create'),
    path('note-categories/<uuid:org_id>/<uuid:pk>', NoteCategoryAPIView.as_view(), name='note-category-detail'),
    path('notes/<uuid:user_id>', NoteAPIView.as_view(), name='note-list-create'),
    path('notes/<uuid:user_id>/<uuid:pk>', NoteAPIView.as_view(), name='note-detail'),
    path('note-comments/<uuid:note_id>', NoteCommentAPIView.as_view(), name='note-comments'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', NotesDashboardAPIView.as_view(), name='notes-dashboard'),
    path('employee-notes/<str:org_id>/<str:employee_id>', EmployeeNotesListAPIView.as_view(), name='employee-notes'),
]

