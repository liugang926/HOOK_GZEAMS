import uuid

import django.db.models.deletion
from django.db import migrations, models


def seed_default_relation_definitions(apps, schema_editor):
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    rows = [
        {
            'relation_code': 'maintenance_records',
            'parent_object_code': 'Asset',
            'target_object_code': 'Maintenance',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'asset',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
        },
        {
            'relation_code': 'pickup_orders',
            'parent_object_code': 'Asset',
            'target_object_code': 'AssetPickup',
            'relation_kind': 'through_line_item',
            'through_object_code': 'PickupItem',
            'through_parent_fk_field': 'asset',
            'through_target_fk_field': 'pickup',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
        },
        {
            'relation_code': 'transfer_orders',
            'parent_object_code': 'Asset',
            'target_object_code': 'AssetTransfer',
            'relation_kind': 'through_line_item',
            'through_object_code': 'TransferItem',
            'through_parent_fk_field': 'asset',
            'through_target_fk_field': 'transfer',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
        },
        {
            'relation_code': 'return_orders',
            'parent_object_code': 'Asset',
            'target_object_code': 'AssetReturn',
            'relation_kind': 'through_line_item',
            'through_object_code': 'ReturnItem',
            'through_parent_fk_field': 'asset',
            'through_target_fk_field': 'asset_return',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
        },
        {
            'relation_code': 'loan_orders',
            'parent_object_code': 'Asset',
            'target_object_code': 'AssetLoan',
            'relation_kind': 'through_line_item',
            'through_object_code': 'LoanItem',
            'through_parent_fk_field': 'asset',
            'through_target_fk_field': 'loan',
            'display_mode': 'inline_readonly',
            'sort_order': 50,
        },
        {
            'relation_code': 'disposal_requests',
            'parent_object_code': 'Asset',
            'target_object_code': 'DisposalRequest',
            'relation_kind': 'through_line_item',
            'through_object_code': 'DisposalItem',
            'through_parent_fk_field': 'asset',
            'through_target_fk_field': 'disposal_request',
            'display_mode': 'inline_readonly',
            'sort_order': 60,
        },
        {
            'relation_code': 'it_asset_profile',
            'parent_object_code': 'Asset',
            'target_object_code': 'ITAsset',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'asset',
            'display_mode': 'inline_readonly',
            'sort_order': 70,
        },
        {
            'relation_code': 'asset_card',
            'parent_object_code': 'ITAsset',
            'target_object_code': 'Asset',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'asset_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
        },
        {
            'relation_code': 'maintenance_records',
            'parent_object_code': 'ITAsset',
            'target_object_code': 'ITMaintenanceRecord',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'asset_id',
            'derived_target_key_field': 'asset_id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
        },
        {
            'relation_code': 'configuration_changes',
            'parent_object_code': 'ITAsset',
            'target_object_code': 'ConfigurationChange',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'asset_id',
            'derived_target_key_field': 'asset_id',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
        },
        {
            'relation_code': 'license_allocations',
            'parent_object_code': 'ITAsset',
            'target_object_code': 'ITLicenseAllocation',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'asset_id',
            'derived_target_key_field': 'asset_id',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
        },
    ]

    for item in rows:
        key = {
            'parent_object_code': item['parent_object_code'],
            'relation_code': item['relation_code'],
        }
        defaults = {
            'target_object_code': item['target_object_code'],
            'relation_kind': item['relation_kind'],
            'target_fk_field': item.get('target_fk_field', ''),
            'through_object_code': item.get('through_object_code', ''),
            'through_parent_fk_field': item.get('through_parent_fk_field', ''),
            'through_target_fk_field': item.get('through_target_fk_field', ''),
            'derived_parent_key_field': item.get('derived_parent_key_field', ''),
            'derived_target_key_field': item.get('derived_target_key_field', ''),
            'display_mode': item.get('display_mode', 'inline_readonly'),
            'sort_order': item.get('sort_order', 0),
            'is_active': True,
            'extra_config': {},
        }
        ObjectRelationDefinition.objects.update_or_create(**key, defaults=defaults)


def unseed_default_relation_definitions(apps, schema_editor):
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')
    ObjectRelationDefinition.objects.filter(parent_object_code__in=['Asset', 'ITAsset']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0024_seed_layout_object_i18n_feature_flags'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObjectRelationDefinition',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(db_comment='Soft delete flag, records are filtered out by default', db_index=True, default=False, verbose_name='Is Deleted')),
                ('deleted_at', models.DateTimeField(blank=True, db_comment='Timestamp when record was soft deleted', null=True, verbose_name='Deleted At')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_comment='Timestamp when record was created', verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, db_comment='Timestamp when record was last updated', verbose_name='Updated At')),
                ('custom_fields', models.JSONField(blank=True, db_comment='Dynamic fields for metadata-driven extensions', default=dict, verbose_name='Custom Fields')),
                ('relation_code', models.CharField(db_comment='Stable relation code (unique within parent object)', max_length=80)),
                ('parent_object_code', models.CharField(db_comment='Parent business object code', db_index=True, max_length=50)),
                ('target_object_code', models.CharField(db_comment='Target business object code', db_index=True, max_length=50)),
                ('relation_kind', models.CharField(choices=[('direct_fk', 'Direct FK'), ('through_line_item', 'Through Line Item'), ('derived_query', 'Derived Query')], db_comment='Relation strategy kind', default='direct_fk', max_length=30)),
                ('target_fk_field', models.CharField(blank=True, db_comment='FK field on target model for direct_fk', max_length=100)),
                ('through_object_code', models.CharField(blank=True, db_comment='Intermediate business object code for through relation', max_length=50)),
                ('through_parent_fk_field', models.CharField(blank=True, db_comment='FK field on through model pointing to parent object', max_length=100)),
                ('through_target_fk_field', models.CharField(blank=True, db_comment='FK field on through model pointing to target object', max_length=100)),
                ('derived_parent_key_field', models.CharField(blank=True, db_comment='Field on parent object used as derived query key', max_length=100)),
                ('derived_target_key_field', models.CharField(blank=True, db_comment='Field on target object used as derived query key', max_length=100)),
                ('relation_name', models.CharField(blank=True, db_comment='Display name override', max_length=120)),
                ('relation_name_en', models.CharField(blank=True, db_comment='English display name override', max_length=120)),
                ('display_mode', models.CharField(choices=[('inline_editable', 'Inline Editable'), ('inline_readonly', 'Inline Readonly'), ('tab_readonly', 'Tab Readonly'), ('hidden', 'Hidden')], db_comment='Runtime display mode', default='inline_readonly', max_length=20)),
                ('sort_order', models.IntegerField(db_comment='Display order within parent object', default=0)),
                ('is_active', models.BooleanField(db_comment='Whether relation is active', default=True)),
                ('extra_config', models.JSONField(blank=True, db_comment='Additional relation options', default=dict)),
                ('created_by', models.ForeignKey(blank=True, db_comment='User who created this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_objectrelationdefinition_created', to='accounts.user', verbose_name='Created By')),
                ('updated_by', models.ForeignKey(blank=True, db_comment='User who last updated this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_objectrelationdefinition_updated', to='accounts.user', verbose_name='Updated By')),
                ('deleted_by', models.ForeignKey(blank=True, db_comment='User who soft deleted this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_objectrelationdefinition_deleted', to='accounts.user', verbose_name='Deleted By')),
                ('organization', models.ForeignKey(blank=True, db_comment='Organization for multi-tenant data isolation', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='system_objectrelationdefinition_set', to='organizations.organization', verbose_name='Organization')),
            ],
            options={
                'verbose_name': 'Object Relation Definition',
                'verbose_name_plural': 'Object Relation Definitions',
                'db_table': 'object_relation_definitions',
                'unique_together': {('parent_object_code', 'relation_code')},
            },
        ),
        migrations.AddIndex(
            model_name='objectrelationdefinition',
            index=models.Index(fields=['parent_object_code', 'sort_order'], name='object_rela_parent__7fcf47_idx'),
        ),
        migrations.AddIndex(
            model_name='objectrelationdefinition',
            index=models.Index(fields=['parent_object_code', 'is_active'], name='object_rela_parent__772d85_idx'),
        ),
        migrations.AddIndex(
            model_name='objectrelationdefinition',
            index=models.Index(fields=['target_object_code'], name='object_rela_target__b817f2_idx'),
        ),
        migrations.AddIndex(
            model_name='objectrelationdefinition',
            index=models.Index(fields=['relation_kind'], name='object_rela_relatio_be9e0a_idx'),
        ),
        migrations.AddIndex(
            model_name='objectrelationdefinition',
            index=models.Index(fields=['-created_at'], name='object_rela_created_11b960_idx'),
        ),
        migrations.AddIndex(
            model_name='objectrelationdefinition',
            index=models.Index(fields=['is_deleted'], name='object_rela_is_dele_4e121e_idx'),
        ),
        migrations.RunPython(seed_default_relation_definitions, unseed_default_relation_definitions),
    ]
