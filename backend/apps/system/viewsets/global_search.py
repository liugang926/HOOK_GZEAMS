"""
Global Search API View — cross-object search endpoint.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses.base import BaseResponse
from apps.system.services.global_search_service import GlobalSearchService


class GlobalSearchAPIView(APIView):
    """
    GET /api/system/global-search/?q=<keyword>&limit=5&object_codes=code1,code2

    Returns search results grouped by object type.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        keyword = (request.query_params.get('q') or '').strip()
        if len(keyword) < 2:
            return BaseResponse.success(data=[])

        limit = min(int(request.query_params.get('limit', 5)), 10)

        object_codes_raw = request.query_params.get('object_codes', '')
        object_codes = (
            [c.strip() for c in object_codes_raw.split(',') if c.strip()]
            if object_codes_raw else None
        )

        service = GlobalSearchService()
        try:
            results = service.search(
                keyword=keyword,
                limit_per_object=limit,
                object_codes=object_codes,
            )
            return BaseResponse.success(data=results)
        except Exception as exc:
            return BaseResponse.error(
                code='SEARCH_ERROR',
                message=str(exc),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
