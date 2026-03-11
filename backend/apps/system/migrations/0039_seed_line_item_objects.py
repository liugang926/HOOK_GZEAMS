"""
Seed migration: register 4 LineItem BusinessObjects and configure
L1 direct_fk relations from parent documents to their items.

This enables the frontend to:
1. Know that PickupItem/TransferItem/ReturnItem/LoanItem are first-class objects
2. Render them inline in the Details tab (display_tier=L1) instead of Related tab
"""
from django.db import migrations


def seed_line_item_objects(apps, schema_editor):
    BusinessObject = apps.get_model('system', 'BusinessObject')
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    # ── Register *Item BusinessObjects ──────────────────────────
    item_objects = [
        {
            'code': 'PickupItem',
            'name': '领用明细',
            'name_en': 'Pickup Item',
            'description': 'Asset Pickup Order Line Item',
            'is_hardcoded': True,
            'django_model_path': 'apps.assets.models.PickupItem',
            'is_menu_hidden': True,
            'menu_category': 'assets',
        },
        {
            'code': 'TransferItem',
            'name': '调拨明细',
            'name_en': 'Transfer Item',
            'description': 'Asset Transfer Order Line Item',
            'is_hardcoded': True,
            'django_model_path': 'apps.assets.models.TransferItem',
            'is_menu_hidden': True,
            'menu_category': 'assets',
        },
        {
            'code': 'ReturnItem',
            'name': '归还明细',
            'name_en': 'Return Item',
            'description': 'Asset Return Order Line Item',
            'is_hardcoded': True,
            'django_model_path': 'apps.assets.models.ReturnItem',
            'is_menu_hidden': True,
            'menu_category': 'assets',
        },
        {
            'code': 'LoanItem',
            'name': '借用明细',
            'name_en': 'Loan Item',
            'description': 'Asset Loan Order Line Item',
            'is_hardcoded': True,
            'django_model_path': 'apps.assets.models.LoanItem',
            'is_menu_hidden': True,
            'menu_category': 'assets',
        },
    ]

    for obj_data in item_objects:
        code = obj_data.pop('code')
        BusinessObject.objects.update_or_create(
            code=code,
            defaults=obj_data,
        )

    # ── Register L1 direct_fk relations: Document → *Item ──────
    l1_relations = [
        {
            'parent_object_code': 'AssetPickup',
            'relation_code': 'pickup_items',
            'target_object_code': 'PickupItem',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'pickup',
            'display_mode': 'inline_editable',
            'display_tier': 'L1',
            'sort_order': 1,
            'relation_name': '领用明细',
            'relation_name_en': 'Pickup Items',
        },
        {
            'parent_object_code': 'AssetTransfer',
            'relation_code': 'transfer_items',
            'target_object_code': 'TransferItem',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'transfer',
            'display_mode': 'inline_editable',
            'display_tier': 'L1',
            'sort_order': 1,
            'relation_name': '调拨明细',
            'relation_name_en': 'Transfer Items',
        },
        {
            'parent_object_code': 'AssetReturn',
            'relation_code': 'return_items',
            'target_object_code': 'ReturnItem',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'asset_return',
            'display_mode': 'inline_editable',
            'display_tier': 'L1',
            'sort_order': 1,
            'relation_name': '归还明细',
            'relation_name_en': 'Return Items',
        },
        {
            'parent_object_code': 'AssetLoan',
            'relation_code': 'loan_items',
            'target_object_code': 'LoanItem',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'loan',
            'display_mode': 'inline_editable',
            'display_tier': 'L1',
            'sort_order': 1,
            'relation_name': '借用明细',
            'relation_name_en': 'Loan Items',
        },
    ]

    for rel_data in l1_relations:
        key = {
            'parent_object_code': rel_data['parent_object_code'],
            'relation_code': rel_data['relation_code'],
        }
        defaults = {
            'target_object_code': rel_data['target_object_code'],
            'relation_kind': rel_data['relation_kind'],
            'target_fk_field': rel_data.get('target_fk_field', ''),
            'display_mode': rel_data.get('display_mode', 'inline_editable'),
            'display_tier': rel_data.get('display_tier', 'L1'),
            'sort_order': rel_data.get('sort_order', 0),
            'relation_name': rel_data.get('relation_name', ''),
            'relation_name_en': rel_data.get('relation_name_en', ''),
            'is_active': True,
        }
        ObjectRelationDefinition.objects.update_or_create(**key, defaults=defaults)


def reverse_seed(apps, schema_editor):
    BusinessObject = apps.get_model('system', 'BusinessObject')
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    # Remove the L1 relations
    ObjectRelationDefinition.objects.filter(
        relation_code__in=['pickup_items', 'transfer_items', 'return_items', 'loan_items'],
        display_tier='L1',
    ).delete()

    # Remove the BusinessObject registrations
    BusinessObject.objects.filter(
        code__in=['PickupItem', 'TransferItem', 'ReturnItem', 'LoanItem'],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0038_deprecate_field_definition_reverse_relation'),
    ]

    operations = [
        migrations.RunPython(seed_line_item_objects, reverse_seed),
    ]
