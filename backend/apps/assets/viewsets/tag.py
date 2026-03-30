"""
ViewSets for asset tag groups and asset tags.
"""
from django.db.models import Count, Prefetch, Q
from django.core.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.assets.filters.tag import AssetTagFilter, TagGroupFilter
from apps.assets.models import AssetTag, TagGroup
from apps.assets.serializers.tag import (
    AssetTagBatchMutationSerializer,
    AssetTagSerializer,
    TagGroupSerializer,
)
from apps.assets.services.tag_service import (
    AssetTagRelationService,
    AssetTagService,
    TagGroupService,
)
from apps.common.responses.base import BaseResponse
from apps.common.viewsets.base import BaseModelViewSetWithBatch


class TagGroupViewSet(BaseModelViewSetWithBatch):
    """CRUD endpoints for asset tag groups."""

    queryset = TagGroup.objects.none()
    serializer_class = TagGroupSerializer
    filterset_class = TagGroupFilter
    service = TagGroupService()
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['sort_order', 'name', 'code', 'created_at', 'updated_at']
    ordering = ['sort_order', 'name']

    def get_queryset(self):
        """Return a scoped queryset with nested active tags prefetched."""
        organization_id = self._resolve_organization_id()
        if not organization_id:
            return TagGroup.all_objects.none()

        return TagGroup.all_objects.filter(
            organization_id=organization_id,
            is_deleted=False,
        ).prefetch_related(
            Prefetch(
                'tags',
                queryset=AssetTag.all_objects.filter(
                    is_deleted=False,
                    is_active=True,
                ).select_related('tag_group').annotate(
                    asset_count=Count(
                        'asset_relations__asset',
                        filter=Q(
                            asset_relations__is_deleted=False,
                            asset_relations__asset__is_deleted=False,
                        ),
                        distinct=True,
                    ),
                ).order_by('sort_order', 'name'),
                to_attr='prefetched_tags',
            ),
        ).annotate(
            tags_count=Count(
                'tags',
                filter=Q(tags__is_deleted=False, tags__is_active=True),
                distinct=True,
            ),
        )

    def create(self, request, *args, **kwargs):
        """Wrap create responses in the standard API envelope."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return BaseResponse.created(
            data=serializer.data,
            message='Tag group created successfully',
        )

    def retrieve(self, request, *args, **kwargs):
        """Wrap detail responses in the standard API envelope."""
        serializer = self.get_serializer(self.get_object())
        return BaseResponse.success(
            data=serializer.data,
            message='Tag group retrieved successfully',
        )

    def update(self, request, *args, **kwargs):
        """Wrap update responses in the standard API envelope."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return BaseResponse.success(
            data=serializer.data,
            message='Tag group updated successfully',
        )

    def partial_update(self, request, *args, **kwargs):
        """Reuse the wrapped update flow for partial updates."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Soft delete tag groups while preventing system-group deletion."""
        instance = self.get_object()
        try:
            self.service.delete_group(instance, user=request.user)
        except ValidationError as exc:
            message = getattr(exc, 'message_dict', None) or getattr(exc, 'messages', None) or [str(exc)]
            if isinstance(message, dict):
                first_value = next(iter(message.values()), ['Tag group deletion is not allowed.'])
                if isinstance(first_value, list):
                    message = first_value[0]
                else:
                    message = first_value
            elif isinstance(message, list):
                message = message[0]
            return BaseResponse.error(
                code='PERMISSION_DENIED',
                message=str(message),
                http_status=403,
            )
        return BaseResponse.success(message='Tag group deleted successfully')


class AssetTagViewSet(BaseModelViewSetWithBatch):
    """CRUD and batch-assignment endpoints for asset tags."""

    queryset = AssetTag.objects.none()
    serializer_class = AssetTagSerializer
    filterset_class = AssetTagFilter
    service = AssetTagService()
    relation_service = AssetTagRelationService()
    search_fields = ['name', 'code', 'description', 'tag_group__name']
    ordering_fields = ['sort_order', 'name', 'code', 'created_at', 'updated_at']
    ordering = ['tag_group__sort_order', 'sort_order', 'name']

    def get_queryset(self):
        """Return a scoped queryset with usage counts annotated."""
        organization_id = self._resolve_organization_id()
        if not organization_id:
            return AssetTag.all_objects.none()

        return AssetTag.all_objects.filter(
            organization_id=organization_id,
            is_deleted=False,
            tag_group__is_deleted=False,
        ).select_related('tag_group').annotate(
            asset_count=Count(
                'asset_relations__asset',
                filter=Q(
                    asset_relations__is_deleted=False,
                    asset_relations__asset__is_deleted=False,
                ),
                distinct=True,
            ),
        )

    def create(self, request, *args, **kwargs):
        """Wrap create responses in the standard API envelope."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return BaseResponse.created(
            data=serializer.data,
            message='Asset tag created successfully',
        )

    def retrieve(self, request, *args, **kwargs):
        """Wrap detail responses in the standard API envelope."""
        serializer = self.get_serializer(self.get_object())
        return BaseResponse.success(
            data=serializer.data,
            message='Asset tag retrieved successfully',
        )

    def update(self, request, *args, **kwargs):
        """Wrap update responses in the standard API envelope."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return BaseResponse.success(
            data=serializer.data,
            message='Asset tag updated successfully',
        )

    def partial_update(self, request, *args, **kwargs):
        """Reuse the wrapped update flow for partial updates."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Soft delete tags and their active relations."""
        instance = self.get_object()
        self.service.delete_tag(instance, user=request.user)
        return BaseResponse.success(message='Asset tag deleted successfully')

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """Return asset tag usage statistics for the current organization."""
        payload = self.service.get_tag_statistics(
            tag_group_id=request.query_params.get('tag_group'),
            organization_id=getattr(request, 'organization_id', None),
            user=request.user,
        )
        return BaseResponse.success(
            data=payload,
            message='Asset tag statistics retrieved successfully',
        )

    @action(detail=False, methods=['post'], url_path='batch-add')
    def batch_add(self, request):
        """Apply selected tags to multiple assets."""
        serializer = AssetTagBatchMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = self.relation_service.batch_add_tags(
            asset_ids=serializer.validated_data['asset_ids'],
            tag_ids=serializer.validated_data['tag_ids'],
            notes=serializer.validated_data.get('notes', ''),
            organization_id=getattr(request, 'organization_id', None),
            user=request.user,
        )
        return Response(
            {
                'success': True,
                'message': 'Batch tag assignment completed',
                'summary': {
                    'total': len(payload['results']),
                    'succeeded': len(payload['results']),
                    'failed': 0,
                    **payload['summary'],
                },
                'results': payload['results'],
            }
        )

    @action(detail=False, methods=['post'], url_path='batch-remove')
    def batch_remove(self, request):
        """Remove selected tags from multiple assets."""
        serializer = AssetTagBatchMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = self.relation_service.batch_remove_tags(
            asset_ids=serializer.validated_data['asset_ids'],
            tag_ids=serializer.validated_data['tag_ids'],
            organization_id=getattr(request, 'organization_id', None),
            user=request.user,
        )
        return Response(
            {
                'success': True,
                'message': 'Batch tag removal completed',
                'summary': {
                    'total': len(payload['results']),
                    'succeeded': len(payload['results']),
                    'failed': 0,
                    **payload['summary'],
                },
                'results': payload['results'],
            }
        )
