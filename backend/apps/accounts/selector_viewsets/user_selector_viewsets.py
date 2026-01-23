"""
ViewSets for User selection components.
"""
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.responses.base import BaseResponse
from apps.accounts.models import User


class UserSelectorViewSet(BaseModelViewSet):
    """
    ViewSet for user selection in forms.

    Provides optimized endpoints for:
    - User search/autocomplete
    - User selection by department
    - Current user info
    """

    permission_classes = [IsAuthenticated]
    queryset = User.objects.filter(is_deleted=False)

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Search users by name or username.

        GET /api/users/selector/search/?q=keyword&organization_id=xxx

        Query params:
        - q: Search keyword (username, full name, email)
        - organization_id: Filter by organization
        - limit: Max results (default 50)
        """
        from apps.accounts.serializers import UserSelectorSerializer

        keyword = request.query_params.get('q', '')
        organization_id = request.query_params.get('organization_id')
        limit = int(request.query_params.get('limit', 50))

        current_org_id = getattr(request, 'organization_id', None)

        queryset = User.objects.filter(
            is_deleted=False,
            is_active=True
        )

        # Filter by current organization context if no specific org requested
        if not organization_id and current_org_id:
            organization_id = current_org_id

        # Filter by organization if specified
        if organization_id:
            from apps.accounts.models import UserOrganization
            user_ids = UserOrganization.objects.filter(
                organization_id=organization_id,
                is_active=True
            ).values_list('user_id', flat=True)
            queryset = queryset.filter(id__in=user_ids)

        if keyword:
            queryset = queryset.filter(
                username__icontains=keyword
            ) | queryset.filter(
                first_name__icontains=keyword
            ) | queryset.filter(
                last_name__icontains=keyword
            ) | queryset.filter(
                email__icontains=keyword
            )

        users = queryset[:limit]
        serializer = UserSelectorSerializer(users, many=True)

        return BaseResponse.success(
            data=serializer.data,
            message='Users retrieved successfully'
        )

    @action(detail=False, methods=['get'], url_path='by-organization/(?P<organization_id>[^/.]+)')
    def by_organization(self, request, organization_id=None):
        """
        Get users in a specific organization.

        GET /api/users/selector/by-organization/{organization_id}/
        """
        from apps.accounts.serializers import UserSelectorSerializer
        from apps.accounts.models import UserOrganization

        current_org_id = getattr(request, 'organization_id', None)

        users = User.objects.filter(
            is_deleted=False,
            is_active=True
        )

        # Filter by organization
        user_ids = UserOrganization.objects.filter(
            organization_id=organization_id,
            is_active=True
        ).values_list('user_id', flat=True)
        users = users.filter(id__in=user_ids)

        serializer = UserSelectorSerializer(users, many=True)

        return BaseResponse.success(
            data=serializer.data,
            message='Organization users retrieved successfully'
        )

    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        """
        Get current user info.

        GET /api/users/selector/current/
        """
        from apps.accounts.serializers import UserSelectorSerializer

        serializer = UserSelectorSerializer(request.user)

        return BaseResponse.success(
            data=serializer.data,
            message='Current user retrieved successfully'
        )
