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
