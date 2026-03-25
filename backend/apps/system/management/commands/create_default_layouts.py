"""
Management command to create default layouts for business objects.

This command generates default form and list layouts for business objects
that don't have layouts configured yet.

Usage:
    python manage.py create_default_layouts
    python manage.py create_default_layouts --code AssetTransfer
    python manage.py create_default_layouts --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.system.services.business_object_service import (
    BusinessObjectService,
    CORE_HARDcoded_MODELS,
    HARDCODED_OBJECT_NAMES,
)
from apps.system.models import BusinessObject, PageLayout
from apps.system.services.layout_generator import LayoutGenerator


SEARCH_SECTION_TITLE = {
    'zh': '搜索条件',
    'en': 'Search Filters',
}


# Default layout configurations for each object type
DEFAULT_LAYOUT_CONFIGS = {
    # Asset Operations
    'AssetTransfer': {
        'form_sections': [
            {'title': '调拨信息', 'fields': ['transfer_no', 'transfer_date', 'from_department', 'to_department', 'handler']},
            {'title': '调拨原因', 'fields': ['reason', 'remark']},
        ],
        'list_columns': ['transfer_no', 'transfer_date', 'from_department', 'to_department', 'status', 'created_at'],
    },
    'AssetReturn': {
        'form_sections': [
            {'title': '归还信息', 'fields': ['return_no', 'return_date', 'borrower', 'handler', 'return_condition']},
            {'title': '备注', 'fields': ['remark']},
        ],
        'list_columns': ['return_no', 'return_date', 'borrower', 'handler', 'status', 'created_at'],
    },
    'AssetLoan': {
        'form_sections': [
            {'title': '借用信息', 'fields': ['loan_no', 'loan_date', 'borrower', 'expected_return_date', 'handler']},
            {'title': '备注', 'fields': ['remark']},
        ],
        'list_columns': ['loan_no', 'loan_date', 'borrower', 'expected_return_date', 'status', 'created_at'],
    },

    # Consumables
    'Consumable': {
        'form_sections': [
            {'title': '基本信息', 'fields': ['code', 'name', 'category', 'specification', 'unit']},
            {'title': '库存信息', 'fields': ['stock_quantity', 'min_stock', 'max_stock', 'safety_stock']},
            {'title': '其他', 'fields': ['remark']},
        ],
        'list_columns': ['code', 'name', 'category', 'stock_quantity', 'unit', 'created_at'],
    },
    'ConsumablePurchase': {
        'form_sections': [
            {'title': '采购信息', 'fields': ['purchase_no', 'purchase_date', 'supplier', 'handler']},
            {'title': '备注', 'fields': ['remark']},
        ],
        'list_columns': ['purchase_no', 'purchase_date', 'supplier', 'total_amount', 'status', 'created_at'],
    },
    'ConsumableIssue': {
        'form_sections': [
            {'title': '领用信息', 'fields': ['issue_no', 'issue_date', 'receiver', 'department', 'handler']},
            {'title': '备注', 'fields': ['remark']},
        ],
        'list_columns': ['issue_no', 'issue_date', 'receiver', 'department', 'status', 'created_at'],
    },

    # Lifecycle
    'PurchaseRequest': {
        'form_sections': [
            {'title': '申请信息', 'fields': ['request_no', 'request_date', 'requester', 'department']},
            {'title': '采购详情', 'fields': ['expected_date', 'budget_amount', 'reason']},
        ],
        'list_columns': ['request_no', 'request_date', 'requester', 'budget_amount', 'status', 'created_at'],
    },
    'AssetReceipt': {
        'form_sections': [
            {'title': '入库信息', 'fields': ['receipt_no', 'receipt_date', 'supplier', 'handler']},
            {'title': '备注', 'fields': ['remark']},
        ],
        'list_columns': ['receipt_no', 'receipt_date', 'supplier', 'quantity', 'status', 'created_at'],
    },
    'Maintenance': {
        'form_sections': [
            {'title': '维修信息', 'fields': ['maintenance_no', 'maintenance_date', 'asset', 'maintenance_type', 'cost']},
            {'title': '详情', 'fields': ['description', 'result', 'handler']},
        ],
        'list_columns': ['maintenance_no', 'maintenance_date', 'asset', 'maintenance_type', 'cost', 'status'],
    },
    'DisposalRequest': {
        'form_sections': [
            {'title': '报废申请', 'fields': ['disposal_no', 'application_date', 'asset', 'disposal_reason']},
            {'title': '审批', 'fields': ['estimated_value', 'approver', 'remark']},
        ],
        'list_columns': ['disposal_no', 'application_date', 'asset', 'disposal_reason', 'status', 'created_at'],
    },

    # IT Assets
    'ITAsset': {
        'form_sections': [
            {'title': '基本信息', 'fields': ['asset_no', 'name', 'category', 'model', 'serial_number']},
            {'title': '配置信息', 'fields': ['cpu', 'memory', 'disk', 'os', 'ip_address']},
            {'title': '使用信息', 'fields': ['user', 'department', 'location', 'purchase_date']},
        ],
        'list_columns': ['asset_no', 'name', 'category', 'model', 'user', 'department', 'status'],
    },
}


def generate_form_layout_config(object_code: str, field_names: list) -> dict:
    """Generate form layout configuration based on available fields."""
    config = DEFAULT_LAYOUT_CONFIGS.get(object_code, {})

    if config.get('form_sections'):
        # Use predefined sections
        sections = []
        for section_config in config['form_sections']:
            section_fields = []
            for field_name in section_config['fields']:
                if field_name in field_names:
                    section_fields.append({
                        'id': f'field_{field_name}',
                        'field_code': field_name,
                        'label': field_name,
                        'span': 12,
                        'visible': True,
                        'required': field_name in ['code', 'name', 'transfer_date', 'loan_date']
                    })

            sections.append({
                'id': f"section_{len(sections)}",
                'type': 'section',
                'title': section_config['title'],
                'collapsible': True,
                'collapsed': False,
                'border': True,
                'columns': 2,
                'fields': section_fields
            })

        return {'sections': sections} if sections else None

    # Generate default layout
    section_fields = []
    for i, field_name in enumerate(field_names[:20]):  # Limit to 20 fields
        section_fields.append({
            'id': f'field_{field_name}',
            'field_code': field_name,
            'label': field_name,
            'span': 12,
            'visible': True,
            'required': field_name in ['code', 'name']
        })

    return {
        'sections': [{
            'id': 'section_0',
            'type': 'section',
            'title': '基本信息',
            'collapsible': False,
            'border': True,
            'columns': 2,
            'fields': section_fields
        }]
    }


def generate_list_layout_config(object_code: str, field_names: list) -> dict:
    """Generate list layout configuration based on available fields."""
    config = DEFAULT_LAYOUT_CONFIGS.get(object_code, {})

    if config.get('list_columns'):
        # Use predefined columns
        columns = []
        for i, field_name in enumerate(config['list_columns']):
            if field_name in field_names:
                columns.append({
                    'id': f'col_{field_name}',
                    'field_code': field_name,
                    'label': field_name,
                    'width': 120,
                    'sortable': True,
                    'fixed': 'left' if i == 0 else ''
                })

        if columns:
            return {'columns': columns, 'actions': [
                {'code': 'view', 'label': '查看', 'type': 'primary', 'position': 'table'},
                {'code': 'edit', 'label': '编辑', 'type': 'default', 'position': 'table'},
                {'code': 'delete', 'label': '删除', 'type': 'danger', 'position': 'table'}
            ]}

    # Generate default columns
    columns = []
    display_fields = ['code', 'name', 'status', 'created_at']

    for field_name in display_fields:
        if field_name in field_names:
            columns.append({
                'id': f'col_{field_name}',
                'field_code': field_name,
                'label': field_name,
                'width': 120,
                'sortable': True,
                'fixed': 'left' if field_name == 'code' else ''
            })

    return {'columns': columns, 'actions': [
        {'code': 'view', 'label': '查看', 'type': 'primary', 'position': 'table'},
        {'code': 'edit', 'label': '编辑', 'type': 'default', 'position': 'table'},
        {'code': 'delete', 'label': '删除', 'type': 'danger', 'position': 'table'}
    ]}


def generate_detail_layout_config(object_code: str, field_names: list) -> dict:
    """Generate detail layout configuration based on available fields."""
    # Detail layout is similar to form but all fields are readonly
    form_config = generate_form_layout_config(object_code, field_names)
    if form_config and form_config.get('sections'):
        # Make all fields readonly
        for section in form_config['sections']:
            section['collapsed'] = False
            if section.get('fields'):
                for field in section['fields']:
                    field['readonly'] = True
        return form_config

    # Generate default detail layout
    section_fields = []
    for i, field_name in enumerate(field_names[:20]):
        section_fields.append({
            'id': f'field_{field_name}',
            'field_code': field_name,
            'label': field_name,
            'span': 12,
            'visible': True,
            'readonly': True
        })

    return {
        'sections': [{
            'id': 'section_0',
            'type': 'section',
            'title': '详细信息',
            'collapsible': False,
            'border': True,
            'columns': 2,
            'fields': section_fields
        }]
    }


def generate_search_layout_config(object_code: str, field_names: list) -> dict:
    """Generate search layout configuration based on available fields."""
    # Common searchable fields
    searchable_fields = ['code', 'name', 'status', 'created_at']

    # Add object-specific search fields
    if 'Asset' in object_code:
        searchable_fields.extend(['category', 'location', 'department'])
    elif 'Transfer' in object_code or 'Loan' in object_code or 'Return' in object_code:
        searchable_fields.extend(['from_department', 'to_department', 'borrower', 'status'])
    elif 'Consumable' in object_code:
        searchable_fields.extend(['category', 'unit'])

    search_fields = []
    for field_name in searchable_fields:
        if field_name in field_names:
            search_fields.append({
                'id': f'search_{field_name}',
                'field_code': field_name,
                'label': field_name,
                'span': 1,
                'visible': True,
                'component': _get_search_component(field_name)
            })

    return {
        'sections': [{
            'id': 'search_section',
            'type': 'section',
            'title': SEARCH_SECTION_TITLE,
            'collapsible': False,
            'border': True,
            'columns': 3,
            'fields': search_fields[:12]  # Limit to 12 search fields
        }]
    }


def _get_search_component(field_name: str) -> str:
    """Get appropriate search component for a field."""
    component_map = {
        'status': 'select',
        'created_at': 'date_range',
        'updated_at': 'date_range',
        'department': 'department',
        'from_department': 'department',
        'to_department': 'department',
        'category': 'tree_select',
        'location': 'tree_select',
        'user': 'user',
        'borrower': 'user',
        'handler': 'user',
        'created_by': 'user',
    }
    return component_map.get(field_name, 'input')


def get_available_field_names(business_object: BusinessObject, *, for_search: bool = False) -> list[str]:
    """Return field codes available for default layout generation."""
    if business_object.is_hardcoded:
        rows = business_object.model_fields.filter(
            is_deleted=False,
        ).order_by('sort_order', 'field_name')
        visible_rows = [
            row for row in rows
            if str(row.field_name or '').strip() and getattr(row, 'field_type', '') != 'sub_table'
        ]
        if for_search:
            search_rows = [row for row in visible_rows if getattr(row, 'show_in_list', False)]
            visible_rows = search_rows or visible_rows
        return [
            str(row.field_name or '').strip()
            for row in visible_rows
        ]

    rows = business_object.field_definitions.filter(
        is_deleted=False,
    ).order_by('sort_order', 'code')
    visible_rows = [
        row for row in rows
        if (
            str(row.code or '').strip()
            and not getattr(row, 'is_reverse_relation', False)
            and getattr(row, 'field_type', '') != 'sub_table'
        )
    ]
    if for_search:
        search_rows = [
            row for row in visible_rows
            if getattr(row, 'show_in_filter', False) or getattr(row, 'is_searchable', False)
        ]
        visible_rows = search_rows or visible_rows
    return [
        str(row.code or '').strip()
        for row in visible_rows
    ]


class Command(BaseCommand):
    help = 'Create default layouts for business objects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--code',
            type=str,
            help='Create layouts for a specific business object only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='Overwrite existing layouts',
        )

    def handle(self, *args, **options):
        specific_code = options.get('code')
        force = options.get('force', False)

        service = BusinessObjectService()

        # Determine which objects to process
        if specific_code:
            if specific_code in CORE_HARDcoded_MODELS or BusinessObject.objects.filter(code=specific_code).exists():
                object_codes = [specific_code]
            else:
                self.stderr.write(
                    self.style.ERROR(f'Unknown business object: {specific_code}')
                )
                return
        else:
            object_codes = sorted({
                *CORE_HARDcoded_MODELS.keys(),
                *BusinessObject.objects.filter(is_deleted=False).values_list('code', flat=True),
            })

        # Statistics
        created_count = 0
        skipped_count = 0
        error_count = 0

        # Layout types to create
        layout_types = [
            ('form', 'form', generate_form_layout_config),
            ('list', 'list', generate_list_layout_config),
            ('detail', 'detail', generate_detail_layout_config),
            ('search', 'search', generate_search_layout_config),
        ]

        with transaction.atomic():
            for code in object_codes:
                try:
                    # Get or register BusinessObject
                    obj = BusinessObject.objects.filter(code=code).first()

                    if not obj:
                        if code in CORE_HARDcoded_MODELS:
                            names = HARDCODED_OBJECT_NAMES.get(code, (code, code))
                            obj = service.register_hardcoded_object(code, names[0], names[1])
                            self.stdout.write(f'  {self.style.SUCCESS("REGISTERED")}: {code}')
                        else:
                            self.stdout.write(f'  {self.style.WARNING("SKIP")}: {code} not registered')
                            skipped_count += 1
                            continue

                    # Sync fields first
                    if obj.is_hardcoded and code in CORE_HARDcoded_MODELS:
                        try:
                            service.sync_model_fields(code)
                            self.stdout.write(f'    {self.style.SUCCESS("SYNCED")}: Fields synced')
                        except Exception as e:
                            self.stdout.write(f'    {self.style.WARNING("WARNING")}: Could not sync fields - {e}')

                    # Get available field names
                    field_names = get_available_field_names(obj)
                    search_field_names = get_available_field_names(obj, for_search=True)

                    if not field_names:
                        self.stdout.write(f'    {self.style.WARNING("SKIP")}: No fields available')
                        skipped_count += 1
                        continue

                    # Create all layout types
                    for layout_type, layout_name_suffix, config_generator in layout_types:
                        layout_code = f'{code.lower()}_{layout_type}'
                        existing_layout = PageLayout.objects.filter(
                            business_object=obj,
                            layout_code=layout_code
                        ).first()

                        should_update = force or existing_layout is None or bool(existing_layout.is_default)

                        if existing_layout and not should_update:
                            self.stdout.write(f'    {self.style.SUCCESS("EXISTS")}: {layout_name_suffix} layout')
                        else:
                            if layout_type == 'form':
                                layout_config = LayoutGenerator.generate_form_layout(obj)
                            elif layout_type == 'list':
                                layout_config = LayoutGenerator.generate_list_layout(obj)
                            elif layout_type == 'detail':
                                layout_config = LayoutGenerator.generate_detail_layout(obj)
                            else:
                                layout_config = config_generator(code, search_field_names)

                            if layout_config:
                                PageLayout.objects.update_or_create(
                                    business_object=obj,
                                    layout_code=layout_code,
                                    defaults={
                                        'layout_name': f'{obj.name} [{layout_name_suffix}]',
                                        'layout_type': layout_type,
                                        'layout_config': layout_config,
                                        'is_default': True,
                                        'status': 'published',
                                        'version': '1.0.0',
                                    }
                                )
                                self.stdout.write(f'    {self.style.SUCCESS("CREATED")}: {layout_name_suffix} layout')
                                created_count += 1

                    self.stdout.write('')

                except Exception as e:
                    self.stderr.write(
                        f'  {self.style.ERROR("ERROR")}: {code} - {e}'
                    )
                    error_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Summary:')
        self.stdout.write(f'  Total processed: {len(object_codes)}')
        self.stdout.write(f'  Created/Updated: {created_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write(f'  Errors: {error_count}')
        self.stdout.write('=' * 60)
