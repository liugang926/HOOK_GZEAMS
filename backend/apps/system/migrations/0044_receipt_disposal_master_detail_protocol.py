from django.db import migrations


def seed_receipt_disposal_master_detail_protocol(apps, schema_editor):
    BusinessObject = apps.get_model('system', 'BusinessObject')
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    BusinessObject.objects.filter(code__in=['AssetReceipt', 'DisposalRequest']).update(
        object_role='root',
        is_top_level_navigable=True,
    )

    BusinessObject.objects.update_or_create(
        code='AssetReceiptItem',
        defaults={
            'name': '\u8d44\u4ea7\u5165\u5e93\u660e\u7ec6',
            'name_en': 'Asset Receipt Item',
            'is_hardcoded': True,
            'is_menu_hidden': True,
            'django_model_path': 'apps.lifecycle.models.AssetReceiptItem',
            'menu_category': 'lifecycle',
            'object_role': 'detail',
            'is_top_level_navigable': False,
            'allow_standalone_query': True,
            'allow_standalone_route': False,
            'inherit_permissions': True,
            'inherit_workflow': True,
            'inherit_status': True,
            'inherit_lifecycle': True,
        },
    )
    BusinessObject.objects.update_or_create(
        code='DisposalItem',
        defaults={
            'name': '\u62a5\u5e9f\u660e\u7ec6',
            'name_en': 'Disposal Item',
            'is_hardcoded': True,
            'is_menu_hidden': True,
            'django_model_path': 'apps.lifecycle.models.DisposalItem',
            'menu_category': 'lifecycle',
            'object_role': 'detail',
            'is_top_level_navigable': False,
            'allow_standalone_query': True,
            'allow_standalone_route': False,
            'inherit_permissions': True,
            'inherit_workflow': True,
            'inherit_status': True,
            'inherit_lifecycle': True,
        },
    )

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='AssetReceipt',
        relation_code='receipt_items',
        defaults={
            'target_object_code': 'AssetReceiptItem',
            'relation_name': '\u5165\u5e93\u660e\u7ec6',
            'relation_name_en': 'Receipt Items',
            'relation_kind': 'direct_fk',
            'relation_type': 'master_detail',
            'display_mode': 'inline_editable',
            'detail_edit_mode': 'inline_table',
            'display_tier': 'L1',
            'sort_order': 5,
            'target_fk_field': 'asset_receipt',
            'is_active': True,
            'cascade_soft_delete': True,
            'detail_toolbar_config': {
                'actions': ['add_row'],
            },
            'detail_summary_rules': [
                {'field': 'received_quantity', 'aggregate': 'sum'},
                {'field': 'total_amount', 'aggregate': 'sum'},
            ],
            'detail_validation_rules': [
                {'rule': 'required_item_name'},
            ],
            'extra_config': {
                'relation_name_i18n': {
                    'zh-CN': '\u5165\u5e93\u660e\u7ec6',
                    'en-US': 'Receipt Items',
                },
                'relation_translation_key': 'assets.lifecycle.assetReceipt.form.itemsTitle',
            },
        },
    )

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='DisposalRequest',
        relation_code='disposal_items',
        defaults={
            'target_object_code': 'DisposalItem',
            'relation_name': '\u62a5\u5e9f\u660e\u7ec6',
            'relation_name_en': 'Disposal Items',
            'relation_kind': 'direct_fk',
            'relation_type': 'master_detail',
            'display_mode': 'inline_editable',
            'detail_edit_mode': 'inline_table',
            'display_tier': 'L1',
            'sort_order': 5,
            'target_fk_field': 'disposal_request',
            'is_active': True,
            'cascade_soft_delete': True,
            'detail_toolbar_config': {
                'actions': ['add_row'],
            },
            'detail_summary_rules': [
                {'field': 'net_value', 'aggregate': 'sum'},
                {'field': 'actual_residual_value', 'aggregate': 'sum'},
            ],
            'detail_validation_rules': [
                {'rule': 'required_asset'},
            ],
            'extra_config': {
                'relation_name_i18n': {
                    'zh-CN': '\u62a5\u5e9f\u660e\u7ec6',
                    'en-US': 'Disposal Items',
                },
                'relation_translation_key': 'assets.lifecycle.disposalRequest.form.itemsTitle',
            },
        },
    )


def reverse_receipt_disposal_master_detail_protocol(apps, schema_editor):
    BusinessObject = apps.get_model('system', 'BusinessObject')
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    ObjectRelationDefinition.objects.filter(
        parent_object_code='AssetReceipt',
        relation_code='receipt_items',
    ).delete()
    ObjectRelationDefinition.objects.filter(
        parent_object_code='DisposalRequest',
        relation_code='disposal_items',
    ).delete()

    BusinessObject.objects.filter(code__in=['AssetReceiptItem', 'DisposalItem']).update(
        object_role='root',
        is_top_level_navigable=True,
        allow_standalone_query=True,
        allow_standalone_route=True,
        inherit_permissions=False,
        inherit_workflow=False,
        inherit_status=False,
        inherit_lifecycle=False,
        is_menu_hidden=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0043_purchase_request_master_detail_protocol'),
    ]

    operations = [
        migrations.RunPython(
            seed_receipt_disposal_master_detail_protocol,
            reverse_receipt_disposal_master_detail_protocol,
        ),
    ]
