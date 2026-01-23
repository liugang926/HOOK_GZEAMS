"""
ViewSets for Asset models.
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.assets.models import AssetCategory
from apps.assets.serializers import (
    AssetCategorySerializer,
    AssetCategoryTreeSerializer,
    AssetCategoryCreateSerializer,
    AssetCategoryListSerializer,
    AddChildSerializer,
)
from apps.assets.filters import AssetCategoryFilter
from apps.assets.services import AssetCategoryService


class AssetCategoryViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Asset Category management.

    Provides:
    - Standard CRUD operations
    - Tree endpoint for hierarchical data
    - add_child action for quick subcategory creation
    """
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    filterset_class = AssetCategoryFilter
    service = AssetCategoryService()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AssetCategoryListSerializer
        if self.action == 'create':
            return AssetCategoryCreateSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        """Add organization_id to serializer context."""
        context = super().get_serializer_context()
        # Try to get organization_id from request
        if hasattr(self.request, 'organization_id'):
            context['organization_id'] = self.request.organization_id
        return context

    def perform_create(self, serializer):
        """Set organization and created_by on create."""
        organization_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            organization_id=organization_id,
            created_by=self.request.user
        )

    def perform_update(self, serializer):
        """Set updated_by on update."""
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Override to check if category can be deleted."""
        instance = self.get_object()

        if not instance.can_delete():
            return BaseResponse.error(
                    code='VALIDATION_ERROR',
                    message='Cannot delete category with children or associated assets.',
                    details={'reason': 'has_children_or_assets'}
                )

        # Perform soft delete
        return super().destroy(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return BaseResponse.created(
            data=serializer.data,
            message='Create successful'
        )

    def list(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Use the default paginated response format
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return BaseResponse.success(
                data=serializer.data,
                message='Query successful'
            )

    def retrieve(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return BaseResponse.success(
                data=serializer.data,
                message='Query successful'
            )

    def update(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return BaseResponse.success(
                data=serializer.data,
                message='Update successful'
            )

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """
        Get complete category tree.

        GET /api/assets/categories/tree/
        """
        organization_id = getattr(request, 'organization_id', None)

        if not organization_id:
            return BaseResponse.error(
                    code='UNAUTHORIZED',
                    message='Organization context required'
                )

        tree_data = self.service.get_tree(organization_id)

        return BaseResponse.success(
                data=tree_data,
                message='Query successful'
            )

    @action(detail=True, methods=['get'], url_path='path')
    def path(self, request, pk=None):
        """
        Get breadcrumb path for a category.

        GET /api/assets/categories/{id}/path/

        Returns array of ancestors from root to current category.
        """
        category = self.get_object()
        path_data = self.service.get_category_path(category.id)

        return BaseResponse.success(
                data=path_data,
                message='Category path retrieved successfully'
            )

    @action(detail=True, methods=['post'], url_path='add_child')
    def add_child(self, request, pk=None):
        """
        Add child category to this category.

        POST /api/assets/categories/{id}/add_child/
        """
        parent = self.get_object()
        serializer = AddChildSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            child = self.service.add_child(
                parent_id=parent.id,
                data=serializer.validated_data,
                organization_id=getattr(request, 'organization_id', None),
                user=request.user
            )
        except ValueError as e:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message=str(e)
            )

        response_serializer = AssetCategoryCreateSerializer(child)

        return BaseResponse.created(
            data=response_serializer.data,
            message='Create successful'
        )
