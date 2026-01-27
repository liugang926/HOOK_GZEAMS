"""
ViewSets for User management.

Provides API endpoints for user CRUD operations and organization management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.accounts.models import User, UserOrganization
from apps.accounts.serializers import (
    UserSerializer,
    UserBasicSerializer,
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserOrganizationSerializer,
)
from apps.accounts.services.user_service import UserService


class UserViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for User management.

    Provides CRUD operations for users with organization-based filtering.
    """

    queryset = User.objects.filter(is_deleted=False)
    serializer_class = UserListSerializer
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return UserListSerializer
        if self.action == 'retrieve':
            return UserDetailSerializer
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserListSerializer

    def get_queryset(self):
        """Filter users based on organization context."""
        queryset = super().get_queryset()
        org_id = getattr(self.request, 'organization_id', None)

        if org_id:
            # Only show users in this organization
            user_ids = UserOrganization.objects.filter(
                organization_id=org_id,
                is_active=True
            ).values_list('user_id', flat=True)
            queryset = queryset.filter(id__in=user_ids)

        return queryset

    def retrieve(self, request, *args, **kwargs):
        """Get single user with full details."""
        instance = self.get_object()
        serializer = UserDetailSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Create a new user."""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Set created_by if not set
        if not user.created_by_id and request.user.is_authenticated:
            user.created_by = request.user
            user.save()

        result_serializer = UserDetailSerializer(user)
        return Response({
            'success': True,
            'data': result_serializer.data,
            'message': 'User created successfully.'
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update user information."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # For non-self updates, use specific serializer
        if instance == request.user:
            serializer = UserUpdateSerializer(
                instance,
                data=request.data,
                partial=partial
            )
        else:
            serializer = UserUpdateSerializer(
                instance,
                data=request.data,
                partial=partial
            )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        result_serializer = UserDetailSerializer(instance)
        return Response({
            'success': True,
            'data': result_serializer.data,
            'message': 'User updated successfully.'
        })

    def destroy(self, request, *args, **kwargs):
        """Soft delete a user."""
        instance = self.get_object()

        # Prevent deleting self
        if instance == request.user:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_OPERATION',
                    'message': 'Cannot delete your own account'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Use soft delete
        instance.soft_delete(request.user)

        return Response({
            'success': True,
            'message': 'User deleted successfully.'
        })

    @action(detail=False, methods=['post'], url_path='login', authentication_classes=[])
    def login(self, request):
        """
        Login endpoint for user authentication.

        Accepts username and password, returns JWT access token.
        Does not require authentication (authentication_classes=[]).
        """
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Username and password are required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate user
        user = authenticate(username=username, password=password)

        if user is None:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid username or password'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({
                'success': False,
                'error': {
                    'code': 'ACCOUNT_DISABLED',
                    'message': 'This account has been disabled'
                }
            }, status=status.HTTP_403_FORBIDDEN)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Get user's primary organization
        primary_org = user.user_orgs.filter(is_primary=True, is_active=True).first()
        if not primary_org:
            # Fallback to any active organization
            primary_org = user.user_orgs.filter(is_active=True).first()

        org_data = None
        if primary_org:
            org_data = {
                'id': str(primary_org.organization.id),
                'name': primary_org.organization.name,
                'role': primary_org.role
            }

        # Serialize user data
        serializer = UserDetailSerializer(user)

        return Response({
            'success': True,
            'data': {
                'token': access_token,
                'refresh_token': str(refresh),
                'user': serializer.data,
                'organization': org_data
            },
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        """
        Logout endpoint.

        In JWT-based auth, logout is typically handled client-side by deleting the token.
        This endpoint can be used to blacklist tokens if blacklist app is enabled.
        """
        return Response({
            'success': True,
            'message': 'Logout successful'
        })

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Get current user information."""
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserDetailSerializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='me/change-password')
    def change_password(self, request):
        """Change current user's password."""
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # Update password
        request.user.password = make_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response({
            'success': True,
            'message': 'Password changed successfully.'
        })

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Get user statistics for current organization."""
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        org_id = getattr(request, 'organization_id', None)
        if not org_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Organization context required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        service = UserService()
        stats = service.get_user_stats(org_id)

        return Response({
            'success': True,
            'data': stats
        })

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """Activate a user account."""
        instance = self.get_object()
        service = UserService()
        service.activate_user(str(instance.id))

        return Response({
            'success': True,
            'message': 'User activated successfully.'
        })

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        """Deactivate a user account."""
        instance = self.get_object()

        # Prevent deactivating self
        if instance == request.user:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_OPERATION',
                    'message': 'Cannot deactivate your own account'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        service = UserService()
        service.deactivate_user(str(instance.id))

        return Response({
            'success': True,
            'message': 'User deactivated successfully.'
        })

    @action(detail=True, methods=['get'], url_path='organizations')
    def organizations(self, request, pk=None):
        """Get user's organization memberships."""
        instance = self.get_object()
        user_orgs = instance.user_orgs.filter(is_active=True).select_related('organization')

        serializer = UserOrganizationSerializer(user_orgs, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='switch-org')
    def switch_org(self, request, pk=None):
        """Switch user's current organization."""
        instance = self.get_object()

        # Only allow users to switch their own organization
        if instance != request.user:
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'Can only switch your own organization'
                }
            }, status=status.HTTP_403_FORBIDDEN)

        org_id = request.data.get('organization_id')
        if not org_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'organization_id is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        service = UserService()
        success = service.switch_organization(str(instance.id), org_id)

        if not success:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_OPERATION',
                    'message': 'Cannot switch to specified organization'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserDetailSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Organization switched successfully.'
        })

    @action(detail=False, methods=['get'], url_path='accessible')
    def accessible(self, request):
        """Get users accessible to current user in current organization."""
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        org_id = getattr(request, 'organization_id', None)
        service = UserService()

        filters = {}
        search = request.query_params.get('search')
        if search:
            filters['search'] = search

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            filters['is_active'] = is_active.lower() == 'true'

        queryset = service.get_accessible_users(org_id, filters)

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        users = queryset[start:end]

        serializer = UserBasicSerializer(users, many=True)
        return Response({
            'success': True,
            'data': {
                'count': total,
                'results': serializer.data,
                'page': page,
                'page_size': page_size,
            }
        })
