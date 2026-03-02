"""
Metadata Auto-Sync Service

Automatically synchronizes hardcoded Django models with the metadata engine.
Ensures BusinessObject records exist and fields are synced to ModelFieldDefinition.

This service is called during app startup to maintain consistency between
hardcoded models and the low-code metadata system.
"""
import logging
from uuid import uuid4
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils.module_loading import import_string
from django.core.exceptions import ValidationError

from apps.system.models import (
    BusinessObject,
    ModelFieldDefinition,
    FieldDefinition,
    PageLayout,
)
from apps.system.services.business_object_service import (
    CORE_HARDcoded_MODELS,
    HARDCODED_OBJECT_NAMES,
)
from apps.system.services.layout_generator import LayoutGenerator

logger = logging.getLogger(__name__)


class MetadataSyncService:
    """
    Service for automatically syncing hardcoded models to metadata.

    Responsibilities:
    1. Create BusinessObject records for hardcoded models if missing
    2. Sync model fields to ModelFieldDefinition
    3. Create default layouts if missing
    """

    def __init__(self):
        self.sync_results = {
            'created_objects': [],
            'updated_objects': [],
            'synced_fields': {},
            'created_layouts': [],
            'errors': []
        }

    def sync_all_hardcoded_models(self, force: bool = False) -> Dict[str, Any]:
        """
        Sync all hardcoded models to metadata.

        Args:
            force: Force re-sync of fields even if BusinessObject exists

        Returns:
            Sync results with created/updated objects and fields
        """
        self.sync_results = {
            'created_objects': [],
            'updated_objects': [],
            'synced_fields': {},
            'created_layouts': [],
            'errors': []
        }

        for object_code, model_path in CORE_HARDcoded_MODELS.items():
            try:
                self._sync_single_model(object_code, model_path, force)
            except Exception as e:
                logger.error(f"Failed to sync {object_code}: {e}")
                self.sync_results['errors'].append({
                    'object_code': object_code,
                    'error': str(e)
                })

        logger.info(f"Metadata sync completed: {self.sync_results}")
        return self.sync_results

    def _sync_single_model(self, object_code: str, model_path: str, force: bool = False):
        """Sync a single hardcoded model to metadata."""
        # Import the model class
        try:
            model_class = import_string(model_path)
        except ImportError as e:
            logger.warning(f"Could not import {model_path}: {e}")
            return

        # Get or create BusinessObject
        obj, created = BusinessObject.objects.get_or_create(
            code=object_code,
            defaults={
                'name': HARDCODED_OBJECT_NAMES.get(object_code, (object_code, object_code))[0],
                'name_en': HARDCODED_OBJECT_NAMES.get(object_code, (object_code, object_code))[1],
                'is_hardcoded': True,
                'django_model_path': model_path,
                'description': f'Hardcoded model: {model_path}',
                'enable_workflow': False,
                'enable_version': True,
                'enable_soft_delete': True,
            }
        )

        if created:
            self.sync_results['created_objects'].append(object_code)
            logger.info(f"Created BusinessObject for {object_code}")
        elif force:
            self.sync_results['updated_objects'].append(object_code)
            logger.info(f"Updated BusinessObject for {object_code}")

        # Sync fields
        field_count = self._sync_model_fields(obj, model_class)
        self.sync_results['synced_fields'][object_code] = field_count

        # Create default layouts if missing
        self._ensure_default_layouts(obj, object_code)

    def _sync_model_fields(self, business_obj: BusinessObject, model_class) -> int:
        """
        Sync model fields to ModelFieldDefinition.

        Analyzes Django model fields and creates corresponding
        ModelFieldDefinition records.
        """
        synced_count = 0

        # Get existing field definitions to avoid duplicates
        existing_fields = {
            fd.field_name: fd
            for fd in ModelFieldDefinition.objects.filter(
                business_object=business_obj,
                is_deleted=False
            )
        }

        # Process each model field
        for field in model_class._meta.get_fields():
            # Skip auto-generated relations and many-to-many fields
            if field.auto_created or field.many_to_many:
                if not field.concrete:
                    continue

            field_name = field.name
            field_type = self._get_field_type(field)
            if not field_type:
                continue

            # Determine if field is required
            is_required = not field.null and not field.blank and not field.default

            # Get field properties
            max_length = getattr(field, 'max_length', None)
            decimal_places = getattr(field, 'decimal_places', None)
            help_text = getattr(field, 'help_text', '')
            verbose_name = getattr(field, 'verbose_name', field_name)

            # Check if this is a foreign key
            ref_model_path = None
            if field.is_relation and field.many_to_one:
                ref_model = field.related_model
                if ref_model:
                    ref_model_path = f"{ref_model.__module__}.{ref_model.__name__}"

            # Update or create field definition
            if field_name in existing_fields:
                # Update existing
                fd = existing_fields[field_name]
                fd.field_type = field_type
                fd.is_required = is_required
                fd.max_length = max_length or fd.max_length
                fd.decimal_places = decimal_places or fd.decimal_places
                fd.display_name = verbose_name or fd.display_name
                fd.reference_model_path = ref_model_path or fd.reference_model_path
                fd.save()
                synced_count += 1
            else:
                # Create new - only use fields that exist in ModelFieldDefinition
                create_kwargs = {
                    'business_object': business_obj,
                    'field_name': field_name,
                    'display_name': verbose_name or field_name,
                    'field_type': field_type,
                    'is_required': is_required,
                    'is_readonly': False,
                    'show_in_list': self._should_show_in_list(field_name),
                    'show_in_detail': True,
                    'show_in_form': True,
                    'sort_order': synced_count + 1,
                    'reference_model_path': ref_model_path or '',
                    'reference_display_field': 'name' if ref_model_path else '',
                }

                # Only add optional fields if they have values
                if max_length:
                    create_kwargs['max_length'] = max_length
                if decimal_places is not None:
                    create_kwargs['decimal_places'] = decimal_places

                ModelFieldDefinition.objects.create(**create_kwargs)
                synced_count += 1

        return synced_count

    def _get_field_type(self, field) -> Optional[str]:
        """
        Map Django field type to metadata field type.

        Special field types are detected based on field name patterns:
        - qr_code: QR code field (CharField with 'qr' and 'code' in name)
        - image: Image storage field (JSONField with 'image', 'photo', or 'picture' in name)
        - file: File storage field (JSONField with 'attachment', 'file', or 'document' in name)
        """
        return ModelFieldDefinition.get_metadata_field_type(field)

    def _should_show_in_list(self, field_name: str) -> bool:
        """Determine if field should be shown in list view by default."""
        # Common fields to show in list
        list_fields = {
            'asset_code', 'asset_name', 'code', 'name', 'status', 'asset_status',
            'category', 'asset_category', 'department', 'custodian', 'location',
            'purchase_price', 'current_value', 'created_at', 'updated_at'
        }
        return field_name in list_fields

    def _get_object_code_for_model(self, model_class) -> Optional[str]:
        """Get object code for a related model class."""
        model_path = f"{model_class.__module__}.{model_class.__name__}"
        for code, path in CORE_HARDcoded_MODELS.items():
            if path == model_path:
                return code
        return None

    def _ensure_default_layouts(self, business_obj: BusinessObject, object_code: str):
        """
        Ensure default layouts are properly configured for the business object.

        - Updates existing layouts with synced fields
        - Creates default form layout if it doesn't exist
        - Archives legacy list layouts (list rendering is field-driven)
        """
        # Find or create form layout
        form_layout = PageLayout.objects.filter(
            business_object=business_obj,
            layout_type='form',
            is_default=True,
            is_deleted=False
        ).first()

        # Update or create form layout
        if form_layout:
            if business_obj.is_hardcoded:
                self._update_form_layout(form_layout, object_code)
            else:
                self._update_form_layout_dynamic(form_layout, object_code)
            self.sync_results['created_layouts'].append(
                f"{object_code}_form (updated)"
            )
        else:
            if business_obj.is_hardcoded:
                form_layout = self._create_default_form_layout(business_obj, object_code)
            else:
                form_layout = self._create_default_form_layout_dynamic(business_obj, object_code)
            if form_layout:
                self.sync_results['created_layouts'].append(
                    f"{object_code}_form (created)"
                )

        # Single-layout model:
        # list pages are generated from FieldDefinition.show_in_list + user column preferences.
        # Keep any historical list rows archived so they no longer participate in runtime selection.
        archived_count = (
            PageLayout.objects
            .filter(
                business_object=business_obj,
                layout_type='list',
                is_deleted=False
            )
            .exclude(status='archived', is_active=False, is_default=False)
            .update(status='archived', is_active=False, is_default=False)
        )
        if archived_count:
            self.sync_results['created_layouts'].append(
                f"{object_code}_list (archived:{archived_count})"
            )

        # Link to business object
        if form_layout and not business_obj.default_form_layout:
            business_obj.default_form_layout = form_layout
        if business_obj.default_list_layout_id:
            business_obj.default_list_layout = None
        business_obj.save()

    def _update_form_layout(self, layout: PageLayout, object_code: str):
        """Update existing form layout with synced fields (append missing only)."""
        try:
            fields = ModelFieldDefinition.objects.filter(
                business_object=layout.business_object,
                is_deleted=False,
                show_in_form=True
            ).order_by('sort_order')

            if not fields.exists():
                return

            layout_config = layout.layout_config or {}
            sections = layout_config.get('sections') or []

            # Normalize existing sections and collect existing field codes
            existing_field_codes = set()
            for section in sections:
                section.setdefault('id', f"section-{uuid4().hex}")
                section.setdefault('type', 'section')
                for field in section.get('fields', []) or []:
                    field_code = field.get('fieldCode') or field.get('field') or field.get('field_code') or field.get('code')
                    if field_code:
                        existing_field_codes.add(field_code)
                    field.setdefault('id', f"field-{uuid4().hex}")

            missing_fields = []
            for field_def in fields:
                if field_def.field_name in existing_field_codes:
                    continue
                missing_fields.append({
                    'id': f"field-{uuid4().hex}",
                    'fieldCode': field_def.field_name,
                    'label': field_def.display_name or field_def.field_name,
                    'span': self._get_field_span(field_def.field_name),
                    'required': field_def.is_required,
                    'readonly': field_def.is_readonly,
                    'visible': True
                })

            if missing_fields:
                sections.append({
                    'id': f"section-{uuid4().hex}",
                    'type': 'section',
                    'title': 'Auto Added',
                    'collapsed': True,
                    'fields': missing_fields
                })

            layout.layout_config = {
                **layout_config,
                'sections': sections,
                'columns': layout_config.get('columns', 2)
            }
            layout.save(update_fields=['layout_config'])
            logger.info(f"Updated form layout for {object_code} (missing fields appended)")

        except Exception as e:
            logger.error(f"Failed to update form layout for {object_code}: {e}")

    def _update_list_layout(self, layout: PageLayout, object_code: str):
        """Update existing list layout with synced fields (append missing only)."""
        try:
            fields = ModelFieldDefinition.objects.filter(
                business_object=layout.business_object,
                is_deleted=False,
                show_in_list=True
            ).order_by('sort_order')

            if not fields.exists():
                return

            layout_config = layout.layout_config or {}
            columns = layout_config.get('columns') or []
            existing_column_codes = set()
            for col in columns:
                col_code = col.get('fieldCode') or col.get('field_code') or col.get('prop') or col.get('code')
                if col_code:
                    existing_column_codes.add(col_code)

            for field_def in fields:
                if field_def.field_name in existing_column_codes:
                    continue
                columns.append({
                    'field_code': field_def.field_name,
                    'fieldCode': field_def.field_name,
                    'prop': field_def.field_name,
                    'label': field_def.display_name or field_def.field_name,
                    'width': 120,
                    'sortable': True,
                    'visible': True,
                    'type': field_def.field_type
                })

            layout.layout_config = {
                **layout_config,
                'columns': columns,
                'page_size': layout_config.get('page_size', 20),
                'show_index': layout_config.get('show_index', True),
                'show_selection': layout_config.get('show_selection', True)
            }
            layout.save(update_fields=['layout_config'])
            logger.info(f"Updated list layout for {object_code} (missing fields appended)")

        except Exception as e:
            logger.error(f"Failed to update list layout for {object_code}: {e}")

    def _normalize_form_layout_config(self, layout_config: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure layout config has required ids/types for sections and fields."""
        config = layout_config or {}
        sections = config.get('sections') or []
        for section in sections:
            section.setdefault('id', f"section-{uuid4().hex}")
            section.setdefault('type', 'section')
            fields = section.get('fields') or []
            for field in fields:
                field.setdefault('id', f"field-{uuid4().hex}")
                if 'fieldCode' not in field and 'field' in field:
                    field['fieldCode'] = field.get('field')
                if 'label' not in field:
                    field['label'] = field.get('fieldCode', '')
                field.setdefault('span', 1)
                field.setdefault('visible', True)
        config['sections'] = sections
        config.setdefault('columns', 2)
        return config

    def _update_form_layout_dynamic(self, layout: PageLayout, object_code: str):
        """Update existing form layout for dynamic objects (append missing only)."""
        try:
            fields = FieldDefinition.objects.filter(
                business_object=layout.business_object,
                is_deleted=False,
                show_in_form=True
            ).order_by('sort_order')

            if not fields.exists():
                return

            layout_config = self._normalize_form_layout_config(layout.layout_config or {})
            sections = layout_config.get('sections') or []

            existing_field_codes = set()
            for section in sections:
                for field in section.get('fields', []) or []:
                    field_code = field.get('fieldCode') or field.get('field') or field.get('field_code') or field.get('code')
                    if field_code:
                        existing_field_codes.add(field_code)

            missing_fields = []
            for field_def in fields:
                if field_def.code in existing_field_codes:
                    continue
                missing_fields.append({
                    'id': f"field-{uuid4().hex}",
                    'fieldCode': field_def.code,
                    'label': field_def.name,
                    'span': field_def.span if hasattr(field_def, 'span') else 12,
                    'required': field_def.is_required,
                    'readonly': field_def.is_readonly,
                    'visible': True
                })

            if missing_fields:
                sections.append({
                    'id': f"section-{uuid4().hex}",
                    'type': 'section',
                    'title': 'Auto Added',
                    'collapsed': True,
                    'fields': missing_fields
                })

            layout.layout_config = {
                **layout_config,
                'sections': sections
            }
            layout.save(update_fields=['layout_config'])
            logger.info(f"Updated dynamic form layout for {object_code} (missing fields appended)")

        except Exception as e:
            logger.error(f"Failed to update dynamic form layout for {object_code}: {e}")

    def _update_list_layout_dynamic(self, layout: PageLayout, object_code: str):
        """Update existing list layout for dynamic objects (append missing only)."""
        try:
            fields = FieldDefinition.objects.filter(
                business_object=layout.business_object,
                is_deleted=False,
                show_in_list=True
            ).order_by('sort_order')

            if not fields.exists():
                return

            layout_config = layout.layout_config or {}
            columns = layout_config.get('columns') or []
            existing_column_codes = set()
            for col in columns:
                col_code = col.get('fieldCode') or col.get('field_code') or col.get('prop') or col.get('code')
                if col_code:
                    existing_column_codes.add(col_code)

            for field_def in fields:
                if field_def.code in existing_column_codes:
                    continue
                columns.append({
                    'field_code': field_def.code,
                    'fieldCode': field_def.code,
                    'prop': field_def.code,
                    'label': field_def.name,
                    'width': 120,
                    'sortable': True,
                    'visible': True,
                    'type': field_def.field_type
                })

            layout.layout_config = {
                **layout_config,
                'columns': columns,
                'page_size': layout_config.get('page_size', 20),
                'show_index': layout_config.get('show_index', True),
                'show_selection': layout_config.get('show_selection', True)
            }
            layout.save(update_fields=['layout_config'])
            logger.info(f"Updated dynamic list layout for {object_code} (missing fields appended)")

        except Exception as e:
            logger.error(f"Failed to update dynamic list layout for {object_code}: {e}")

    def _create_default_form_layout_dynamic(self, business_obj: BusinessObject, object_code: str) -> Optional[PageLayout]:
        """Create default form layout for dynamic object."""
        try:
            layout_config = LayoutGenerator.generate_form_layout(business_obj)
            layout_config = self._normalize_form_layout_config(layout_config)

            layout = PageLayout.objects.create(
                business_object=business_obj,
                layout_code=f'{object_code.lower()}_default_form',
                layout_name=f'{business_obj.name} Default Form',
                layout_type='form',
                layout_config=layout_config,
                is_default=True,
                is_active=True,
                status='published',
                version='1.0.0'
            )

            logger.info(f"Created default form layout for {object_code}")
            return layout

        except Exception as e:
            logger.error(f"Failed to create dynamic form layout for {object_code}: {e}")
            return None

    def _create_default_list_layout_dynamic(self, business_obj: BusinessObject, object_code: str) -> Optional[PageLayout]:
        """Create default list layout for dynamic object."""
        try:
            layout_config = LayoutGenerator.generate_list_layout(business_obj)
            layout = PageLayout.objects.create(
                business_object=business_obj,
                layout_code=f'{object_code.lower()}_default_list',
                layout_name=f'{business_obj.name} Default List',
                layout_type='list',
                layout_config=layout_config,
                is_default=True,
                is_active=True,
                status='published',
                version='1.0.0'
            )

            logger.info(f"Created default list layout for {object_code}")
            return layout

        except Exception as e:
            logger.error(f"Failed to create dynamic list layout for {object_code}: {e}")
            return None

    def _create_default_form_layout(self, business_obj: BusinessObject, object_code: str) -> Optional[PageLayout]:
        """Create default form layout for an object."""
        try:
            # Get all field definitions
            fields = ModelFieldDefinition.objects.filter(
                business_object=business_obj,
                is_deleted=False
            ).order_by('sort_order')

            # Build layout config with sections
            sections = self._build_form_sections(object_code, fields)

            layout_config = {
                'sections': sections,
                'columns': 2
            }

            layout = PageLayout.objects.create(
                business_object=business_obj,
                layout_code=f'{object_code.lower()}_default_form',
                layout_name=f'{business_obj.name} Default Form',
                layout_type='form',
                layout_config=layout_config,
                is_default=True,
                is_active=True,
                status='published',
                version='1.0.0'
            )

            logger.info(f"Created default form layout for {object_code}")
            return layout

        except Exception as e:
            logger.error(f"Failed to create form layout for {object_code}: {e}")
            return None

    def _create_default_list_layout(self, business_obj: BusinessObject, object_code: str) -> Optional[PageLayout]:
        """Create default list layout for an object."""
        try:
            # Get list fields
            fields = ModelFieldDefinition.objects.filter(
                business_object=business_obj,
                is_deleted=False,
                show_in_list=True
            ).order_by('sort_order')

            columns = []
            for field in fields:
                columns.append({
                    'field_code': field.field_name,
                    'fieldCode': field.field_name,
                    'prop': field.field_name,
                    'label': field.display_name or field.field_name,
                    'width': 120,
                    'sortable': True,
                    'visible': True,
                    'type': field.field_type
                })

            layout_config = {
                'columns': columns,
                'page_size': 20,
                'show_index': True,
                'show_selection': True
            }

            layout = PageLayout.objects.create(
                business_object=business_obj,
                layout_code=f'{object_code.lower()}_default_list',
                layout_name=f'{business_obj.name} Default List',
                layout_type='list',
                layout_config=layout_config,
                is_default=True,
                is_active=True,
                status='published',
                version='1.0.0'
            )

            logger.info(f"Created default list layout for {object_code}")
            return layout

        except Exception as e:
            logger.error(f"Failed to create list layout for {object_code}: {e}")
            return None

    def _build_form_sections(self, object_code: str, fields) -> List[Dict]:
        """Build form sections based on object type and field names."""
        # Group fields by section
        sections_map = self._get_section_mapping(object_code)

        sections = []
        for section_title, field_patterns in sections_map:
            section_fields = []
            for field in fields:
                if any(fp in field.field_name for fp in field_patterns):
                    section_fields.append({
                        'id': f"field-{uuid4().hex}",
                        'fieldCode': field.field_name,
                        'label': field.display_name or field.field_name,
                        'span': self._get_field_span(field.field_name),
                        'required': field.is_required,
                        'readonly': field.is_readonly,
                        'visible': True
                    })

            if section_fields:
                sections.append({
                    'id': f"section-{uuid4().hex}",
                    'type': 'section',
                    'title': section_title,
                    'collapsed': False,
                    'fields': section_fields
                })

        # Add any remaining fields to "Other" section
        assigned_fields = set()
        for section in sections:
            for f in section['fields']:
                field_code = f.get('fieldCode') or f.get('field')
                if field_code:
                    assigned_fields.add(field_code)

        other_fields = []
        for field in fields:
            if field.field_name not in assigned_fields and field.field_name not in ['id', 'created_at', 'updated_at', 'created_by', 'organization']:
                other_fields.append({
                    'id': f"field-{uuid4().hex}",
                    'fieldCode': field.field_name,
                    'label': field.display_name or field.field_name,
                    'span': 1,
                    'required': field.is_required,
                    'readonly': field.is_readonly,
                    'visible': True
                })

        if other_fields:
            sections.append({
                'id': f"section-{uuid4().hex}",
                'type': 'section',
                'title': 'Other',
                'collapsed': True,
                'fields': other_fields
            })

        return sections or [{
            'id': f"section-{uuid4().hex}",
            'type': 'section',
            'title': 'Basic',
            'collapsed': False,
            'fields': []
        }]

    def _get_section_mapping(self, object_code: str) -> List[tuple]:
        """Get section mapping for specific object types."""
        if object_code == 'Asset':
            return [
                ('Basic Information', ['asset_code', 'asset_name', 'specification', 'brand', 'model', 'serial_number']),
                ('Category', ['asset_category', 'unit']),
                ('Financial', ['purchase_price', 'current_value', 'accumulated_depreciation', 'purchase_date', 'depreciation_start_date', 'useful_life', 'residual_rate']),
                ('Supplier', ['supplier', 'supplier_order_no', 'invoice_no']),
                ('Usage', ['department', 'location', 'custodian', 'user']),
                ('Status', ['asset_status', 'qr_code', 'rfid_code']),
            ]
        elif object_code == 'AssetCategory':
            return [
                ('Basic', ['code', 'name', 'parent']),
                ('Depreciation', ['depreciation_method', 'default_useful_life', 'residual_rate']),
            ]
        else:
            # Generic mapping
            return [
                ('Basic', ['code', 'name', 'description']),
                ('Details', []),
            ]

    def _get_field_span(self, field_name: str) -> int:
        """Determine field span (1 or 2 columns)."""
        # Fields that take full width
        full_width_fields = ['remarks', 'description', 'attachments']
        return 2 if field_name in full_width_fields else 1


# Singleton instance
_metadata_sync_service = None


def get_metadata_sync_service() -> MetadataSyncService:
    """Get the singleton metadata sync service instance."""
    global _metadata_sync_service
    if _metadata_sync_service is None:
        _metadata_sync_service = MetadataSyncService()
    return _metadata_sync_service


def sync_metadata_on_startup(force: bool = False) -> Dict[str, Any]:
    """
    Sync metadata during app startup.

    This function is called from apps.py ready() method.

    Args:
        force: Force re-sync of all fields

    Returns:
        Sync results
    """
    service = get_metadata_sync_service()
    results = service.sync_all_hardcoded_models(force=force)

    # Ensure default layouts for dynamic business objects
    try:
        dynamic_objects = BusinessObject.objects.filter(is_hardcoded=False, is_deleted=False)
        for obj in dynamic_objects:
            service._ensure_default_layouts(obj, obj.code)
        logger.info(f"Ensured default layouts for {dynamic_objects.count()} dynamic objects")
    except Exception as e:
        logger.warning(f"Failed to ensure default layouts for dynamic objects: {e}")

    return results
