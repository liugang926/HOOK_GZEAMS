"""
Tests for BaseModelSerializer and related serializers.
"""
import pytest
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class TestBaseModelSerializer:
    """Test BaseModelSerializer functionality."""

    def test_serializer_fields(self):
        """Test that BaseModelSerializer defines expected fields."""
        from apps.common.serializers.base import BaseModelSerializer

        # Check Meta.fields
        expected_fields = [
            'id', 'organization', 'is_deleted', 'deleted_at',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'deleted_by', 'custom_fields'
        ]

        for field in expected_fields:
            assert field in BaseModelSerializer.Meta.fields

    def test_read_only_fields(self):
        """Test that read-only fields are correctly set."""
        from apps.common.serializers.base import BaseModelSerializer

        read_only = BaseModelSerializer.Meta.read_only_fields
        assert 'id' in read_only
        assert 'created_at' in read_only
        assert 'updated_at' in read_only

    def test_nested_user_serializer(self, db, organization, user):
        """Test that created_by is serialized as nested user info."""
        from apps.common.serializers.base import UserSerializer

        serializer = UserSerializer(user)
        data = serializer.data

        assert 'id' in data
        assert 'username' in data
        assert 'email' in data
        assert data['username'] == 'testuser'

    def test_nested_organization_serializer(self, db, organization):
        """Test that organization is serialized as nested info."""
        from apps.common.serializers.base import OrganizationSerializer

        serializer = OrganizationSerializer(organization)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'code' in data
        assert data['code'] == 'TEST_ORG'


class TestBaseListSerializer:
    """Test BaseListSerializer for optimized list views."""

    def test_uses_uuid_instead_of_nested(self):
        """Test that BaseListSerializer uses UUID fields for relations."""
        from apps.common.serializers.base import BaseListSerializer

        # Check that organization and created_by are UUIDs, not nested
        assert 'organization' in BaseListSerializer.Meta.fields
        assert 'created_by' in BaseListSerializer.Meta.fields

    def test_excludes_unnecessary_fields(self):
        """Test that list serializer excludes heavy fields."""
        from apps.common.serializers.base import BaseListSerializer

        # List view should have fewer fields
        assert len(BaseListSerializer.Meta.fields) < 10


class TestBaseModelWithAuditSerializer:
    """Test BaseModelWithAuditSerializer with full audit info."""

    def test_includes_audit_fields(self):
        """Test that full audit serializer includes all audit fields."""
        from apps.common.serializers.base import BaseModelWithAuditSerializer

        assert 'updated_by' in BaseModelWithAuditSerializer.Meta.fields
        assert 'deleted_by' in BaseModelWithAuditSerializer.Meta.fields

    def test_extends_base_serializer(self):
        """Test that it extends BaseModelSerializer."""
        from apps.common.serializers.base import (
            BaseModelWithAuditSerializer,
            BaseModelSerializer
        )

        assert issubclass(BaseModelWithAuditSerializer, BaseModelSerializer)


class TestUserSerializer:
    """Test lightweight UserSerializer."""

    def test_user_fields(self):
        """Test UserSerializer field list."""
        from apps.common.serializers.base import UserSerializer

        expected = ['id', 'username', 'email', 'first_name', 'last_name']
        for field in expected:
            assert field in UserSerializer.Meta.fields

    def test_password_not_included(self):
        """Test that password is not serialized."""
        from apps.common.serializers.base import UserSerializer

        assert 'password' not in UserSerializer.Meta.fields


class TestOrganizationSerializer:
    """Test lightweight OrganizationSerializer."""

    def test_organization_fields(self):
        """Test OrganizationSerializer field list."""
        from apps.common.serializers.base import OrganizationSerializer

        expected = ['id', 'name', 'code']
        for field in expected:
            assert field in OrganizationSerializer.Meta.fields

    def test_minimal_fields(self):
        """Test that only essential fields are included."""
        from apps.common.serializers.base import OrganizationSerializer

        # Should be lightweight - only 3 fields
        assert len(OrganizationSerializer.Meta.fields) == 3
