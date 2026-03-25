from django.db import migrations


def _i18n_name(zh_cn: str, en_us: str) -> dict:
    return {
        'zh-CN': zh_cn,
        'en-US': en_us,
        'default': zh_cn,
    }


def seed_relation_closed_loop_finance_workflow(apps, schema_editor):
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    rows = [
        # Finance voucher
        {
            'parent_object_code': 'FinanceVoucher',
            'relation_code': 'organization_card',
            'target_object_code': 'Organization',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'organization_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '所属组织',
            'relation_name_en': 'Organization',
        },
        {
            'parent_object_code': 'FinanceVoucher',
            'relation_code': 'posted_by_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'posted_by_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '过账人',
            'relation_name_en': 'Posted By',
        },
        {
            'parent_object_code': 'FinanceVoucher',
            'relation_code': 'creator_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'created_by_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
            'relation_name': '创建人',
            'relation_name_en': 'Created By',
        },
        {
            'parent_object_code': 'FinanceVoucher',
            'relation_code': 'workflow_instances',
            'target_object_code': 'WorkflowInstance',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'id',
            'derived_target_key_field': 'business_id',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
            'relation_name': '流程实例',
            'relation_name_en': 'Workflow Instances',
        },

        # Voucher template
        {
            'parent_object_code': 'VoucherTemplate',
            'relation_code': 'organization_card',
            'target_object_code': 'Organization',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'organization_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '所属组织',
            'relation_name_en': 'Organization',
        },
        {
            'parent_object_code': 'VoucherTemplate',
            'relation_code': 'creator_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'created_by_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '创建人',
            'relation_name_en': 'Created By',
        },

        # Workflow definition
        {
            'parent_object_code': 'WorkflowDefinition',
            'relation_code': 'instances',
            'target_object_code': 'WorkflowInstance',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'definition',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '流程实例',
            'relation_name_en': 'Workflow Instances',
        },
        {
            'parent_object_code': 'WorkflowDefinition',
            'relation_code': 'organization_card',
            'target_object_code': 'Organization',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'organization_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '所属组织',
            'relation_name_en': 'Organization',
        },
        {
            'parent_object_code': 'WorkflowDefinition',
            'relation_code': 'published_by_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'published_by_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
            'relation_name': '发布人',
            'relation_name_en': 'Published By',
        },
        {
            'parent_object_code': 'WorkflowDefinition',
            'relation_code': 'creator_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'created_by_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
            'relation_name': '创建人',
            'relation_name_en': 'Created By',
        },

        # Workflow instance
        {
            'parent_object_code': 'WorkflowInstance',
            'relation_code': 'definition_card',
            'target_object_code': 'WorkflowDefinition',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'definition_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '流程定义',
            'relation_name_en': 'Workflow Definition',
        },
        {
            'parent_object_code': 'WorkflowInstance',
            'relation_code': 'organization_card',
            'target_object_code': 'Organization',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'organization_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '所属组织',
            'relation_name_en': 'Organization',
        },
        {
            'parent_object_code': 'WorkflowInstance',
            'relation_code': 'initiator_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'initiator_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
            'relation_name': '发起人',
            'relation_name_en': 'Initiator',
        },
        {
            'parent_object_code': 'WorkflowInstance',
            'relation_code': 'terminated_by_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'terminated_by_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
            'relation_name': '终止人',
            'relation_name_en': 'Terminated By',
        },

        # Organization
        {
            'parent_object_code': 'Organization',
            'relation_code': 'finance_vouchers',
            'target_object_code': 'FinanceVoucher',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 80,
            'relation_name': '财务凭证',
            'relation_name_en': 'Finance Vouchers',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'voucher_templates',
            'target_object_code': 'VoucherTemplate',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 90,
            'relation_name': '凭证模板',
            'relation_name_en': 'Voucher Templates',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'workflow_definitions',
            'target_object_code': 'WorkflowDefinition',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 100,
            'relation_name': '流程定义',
            'relation_name_en': 'Workflow Definitions',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'workflow_instances',
            'target_object_code': 'WorkflowInstance',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 110,
            'relation_name': '流程实例',
            'relation_name_en': 'Workflow Instances',
        },

        # User
        {
            'parent_object_code': 'User',
            'relation_code': 'posted_finance_vouchers',
            'target_object_code': 'FinanceVoucher',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'posted_by',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '过账凭证',
            'relation_name_en': 'Posted Vouchers',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'created_finance_vouchers',
            'target_object_code': 'FinanceVoucher',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'created_by',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '创建的财务凭证',
            'relation_name_en': 'Created Finance Vouchers',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'created_voucher_templates',
            'target_object_code': 'VoucherTemplate',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'created_by',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
            'relation_name': '创建的凭证模板',
            'relation_name_en': 'Created Voucher Templates',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'published_workflow_definitions',
            'target_object_code': 'WorkflowDefinition',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'published_by',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
            'relation_name': '发布的流程定义',
            'relation_name_en': 'Published Workflow Definitions',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'created_workflow_definitions',
            'target_object_code': 'WorkflowDefinition',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'created_by',
            'display_mode': 'inline_readonly',
            'sort_order': 50,
            'relation_name': '创建的流程定义',
            'relation_name_en': 'Created Workflow Definitions',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'initiated_workflow_instances',
            'target_object_code': 'WorkflowInstance',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'initiator',
            'display_mode': 'inline_readonly',
            'sort_order': 60,
            'relation_name': '发起的流程实例',
            'relation_name_en': 'Initiated Workflow Instances',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'terminated_workflow_instances',
            'target_object_code': 'WorkflowInstance',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'terminated_by',
            'display_mode': 'inline_readonly',
            'sort_order': 70,
            'relation_name': '终止的流程实例',
            'relation_name_en': 'Terminated Workflow Instances',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'created_workflow_instances',
            'target_object_code': 'WorkflowInstance',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'created_by',
            'display_mode': 'inline_readonly',
            'sort_order': 80,
            'relation_name': '创建的流程实例',
            'relation_name_en': 'Created Workflow Instances',
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
            'relation_name': item.get('relation_name', ''),
            'relation_name_en': item.get('relation_name_en', ''),
        }
        relation, _ = ObjectRelationDefinition.objects.update_or_create(**key, defaults=defaults)

        next_extra = dict(relation.extra_config or {})
        next_extra['relation_name_i18n'] = _i18n_name(
            item.get('relation_name', '') or '',
            item.get('relation_name_en', '') or '',
        )
        if relation.extra_config != next_extra:
            relation.extra_config = next_extra
            relation.save(update_fields=['extra_config', 'updated_at'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0028_seed_relation_closed_loop_domain_stable'),
    ]

    operations = [
        migrations.RunPython(seed_relation_closed_loop_finance_workflow, noop_reverse),
    ]
