"""
ViewSet for system tag management and batch association actions.
"""
from rest_framework import status
from rest_framework.decorators import action

from apps.common.responses.base import BaseResponse
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.system.models import Tag
from apps.system.tag_filter import TagFilter
from apps.system.tag_serializer import TagObjectActionSerializer, TagSerializer
from apps.system.tag_service import TagService


class TagViewSet(BaseModelViewSetWithBatch):
    """CRUD and association endpoints for system tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filterset_class = TagFilter
    service = TagService()
    search_fields = ['name', 'description', 'biz_type']
    ordering_fields = ['name', 'biz_type', 'usage_count', 'created_at', 'updated_at']
    ordering = ['-usage_count', 'name']

    @action(detail=False, methods=['get'], url_path='business-object-options')
    def business_object_options(self, request):
        """Return selectable business object codes for tag grouping."""
        return BaseResponse.success(
            data=self.service.get_business_object_options(),
            message='Business object options retrieved successfully',
        )

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """Return tag summary metrics for the current organization."""
        return BaseResponse.success(
            data=self.service.get_statistics(
                organization_id=getattr(request, 'organization_id', None),
                user=request.user,
            ),
            message='Tag statistics retrieved successfully',
        )

    @action(detail=False, methods=['post'], url_path='apply')
    def apply(self, request):
        """Assign selected tags to selected business object records."""
        serializer = TagObjectActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = self.service.apply_tags(
            **serializer.validated_data,
            user=request.user,
            organization_id=getattr(request, 'organization_id', None),
        )
        return BaseResponse.success(
            data=result,
            message='Tags applied successfully',
        )

    @action(detail=False, methods=['post'], url_path='remove')
    def remove(self, request):
        """Remove selected tags from selected business object records."""
        serializer = TagObjectActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = self.service.remove_tags(
            **serializer.validated_data,
            user=request.user,
            organization_id=getattr(request, 'organization_id', None),
        )
        return BaseResponse.success(
            data=result,
            message='Tags removed successfully',
        )
