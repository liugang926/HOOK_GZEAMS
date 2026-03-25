from django.db import migrations, models


LINE_ITEM_OBJECT_CODES = ['PickupItem', 'TransferItem', 'ReturnItem', 'LoanItem']
LINE_ITEM_RELATION_CODES = ['pickup_items', 'transfer_items', 'return_items', 'loan_items']


def seed_master_detail_protocol(apps, schema_editor):
    BusinessObject = apps.get_model('system', 'BusinessObject')
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    BusinessObject.objects.filter(code__in=LINE_ITEM_OBJECT_CODES).update(
        object_role='detail',
        is_menu_hidden=True,
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_workflow=True,
        inherit_status=True,
        inherit_lifecycle=True,
    )

    ObjectRelationDefinition.objects.filter(
        relation_code__in=LINE_ITEM_RELATION_CODES,
    ).update(
        relation_type='master_detail',
        detail_edit_mode='inline_table',
        cascade_soft_delete=True,
    )


def reverse_master_detail_protocol(apps, schema_editor):
    BusinessObject = apps.get_model('system', 'BusinessObject')
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    BusinessObject.objects.filter(code__in=LINE_ITEM_OBJECT_CODES).update(
        object_role='root',
        is_top_level_navigable=True,
        allow_standalone_query=True,
        allow_standalone_route=True,
        inherit_permissions=False,
        inherit_workflow=False,
        inherit_status=False,
        inherit_lifecycle=False,
    )

    ObjectRelationDefinition.objects.filter(
        relation_code__in=LINE_ITEM_RELATION_CODES,
    ).update(
        relation_type='lookup',
        detail_edit_mode='readonly_table',
        cascade_soft_delete=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0041_fix_line_item_object_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessobject',
            name='allow_standalone_query',
            field=models.BooleanField(
                db_comment='Whether this object supports standalone read/query experiences',
                default=True,
            ),
        ),
        migrations.AddField(
            model_name='businessobject',
            name='allow_standalone_route',
            field=models.BooleanField(
                db_comment='Whether this object supports standalone runtime routing',
                default=True,
            ),
        ),
        migrations.AddField(
            model_name='businessobject',
            name='inherit_lifecycle',
            field=models.BooleanField(
                db_comment='Whether this object inherits lifecycle constraints from a parent aggregate',
                default=False,
            ),
        ),
        migrations.AddField(
            model_name='businessobject',
            name='inherit_permissions',
            field=models.BooleanField(
                db_comment='Whether this object inherits permission checks from a parent aggregate',
                default=False,
            ),
        ),
        migrations.AddField(
            model_name='businessobject',
            name='inherit_status',
            field=models.BooleanField(
                db_comment='Whether this object inherits status context from a parent aggregate',
                default=False,
            ),
        ),
        migrations.AddField(
            model_name='businessobject',
            name='inherit_workflow',
            field=models.BooleanField(
                db_comment='Whether this object inherits workflow behavior from a parent aggregate',
                default=False,
            ),
        ),
        migrations.AddField(
            model_name='businessobject',
            name='is_top_level_navigable',
            field=models.BooleanField(
                db_comment='Whether this object can appear as a top-level navigable entry',
                default=True,
            ),
        ),
        migrations.AddField(
            model_name='businessobject',
            name='object_role',
            field=models.CharField(
                choices=[('root', 'Root'), ('detail', 'Detail'), ('reference', 'Reference'), ('log', 'Log')],
                db_comment='Business object role (root/detail/reference/log)',
                default='root',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='objectrelationdefinition',
            name='cascade_soft_delete',
            field=models.BooleanField(
                db_comment='Whether soft delete should cascade from parent to child',
                default=False,
            ),
        ),
        migrations.AddField(
            model_name='objectrelationdefinition',
            name='detail_edit_mode',
            field=models.CharField(
                choices=[('inline_table', 'Inline Table'), ('nested_form', 'Nested Form'), ('readonly_table', 'Readonly Table')],
                db_comment='Detail region renderer for master-detail relations',
                default='readonly_table',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='objectrelationdefinition',
            name='detail_summary_rules',
            field=models.JSONField(
                blank=True,
                db_comment='Summary/aggregate rules for detail regions',
                default=list,
            ),
        ),
        migrations.AddField(
            model_name='objectrelationdefinition',
            name='detail_toolbar_config',
            field=models.JSONField(
                blank=True,
                db_comment='Toolbar configuration for detail regions',
                default=dict,
            ),
        ),
        migrations.AddField(
            model_name='objectrelationdefinition',
            name='detail_validation_rules',
            field=models.JSONField(
                blank=True,
                db_comment='Validation rules for detail regions',
                default=list,
            ),
        ),
        migrations.AddField(
            model_name='objectrelationdefinition',
            name='relation_type',
            field=models.CharField(
                choices=[('lookup', 'Lookup'), ('master_detail', 'Master Detail'), ('derived', 'Derived')],
                db_comment='Business relation type (lookup/master_detail/derived)',
                default='lookup',
                max_length=20,
            ),
        ),
        migrations.RunPython(seed_master_detail_protocol, reverse_master_detail_protocol),
    ]
