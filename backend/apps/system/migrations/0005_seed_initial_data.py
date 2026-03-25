"""
Data migration to seed initial dictionary data.

This migration creates the foundational dictionary types and items
that are used across the system:
- ASSET_STATUS: Asset status options
- UNIT: Measurement units
- ASSET_BRAND: Common asset brands
- INVENTORY_DISCREPANCY_TYPE: Inventory discrepancy types
"""
from django.db import migrations


def seed_dictionaries(apps, schema_editor):
    """Seed initial dictionary data."""
    DictionaryType = apps.get_model('system', 'DictionaryType')
    DictionaryItem = apps.get_model('system', 'DictionaryItem')

    # =========================================================================
    # ASSET_STATUS - Asset Status
    # =========================================================================
    asset_status_type, _ = DictionaryType.objects.get_or_create(
        code='ASSET_STATUS',
        organization_id=None,  # Global dictionary
        defaults={
            'name': 'Asset Status',
            'name_en': 'Asset Status',
            'description': 'Current status of the asset',
            'is_system': True,
            'is_active': True,
            'sort_order': 1,
        }
    )
    # Ensure name is English
    if asset_status_type.name != 'Asset Status':
         asset_status_type.name = 'Asset Status'
         asset_status_type.save()

    asset_status_items = [
        {'code': 'pending', 'name': 'Pending Entry', 'name_en': 'Pending Entry', 'color': '#909399', 'sort_order': 1},
        {'code': 'in_use', 'name': 'In Use', 'name_en': 'In Use', 'color': '#67C23A', 'is_default': True, 'sort_order': 2},
        {'code': 'idle', 'name': 'Idle', 'name_en': 'Idle', 'color': '#E6A23C', 'sort_order': 3},
        {'code': 'maintenance', 'name': 'Under Maintenance', 'name_en': 'Under Maintenance', 'color': '#F56C6C', 'sort_order': 4},
        {'code': 'lent', 'name': 'Lent Out', 'name_en': 'Lent Out', 'color': '#409EFF', 'sort_order': 5},
        {'code': 'lost', 'name': 'Lost', 'name_en': 'Lost', 'color': '#F56C6C', 'sort_order': 6},
        {'code': 'scrapped', 'name': 'Scrapped', 'name_en': 'Scrapped', 'color': '#909399', 'sort_order': 7},
    ]

    for item_data in asset_status_items:
        obj, created = DictionaryItem.objects.get_or_create(
            dictionary_type=asset_status_type,
            code=item_data['code'],
            organization_id=None,
            defaults={
                'name': item_data['name'],
                'name_en': item_data['name_en'],
                'color': item_data.get('color', ''),
                'is_default': item_data.get('is_default', False),
                'is_active': True,
                'sort_order': item_data['sort_order'],
            }
        )
        # Update name if it matches old Chinese or just enforce English
        if not created and obj.name != item_data['name']:
            obj.name = item_data['name']
            obj.name_en = item_data['name_en']
            obj.save()

    # =========================================================================
    # UNIT - Unit of Measurement
    # =========================================================================
    unit_type, _ = DictionaryType.objects.get_or_create(
        code='UNIT',
        organization_id=None,
        defaults={
            'name': 'Unit of Measurement',
            'name_en': 'Unit of Measurement',
            'description': 'Units for assets and items',
            'is_system': True,
            'is_active': True,
            'sort_order': 2,
        }
    )
    if unit_type.name != 'Unit of Measurement':
         unit_type.name = 'Unit of Measurement'
         unit_type.save()

    unit_items = [
        {'code': 'piece', 'name': 'Piece', 'name_en': 'Piece', 'sort_order': 1},
        {'code': 'unit', 'name': 'Unit', 'name_en': 'Unit', 'is_default': True, 'sort_order': 2},
        {'code': 'set', 'name': 'Set', 'name_en': 'Set', 'sort_order': 3},
        {'code': 'batch', 'name': 'Batch', 'name_en': 'Batch', 'sort_order': 4},
        {'code': 'box', 'name': 'Box', 'name_en': 'Box', 'sort_order': 5},
        {'code': 'bottle', 'name': 'Bottle', 'name_en': 'Bottle', 'sort_order': 6},
        {'code': 'pack', 'name': 'Pack', 'name_en': 'Pack', 'sort_order': 7},
        {'code': 'meter', 'name': 'Meter', 'name_en': 'Meter', 'sort_order': 8},
        {'code': 'kg', 'name': 'Kilogram', 'name_en': 'Kilogram', 'sort_order': 9},
    ]

    for item_data in unit_items:
        obj, created = DictionaryItem.objects.get_or_create(
            dictionary_type=unit_type,
            code=item_data['code'],
            organization_id=None,
            defaults={
                'name': item_data['name'],
                'name_en': item_data['name_en'],
                'color': item_data.get('color', ''),
                'is_default': item_data.get('is_default', False),
                'is_active': True,
                'sort_order': item_data['sort_order'],
            }
        )
        if not created and obj.name != item_data['name']:
            obj.name = item_data['name']
            obj.name_en = item_data['name_en']
            obj.save()

    # =========================================================================
    # INVENTORY_DISCREPANCY_TYPE - Inventory Discrepancy Type
    # =========================================================================
    discrepancy_type, _ = DictionaryType.objects.get_or_create(
        code='INVENTORY_DISCREPANCY_TYPE',
        organization_id=None,
        defaults={
            'name': 'Inventory Discrepancy Type',
            'name_en': 'Inventory Discrepancy Type',
            'description': 'Types of inventory discrepancies',
            'is_system': True,
            'is_active': True,
            'sort_order': 3,
        }
    )
    if discrepancy_type.name != 'Inventory Discrepancy Type':
         discrepancy_type.name = 'Inventory Discrepancy Type'
         discrepancy_type.save()

    discrepancy_items = [
        {'code': 'shortage', 'name': 'Shortage', 'name_en': 'Shortage', 'color': '#F56C6C', 'sort_order': 1},
        {'code': 'surplus', 'name': 'Surplus', 'name_en': 'Surplus', 'color': '#67C23A', 'sort_order': 2},
        {'code': 'damage', 'name': 'Damaged', 'name_en': 'Damaged', 'color': '#E6A23C', 'sort_order': 3},
        {'code': 'location_mismatch', 'name': 'Location Mismatch', 'name_en': 'Location Mismatch', 'color': '#409EFF', 'sort_order': 4},
    ]

    for item_data in discrepancy_items:
        obj, created = DictionaryItem.objects.get_or_create(
            dictionary_type=discrepancy_type,
            code=item_data['code'],
            organization_id=None,
            defaults={
                'name': item_data['name'],
                'name_en': item_data['name_en'],
                'color': item_data.get('color', ''),
                'is_default': item_data.get('is_default', False),
                'is_active': True,
                'sort_order': item_data['sort_order'],
            }
        )
        if not created and obj.name != item_data['name']:
            obj.name = item_data['name']
            obj.save()


def seed_sequence_rules(apps, schema_editor):
    """Seed initial sequence rules."""
    SequenceRule = apps.get_model('system', 'SequenceRule')

    sequence_rules = [
        {
            'code': 'ASSET_CODE',
            'name': '资产编码',
            'prefix': 'ZC',
            'pattern': '{PREFIX}{YYYY}{MM}{SEQ}',
            'seq_length': 4,
            'reset_period': 'monthly',
            'description': '资产卡片编码规则，格式：ZC+年月+4位序号',
        },
        {
            'code': 'PICKUP_NO',
            'name': '领用单号',
            'prefix': 'LY',
            'pattern': '{PREFIX}{YYYY}{MM}{SEQ}',
            'seq_length': 4,
            'reset_period': 'monthly',
            'description': '资产领用单编号规则',
        },
        {
            'code': 'TRANSFER_NO',
            'name': '调拨单号',
            'prefix': 'DB',
            'pattern': '{PREFIX}{YYYY}{MM}{SEQ}',
            'seq_length': 4,
            'reset_period': 'monthly',
            'description': '资产调拨单编号规则',
        },
        {
            'code': 'INVENTORY_NO',
            'name': '盘点单号',
            'prefix': 'PD',
            'pattern': '{PREFIX}{YYYY}{MM}{DD}{SEQ}',
            'seq_length': 3,
            'reset_period': 'daily',
            'description': '盘点任务单编号规则',
        },
        {
            'code': 'SCRAP_NO',
            'name': '报废单号',
            'prefix': 'BF',
            'pattern': '{PREFIX}{YYYY}{MM}{SEQ}',
            'seq_length': 4,
            'reset_period': 'monthly',
            'description': '资产报废单编号规则',
        },
    ]

    for rule_data in sequence_rules:
        SequenceRule.objects.get_or_create(
            code=rule_data['code'],
            organization_id=None,  # Global rule
            defaults={
                'name': rule_data['name'],
                'prefix': rule_data['prefix'],
                'pattern': rule_data['pattern'],
                'seq_length': rule_data['seq_length'],
                'reset_period': rule_data['reset_period'],
                'description': rule_data['description'],
                'current_value': 0,
                'is_active': True,
            }
        )


def seed_system_configs(apps, schema_editor):
    """Seed initial system configurations."""
    SystemConfig = apps.get_model('system', 'SystemConfig')

    configs = [
        {
            'config_key': 'QR_CODE_TEMPLATE',
            'config_value': 'QR-{asset_code}-{org_code}',
            'value_type': 'string',
            'name': '二维码内容模板',
            'category': 'asset',
            'description': '资产二维码的内容格式模板',
        },
        {
            'config_key': 'DEFAULT_DEPRECIATION_METHOD',
            'config_value': 'straight_line',
            'value_type': 'string',
            'name': '默认折旧方法',
            'category': 'asset',
            'description': '新建资产分类时的默认折旧方法',
        },
        {
            'config_key': 'ENABLE_ASSET_APPROVAL',
            'config_value': 'true',
            'value_type': 'boolean',
            'name': '启用资产审批',
            'category': 'workflow',
            'description': '是否启用资产变更审批流程',
        },
        {
            'config_key': 'MAX_ATTACHMENT_SIZE_MB',
            'config_value': '10',
            'value_type': 'integer',
            'name': '最大附件大小(MB)',
            'category': 'upload',
            'description': '单个附件的最大上传大小',
        },
    ]

    for config_data in configs:
        SystemConfig.objects.get_or_create(
            config_key=config_data['config_key'],
            organization_id=None,
            defaults={
                'config_value': config_data['config_value'],
                'value_type': config_data['value_type'],
                'name': config_data['name'],
                'category': config_data['category'],
                'description': config_data['description'],
                'is_system': True,
            }
        )


def reverse_seed(apps, schema_editor):
    """Reverse the seeding (optional, for rollback)."""
    # We don't delete system data on rollback to prevent data loss
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0004_public_models'),
    ]

    operations = [
        migrations.RunPython(seed_dictionaries, reverse_seed),
        migrations.RunPython(seed_sequence_rules, reverse_seed),
        migrations.RunPython(seed_system_configs, reverse_seed),
    ]
