"""
Custom pagination classes for standardized API responses.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.common.responses.base import success_response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class that wraps results in the standard response format.

    Returns:
    {
        "success": true,
        "message": "Operation successful",
        "data": {
            "count": 100,
            "next": "...",
            "previous": "...",
            "results": [...]
        }
    }
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Return a paginated response in the standard format.
        """
        return Response({
            'success': True,
            'message': 'Operation successful',
            'data': {
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data
            }
        })
