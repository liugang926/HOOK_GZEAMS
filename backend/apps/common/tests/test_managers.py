"""
Unit tests for GlobalMetadataManager.

Tests cover:
- GlobalMetadataManager filters by is_deleted=False
- GlobalMetadataManager does NOT filter by organization
- All metadata models use GlobalMetadataManager correctly
- Comparison with TenantManager behavior
"""
import pytest
import uuid
from django.utils import timezone
from apps.common.managers import GlobalMetadataManager, TenantManager
from apps.common.middleware import set_current_organization, clear_current_organization
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    PageLayout,
    DictionaryType,
    DictionaryItem,
    SequenceRule,
    SystemConfig,
)
from apps.organizations.models import Organization, Department
from django.contrib.auth import get_user_model

User = get_user_model()


class TestGlobalMetadataManager:
    """Test GlobalMetadataManager behavior for metadata models."""

    def test_filters_soft_deleted_records(self, db):
        """Test that GlobalMetadataManager filters out soft-deleted records."""
        # Create a BusinessObject
        bo = BusinessObject.all_objects.create(
            code='TEST_OBJ',
            name='Test Object',
            is_deleted=False
        )
        bo_id = bo.id

        # Verify it's in the objects queryset
        assert BusinessObject.objects.filter(id=bo_id).exists()

        # Soft delete it
        bo.is_deleted = True
        bo.deleted_at = timezone.now()
        bo.save()

        # Verify it's no longer in the objects queryset
        assert not BusinessObject.objects.filter(id=bo_id).exists()

        # But it should still be in all_objects
        assert BusinessObject.all_objects.filter(id=bo_id).exists()

    def test_does_not_filter_by_organization(self, db):
        """Test that GlobalMetadataManager does NOT filter by organization."""
        # Create two organizations
        org1 = Organization.objects.create(
            name='Org 1',
            code='ORG1',
            org_type='company'
        )
        org2 = Organization.objects.create(
            name='Org 2',
            code='ORG2',
            org_type='company'
        )

        # Create BusinessObjects in different organizations
        bo1 = BusinessObject.objects.create(
            code='BO_ORG1',
            name='Business Object Org1',
            organization=org1
        )
        bo2 = BusinessObject.objects.create(
            code='BO_ORG2',
            name='Business Object Org2',
            organization=org2
        )

        # Set organization context to org1
        set_current_organization(str(org1.id))

        try:
            # GlobalMetadataManager should return BOTH objects
            # because it does NOT filter by organization
            all_bos = list(BusinessObject.objects.all())

            assert bo1 in all_bos, "bo1 should be visible"
            assert bo2 in all_bos, "bo2 should be visible (metadata is global)"
        finally:
            clear_current_organization()

    def test_comparison_with_tenant_manager(self, db):
        """Test that TenantManager DOES filter by organization, unlike GlobalMetadataManager."""
        # Create two organizations
        org1 = Organization.objects.create(
            name='Org 1',
            code='ORG1',
            org_type='company'
        )
        org2 = Organization.objects.create(
            name='Org 2',
            code='ORG2',
            org_type='company'
        )

        # Create Departments in different organizations (Department uses TenantManager)
        dept1 = Department.objects.create(
            name='Dept 1',
            code='DEPT1',
            organization=org1
        )
        dept2 = Department.objects.create(
            name='Dept 2',
            code='DEPT2',
            organization=org2
        )

        # Create BusinessObjects in different organizations (BusinessObject uses GlobalMetadataManager)
        bo1 = BusinessObject.objects.create(
            code='BO1',
            name='BO 1',
            organization=org1
        )
        bo2 = BusinessObject.objects.create(
            code='BO2',
            name='BO 2',
            organization=org2
        )

        # Set organization context to org1
        set_current_organization(str(org1.id))

        try:
            # TenantManager: Only dept1 should be visible
            depts = list(Department.objects.all())
            assert dept1 in depts, "dept1 should be visible for org1"
            assert dept2 not in depts, "dept2 should NOT be visible (filtered by org)"

            # GlobalMetadataManager: BOTH bo1 and bo2 should be visible
            bos = list(BusinessObject.objects.all())
            assert bo1 in bos, "bo1 should be visible"
            assert bo2 in bos, "bo2 should be visible (metadata is global)"
        finally:
            clear_current_organization()


class TestMetadataModelsUseGlobalMetadataManager:
    """Test that all metadata models use GlobalMetadataManager correctly."""

    def test_business_object_uses_global_metadata_manager(self, db):
        """Test BusinessObject uses GlobalMetadataManager."""
        assert isinstance(BusinessObject.objects, GlobalMetadataManager)

    def test_field_definition_uses_global_metadata_manager(self, db):
        """Test FieldDefinition uses GlobalMetadataManager."""
        assert isinstance(FieldDefinition.objects, GlobalMetadataManager)

    def test_page_layout_uses_global_metadata_manager(self, db):
        """Test PageLayout uses GlobalMetadataManager."""
        assert isinstance(PageLayout.objects, GlobalMetadataManager)

    def test_dictionary_type_uses_global_metadata_manager(self, db):
        """Test DictionaryType uses GlobalMetadataManager."""
        assert isinstance(DictionaryType.objects, GlobalMetadataManager)

    def test_dictionary_item_uses_global_metadata_manager(self, db):
        """Test DictionaryItem uses GlobalMetadataManager."""
        assert isinstance(DictionaryItem.objects, GlobalMetadataManager)

    def test_sequence_rule_uses_global_metadata_manager(self, db):
        """Test SequenceRule uses GlobalMetadataManager."""
        assert isinstance(SequenceRule.objects, GlobalMetadataManager)

    def test_system_config_uses_global_metadata_manager(self, db):
        """Test SystemConfig uses GlobalMetadataManager."""
        assert isinstance(SystemConfig.objects, GlobalMetadataManager)


class TestMetadataModelsCrossOrganizationVisibility:
    """Test that metadata models are visible across organizations."""

    def test_business_object_cross_org_visibility(self, db):
        """Test BusinessObject is visible to all organizations."""
        org1 = Organization.objects.create(
            name='Org 1',
            code='ORG1',
            org_type='company'
        )
        org2 = Organization.objects.create(
            name='Org 2',
            code='ORG2',
            org_type='company'
        )

        # Create BusinessObject in org1
        bo = BusinessObject.objects.create(
            code='TEST_BO',
            name='Test Business Object',
            organization=org1
        )

        # Set org2 as current context
        set_current_organization(str(org2.id))

        try:
            # Should still be able to access the BusinessObject
            assert BusinessObject.objects.filter(code='TEST_BO').exists()
        finally:
            clear_current_organization()

    def test_field_definition_cross_org_visibility(self, db):
        """Test FieldDefinition is visible to all organizations."""
        org1 = Organization.objects.create(
            name='Org 1',
            code='ORG1',
            org_type='company'
        )
        org2 = Organization.objects.create(
            name='Org 2',
            code='ORG2',
            org_type='company'
        )

        # Create BusinessObject and FieldDefinition in org1
        bo = BusinessObject.objects.create(
            code='TEST_BO',
            name='Test Business Object',
            organization=org1
        )
        field = FieldDefinition.objects.create(
            business_object=bo,
            code='test_field',
            name='Test Field',
            field_type='text',
            organization=org1
        )

        # Set org2 as current context
        set_current_organization(str(org2.id))

        try:
            # Should still be able to access the FieldDefinition
            assert FieldDefinition.objects.filter(code='test_field').exists()
        finally:
            clear_current_organization()

    def test_page_layout_cross_org_visibility(self, db):
        """Test PageLayout is visible to all organizations."""
        org1 = Organization.objects.create(
            name='Org 1',
            code='ORG1',
            org_type='company'
        )
        org2 = Organization.objects.create(
            name='Org 2',
            code='ORG2',
            org_type='company'
        )

        # Create BusinessObject and PageLayout in org1
        bo = BusinessObject.objects.create(
            code='TEST_BO',
            name='Test Business Object',
            organization=org1
        )
        layout = PageLayout.objects.create(
            business_object=bo,
            layout_code='test_layout',
            layout_name='Test Layout',
            layout_type='form',
            organization=org1
        )

        # Set org2 as current context
        set_current_organization(str(org2.id))

        try:
            # Should still be able to access the PageLayout
            assert PageLayout.objects.filter(layout_code='test_layout').exists()
        finally:
            clear_current_organization()

    def test_dictionary_cross_org_visibility(self, db):
        """Test DictionaryType and DictionaryItem are visible to all organizations."""
        org1 = Organization.objects.create(
            name='Org 1',
            code='ORG1',
            org_type='company'
        )
        org2 = Organization.objects.create(
            name='Org 2',
            code='ORG2',
            org_type='company'
        )

        # Create DictionaryType and DictionaryItem in org1
        dict_type = DictionaryType.objects.create(
            code='TEST_DICT',
            name='Test Dictionary',
            organization=org1
        )
        item = DictionaryItem.objects.create(
            dictionary_type=dict_type,
            code='item1',
            name='Item 1',
            organization=org1
        )

        # Set org2 as current context
        set_current_organization(str(org2.id))

        try:
            # Should still be able to access DictionaryType and DictionaryItem
            assert DictionaryType.objects.filter(code='TEST_DICT').exists()
            assert DictionaryItem.objects.filter(code='item1').exists()
        finally:
            clear_current_organization()

    def test_sequence_rule_cross_org_visibility(self, db):
        """Test SequenceRule is visible to all organizations."""
        org1 = Organization.objects.create(
            name='Org 1',
            code='ORG1',
            org_type='company'
        )
        org2 = Organization.objects.create(
            name='Org 2',
            code='ORG2',
            org_type='company'
        )

        # Create SequenceRule in org1
        rule = SequenceRule.objects.create(
            code='TEST_SEQ',
            name='Test Sequence',
            prefix='SEQ',
            pattern='{PREFIX}{YYYY}{MM}{SEQ}',
            seq_length=4,
            organization=org1
        )

        # Set org2 as current context
        set_current_organization(str(org2.id))

        try:
            # Should still be able to access the SequenceRule
            assert SequenceRule.objects.filter(code='TEST_SEQ').exists()
        finally:
            clear_current_organization()

    def test_system_config_cross_org_visibility(self, db):
        """Test SystemConfig is visible to all organizations."""
        org1 = Organization.objects.create(
            name='Org 1',
            code='ORG1',
            org_type='company'
        )
        org2 = Organization.objects.create(
            name='Org 2',
            code='ORG2',
            org_type='company'
        )

        # Create SystemConfig in org1
        config = SystemConfig.objects.create(
            config_key='test.config',
            config_value='test_value',
            name='Test Config',
            organization=org1
        )

        # Set org2 as current context
        set_current_organization(str(org2.id))

        try:
            # Should still be able to access the SystemConfig
            assert SystemConfig.objects.filter(config_key='test.config').exists()
        finally:
            clear_current_organization()


class TestGlobalMetadataManagerSoftDeleteBehavior:
    """Test soft delete behavior for GlobalMetadataManager models."""

    def test_business_object_soft_delete(self, db):
        """Test BusinessObject soft delete behavior."""
        bo = BusinessObject.objects.create(
            code='TEST_DELETE',
            name='Test Delete'
        )

        # Soft delete
        bo.soft_delete()

        # Should not be in objects queryset
        assert not BusinessObject.objects.filter(code='TEST_DELETE').exists()

        # Should be in all_objects queryset
        assert BusinessObject.all_objects.filter(code='TEST_DELETE').exists()

    def test_field_definition_soft_delete(self, db):
        """Test FieldDefinition soft delete behavior."""
        org = Organization.objects.create(
            name='Test Org',
            code='TEST_ORG',
            org_type='company'
        )
        bo = BusinessObject.objects.create(
            code='TEST_BO',
            name='Test BO',
            organization=org
        )
        field = FieldDefinition.objects.create(
            business_object=bo,
            code='test_field',
            name='Test Field',
            field_type='text',
            organization=org
        )

        # Soft delete
        field.soft_delete()

        # Should not be in objects queryset
        assert not FieldDefinition.objects.filter(code='test_field').exists()

        # Should be in all_objects queryset
        assert FieldDefinition.all_objects.filter(code='test_field').exists()

    def test_page_layout_soft_delete(self, db):
        """Test PageLayout soft delete behavior."""
        org = Organization.objects.create(
            name='Test Org',
            code='TEST_ORG',
            org_type='company'
        )
        bo = BusinessObject.objects.create(
            code='TEST_BO',
            name='Test BO',
            organization=org
        )
        layout = PageLayout.objects.create(
            business_object=bo,
            layout_code='test_layout',
            layout_name='Test Layout',
            layout_type='form',
            organization=org
        )

        # Soft delete
        layout.soft_delete()

        # Should not be in objects queryset
        assert not PageLayout.objects.filter(layout_code='test_layout').exists()

        # Should be in all_objects queryset
        assert PageLayout.all_objects.filter(layout_code='test_layout').exists()


class TestGlobalMetadataManagerQueries:
    """Test various query patterns with GlobalMetadataManager."""

    def test_get_method(self, db):
        """Test get() method works correctly."""
        bo = BusinessObject.objects.create(
            code='TEST_GET',
            name='Test Get'
        )

        # Should be able to get it
        retrieved = BusinessObject.objects.get(code='TEST_GET')
        assert retrieved.id == bo.id

    def test_filter_method(self, db):
        """Test filter() method works correctly."""
        bo1 = BusinessObject.objects.create(
            code='TEST_FILTER_1',
            name='Test Filter 1'
        )
        bo2 = BusinessObject.objects.create(
            code='TEST_FILTER_2',
            name='Test Filter 2'
        )

        # Filter by code pattern
        results = BusinessObject.objects.filter(code__startswith='TEST_FILTER')
        assert bo1 in results
        assert bo2 in results

    def test_exclude_method(self, db):
        """Test exclude() method works correctly."""
        bo1 = BusinessObject.objects.create(
            code='TEST_EXCLUDE_1',
            name='Test Exclude 1'
        )
        bo2 = BusinessObject.objects.create(
            code='OTHER',
            name='Other'
        )

        # Exclude by code pattern
        results = BusinessObject.objects.exclude(code__startswith='TEST_EXCLUDE')
        assert bo2 in results
        assert bo1 not in results

    def test_order_by_method(self, db):
        """Test order_by() method works correctly."""
        prefix = f'ORDER_{uuid.uuid4().hex[:8].upper()}_'
        BusinessObject.objects.create(code=f'{prefix}C', name='C')
        BusinessObject.objects.create(code=f'{prefix}A', name='A')
        BusinessObject.objects.create(code=f'{prefix}B', name='B')

        # Order by code
        results = list(BusinessObject.objects.filter(code__startswith=prefix).order_by('code'))
        assert results[0].code == f'{prefix}A'
        assert results[1].code == f'{prefix}B'
        assert results[2].code == f'{prefix}C'

    def test_count_method(self, db):
        """Test count() method works correctly."""
        initial_count = BusinessObject.objects.count()

        BusinessObject.objects.create(code='TEST_COUNT_1', name='Test 1')
        BusinessObject.objects.create(code='TEST_COUNT_2', name='Test 2')

        assert BusinessObject.objects.count() == initial_count + 2

    def test_first_and_last_methods(self, db):
        """Test first() and last() methods work correctly."""
        prefix = f'EDGE_{uuid.uuid4().hex[:8].upper()}_'
        bo1 = BusinessObject.objects.create(code=f'{prefix}AAA', name='First')
        bo2 = BusinessObject.objects.create(code=f'{prefix}ZZZ', name='Last')

        queryset = BusinessObject.objects.filter(code__startswith=prefix).order_by('code')
        first = queryset.first()
        last = queryset.last()

        assert first.code == f'{prefix}AAA'
        assert last.code == f'{prefix}ZZZ'

    def test_exists_method(self, db):
        """Test exists() method works correctly."""
        BusinessObject.objects.create(code='TEST_EXISTS', name='Test Exists')

        assert BusinessObject.objects.filter(code='TEST_EXISTS').exists()
        assert not BusinessObject.objects.filter(code='NONEXISTENT').exists()
