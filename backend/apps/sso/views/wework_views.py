"""
WeWork ViewSets

All viewsets inherit from BaseModelViewSetWithBatch for automatic
organization filtering, soft delete, and batch operations.
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.sso.models import WeWorkConfig, UserMapping
from apps.sso.serializers.wework_serializer import (
    WeWorkConfigSerializer,
    WeWorkConfigDetailSerializer,
    UserMappingSerializer,
)
from apps.sso.services.sso_service import WeWorkSSOService
from apps.sso.filters import WeWorkConfigFilter, UserMappingFilter


class WeWorkConfigViewSet(BaseModelViewSetWithBatch):
    """WeWork configuration management ViewSet."""

    queryset = WeWorkConfig.objects.all()
    serializer_class = WeWorkConfigDetailSerializer
    # Auto: organization filtering, soft delete, batch operations

    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = WeWorkConfigFilter
    search_fields = ['corp_name', 'corp_id']
    ordering_fields = ['created_at', 'corp_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Select serializer based on action."""
        if self.action == 'list':
            return WeWorkConfigSerializer
        return WeWorkConfigDetailSerializer

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public_config(self, request):
        """Get public WeWork configuration (for login page)."""
        try:
            sso_service = WeWorkSSOService()
            config = sso_service.get_config()
            return Response({
                'enabled': True,
                'corp_name': config.corp_name,
                'agent_id': config.agent_id
            })
        except ValueError:
            return Response({
                'enabled': False,
                'message': 'WeWork not configured or not enabled'
            })

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def auth_url(self, request):
        """Get WeWork OAuth authorization URL (for in-page redirect)."""
        redirect_uri = request.build_absolute_uri('/api/sso/callback/wework/')

        try:
            sso_service = WeWorkSSOService()
            auth_url = sso_service.get_auth_url(redirect_uri)
            return Response({'auth_url': auth_url})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def qr_url(self, request):
        """Get WeWork QR code login URL (for PC scan login)."""
        redirect_uri = request.build_absolute_uri('/api/sso/callback/wework/')

        try:
            sso_service = WeWorkSSOService()
            qr_url = sso_service.get_qr_connect_url(redirect_uri)
            return Response({'qr_url': qr_url})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def callback(self, request):
        """Handle WeWork OAuth callback."""
        code = request.data.get('code')
        state = request.data.get('state')

        if not code or not state:
            return Response({'error': 'Missing required parameters'}, status=400)

        try:
            sso_service = WeWorkSSOService()
            result = sso_service.handle_callback(code, state)
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': f'Login failed: {str(e)}'}, status=500)


class UserMappingViewSet(BaseModelViewSetWithBatch):
    """User platform mapping management ViewSet."""

    queryset = UserMapping.objects.all()
    serializer_class = UserMappingSerializer
    # Auto: organization filtering, soft delete, batch operations

    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = UserMappingFilter
    search_fields = ['platform_name', 'platform_userid']
    ordering_fields = ['created_at', 'platform']
    ordering = ['-created_at']

    def get_queryset(self):
        """Only return current user's mappings."""
        queryset = super().get_queryset()
        if self.request.user and self.request.user.is_authenticated:
            return queryset.filter(system_user=self.request.user)
        return queryset.none()

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bind_wework(self, request):
        """Bind WeWork account."""
        from apps.sso.adapters.wework_adapter import WeWorkAdapter

        user = request.user
        sso_service = WeWorkSSOService()
        config = sso_service.get_config()
        adapter = WeWorkAdapter(config)

        # Bind by userid or mobile
        wework_userid = request.data.get('wework_userid')
        mobile = request.data.get('mobile')

        try:
            if wework_userid:
                user_info = adapter.get_user_detail(wework_userid)
            elif mobile:
                # Find user by mobile
                user_list = adapter.get_user_list()
                found = None
                for u in user_list:
                    if u.get('mobile') == mobile:
                        found = u
                        break
                if not found:
                    return Response({
                        'error': 'No matching WeWork account found'
                    }, status=404)
                user_info = found
            else:
                return Response({
                    'error': 'Please provide WeWork userid or mobile'
                }, status=400)

            # Create binding using mapping service
            sso_service.mapping_service.create_or_update_mapping(
                user=user,
                platform='wework',
                platform_userid=user_info['userid'],
                platform_name=user_info['name']
            )

            return Response({'message': 'Binding successful'})

        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unbind(self, request, pk=None):
        """Unbind platform account."""
        instance = self.get_object()
        instance.soft_delete()
        return Response({'message': 'Unbind successful'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_mappings(self, request):
        """Get all platform mappings for current user."""
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'Not logged in'}, status=401)

        sso_service = WeWorkSSOService()
        mappings = sso_service.mapping_service.get_user_mappings(str(request.user.id))

        serializer = UserMappingSerializer(
            instance=mappings.values(),
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
