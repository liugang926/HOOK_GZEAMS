"""View and ViewSet implementations for smart search."""
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses.base import BaseResponse
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.search.filters import SavedSearchFilter, SearchHistoryFilter
from apps.search.models import SavedSearch, SearchHistory, SearchType
from apps.search.serializers import (
    SavedSearchSerializer,
    SearchHistorySerializer,
    SearchRequestSerializer,
    SuggestionQuerySerializer,
)
from apps.search.services import AssetSearchService, SavedSearchService, SearchHistoryService


def resolve_request_organization_id(request) -> str | None:
    """Resolve the active organization identifier from request context."""
    organization_id = getattr(request, 'organization_id', None)
    if organization_id:
        return str(organization_id)

    if getattr(request.user, 'current_organization_id', None):
        return str(request.user.current_organization_id)

    if getattr(request.user, 'organization_id', None):
        return str(request.user.organization_id)

    return None


class AssetSearchAPIView(APIView):
    """POST endpoint for smart asset search."""

    permission_classes = [IsAuthenticated]
    search_service = AssetSearchService()

    def post(self, request, *args, **kwargs):
        """Search assets using Elasticsearch or the database fallback."""
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization_id = resolve_request_organization_id(request)
        if not organization_id:
            return BaseResponse.error(
                code='ORGANIZATION_MISMATCH',
                message='Organization context is required for search.',
                http_status=status.HTTP_403_FORBIDDEN,
            )

        if serializer.validated_data.get('search_type') != SearchType.ASSET:
            return BaseResponse.error(
                code='METHOD_NOT_ALLOWED',
                message='Only asset smart search is implemented in this phase.',
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        payload = self.search_service.search_assets(
            organization_id=organization_id,
            user=request.user,
            keyword=serializer.validated_data.get('keyword', ''),
            filters=serializer.validated_data.get('filters', {}),
            sort_by=serializer.validated_data.get('sort_by', 'relevance'),
            sort_order=serializer.validated_data.get('sort_order', 'desc'),
            page=serializer.validated_data.get('page', 1),
            page_size=serializer.validated_data.get('page_size', 20),
        )
        return BaseResponse.success(data=payload, message='Search completed successfully')


class SearchSuggestionAPIView(APIView):
    """GET endpoint for type-ahead suggestions."""

    permission_classes = [IsAuthenticated]
    search_service = AssetSearchService()

    def get(self, request, *args, **kwargs):
        """Return live suggestions for the current keyword."""
        serializer = SuggestionQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        organization_id = resolve_request_organization_id(request)
        if not organization_id:
            return BaseResponse.error(
                code='ORGANIZATION_MISMATCH',
                message='Organization context is required for search suggestions.',
                http_status=status.HTTP_403_FORBIDDEN,
            )

        suggestions = self.search_service.get_suggestions(
            organization_id=organization_id,
            keyword=serializer.validated_data['keyword'],
            search_type=serializer.validated_data.get('type', SearchType.ASSET),
            limit=serializer.validated_data.get('limit', 10),
        )
        return BaseResponse.success(data=suggestions, message='Suggestions loaded successfully')


class SearchHistoryViewSet(BaseModelViewSetWithBatch):
    """ViewSet for search history management."""

    queryset = SearchHistory.objects.select_related(
        'organization',
        'user',
        'created_by',
        'updated_by',
        'deleted_by',
    ).all()
    serializer_class = SearchHistorySerializer
    filterset_class = SearchHistoryFilter
    service = SearchHistoryService()
    http_method_names = ['get', 'delete', 'head', 'options']

    def get_queryset(self):
        """Restrict search history to the current user."""
        queryset = super().get_queryset().filter(user=self.request.user)
        search_type = self.request.query_params.get('type')
        if search_type:
            queryset = queryset.filter(search_type=search_type)
        return queryset

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Soft-delete all history entries for the current user."""
        queryset = self.get_queryset()
        now = timezone.now()
        updated = queryset.update(
            is_deleted=True,
            deleted_at=now,
            deleted_by=request.user,
            updated_at=now,
        )
        return BaseResponse.success(
            data={'cleared_count': updated},
            message='Search history cleared successfully',
        )

    def destroy(self, request, *args, **kwargs):
        """Soft-delete a single history record with a standard response body."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return BaseResponse.success(message='Search history deleted successfully')


class SavedSearchViewSet(BaseModelViewSetWithBatch):
    """ViewSet for saved search presets."""

    queryset = SavedSearch.objects.select_related(
        'organization',
        'user',
        'created_by',
        'updated_by',
        'deleted_by',
    ).all()
    serializer_class = SavedSearchSerializer
    filterset_class = SavedSearchFilter
    service = SavedSearchService()

    def get_queryset(self):
        """Return current-user searches plus organization-shared searches."""
        queryset = super().get_queryset()
        search_type = self.request.query_params.get('type')
        if search_type:
            queryset = queryset.filter(search_type=search_type)

        if self.action in {'update', 'partial_update', 'destroy', 'restore', 'batch_delete', 'batch_update'}:
            return queryset.filter(user=self.request.user)

        return queryset.filter(
            Q(user=self.request.user) | Q(is_shared=True)
        ).distinct()

    def perform_create(self, serializer):
        """Assign the current user as the saved-search owner."""
        organization_id = resolve_request_organization_id(self.request)
        serializer.save(
            user=self.request.user,
            organization_id=organization_id,
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        """Preserve ownership and update audit fields."""
        serializer.save(user=self.request.user, updated_by=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create a saved search with a standard response envelope."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return BaseResponse.created(
            data=serializer.data,
            message='Saved search created successfully',
        )

    def retrieve(self, request, *args, **kwargs):
        """Return saved-search detail with a standard response envelope."""
        serializer = self.get_serializer(self.get_object())
        return BaseResponse.success(
            data=serializer.data,
            message='Saved search retrieved successfully',
        )

    def update(self, request, *args, **kwargs):
        """Update a saved search with a standard response envelope."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return BaseResponse.success(
            data=serializer.data,
            message='Saved search updated successfully',
        )

    def destroy(self, request, *args, **kwargs):
        """Soft-delete a saved search with a standard response envelope."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return BaseResponse.success(message='Saved search deleted successfully')

    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """Mark a saved search as used and return the reusable payload."""
        saved_search = self.get_object()
        AssetSearchService().increment_saved_search_usage(saved_search)
        return BaseResponse.success(
            data={
                'id': str(saved_search.id),
                'name': saved_search.name,
                'search_type': saved_search.search_type,
                'keyword': saved_search.keyword,
                'filters': saved_search.filters,
                'is_shared': saved_search.is_shared,
                'use_count': saved_search.use_count,
            },
            message='Saved search loaded successfully',
        )
