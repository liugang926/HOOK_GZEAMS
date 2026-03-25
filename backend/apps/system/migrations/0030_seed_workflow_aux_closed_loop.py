from django.db import migrations


def _i18n_name(zh_cn: str, en_us: str) -> dict:
    return {
        'zh-CN': zh_cn,
        'en-US': en_us,
        'default': zh_cn,
    }


def seed_workflow_aux_business_objects_and_relations(apps, schema_editor):
    BusinessObject = apps.get_model('system', 'BusinessObject')
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    object_rows = [
        {
            'code': 'WorkflowTemplate',
            'name': '工作流模板',
            'name_en': 'Workflow Template',
            'django_model_path': 'apps.workflows.models.WorkflowTemplate',
        },
        {
            'code': 'WorkflowTask',
            'name': '工作流任务',
            'name_en': 'Workflow Task',
            'django_model_path': 'apps.workflows.models.WorkflowTask',
        },
        {
            'code': 'WorkflowApproval',
            'name': '工作流审批记录',
            'name_en': 'Workflow Approval',
            'django_model_path': 'apps.workflows.models.WorkflowApproval',
        },
        {
            'code': 'WorkflowOperationLog',
            'name': '工作流操作日志',
            'name_en': 'Workflow Operation Log',
            'django_model_path': 'apps.workflows.models.WorkflowOperationLog',
        },
    ]

    for item in object_rows:
        defaults = {
            'name': item['name'],
            'name_en': item['name_en'],
            'is_hardcoded': True,
            'django_model_path': item['django_model_path'],
            'enable_workflow': True,
            'enable_version': True,
            'enable_soft_delete': True,
        }
        BusinessObject.objects.update_or_create(code=item['code'], defaults=defaults)

    rows = [
        # WorkflowDefinition
        {
            'parent_object_code': 'WorkflowDefinition',
            'relation_code': 'source_template_card',
            'target_object_code': 'WorkflowTemplate',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'source_template_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 50,
            'relation_name': '来源模板',
            'relation_name_en': 'Source Template',
        },
        {
            'parent_object_code': 'WorkflowDefinition',
            'relation_code': 'operation_logs',
            'target_object_code': 'WorkflowOperationLog',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'workflow_definition',
            'display_mode': 'inline_readonly',
            'sort_order': 60,
            'relation_name': '操作日志',
            'relation_name_en': 'Operation Logs',
        },

        # WorkflowTemplate
        {
            'parent_object_code': 'WorkflowTemplate',
            'relation_code': 'workflow_definitions',
            'target_object_code': 'WorkflowDefinition',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'source_template',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '流程定义',
            'relation_name_en': 'Workflow Definitions',
        },
        {
            'parent_object_code': 'WorkflowTemplate',
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
            'parent_object_code': 'WorkflowTemplate',
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
            'parent_object_code': 'WorkflowTemplate',
            'relation_code': 'operation_logs',
            'target_object_code': 'WorkflowOperationLog',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'workflow_template',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
            'relation_name': '操作日志',
            'relation_name_en': 'Operation Logs',
        },

        # WorkflowInstance
        {
            'parent_object_code': 'WorkflowInstance',
            'relation_code': 'tasks',
            'target_object_code': 'WorkflowTask',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'instance',
            'display_mode': 'inline_readonly',
            'sort_order': 50,
            'relation_name': '流程任务',
            'relation_name_en': 'Workflow Tasks',
        },
        {
            'parent_object_code': 'WorkflowInstance',
            'relation_code': 'operation_logs',
            'target_object_code': 'WorkflowOperationLog',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'workflow_instance',
            'display_mode': 'inline_readonly',
            'sort_order': 60,
            'relation_name': '操作日志',
            'relation_name_en': 'Operation Logs',
        },

        # WorkflowTask
        {
            'parent_object_code': 'WorkflowTask',
            'relation_code': 'instance_card',
            'target_object_code': 'WorkflowInstance',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'instance_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '流程实例',
            'relation_name_en': 'Workflow Instance',
        },
        {
            'parent_object_code': 'WorkflowTask',
            'relation_code': 'assignee_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'assignee_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '处理人',
            'relation_name_en': 'Assignee',
        },
        {
            'parent_object_code': 'WorkflowTask',
            'relation_code': 'completed_by_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'completed_by_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
            'relation_name': '完成人',
            'relation_name_en': 'Completed By',
        },
        {
            'parent_object_code': 'WorkflowTask',
            'relation_code': 'delegated_to_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'delegated_to_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
            'relation_name': '委派给',
            'relation_name_en': 'Delegated To',
        },
        {
            'parent_object_code': 'WorkflowTask',
            'relation_code': 'delegated_from_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'delegated_from_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 50,
            'relation_name': '委派来源',
            'relation_name_en': 'Delegated From',
        },
        {
            'parent_object_code': 'WorkflowTask',
            'relation_code': 'approvals',
            'target_object_code': 'WorkflowApproval',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'task',
            'display_mode': 'inline_readonly',
            'sort_order': 60,
            'relation_name': '审批记录',
            'relation_name_en': 'Approvals',
        },
        {
            'parent_object_code': 'WorkflowTask',
            'relation_code': 'operation_logs',
            'target_object_code': 'WorkflowOperationLog',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'workflow_task',
            'display_mode': 'inline_readonly',
            'sort_order': 70,
            'relation_name': '操作日志',
            'relation_name_en': 'Operation Logs',
        },

        # WorkflowApproval
        {
            'parent_object_code': 'WorkflowApproval',
            'relation_code': 'task_card',
            'target_object_code': 'WorkflowTask',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'task_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '流程任务',
            'relation_name_en': 'Workflow Task',
        },
        {
            'parent_object_code': 'WorkflowApproval',
            'relation_code': 'approver_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'approver_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '审批人',
            'relation_name_en': 'Approver',
        },
        {
            'parent_object_code': 'WorkflowApproval',
            'relation_code': 'delegated_to_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'delegated_to_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
            'relation_name': '委派给',
            'relation_name_en': 'Delegated To',
        },

        # WorkflowOperationLog
        {
            'parent_object_code': 'WorkflowOperationLog',
            'relation_code': 'actor_user',
            'target_object_code': 'User',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'actor_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '操作人',
            'relation_name_en': 'Actor',
        },
        {
            'parent_object_code': 'WorkflowOperationLog',
            'relation_code': 'workflow_definition_card',
            'target_object_code': 'WorkflowDefinition',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'workflow_definition_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '流程定义',
            'relation_name_en': 'Workflow Definition',
        },
        {
            'parent_object_code': 'WorkflowOperationLog',
            'relation_code': 'workflow_template_card',
            'target_object_code': 'WorkflowTemplate',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'workflow_template_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
            'relation_name': '流程模板',
            'relation_name_en': 'Workflow Template',
        },
        {
            'parent_object_code': 'WorkflowOperationLog',
            'relation_code': 'workflow_instance_card',
            'target_object_code': 'WorkflowInstance',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'workflow_instance_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
            'relation_name': '流程实例',
            'relation_name_en': 'Workflow Instance',
        },
        {
            'parent_object_code': 'WorkflowOperationLog',
            'relation_code': 'workflow_task_card',
            'target_object_code': 'WorkflowTask',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'workflow_task_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 50,
            'relation_name': '流程任务',
            'relation_name_en': 'Workflow Task',
        },

        # Organization reverse relations
        {
            'parent_object_code': 'Organization',
            'relation_code': 'workflow_templates',
            'target_object_code': 'WorkflowTemplate',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 120,
            'relation_name': '流程模板',
            'relation_name_en': 'Workflow Templates',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'workflow_tasks',
            'target_object_code': 'WorkflowTask',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 130,
            'relation_name': '流程任务',
            'relation_name_en': 'Workflow Tasks',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'workflow_approvals',
            'target_object_code': 'WorkflowApproval',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 140,
            'relation_name': '流程审批记录',
            'relation_name_en': 'Workflow Approvals',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'workflow_operation_logs',
            'target_object_code': 'WorkflowOperationLog',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 150,
            'relation_name': '流程操作日志',
            'relation_name_en': 'Workflow Operation Logs',
        },

        # User reverse relations
        {
            'parent_object_code': 'User',
            'relation_code': 'created_workflow_templates',
            'target_object_code': 'WorkflowTemplate',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'created_by',
            'display_mode': 'inline_readonly',
            'sort_order': 90,
            'relation_name': '创建的流程模板',
            'relation_name_en': 'Created Workflow Templates',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'assigned_workflow_tasks',
            'target_object_code': 'WorkflowTask',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'assignee',
            'display_mode': 'inline_readonly',
            'sort_order': 100,
            'relation_name': '分配的流程任务',
            'relation_name_en': 'Assigned Workflow Tasks',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'completed_workflow_tasks',
            'target_object_code': 'WorkflowTask',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'completed_by',
            'display_mode': 'inline_readonly',
            'sort_order': 110,
            'relation_name': '完成的流程任务',
            'relation_name_en': 'Completed Workflow Tasks',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'delegated_to_workflow_tasks',
            'target_object_code': 'WorkflowTask',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'delegated_to',
            'display_mode': 'inline_readonly',
            'sort_order': 120,
            'relation_name': '委派给我的流程任务',
            'relation_name_en': 'Delegated-To Workflow Tasks',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'delegated_from_workflow_tasks',
            'target_object_code': 'WorkflowTask',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'delegated_from',
            'display_mode': 'inline_readonly',
            'sort_order': 130,
            'relation_name': '我发起委派的流程任务',
            'relation_name_en': 'Delegated-From Workflow Tasks',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'workflow_approvals',
            'target_object_code': 'WorkflowApproval',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'approver',
            'display_mode': 'inline_readonly',
            'sort_order': 140,
            'relation_name': '流程审批记录',
            'relation_name_en': 'Workflow Approvals',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'received_workflow_delegation_approvals',
            'target_object_code': 'WorkflowApproval',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'delegated_to',
            'display_mode': 'inline_readonly',
            'sort_order': 150,
            'relation_name': '接收的委派审批记录',
            'relation_name_en': 'Received Delegation Approvals',
        },
        {
            'parent_object_code': 'User',
            'relation_code': 'workflow_operation_logs',
            'target_object_code': 'WorkflowOperationLog',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'actor',
            'display_mode': 'inline_readonly',
            'sort_order': 160,
            'relation_name': '流程操作日志',
            'relation_name_en': 'Workflow Operation Logs',
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
        ('system', '0029_seed_relation_closed_loop_finance_workflow'),
    ]

    operations = [
        migrations.RunPython(seed_workflow_aux_business_objects_and_relations, noop_reverse),
    ]
