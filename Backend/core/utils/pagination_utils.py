
# =================================PAGINATION=================================
from rest_framework import pagination
from rest_framework.exceptions import NotFound

class CustomPagination(pagination.PageNumberPagination):
    page_size = 50000000000000
    page_size_query_param = 'page_size'
    max_page_size = 50000000000000
    page_query_param = 'page'

    def paginate_queryset(self, queryset, request, view=None):
        page_number = request.query_params.get(self.page_query_param)

        try:
            page = super().paginate_queryset(queryset, request, view)
        except NotFound as e:
            raise NotFound(detail=f"Invalid page number: {page_number}")
        
        if 'page_size' not in request.query_params:
            self.page_size = self.max_page_size

        return page

    def get_paginated_response(self, data):
        next_page_number = self.page.next_page_number() if self.page.has_next() else None
        previous_page_number = self.page.previous_page_number() if self.page.has_previous() else None
        return ({
            'total_pages': self.page.paginator.num_pages,
            'current_page_number': self.page.number,
            'page_size': self.page_size_query_param,
            'total_objects': self.page.paginator.count,
            'previous_page_number': previous_page_number,
            'next_page_number': next_page_number,
        })