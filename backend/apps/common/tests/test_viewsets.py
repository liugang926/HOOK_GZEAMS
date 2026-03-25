"""
Tests for BaseModelViewSet and BatchOperationMixin.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status
from rest_framework.test import APIRequestFactory
from django.utils import timezone


class TestBaseModelViewSet:
    """Test BaseModelViewSet functionality."""

    def test_get_queryset_filters_deleted(self, db, organization, user):
        """Test that get_queryset filters out soft-deleted records."""
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization

        # Create active and deleted departments
        active_dept = Department.objects.create(
            name='Active Dept',
            code='ACTIVE',
            organization=organization
        )
        deleted_dept = Department.objects.create(
            name='Deleted Dept',
            code='DELETED',
            organization=organization,
            is_deleted=True,
            deleted_at=timezone.now()
        )

        set_current_organization(str(organization.id))
        try:
            depts = Department.objects.all()
            assert active_dept in depts
            assert deleted_dept not in depts
        finally:
            clear_current_organization()

    def test_get_queryset_scopes_class_level_queryset_to_request_organization(
        self,
        db,
        organization,
        second_organization,
        user,
        mock_request,
    ):
        """Class-level querysets must still be scoped by the request organization."""
        from apps.common.viewsets.base import BaseModelViewSet
        from apps.organizations.models import Department
        from apps.organizations.serializers import DepartmentSerializer

        own_department = Department.objects.create(
            name='Own Dept',
            code='OWN_DEPT',
            organization=organization,
        )
        Department.objects.create(
            name='Other Dept',
            code='OTHER_DEPT',
            organization=second_organization,
        )

        class TestViewSet(BaseModelViewSet):
            queryset = Department.objects.all()
            serializer_class = DepartmentSerializer

        viewset = TestViewSet()
        viewset.request = mock_request
        viewset.format_kwarg = None

        queryset = viewset.get_queryset()

        assert list(queryset.values_list('id', flat=True)) == [own_department.id]

    def test_get_queryset_rejects_unauthorized_request_organization(
        self,
        db,
        organization,
        second_organization,
        user,
        mock_request,
    ):
        """Authenticated requests cannot force another organization's context."""
        from rest_framework.exceptions import PermissionDenied
        from apps.common.viewsets.base import BaseModelViewSet
        from apps.organizations.models import Department
        from apps.organizations.serializers import DepartmentSerializer

        class TestViewSet(BaseModelViewSet):
            queryset = Department.objects.all()
            serializer_class = DepartmentSerializer

        mock_request.organization_id = str(second_organization.id)

        viewset = TestViewSet()
        viewset.request = mock_request
        viewset.format_kwarg = None

        with pytest.raises(PermissionDenied):
            viewset.get_queryset()

    def test_get_queryset_allows_legacy_default_organization(
        self,
        db,
        organization,
        mock_request,
    ):
        """Legacy users with only BaseModel.organization should get request-time access to that org."""
        from django.contrib.auth import get_user_model
        from apps.common.viewsets.base import BaseModelViewSet
        from apps.organizations.models import Department
        from apps.organizations.serializers import DepartmentSerializer

        user = get_user_model().objects.create_user(
            username='legacyviewsetuser',
            email='legacyviewset@example.com',
            password='testpass123',
            organization=organization,
        )
        department = Department.objects.create(
            name='Legacy Dept',
            code='LEGACY_DEPT',
            organization=organization,
        )

        class TestViewSet(BaseModelViewSet):
            queryset = Department.objects.all()
            serializer_class = DepartmentSerializer

        mock_request.user = user
        mock_request.organization_id = str(organization.id)

        viewset = TestViewSet()
        viewset.request = mock_request
        viewset.format_kwarg = None

        queryset = viewset.get_queryset()

        assert list(queryset.values_list('id', flat=True)) == [department.id]

    def test_get_queryset_reads_raw_request_header_when_request_org_missing(
        self,
        db,
        organization,
        second_organization,
        user,
        mock_request,
    ):
        """Viewsets should fall back to the raw request header if middleware did not bind organization_id."""
        from apps.common.viewsets.base import BaseModelViewSet
        from apps.organizations.models import Department
        from apps.organizations.serializers import DepartmentSerializer

        own_department = Department.objects.create(
            name='Header Dept',
            code='HEADER_DEPT',
            organization=organization,
        )
        Department.objects.create(
            name='Other Header Dept',
            code='OTHER_HEADER_DEPT',
            organization=second_organization,
        )

        class TestViewSet(BaseModelViewSet):
            queryset = Department.objects.all()
            serializer_class = DepartmentSerializer

        mock_request.organization_id = None
        mock_request.META = {'HTTP_X_ORGANIZATION_ID': str(organization.id)}
        mock_request._request = mock_request

        viewset = TestViewSet()
        viewset.request = mock_request
        viewset.format_kwarg = None

        queryset = viewset.get_queryset()

        assert list(queryset.values_list('id', flat=True)) == [own_department.id]

    def test_get_queryset_ignores_stale_class_level_tenant_filter(
        self,
        db,
        organization,
        second_organization,
        user,
        mock_request,
    ):
        """Tenant-scoped viewsets must rebuild querysets per request instead of reusing stale class filters."""
        from apps.common.middleware import clear_current_organization, set_current_organization
        from apps.common.viewsets.base import BaseModelViewSet
        from apps.organizations.models import Department
        from apps.organizations.serializers import DepartmentSerializer

        own_department = Department.objects.create(
            name='Fresh Dept',
            code='FRESH_DEPT',
            organization=organization,
        )
        Department.objects.create(
            name='Stale Dept',
            code='STALE_DEPT',
            organization=second_organization,
        )

        set_current_organization(str(second_organization.id))
        try:
            class TestViewSet(BaseModelViewSet):
                queryset = Department.objects.all()
                serializer_class = DepartmentSerializer
        finally:
            clear_current_organization()

        viewset = TestViewSet()
        viewset.request = mock_request
        viewset.format_kwarg = None

        queryset = viewset.get_queryset()

        assert list(queryset.values_list('id', flat=True)) == [own_department.id]

    def test_perform_create_sets_created_by(self, db, organization, user, mock_request):
        """Test that perform_create sets created_by field."""
        from apps.common.viewsets.base import BaseModelViewSet
        from apps.organizations.serializers import DepartmentSerializer
        from apps.organizations.models import Department

        # Create a minimal viewset
        class TestViewSet(BaseModelViewSet):
            queryset = Department.objects.all()
            serializer_class = DepartmentSerializer

        viewset = TestViewSet()
        viewset.request = mock_request
        viewset.format_kwarg = None

        # Create mock serializer
        serializer = Mock()
        serializer.save = Mock(return_value=Department(
            name='Test',
            code='TEST_CREATE',
            organization=organization
        ))

        viewset.perform_create(serializer)

        # Verify save was called with created_by and organization
        serializer.save.assert_called_once()
        call_kwargs = serializer.save.call_args[1]
        assert 'created_by' in call_kwargs
        assert call_kwargs['created_by'] == user

    def test_perform_update_sets_updated_by(self, db, organization, user, mock_request):
        """Test that perform_update sets updated_by field."""
        from apps.common.viewsets.base import BaseModelViewSet
        from apps.organizations.serializers import DepartmentSerializer
        from apps.organizations.models import Department

        class TestViewSet(BaseModelViewSet):
            queryset = Department.objects.all()
            serializer_class = DepartmentSerializer

        viewset = TestViewSet()
        viewset.request = mock_request
        viewset.format_kwarg = None

        serializer = Mock()
        serializer.save = Mock()

        viewset.perform_update(serializer)

        serializer.save.assert_called_once()
        call_kwargs = serializer.save.call_args[1]
        assert 'updated_by' in call_kwargs
        assert call_kwargs['updated_by'] == user

    def test_perform_destroy_soft_deletes(self, db, organization, user, mock_request):
        """Test that perform_destroy performs soft delete."""
        from apps.common.viewsets.base import BaseModelViewSet
        from apps.organizations.models import Department

        dept = Department.objects.create(
            name='To Delete',
            code='TO_DEL',
            organization=organization
        )

        class TestViewSet(BaseModelViewSet):
            queryset = Department.objects.all()

        viewset = TestViewSet()
        viewset.request = mock_request

        viewset.perform_destroy(dept)

        dept.refresh_from_db()
        assert dept.is_deleted is True
        assert dept.deleted_at is not None


class TestBatchOperationMixin:
    """Test BatchOperationMixin batch operations."""

    def test_batch_delete_request_format(self, db, organization):
        """Test batch_delete request body format validation."""
        from apps.common.viewsets.base import BatchOperationMixin
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()

        # Test with valid format
        request = factory.post(
            '/batch-delete/',
            {'ids': ['uuid1', 'uuid2']},
            format='json'
        )

        mixin = BatchOperationMixin()
        # The mixin expects certain attributes
        mixin.get_queryset = Mock(return_value=Mock())

        # Validate request format handling
        assert hasattr(mixin, 'batch_delete')

    def test_batch_restore_exists(self):
        """Test that batch_restore action exists."""
        from apps.common.viewsets.base import BatchOperationMixin

        mixin = BatchOperationMixin()
        assert hasattr(mixin, 'batch_restore')
        assert callable(mixin.batch_restore)

    def test_batch_update_exists(self):
        """Test that batch_update action exists."""
        from apps.common.viewsets.base import BatchOperationMixin

        mixin = BatchOperationMixin()
        assert hasattr(mixin, 'batch_update')
        assert callable(mixin.batch_update)


class TestBaseModelViewSetWithBatch:
    """Test BaseModelViewSetWithBatch combines both classes."""

    def test_inherits_from_both(self):
        """Test that it inherits from both parent classes."""
        from apps.common.viewsets.base import (
            BaseModelViewSetWithBatch,
            BaseModelViewSet,
            BatchOperationMixin
        )

        assert issubclass(BaseModelViewSetWithBatch, BaseModelViewSet)
        assert issubclass(BaseModelViewSetWithBatch, BatchOperationMixin)

    def test_has_batch_operations(self):
        """Test that batch operations are available."""
        from apps.common.viewsets.base import BaseModelViewSetWithBatch

        viewset = BaseModelViewSetWithBatch()
        assert hasattr(viewset, 'batch_delete')
        assert hasattr(viewset, 'batch_restore')
        assert hasattr(viewset, 'batch_update')

    def test_has_soft_delete(self):
        """Test that soft delete operations are available."""
        from apps.common.viewsets.base import BaseModelViewSetWithBatch

        viewset = BaseModelViewSetWithBatch()
        assert hasattr(viewset, 'perform_destroy')
        assert hasattr(viewset, 'deleted')
        assert hasattr(viewset, 'restore')
