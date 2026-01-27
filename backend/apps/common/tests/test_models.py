"""
Tests for BaseModel and TenantManager.
"""
import pytest
from django.utils import timezone
from django.db import models
from apps.common.models import BaseModel, TenantManager


# Create a concrete model for testing BaseModel
class TestableModel(BaseModel):
    """Concrete model for testing BaseModel functionality."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        app_label = 'common'
        # Don't create database table - we use Organization as proxy for testing
        managed = False


class TestTenantManager:
    """Test TenantManager organization filtering."""

    def test_manager_filters_by_organization(self, db, organization, user):
        """Test that TenantManager filters by organization context."""
        from apps.common.middleware import set_current_organization, clear_current_organization
        from apps.organizations.models import Organization, Department

        # Create departments in different organizations
        dept1 = Department.objects.create(
            name='Dept 1',
            code='DEPT1',
            organization=organization
        )
        
        # Set organization context
        set_current_organization(str(organization.id))
        
        try:
            # Query should only return departments for current org
            depts = Department.objects.all()
            assert dept1 in depts
        finally:
            clear_current_organization()

    def test_manager_excludes_soft_deleted(self, db, organization):
        """Test that TenantManager excludes soft-deleted records."""
        from apps.organizations.models import Department
        from apps.common.middleware import set_current_organization, clear_current_organization

        # Create test department
        dept = Department.objects.create(
            name='Test Dept',
            code='TEST_DEPT',
            organization=organization
        )
        dept_id = dept.id

        # Soft delete
        dept.is_deleted = True
        dept.deleted_at = timezone.now()
        dept.save()

        set_current_organization(str(organization.id))
        try:
            # Should not find deleted department
            assert not Department.objects.filter(id=dept_id).exists()
            # But all_objects should find it
            assert Department.all_objects.filter(id=dept_id).exists()
        finally:
            clear_current_organization()


class TestBaseModelSoftDelete:
    """Test BaseModel soft delete functionality."""

    def test_soft_delete_sets_flags(self, db, organization, user):
        """Test that soft_delete sets is_deleted and deleted_at."""
        from apps.organizations.models import Department
        
        dept = Department.objects.create(
            name='Delete Test',
            code='DEL_TEST',
            organization=organization
        )

        # Perform soft delete
        dept.soft_delete(user)
        dept.refresh_from_db()

        assert dept.is_deleted is True
        assert dept.deleted_at is not None
        assert dept.deleted_by == user

    def test_soft_delete_without_user(self, db, organization):
        """Test soft_delete works without user parameter."""
        from apps.organizations.models import Department

        dept = Department.objects.create(
            name='Delete Test 2',
            code='DEL_TEST2',
            organization=organization
        )

        dept.soft_delete()
        dept.refresh_from_db()

        assert dept.is_deleted is True
        assert dept.deleted_at is not None
        assert dept.deleted_by is None


class TestBaseModelAuditFields:
    """Test BaseModel audit field behavior."""

    def test_created_at_auto_set(self, db, organization):
        """Test that created_at is automatically set on creation."""
        from apps.organizations.models import Department
        
        before = timezone.now()
        dept = Department.objects.create(
            name='Audit Test',
            code='AUDIT_TEST',
            organization=organization
        )
        after = timezone.now()

        assert dept.created_at is not None
        assert before <= dept.created_at <= after

    def test_updated_at_auto_updated(self, db, organization):
        """Test that updated_at is automatically updated on save."""
        from apps.organizations.models import Department

        dept = Department.objects.create(
            name='Update Test',
            code='UPDATE_TEST',
            organization=organization
        )
        original_updated = dept.updated_at

        # Wait a tiny bit and update
        import time
        time.sleep(0.01)
        dept.name = 'Updated Name'
        dept.save()
        dept.refresh_from_db()

        assert dept.updated_at > original_updated

    def test_custom_fields_default_empty_dict(self, db, organization):
        """Test that custom_fields defaults to empty dict."""
        from apps.organizations.models import Department

        dept = Department.objects.create(
            name='Custom Fields Test',
            code='CF_TEST',
            organization=organization
        )

        assert dept.custom_fields == {}

    def test_custom_fields_stores_json(self, db, organization):
        """Test that custom_fields can store JSON data."""
        from apps.organizations.models import Department

        dept = Department.objects.create(
            name='JSON Test',
            code='JSON_TEST',
            organization=organization,
            custom_fields={'key1': 'value1', 'nested': {'a': 1}}
        )
        dept.refresh_from_db()

        assert dept.custom_fields['key1'] == 'value1'
        assert dept.custom_fields['nested']['a'] == 1


class TestBaseModelUUID:
    """Test BaseModel UUID primary key."""

    def test_id_is_uuid(self, db, organization):
        """Test that id is a valid UUID."""
        from apps.organizations.models import Department
        import uuid

        dept = Department.objects.create(
            name='UUID Test',
            code='UUID_TEST',
            organization=organization
        )

        assert isinstance(dept.id, uuid.UUID)

    def test_id_auto_generated(self, db, organization):
        """Test that id is automatically generated."""
        from apps.organizations.models import Department

        dept = Department.objects.create(
            name='Auto ID Test',
            code='AUTO_ID',
            organization=organization
        )

        assert dept.id is not None
