"""
Integration tests for GlobalMetadataManager.

Tests cover end-to-end scenarios for metadata access:
- Metadata API endpoints work correctly for all organizations
- Services can access metadata without organization context
- ObjectRegistry can load business objects correctly
- Cross-organization metadata visibility
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.organizations.models import Organization
from apps.accounts.models import UserOrganization
from apps.system.models import BusinessObject, FieldDefinition, PageLayout
from apps.common.middleware import set_current_organization, clear_current_organization

User = get_user_model()


@pytest.fixture
def org1(db):
    """Create first test organization."""
    return Organization.objects.create(
        name='Organization 1',
        code='ORG1',
        org_type='company'
    )


@pytest.fixture
def org2(db):
    """Create second test organization."""
    return Organization.objects.create(
        name='Organization 2',
        code='ORG2',
        org_type='company'
    )


@pytest.fixture
def user_org1(db, org1):
    """Create user in org1."""
    user = User.objects.create_user(
        username='user1',
        email='user1@example.com',
        password='testpass123'
    )
    UserOrganization.objects.create(
        user=user,
        organization=org1,
        role='member',
        is_primary=True
    )
    return user


@pytest.fixture
def user_org2(db, org2):
    """Create user in org2."""
    user = User.objects.create_user(
        username='user2',
        email='user2@example.com',
        password='testpass123'
    )
    UserOrganization.objects.create(
        user=user,
        organization=org2,
        role='member',
        is_primary=True
    )
    return user


@pytest.fixture
def metadata_org1(db, org1):
    """Create metadata in org1."""
    bo = BusinessObject.objects.create(
        code='TEST_METADATA',
        name='Test Metadata Object',
        organization=org1
    )

    field = FieldDefinition.objects.create(
        business_object=bo,
        code='test_field',
        name='Test Field',
        field_type='text',
        organization=org1
    )

    layout = PageLayout.objects.create(
        business_object=bo,
        layout_code='test_layout',
        layout_name='Test Layout',
        layout_type='form',
        organization=org1
    )

    return {'bo': bo, 'field': field, 'layout': layout}


class TestMetadataAPIIntegration:
    """Test metadata API endpoints with GlobalMetadataManager."""

    def test_business_object_list_accessible_from_org1(self, db, org1, org2, metadata_org1, user_org1):
        """Test that org1 user can access metadata created in org1."""
        client = APIClient()
        client.force_authenticate(user=user_org1)

        # Set organization context to org1
        set_current_organization(str(org1.id))

        try:
            response = client.get('/api/system/business-objects/')
            assert response.status_code == 200

            # Should find the metadata object
            codes = [obj['code'] for obj in response.data['results']]
            assert 'TEST_METADATA' in codes
        finally:
            clear_current_organization()

    def test_business_object_list_accessible_from_org2(self, db, org1, org2, metadata_org1, user_org2):
        """Test that org2 user can ALSO access metadata created in org1 (metadata is global)."""
        client = APIClient()
        client.force_authenticate(user=user_org2)

        # Set organization context to org2
        set_current_organization(str(org2.id))

        try:
            response = client.get('/api/system/business-objects/')
            assert response.status_code == 200

            # Should STILL find the metadata object (metadata is global)
            codes = [obj['code'] for obj in response.data['results']]
            assert 'TEST_METADATA' in codes
        finally:
            clear_current_organization()

    def test_field_definition_list_cross_org(self, db, org1, org2, metadata_org1, user_org2):
        """Test that field definitions are visible across organizations."""
        client = APIClient()
        client.force_authenticate(user=user_org2)

        set_current_organization(str(org2.id))

        try:
            response = client.get(f'/api/system/business-objects/{metadata_org1["bo"].id}/fields/')
            assert response.status_code == 200

            # Should find the field
            codes = [field['code'] for field in response.data['results']]
            assert 'test_field' in codes
        finally:
            clear_current_organization()

    def test_page_layout_list_cross_org(self, db, org1, org2, metadata_org1, user_org2):
        """Test that page layouts are visible across organizations."""
        client = APIClient()
        client.force_authenticate(user=user_org2)

        set_current_organization(str(org2.id))

        try:
            response = client.get(f'/api/system/business-objects/{metadata_org1["bo"].id}/layouts/')
            assert response.status_code == 200

            # Should find the layout
            codes = [layout['layout_code'] for layout in response.data['results']]
            assert 'test_layout' in codes
        finally:
            clear_current_organization()


class TestObjectRegistryIntegration:
    """Test ObjectRegistry service integration with GlobalMetadataManager."""

    def test_object_registry_loads_from_org1(self, db, org1, org2, metadata_org1):
        """Test ObjectRegistry can load metadata when context is org1."""
        from apps.system.services.object_registry import ObjectRegistry

        set_current_organization(str(org1.id))

        try:
            # Should be able to load the business object
            obj_meta = ObjectRegistry.get(metadata_org1['bo'].code)
            assert obj_meta is not None
            assert obj_meta.code == metadata_org1['bo'].code
        finally:
            clear_current_organization()

    def test_object_registry_loads_from_org2(self, db, org1, org2, metadata_org1):
        """Test ObjectRegistry can load metadata when context is org2 (metadata is global)."""
        from apps.system.services.object_registry import ObjectRegistry

        set_current_organization(str(org2.id))

        try:
            # Should STILL be able to load the business object
            obj_meta = ObjectRegistry.get(metadata_org1['bo'].code)
            assert obj_meta is not None
            assert obj_meta.code == metadata_org1['bo'].code
        finally:
            clear_current_organization()

    def test_object_registry_all_objects(self, db, org1, org2, metadata_org1):
        """Test ObjectRegistry.all_objects() returns global metadata."""
        from apps.system.services.object_registry import ObjectRegistry

        set_current_organization(str(org2.id))

        try:
            # Get all object metadata
            all_metas = ObjectRegistry.all_objects()

            # Should include the test metadata
            codes = [meta.code for meta in all_metas]
            assert 'TEST_METADATA' in codes
        finally:
            clear_current_organization()


class TestMenuAPICrossOrganization:
    """Test menu API works correctly across organizations."""

    def test_menu_api_from_org1(self, db, org1, org2, metadata_org1, user_org1):
        """Test menu API works for org1 user."""
        client = APIClient()
        client.force_authenticate(user=user_org1)

        # Add menu config to the business object
        bo = BusinessObject.objects.get(code='TEST_METADATA')
        bo.menu_config = {
            'show_in_menu': True,
            'group': 'Test Group',
            'item_order': 1
        }
        bo.save()

        set_current_organization(str(org1.id))

        try:
            response = client.get('/api/system/menu/')
            assert response.status_code == 200

            # Should find the test object in menu
            codes = [item['code'] for item in response.data]
            assert 'TEST_METADATA' in codes
        finally:
            clear_current_organization()

    def test_menu_api_from_org2(self, db, org1, org2, metadata_org1, user_org2):
        """Test menu API works for org2 user (metadata is global)."""
        client = APIClient()
        client.force_authenticate(user=user_org2)

        # Add menu config to the business object
        bo = BusinessObject.objects.get(code='TEST_METADATA')
        bo.menu_config = {
            'show_in_menu': True,
            'group': 'Test Group',
            'item_order': 1
        }
        bo.save()

        set_current_organization(str(org2.id))

        try:
            response = client.get('/api/system/menu/')
            assert response.status_code == 200

            # Should STILL find the test object in menu
            codes = [item['code'] for item in response.data]
            assert 'TEST_METADATA' in codes
        finally:
            clear_current_organization()


class TestMetadataServicesIntegration:
    """Test metadata services work correctly with GlobalMetadataManager."""

    def test_column_config_service_cross_org(self, db, org1, org2, metadata_org1, user_org2):
        """Test ColumnConfigService works across organizations."""
        from apps.system.services.column_config_service import ColumnConfigService

        set_current_organization(str(org2.id))

        try:
            # Should be able to get column config for the business object
            config = ColumnConfigService.get_column_config(user_org2, metadata_org1['bo'].code)
            assert config is not None
            assert 'columns' in config
        finally:
            clear_current_organization()

    def test_dictionary_service_cross_org(self, db, org1, org2):
        """Test DictionaryService works across organizations."""
        from apps.system.services.public_services import DictionaryService
        from apps.system.models import DictionaryType, DictionaryItem

        # Create dictionary in org1
        dict_type = DictionaryType.objects.create(
            code='TEST_DICT',
            name='Test Dictionary',
            organization=org1
        )
        DictionaryItem.objects.create(
            dictionary_type=dict_type,
            code='item1',
            name='Item 1',
            organization=org1
        )

        set_current_organization(str(org2.id))

        try:
            # Should be able to access dictionary items
            items = DictionaryService.get_items('TEST_DICT')
            assert len(items) > 0
            assert items[0]['code'] == 'item1'
        finally:
            clear_current_organization()

    def test_sequence_service_cross_org(self, db, org1, org2):
        """Test SequenceService works across organizations."""
        from apps.system.services.public_services import SequenceService
        from apps.system.models import SequenceRule

        # Create sequence rule in org1
        rule = SequenceRule.objects.create(
            code='TEST_SEQ',
            name='Test Sequence',
            prefix='TS',
            pattern='{PREFIX}{SEQ}',
            seq_length=4,
            organization=org1
        )

        set_current_organization(str(org2.id))

        try:
            # Should be able to preview next sequence value
            preview = SequenceService.preview_next('TEST_SEQ')
            assert preview is not None
            assert 'TS' in preview
        finally:
            clear_current_organization()


class TestSoftDeleteIntegration:
    """Test soft delete behavior in API and services."""

    def test_soft_deleted_object_not_in_list(self, db, org1, metadata_org1, user_org1):
        """Test that soft-deleted objects are not returned in API responses."""
        from django.utils import timezone

        # Soft delete the business object
        bo = BusinessObject.objects.get(code='TEST_METADATA')
        bo.is_deleted = True
        bo.deleted_at = timezone.now()
        bo.save()

        client = APIClient()
        client.force_authenticate(user=user_org1)

        set_current_organization(str(org1.id))

        try:
            response = client.get('/api/system/business-objects/')
            assert response.status_code == 200

            # Should NOT find the soft-deleted object
            codes = [obj['code'] for obj in response.data['results']]
            assert 'TEST_METADATA' not in codes
        finally:
            clear_current_organization()

    def test_soft_deleted_object_in_deleted_endpoint(self, db, org1, metadata_org1, user_org1):
        """Test that soft-deleted objects are available in /deleted/ endpoint."""
        from django.utils import timezone

        # Soft delete the business object
        bo = BusinessObject.objects.get(code='TEST_METADATA')
        bo.is_deleted = True
        bo.deleted_at = timezone.now()
        bo.save()

        client = APIClient()
        client.force_authenticate(user=user_org1)

        set_current_organization(str(org1.id))

        try:
            response = client.get('/api/system/business-objects/deleted/')
            assert response.status_code == 200

            # Should find the soft-deleted object
            codes = [obj['code'] for obj in response.data['results']]
            assert 'TEST_METADATA' in codes
        finally:
            clear_current_organization()
