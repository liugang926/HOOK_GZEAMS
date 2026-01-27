"""
Tests for BaseCRUDService.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.core.exceptions import ObjectDoesNotExist


class TestBaseCRUDServiceCreate:
    """Test BaseCRUDService.create() method."""

    def test_create_sets_organization(self, db, organization, user):
        """Test that create sets organization from context."""
        from apps.common.services.base_crud import BaseCRUDService
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization

        service = BaseCRUDService(Department)

        set_current_organization(str(organization.id))
        try:
            dept = service.create(
                data={'name': 'New Dept', 'code': 'NEW_DEPT'},
                user=user,
                organization_id=str(organization.id)
            )
            assert dept.organization == organization
            assert dept.created_by == user
        finally:
            clear_current_organization()

    def test_create_returns_instance(self, db, organization, user):
        """Test that create returns the created instance."""
        from apps.common.services.base_crud import BaseCRUDService
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization

        service = BaseCRUDService(Department)

        set_current_organization(str(organization.id))
        try:
            dept = service.create(
                data={'name': 'Create Test', 'code': 'CREATE_TEST'},
                user=user,
                organization_id=str(organization.id)
            )
            assert dept.id is not None
            assert dept.name == 'Create Test'
        finally:
            clear_current_organization()


class TestBaseCRUDServiceUpdate:
    """Test BaseCRUDService.update() method."""

    def test_update_changes_fields(self, db, organization, user):
        """Test that update modifies specified fields."""
        from apps.common.services.base_crud import BaseCRUDService
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization

        # Create test department
        dept = Department.objects.create(
            name='Original Name',
            code='UPDATE_TEST',
            organization=organization
        )

        service = BaseCRUDService(Department)

        set_current_organization(str(organization.id))
        try:
            updated = service.update(
                instance_id=str(dept.id),
                data={'name': 'Updated Name'},
                user=user
            )
            assert updated.name == 'Updated Name'
        finally:
            clear_current_organization()


class TestBaseCRUDServiceDelete:
    """Test BaseCRUDService.delete() method."""

    def test_delete_soft_deletes(self, db, organization, user):
        """Test that delete performs soft delete."""
        from apps.common.services.base_crud import BaseCRUDService
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization

        dept = Department.objects.create(
            name='Delete Test',
            code='DEL_TEST',
            organization=organization
        )

        service = BaseCRUDService(Department)

        set_current_organization(str(organization.id))
        try:
            result = service.delete(str(dept.id), user)
            assert result is True

            # Refresh and check
            dept.refresh_from_db()
            assert dept.is_deleted is True
        finally:
            clear_current_organization()


class TestBaseCRUDServiceRestore:
    """Test BaseCRUDService.restore() method."""

    def test_restore_undeletes(self, db, organization, user):
        """Test that restore undeletes a soft-deleted record."""
        from apps.common.services.base_crud import BaseCRUDService
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization

        # Create record with organization context
        set_current_organization(str(organization.id))
        try:
            dept = Department.objects.create(
                name='Restore Test',
                code='RESTORE_TEST',
                organization=organization
            )
            dept_id = str(dept.id)

            # Soft delete it
            dept.soft_delete(user)
        finally:
            clear_current_organization()

        # Verify it's deleted
        dept.refresh_from_db()
        assert dept.is_deleted is True

        # Restore without organization context
        # (TenantManager filters deleted records in org context)
        service = BaseCRUDService(Department)
        restored = service.restore(dept_id)

        assert restored.is_deleted is False
        assert restored.deleted_at is None


class TestBaseCRUDServiceQuery:
    """Test BaseCRUDService.query() method."""

    def test_query_returns_queryset(self, db, organization):
        """Test that query returns a QuerySet."""
        from apps.common.services.base_crud import BaseCRUDService
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization
        from django.db.models import QuerySet

        # Create some departments
        for i in range(3):
            Department.objects.create(
                name=f'Query Test {i}',
                code=f'QUERY_{i}',
                organization=organization
            )

        service = BaseCRUDService(Department)

        set_current_organization(str(organization.id))
        try:
            result = service.query()
            assert isinstance(result, QuerySet)
            assert result.count() >= 3
        finally:
            clear_current_organization()

    def test_query_with_filters(self, db, organization):
        """Test query with filter parameters."""
        from apps.common.services.base_crud import BaseCRUDService
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization

        Department.objects.create(
            name='Filter Target',
            code='FILTER_TARGET',
            organization=organization
        )
        Department.objects.create(
            name='Other Dept',
            code='OTHER',
            organization=organization
        )

        service = BaseCRUDService(Department)

        set_current_organization(str(organization.id))
        try:
            result = service.query(filters={'code': 'FILTER_TARGET'})
            assert result.count() == 1
            assert result.first().code == 'FILTER_TARGET'
        finally:
            clear_current_organization()


class TestBaseCRUDServicePaginate:
    """Test BaseCRUDService.paginate() method."""

    def test_paginate_returns_dict(self, db, organization):
        """Test that paginate returns pagination dict."""
        from apps.common.services.base_crud import BaseCRUDService
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization

        # Create test data
        for i in range(25):
            Department.objects.create(
                name=f'Page Test {i}',
                code=f'PAGE_{i}',
                organization=organization
            )

        service = BaseCRUDService(Department)

        set_current_organization(str(organization.id))
        try:
            queryset = service.query()
            result = service.paginate(queryset, page=1, page_size=10)

            assert 'count' in result
            assert 'results' in result
            assert len(result['results']) == 10
        finally:
            clear_current_organization()


class TestBaseCRUDServiceBatchDelete:
    """Test BaseCRUDService.batch_delete() method."""

    def test_batch_delete_returns_summary(self, db, organization, user):
        """Test that batch_delete returns operation summary."""
        from apps.common.services.base_crud import BaseCRUDService
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization

        depts = []
        for i in range(3):
            dept = Department.objects.create(
                name=f'Batch Delete {i}',
                code=f'BATCH_DEL_{i}',
                organization=organization
            )
            depts.append(dept)

        ids = [str(d.id) for d in depts]
        service = BaseCRUDService(Department)

        set_current_organization(str(organization.id))
        try:
            result = service.batch_delete(ids, user)

            # batch_delete returns: {total, succeeded, failed, results}
            assert 'total' in result
            assert 'results' in result
            assert result['total'] == 3
            assert result['succeeded'] == 3
        finally:
            clear_current_organization()
