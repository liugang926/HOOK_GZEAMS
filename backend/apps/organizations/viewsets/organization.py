"""
ViewSets for Organization model.
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from apps.organizations.models import Organization, Department, UserDepartment
from apps.organizations.serializers import (
    OrganizationSerializer,
    OrganizationTreeSerializer,
    OrganizationCreateSerializer,
    OrganizationListSerializer,
    DepartmentSerializer,
    DepartmentTreeSerializer,
    DepartmentListSerializer,
    DepartmentCreateSerializer,
    UserDepartmentSerializer,
    UserDepartmentListSerializer,
    UserDepartmentCreateSerializer,
    SetPrimaryDepartmentSerializer,
)
from apps.organizations.filters import DepartmentFilter, UserDepartmentFilter
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.middleware import get_current_organization
from apps.common.responses.base import BaseResponse


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Organization management.

    Note: Organization does NOT inherit from BaseModel to avoid
    circular references, so we implement standard DRF ViewSet behavior.
    """

    queryset = Organization.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return OrganizationListSerializer
        if self.action == 'create':
            return OrganizationCreateSerializer
        if self.action == 'tree':
            return OrganizationTreeSerializer
        return OrganizationSerializer

    def list(self, request, *args, **kwargs):
        """List all organizations."""
        queryset = self.get_queryset()
        serializer = OrganizationListSerializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """Get single organization."""
        instance = self.get_object()
        serializer = OrganizationSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Create new organization."""
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response({
            'success': True,
            'data': OrganizationSerializer(serializer.instance).data,
            'message': 'Organization created successfully'
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update organization."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = OrganizationSerializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Organization updated successfully'
        })

    def destroy(self, request, *args, **kwargs):
        """Soft delete organization."""
        instance = self.get_object()

        # Check if organization has children
        if instance.children.filter(is_deleted=False).exists():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Cannot delete organization with child organizations.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if organization has users
        from apps.accounts.models import UserOrganization
        if UserOrganization.objects.filter(
            organization=instance,
            is_active=True
        ).exists():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Cannot delete organization with active users.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        instance.is_deleted = True
        instance.save()
        return Response({
            'success': True,
            'message': 'Organization deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """Get organization tree structure."""
        # Get root organizations (no parent)
        roots = Organization.objects.filter(
            parent=None,
            is_deleted=False,
            is_active=True
        )
        serializer = OrganizationTreeSerializer(roots, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='regenerate-invite')
    def regenerate_invite(self, request, pk=None):
        """Regenerate invite code for organization."""
        instance = self.get_object()
        instance.regenerate_invite_code()
        return Response({
            'success': True,
            'data': {
                'invite_code': instance.invite_code,
                'expires_at': instance.invite_code_expires_at
            },
            'message': 'Invite code regenerated'
        })


# =============================================================================
# Department ViewSet
# =============================================================================

class DepartmentViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Department management.

    Inherits from BaseModelViewSetWithBatch for automatic
    organization filtering, soft delete, and batch operations.
    """

    queryset = Department.objects.select_related(
        'parent', 'leader', 'organization'
    ).all()
    serializer_class = DepartmentSerializer
    filterset_class = DepartmentFilter
    search_fields = ['code', 'name', 'full_path_name']
    ordering_fields = ['level', 'order', 'name', 'code']
    ordering = ['level', 'order', 'code']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DepartmentListSerializer
        if self.action == 'tree':
            return DepartmentTreeSerializer
        if self.action == 'create':
            return DepartmentCreateSerializer
        return DepartmentSerializer

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """
        Get full department tree for current organization.

        Returns nested tree structure with all departments.
        """
        organization = get_current_organization()
        if not organization:
            return Response({
                'success': False,
                'error': {
                    'code': 'ORGANIZATION_NOT_FOUND',
                    'message': 'Cannot determine current organization'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get root departments (no parent) for this organization
        roots = Department.objects.filter(
            organization=organization,
            parent=None,
            is_deleted=False,
            is_active=True
        ).order_by('order', 'code')

        # Build tree structure
        tree = [dept.get_full_tree() for dept in roots]

        return Response({
            'success': True,
            'data': {
                'tree': tree,
                'count': Department.objects.filter(
                    organization=organization,
                    is_deleted=False
                ).count()
            }
        })

    @action(detail=True, methods=['get'], url_path='children')
    def children(self, request, pk=None):
        """Get direct children of a department."""
        department = self.get_object()
        children = department.children.filter(
            is_deleted=False,
            is_active=True
        ).order_by('order', 'code')
        serializer = DepartmentListSerializer(children, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['get'], url_path='users')
    def users(self, request, pk=None):
        """Get users in a department."""
        department = self.get_object()
        user_depts = UserDepartment.objects.filter(
            department=department,
            is_deleted=False
        ).select_related('user')
        serializer = UserDepartmentListSerializer(user_depts, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['get'], url_path='descendants')
    def descendants(self, request, pk=None):
        """Get all descendant department IDs."""
        department = self.get_object()
        descendant_ids = department.get_descendant_ids()
        return Response({
            'success': True,
            'data': {
                'department_id': str(department.id),
                'descendant_ids': [str(id) for id in descendant_ids]
            }
        })

    @action(detail=True, methods=['get'], url_path='ancestors')
    def ancestors(self, request, pk=None):
        """Get all ancestor department IDs."""
        department = self.get_object()
        ancestor_ids = department.get_ancestor_ids()
        ancestors = Department.objects.filter(
            id__in=ancestor_ids,
            is_deleted=False
        ).order_by('level')
        serializer = DepartmentListSerializer(ancestors, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['get'], url_path='path')
    def path(self, request, pk=None):
        """
        Get breadcrumb path for a department.

        GET /api/organizations/departments/{id}/path/

        Returns hierarchical path from root to the department.
        """
        from apps.organizations.services.department_service import DepartmentService

        department = self.get_object()
        service = DepartmentService()
        path_data = service.get_department_path(department.id)

        return BaseResponse.success(
            data=path_data,
            message='Department path retrieved successfully'
        )

    @action(detail=False, methods=['get'], url_path='select-options')
    def select_options(self, request):
        """
        Get departments formatted for select component.

        GET /api/organizations/departments/select-options/

        Returns flat list with id, name, and path for display.
        Each option includes the full hierarchical path in the label.
        """
        from apps.organizations.services.department_service import DepartmentService

        organization = get_current_organization()

        if not organization:
            return BaseResponse.error(
                code='ORGANIZATION_NOT_FOUND',
                message='Cannot determine current organization'
            )

        service = DepartmentService()
        options = service.get_select_options(str(organization.id))

        return BaseResponse.success(
            data=options,
            message='Department options retrieved successfully'
        )


# =============================================================================
# UserDepartment ViewSet
# =============================================================================

class UserDepartmentViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for UserDepartment management.

    Manages user-department associations, supporting
    multiple departments per user.
    """

    queryset = UserDepartment.objects.select_related(
        'user', 'department', 'organization'
    ).all()
    serializer_class = UserDepartmentSerializer
    filterset_class = UserDepartmentFilter
    search_fields = ['user__username', 'user__real_name', 'department__name']
    ordering_fields = ['is_primary', 'is_leader', 'created_at']
    ordering = ['-is_primary', 'is_leader', '-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return UserDepartmentListSerializer
        if self.action == 'create':
            return UserDepartmentCreateSerializer
        return UserDepartmentSerializer

    @action(detail=False, methods=['get'], url_path='my-departments')
    def my_departments(self, request):
        """Get current user's departments."""
        user = request.user
        organization = get_current_organization()

        if not organization:
            return Response({
                'success': False,
                'error': {
                    'code': 'ORGANIZATION_NOT_FOUND',
                    'message': 'Cannot determine current organization'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        user_depts = UserDepartment.objects.filter(
            user=user,
            organization=organization,
            is_deleted=False
        ).select_related('department')

        serializer = UserDepartmentListSerializer(user_depts, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='set-primary')
    def set_primary(self, request):
        """
        Set user's primary department.

        Request body:
            user_id: UUID
            department_id: UUID
        """
        serializer = SetPrimaryDepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = request.data.get('user_id')
        department_id = serializer.validated_data['department_id']
        organization = get_current_organization()

        if not organization:
            return Response({
                'success': False,
                'error': {
                    'code': 'ORGANIZATION_NOT_FOUND',
                    'message': 'Cannot determine current organization'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Find the user department association
        user_dept = UserDepartment.objects.filter(
            user_id=user_id,
            department_id=department_id,
            organization=organization,
            is_deleted=False
        ).first()

        if not user_dept:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'User department association not found'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        # Set as primary (save method will handle clearing other primaries)
        user_dept.is_primary = True
        user_dept.save()

        return Response({
            'success': True,
            'message': 'Primary department set successfully',
            'data': UserDepartmentSerializer(user_dept).data
        })

    @action(detail=False, methods=['get'], url_path='by-user')
    def by_user(self, request):
        """Get departments for a specific user."""
        user_id = request.query_params.get('user_id')
        organization = get_current_organization()

        if not user_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'user_id query parameter is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if not organization:
            return Response({
                'success': False,
                'error': {
                    'code': 'ORGANIZATION_NOT_FOUND',
                    'message': 'Cannot determine current organization'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        user_depts = UserDepartment.objects.filter(
            user_id=user_id,
            organization=organization,
            is_deleted=False
        ).select_related('department')

        serializer = UserDepartmentListSerializer(user_depts, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-department')
    def by_department(self, request):
        """Get users for a specific department."""
        department_id = request.query_params.get('department_id')
        organization = get_current_organization()

        if not department_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'department_id query parameter is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if not organization:
            return Response({
                'success': False,
                'error': {
                    'code': 'ORGANIZATION_NOT_FOUND',
                    'message': 'Cannot determine current organization'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        user_depts = UserDepartment.objects.filter(
            department_id=department_id,
            organization=organization,
            is_deleted=False
        ).select_related('user')

        serializer = UserDepartmentListSerializer(user_depts, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
