from django.db import migrations


def seed_purchase_request_master_detail_protocol(apps, schema_editor):
    BusinessObject = apps.get_model('system', 'BusinessObject')
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    BusinessObject.objects.filter(code='PurchaseRequest').update(
        object_role='root',
        is_top_level_navigable=True,
    )

    BusinessObject.objects.update_or_create(
        code='PurchaseRequestItem',
        defaults={
            'name': '\u91c7\u8d2d\u7533\u8bf7\u660e\u7ec6',
            'name_en': 'Purchase Request Item',
            'is_hardcoded': True,
            'is_menu_hidden': True,
            'django_model_path': 'apps.lifecycle.models.PurchaseRequestItem',
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
        parent_object_code='PurchaseRequest',
        relation_code='purchase_request_items',
        defaults={
            'target_object_code': 'PurchaseRequestItem',
            'relation_name': '\u91c7\u8d2d\u7533\u8bf7\u660e\u7ec6',
            'relation_name_en': 'Purchase Request Items',
            'relation_kind': 'direct_fk',
            'relation_type': 'master_detail',
            'display_mode': 'inline_editable',
            'detail_edit_mode': 'inline_table',
            'display_tier': 'L1',
            'sort_order': 5,
            'target_fk_field': 'purchase_request',
            'is_active': True,
            'cascade_soft_delete': True,
            'detail_toolbar_config': {
                'actions': ['add_row', 'import'],
            },
            'detail_summary_rules': [
                {'field': 'quantity', 'aggregate': 'sum'},
                {'field': 'total_amount', 'aggregate': 'sum'},
            ],
            'detail_validation_rules': [
                {'rule': 'required_item_name'},
            ],
            'extra_config': {
                'relation_name_i18n': {
                    'zh-CN': '\u91c7\u8d2d\u7533\u8bf7\u660e\u7ec6',
                    'en-US': 'Purchase Request Items',
                },
                'relation_translation_key': 'assets.lifecycle.purchaseRequest.form.itemsTitle',
            },
        },
    )


def reverse_purchase_request_master_detail_protocol(apps, schema_editor):
    BusinessObject = apps.get_model('system', 'BusinessObject')
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    ObjectRelationDefinition.objects.filter(
        parent_object_code='PurchaseRequest',
        relation_code='purchase_request_items',
    ).delete()

    BusinessObject.objects.filter(code='PurchaseRequestItem').update(
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
        ('system', '0042_master_detail_object_protocol'),
    ]

    operations = [
        migrations.RunPython(
            seed_purchase_request_master_detail_protocol,
            reverse_purchase_request_master_detail_protocol,
        ),
    ]
