"""
Model tests for the metadata-driven low-code engine.

Tests cover:
- BaseModel inheritance compliance (organization isolation, soft delete, audit fields)
- Business object model functionality
- Field definition model functionality
- Page layout model functionality
- Dynamic data model functionality
- Dynamic sub-table data model functionality
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    PageLayout,
    DynamicData,
    DynamicSubTableData
)
from apps.organizations.models import Organization
from apps.accounts.models import User


class BaseModelComplianceTest(TestCase):
    """Test that all models properly inherit BaseModel functionality."""

    def setUp(self):
        """Set up test data."""
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST_ORG'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            organization=self.organization
        )

    def test_business_object_has_base_fields(self):
        """Test BusinessObject has all BaseModel fields."""
        obj = BusinessObject.objects.create(
            code='TEST',
            name='Test Object',
            organization=self.organization,
            created_by=self.user
        )
        self.assertIsNotNone(obj.id)
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)
        self.assertEqual(obj.organization, self.organization)
        self.assertEqual(obj.created_by, self.user)
        self.assertFalse(obj.is_deleted)
        self.assertIsNone(obj.deleted_at)

    def test_field_definition_has_base_fields(self):
        """Test FieldDefinition has all BaseModel fields."""
        bo = BusinessObject.objects.create(
            code='TEST',
            name='Test Object',
            organization=self.organization,
            created_by=self.user
        )
        field = FieldDefinition.objects.create(
            business_object=bo,
            code='test_field',
            name='Test Field',
            organization=self.organization,
            created_by=self.user
        )
        self.assertIsNotNone(field.id)
        self.assertIsNotNone(field.created_at)
        self.assertEqual(field.organization, self.organization)
        self.assertFalse(field.is_deleted)

    def test_soft_delete_business_object(self):
        """Test soft delete functionality on BusinessObject."""
        obj = BusinessObject.objects.create(
            code='TEST',
            name='Test Object',
            organization=self.organization,
            created_by=self.user
        )
        obj_id = obj.id

        # Soft delete
        obj.soft_delete()

        # Refresh from database
        obj.refresh_from_db()

        # Verify soft delete worked
        self.assertTrue(obj.is_deleted)
        self.assertIsNotNone(obj.deleted_at)

        # Verify it's filtered from default queryset
        self.assertNotIn(
            obj_id,
            [bo.id for bo in BusinessObject.objects.all()]
        )


class BusinessObjectModelTest(TestCase):
    """Test BusinessObject model functionality."""

    def setUp(self):
        """Set up test data."""
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST_ORG'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            organization=self.organization
        )

    def test_get_table_name_default(self):
        """Test default table name generation."""
        obj = BusinessObject.objects.create(
            code='TestAsset',
            name='Test Asset',
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(obj.get_table_name(), 'dynamic_data_testasset')

    def test_get_table_name_custom(self):
        """Test custom table name."""
        obj = BusinessObject.objects.create(
            code='TestAsset',
            name='Test Asset',
            table_name='custom_asset_table',
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(obj.get_table_name(), 'custom_asset_table')

    def test_field_count_property(self):
        """Test field_count property."""
        obj = BusinessObject.objects.create(
            code='TEST',
            name='Test Object',
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=obj,
            code='field1',
            name='Field 1',
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=obj,
            code='field2',
            name='Field 2',
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(obj.field_count, 2)

    def test_layout_count_property(self):
        """Test layout_count property."""
        obj = BusinessObject.objects.create(
            code='TEST',
            name='Test Object',
            organization=self.organization,
            created_by=self.user
        )
        PageLayout.objects.create(
            business_object=obj,
            layout_code='form1',
            layout_name='Form 1',
            layout_type='form',
            organization=self.organization,
            created_by=self.user
        )
        PageLayout.objects.create(
            business_object=obj,
            layout_code='list1',
            layout_name='List 1',
            layout_type='list',
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(obj.layout_count, 2)


class FieldDefinitionModelTest(TestCase):
    """Test FieldDefinition model functionality."""

    def setUp(self):
        """Set up test data."""
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST_ORG'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            organization=self.organization
        )
        self.business_object = BusinessObject.objects.create(
            code='TEST',
            name='Test Object',
            organization=self.organization,
            created_by=self.user
        )

    def test_field_type_choices(self):
        """Test all field type choices are available."""
        field_types = [
            'text', 'textarea', 'number', 'currency', 'percent',
            'date', 'datetime', 'boolean', 'select', 'multi_select',
            'radio', 'checkbox', 'user', 'department', 'reference',
            'asset', 'formula', 'sub_table', 'file', 'image',
            'rich_text', 'qr_code', 'barcode', 'location'
        ]
        for field_type in field_types:
            field = FieldDefinition.objects.create(
                business_object=self.business_object,
                code=f'test_{field_type}',
                name=f'Test {field_type}',
                field_type=field_type,
                organization=self.organization,
                created_by=self.user
            )
            self.assertEqual(field.field_type, field_type)

    def test_reference_field_validation(self):
        """Test reference field must have reference_object."""
        field = FieldDefinition(
            business_object=self.business_object,
            code='test_ref',
            name='Test Reference',
            field_type='reference',
            reference_object='',  # Empty reference object
            organization=self.organization,
            created_by=self.user
        )
        with self.assertRaises(ValidationError):
            field.clean()

    def test_formula_field_validation(self):
        """Test formula field must have formula expression."""
        field = FieldDefinition(
            business_object=self.business_object,
            code='test_formula',
            name='Test Formula',
            field_type='formula',
            formula='',  # Empty formula
            organization=self.organization,
            created_by=self.user
        )
        with self.assertRaises(ValidationError):
            field.clean()

    def test_sub_table_field_validation(self):
        """Test sub_table field must have sub_table_fields."""
        field = FieldDefinition(
            business_object=self.business_object,
            code='test_subtable',
            name='Test Sub Table',
            field_type='sub_table',
            sub_table_fields=[],  # Empty sub_table_fields
            organization=self.organization,
            created_by=self.user
        )
        with self.assertRaises(ValidationError):
            field.clean()


class DynamicDataModelTest(TestCase):
    """Test DynamicData model functionality."""

    def setUp(self):
        """Set up test data."""
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST_ORG'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            organization=self.organization
        )
        self.business_object = BusinessObject.objects.create(
            code='Asset',
            name='Asset',
            organization=self.organization,
            created_by=self.user
        )

    def test_get_field_value(self):
        """Test get_field_value method."""
        data = DynamicData.objects.create(
            business_object=self.business_object,
            data_no='ASSET001',
            dynamic_fields={'asset_name': 'Test Asset', 'price': 1000},
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(data.get_field_value('asset_name'), 'Test Asset')
        self.assertEqual(data.get_field_value('price'), 1000)
        self.assertIsNone(data.get_field_value('nonexistent'))

    def test_set_field_value(self):
        """Test set_field_value method."""
        data = DynamicData.objects.create(
            business_object=self.business_object,
            data_no='ASSET001',
            dynamic_fields={},
            organization=self.organization,
            created_by=self.user
        )
        data.set_field_value('asset_name', 'Test Asset')
        data.set_field_value('price', 1000)
        data.save()

        data.refresh_from_db()
        self.assertEqual(data.get_field_value('asset_name'), 'Test Asset')
        self.assertEqual(data.get_field_value('price'), 1000)


class DynamicSubTableDataModelTest(TestCase):
    """Test DynamicSubTableData model functionality."""

    def setUp(self):
        """Set up test data."""
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST_ORG'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            organization=self.organization
        )
        self.business_object = BusinessObject.objects.create(
            code='Asset',
            name='Asset',
            organization=self.organization,
            created_by=self.user
        )
        self.field_definition = FieldDefinition.objects.create(
            business_object=self.business_object,
            code='items',
            name='Items',
            field_type='sub_table',
            sub_table_fields=[
                {'code': 'item_name', 'name': 'Item Name', 'field_type': 'text'},
                {'code': 'quantity', 'name': 'Quantity', 'field_type': 'number'}
            ],
            organization=self.organization,
            created_by=self.user
        )
        self.parent_data = DynamicData.objects.create(
            business_object=self.business_object,
            data_no='ASSET001',
            dynamic_fields={},
            organization=self.organization,
            created_by=self.user
        )

    def test_get_cell_value(self):
        """Test get_cell_value method."""
        row = DynamicSubTableData.objects.create(
            parent_data=self.parent_data,
            field_definition=self.field_definition,
            row_order=0,
            row_data={'item_name': 'Test Item', 'quantity': 10},
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(row.get_cell_value('item_name'), 'Test Item')
        self.assertEqual(row.get_cell_value('quantity'), 10)
        self.assertIsNone(row.get_cell_value('nonexistent'))

    def test_set_cell_value(self):
        """Test set_cell_value method."""
        row = DynamicSubTableData.objects.create(
            parent_data=self.parent_data,
            field_definition=self.field_definition,
            row_order=0,
            row_data={},
            organization=self.organization,
            created_by=self.user
        )
        row.set_cell_value('item_name', 'Test Item')
        row.set_cell_value('quantity', 10)
        row.save()

        row.refresh_from_db()
        self.assertEqual(row.get_cell_value('item_name'), 'Test Item')
        self.assertEqual(row.get_cell_value('quantity'), 10)

    def test_row_ordering(self):
        """Test rows are ordered by row_order."""
        DynamicSubTableData.objects.create(
            parent_data=self.parent_data,
            field_definition=self.field_definition,
            row_order=2,
            row_data={'item_name': 'Third'},
            organization=self.organization,
            created_by=self.user
        )
        DynamicSubTableData.objects.create(
            parent_data=self.parent_data,
            field_definition=self.field_definition,
            row_order=0,
            row_data={'item_name': 'First'},
            organization=self.organization,
            created_by=self.user
        )
        DynamicSubTableData.objects.create(
            parent_data=self.parent_data,
            field_definition=self.field_definition,
            row_order=1,
            row_data={'item_name': 'Second'},
            organization=self.organization,
            created_by=self.user
        )

        rows = self.parent_data.get_sub_table_data('items')
        self.assertEqual(rows[0].row_data['item_name'], 'First')
        self.assertEqual(rows[1].row_data['item_name'], 'Second')
        self.assertEqual(rows[2].row_data['item_name'], 'Third')
