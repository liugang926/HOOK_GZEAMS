"""
Service layer tests for the metadata-driven low-code engine.

Tests cover:
- MetadataService CRUD operations
- MetadataService export functionality
- DynamicDataService CRUD operations
- DynamicDataService formula calculation
- DynamicDataService data number generation
"""
from django.test import TestCase
from django.utils import timezone
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    PageLayout,
    DynamicData,
    DynamicSubTableData
)
from apps.system.services.metadata_service import MetadataService
from apps.system.services.dynamic_data_service import DynamicDataService
from apps.organizations.models import Organization
from apps.accounts.models import User


class MetadataServiceTest(TestCase):
    """Test MetadataService functionality."""

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
        self.service = MetadataService()

    def test_create_business_object(self):
        """Test creating a business object with fields and layouts."""
        data = {
            'code': 'TestAsset',
            'name': 'Test Asset',
            'description': 'Test asset object',
            'enable_workflow': True,
            'enable_version': True,
            'fields': [
                {
                    'code': 'asset_code',
                    'name': 'Asset Code',
                    'field_type': 'text',
                    'is_required': True,
                    'is_system': True
                },
                {
                    'code': 'asset_name',
                    'name': 'Asset Name',
                    'field_type': 'text',
                    'is_required': True
                }
            ],
            'page_layouts': [
                {
                    'layout_code': 'test_form',
                    'layout_name': 'Test Form',
                    'layout_type': 'form',
                    'is_default': True,
                    'layout_config': {
                        'sections': [
                            {
                                'title': 'Basic Information',
                                'columns': 2,
                                'fields': ['asset_code', 'asset_name']
                            }
                        ]
                    }
                }
            ]
        }

        obj = self.service.create_business_object(data)

        self.assertEqual(obj.code, 'TestAsset')
        self.assertEqual(obj.name, 'Test Asset')
        self.assertTrue(obj.enable_workflow)
        self.assertEqual(obj.field_count, 2)
        self.assertEqual(obj.layout_count, 1)

    def test_get_business_object(self):
        """Test retrieving a business object by code."""
        BusinessObject.objects.create(
            code='TEST',
            name='Test Object',
            organization=self.organization,
            created_by=self.user
        )

        obj = self.service.get_business_object('TEST')
        self.assertIsNotNone(obj)
        self.assertEqual(obj.code, 'TEST')

    def test_get_business_object_not_found(self):
        """Test retrieving non-existent business object returns None."""
        obj = self.service.get_business_object('NONEXISTENT')
        self.assertIsNone(obj)

    def test_get_field_definitions(self):
        """Test retrieving field definitions for a business object."""
        bo = BusinessObject.objects.create(
            code='TEST',
            name='Test Object',
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=bo,
            code='field1',
            name='Field 1',
            sort_order=2,
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=bo,
            code='field2',
            name='Field 2',
            sort_order=1,
            organization=self.organization,
            created_by=self.user
        )

        fields = self.service.get_field_definitions('TEST')
        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0].code, 'field2')
        self.assertEqual(fields[1].code, 'field1')

    def test_export_business_object(self):
        """Test exporting a business object as JSON-serializable dict."""
        bo = BusinessObject.objects.create(
            code='TEST',
            name='Test Object',
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=bo,
            code='field1',
            name='Field 1',
            field_type='text',
            organization=self.organization,
            created_by=self.user
        )

        exported = self.service.export_business_object('TEST')

        self.assertEqual(exported['code'], 'TEST')
        self.assertEqual(exported['name'], 'Test Object')
        self.assertEqual(len(exported['fields']), 1)
        self.assertEqual(exported['fields'][0]['code'], 'field1')

    def test_delete_business_object(self):
        """Test soft deleting a business object."""
        BusinessObject.objects.create(
            code='TEST',
            name='Test Object',
            organization=self.organization,
            created_by=self.user
        )

        result = self.service.delete_business_object('TEST')
        self.assertTrue(result)

        # Use all_objects to include soft-deleted records
        obj = BusinessObject.all_objects.get(code='TEST')
        self.assertTrue(obj.is_deleted)

    def test_update_existing_business_object(self):
        """Test updating an existing business object."""
        self.service.create_business_object({
            'code': 'TEST',
            'name': 'Original Name',
            'fields': [],
            'page_layouts': []
        })

        self.service.create_business_object({
            'code': 'TEST',
            'name': 'Updated Name',
            'description': 'Updated description',
            'fields': [
                {
                    'code': 'new_field',
                    'name': 'New Field',
                    'field_type': 'text'
                }
            ],
            'page_layouts': []
        })

        obj = BusinessObject.objects.get(code='TEST')
        self.assertEqual(obj.name, 'Updated Name')
        self.assertEqual(obj.description, 'Updated description')
        self.assertEqual(obj.field_count, 1)


class DynamicDataServiceTest(TestCase):
    """Test DynamicDataService functionality."""

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
        FieldDefinition.objects.create(
            business_object=self.business_object,
            code='asset_name',
            name='Asset Name',
            field_type='text',
            is_required=True,
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=self.business_object,
            code='price',
            name='Price',
            field_type='currency',
            decimal_places=2,
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=self.business_object,
            code='total_value',
            name='Total Value',
            field_type='formula',
            formula='{price}',
            is_readonly=True,
            organization=self.organization,
            created_by=self.user
        )
        self.service = DynamicDataService('Asset')

    def test_create_dynamic_data(self):
        """Test creating dynamic data."""
        data = {
            'asset_name': 'Test Asset',
            'price': 1000
        }

        result = self.service.create(data)

        self.assertIsNotNone(result['id'])
        self.assertEqual(result['asset_name'], 'Test Asset')
        self.assertEqual(result['price'], 1000)
        self.assertEqual(result['status'], 'draft')

    def test_create_with_formula_calculation(self):
        """Test formula field is calculated on creation."""
        data = {
            'asset_name': 'Test Asset',
            'price': 1000
        }

        result = self.service.create(data)

        # Formula field should be calculated
        self.assertEqual(result['total_value'], 1000)

    def test_create_missing_required_field(self):
        """Test validation error for missing required field."""
        data = {
            'price': 1000
        }

        with self.assertRaises(ValueError) as context:
            self.service.create(data)

        # Error message should contain the field name or field display name
        self.assertIn('Asset Name', str(context.exception))

    def test_update_dynamic_data(self):
        """Test updating dynamic data."""
        created = self.service.create({
            'asset_name': 'Original Name',
            'price': 1000
        })

        updated = self.service.update(
            created['id'],
            {'asset_name': 'Updated Name'}
        )

        self.assertEqual(updated['asset_name'], 'Updated Name')
        # Price should remain
        self.assertEqual(updated['price'], 1000)

    def test_get_dynamic_data(self):
        """Test retrieving single dynamic data record."""
        created = self.service.create({
            'asset_name': 'Test Asset',
            'price': 1000
        })

        retrieved = self.service.get(created['id'])

        self.assertEqual(retrieved['asset_name'], 'Test Asset')
        self.assertEqual(retrieved['price'], 1000)

    def test_query_dynamic_data(self):
        """Test querying with pagination and filtering."""
        # Create multiple records
        for i in range(5):
            self.service.create({
                'asset_name': f'Asset {i}',
                'price': 1000 + i
            })

        result = self.service.query(page=1, page_size=2)

        self.assertEqual(result['total'], 5)
        self.assertEqual(len(result['items']), 2)
        self.assertEqual(result['page'], 1)

    def test_data_number_generation(self):
        """Test auto-generated data numbers follow the correct format."""
        data1 = self.service.create({'asset_name': 'Asset 1', 'price': 1000})
        data2 = self.service.create({'asset_name': 'Asset 2', 'price': 2000})

        # Format: ASSET{YYYYMMDD}{SEQUENCE}
        self.assertRegex(data1['data_no'], r'ASSET\d{8}\d{4}')
        self.assertRegex(data2['data_no'], r'ASSET\d{8}\d{4}')

        # Second record should have higher sequence
        seq1 = int(data1['data_no'][-4:])
        seq2 = int(data2['data_no'][-4:])
        self.assertEqual(seq2, seq1 + 1)

    def test_add_sub_table_row(self):
        """Test adding a row to a sub-table field."""
        # Create a sub-table field
        sub_table_field = FieldDefinition.objects.create(
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

        parent_data = self.service.create({
            'asset_name': 'Parent Asset',
            'price': 1000
        })

        row = self.service.add_sub_table_row(
            parent_data['id'],
            'items',
            {'item_name': 'Test Item', 'quantity': 10}
        )

        self.assertEqual(row['row_data']['item_name'], 'Test Item')
        self.assertEqual(row['row_data']['quantity'], 10)
        self.assertEqual(row['row_order'], 0)

    def test_get_sub_table_rows(self):
        """Test retrieving all rows for a sub-table."""
        sub_table_field = FieldDefinition.objects.create(
            business_object=self.business_object,
            code='items',
            name='Items',
            field_type='sub_table',
            sub_table_fields=[
                {'code': 'item_name', 'name': 'Item Name', 'field_type': 'text'}
            ],
            organization=self.organization,
            created_by=self.user
        )

        parent_data = self.service.create({
            'asset_name': 'Parent Asset',
            'price': 1000
        })

        self.service.add_sub_table_row(
            parent_data['id'],
            'items',
            {'item_name': 'Item 1'}
        )
        self.service.add_sub_table_row(
            parent_data['id'],
            'items',
            {'item_name': 'Item 2'}
        )

        rows = self.service.get_sub_table_rows(parent_data['id'], 'items')

        self.assertEqual(len(rows), 2)

    def test_update_sub_table_row(self):
        """Test updating a sub-table row."""
        sub_table_field = FieldDefinition.objects.create(
            business_object=self.business_object,
            code='items',
            name='Items',
            field_type='sub_table',
            sub_table_fields=[
                {'code': 'item_name', 'name': 'Item Name', 'field_type': 'text'}
            ],
            organization=self.organization,
            created_by=self.user
        )

        parent_data = self.service.create({
            'asset_name': 'Parent Asset',
            'price': 1000
        })

        row = self.service.add_sub_table_row(
            parent_data['id'],
            'items',
            {'item_name': 'Original Name'}
        )

        updated = self.service.update_sub_table_row(
            row['id'],
            {'item_name': 'Updated Name'}
        )

        self.assertEqual(updated['row_data']['item_name'], 'Updated Name')

    def test_delete_sub_table_row(self):
        """Test soft deleting a sub-table row."""
        sub_table_field = FieldDefinition.objects.create(
            business_object=self.business_object,
            code='items',
            name='Items',
            field_type='sub_table',
            sub_table_fields=[
                {'code': 'item_name', 'name': 'Item Name', 'field_type': 'text'}
            ],
            organization=self.organization,
            created_by=self.user
        )

        parent_data = self.service.create({
            'asset_name': 'Parent Asset',
            'price': 1000
        })

        row = self.service.add_sub_table_row(
            parent_data['id'],
            'items',
            {'item_name': 'Test Item'}
        )

        result = self.service.delete_sub_table_row(row['id'])
        self.assertTrue(result)

        # Verify row is soft deleted
        rows = self.service.get_sub_table_rows(parent_data['id'], 'items')
        self.assertEqual(len(rows), 0)


class FormulaCalculationTest(TestCase):
    """Test formula field calculation functionality."""

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
            code='Invoice',
            name='Invoice',
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=self.business_object,
            code='quantity',
            name='Quantity',
            field_type='number',
            decimal_places=0,
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=self.business_object,
            code='unit_price',
            name='Unit Price',
            field_type='currency',
            decimal_places=2,
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=self.business_object,
            code='total',
            name='Total',
            field_type='formula',
            formula='{quantity} * {unit_price}',
            is_readonly=True,
            organization=self.organization,
            created_by=self.user
        )
        self.service = DynamicDataService('Invoice')

    def test_simple_formula_calculation(self):
        """Test simple multiplication formula."""
        result = self.service.create({
            'quantity': 10,
            'unit_price': 100
        })

        self.assertEqual(result['total'], 1000)

    def test_formula_with_null_values(self):
        """Test formula handles null values gracefully."""
        result = self.service.create({
            'quantity': None,
            'unit_price': 100
        })

        # Should default to 0 for null values
        self.assertEqual(result['total'], 0)

    def test_complex_formula(self):
        """Test more complex formula expression."""
        FieldDefinition.objects.create(
            business_object=self.business_object,
            code='tax_rate',
            name='Tax Rate',
            field_type='percent',
            decimal_places=2,
            organization=self.organization,
            created_by=self.user
        )
        FieldDefinition.objects.create(
            business_object=self.business_object,
            code='grand_total',
            name='Grand Total',
            field_type='formula',
            formula='{total} * (1 + {tax_rate} / 100)',
            is_readonly=True,
            organization=self.organization,
            created_by=self.user
        )

        result = self.service.create({
            'quantity': 10,
            'unit_price': 100,
            'tax_rate': 10
        })

        # total = 10 * 100 = 1000
        # grand_total = 1000 * (1 + 10/100) = 1100
        self.assertEqual(result['total'], 1000)
        self.assertEqual(result['grand_total'], 1100)
