"""
Helpdesk Management URLs
"""

from django.urls import path
from .views import (
    TicketCategoryAPIView, TicketAPIView, TicketCommentAPIView
)
from .additional_utility_views import *

urlpatterns = [
    # Ticket Categories
    path('categories/<uuid:org_id>', TicketCategoryAPIView.as_view(), name='ticket-categories'),
    path('categories/<uuid:org_id>/<uuid:pk>', TicketCategoryAPIView.as_view(), name='ticket-category-detail'),
    
    # Tickets
    path('tickets/<uuid:org_id>', TicketAPIView.as_view(), name='tickets'),
    path('tickets/<uuid:org_id>/<uuid:pk>', TicketAPIView.as_view(), name='ticket-detail'),
    
    # Ticket Comments
    path('tickets/<uuid:ticket_id>/comments', TicketCommentAPIView.as_view(), name='ticket-comments'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', HelpdeskDashboardAPIView.as_view(), name='helpdesk-dashboard'),
    path('assigned-tickets/<str:org_id>/<str:user_id>', AssignedTicketsAPIView.as_view(), name='assigned-tickets'),
]

