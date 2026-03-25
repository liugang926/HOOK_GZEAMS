from django.db import migrations


def _i18n_name(zh_cn: str, en_us: str) -> dict:
    return {
        'zh-CN': zh_cn,
        'en-US': en_us,
        'default': zh_cn,
    }


def _as_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ('true', '1', 'yes', 'y'):
            return True
        if lowered in ('false', '0', 'no', 'n'):
            return False
    return None


def _infer_group(sample: str):
    if any(token in sample for token in ('workflow', 'approval', 'instance', 'task')):
        return 'workflow', '流程协同', 'Workflow', 20, True
    if any(token in sample for token in ('voucher', 'depreciation', 'finance')):
        return 'finance', '财务', 'Finance', 30, False
    if any(token in sample for token in ('inventory', 'snapshot', 'difference')):
        return 'inventory', '盘点库存', 'Inventory', 40, False
    if any(token in sample for token in ('consumable', 'issue', 'purchaseitem', 'purchase')):
        return 'consumables', '耗材', 'Consumables', 50, False
    if any(token in sample for token in ('itasset', 'itsoftware', 'configuration', 'licenseallocation')):
        return 'it_assets', 'IT资产', 'IT Assets', 60, False
    if any(token in sample for token in ('insurance', 'policy', 'claim', 'premium', 'insured')):
        return 'insurance', '保险', 'Insurance', 70, False
    if any(token in sample for token in ('lease', 'leasing', 'rent')):
        return 'leasing', '租赁', 'Leasing', 80, False
    if any(token in sample for token in ('organization', 'department', 'user')):
        return 'organization', '组织与人员', 'Organization', 90, False
    if any(token in sample for token in ('category', 'supplier', 'location')):
        return 'master_data', '主数据', 'Master Data', 100, False
    return 'business', '业务单据', 'Business', 10, True


def seed_relation_group_metadata(apps, schema_editor):
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    rows = ObjectRelationDefinition.objects.filter(is_active=True)
    for row in rows:
        sample = f'{str(row.parent_object_code or "").lower()}:{str(row.relation_code or "").lower()}:{str(row.target_object_code or "").lower()}'
        inferred_key, zh_name, en_name, inferred_order, inferred_expanded = _infer_group(sample)

        next_extra = dict(row.extra_config or {})
        existing_group = next_extra.get('relation_group')
        next_group = dict(existing_group or {}) if isinstance(existing_group, dict) else {}

        key = str(next_group.get('key') or '').strip() or str(next_extra.get('group_key') or '').strip() or inferred_key
        order = _as_int(next_group.get('order'))
        if order is None:
            order = _as_int(next_extra.get('group_order'))
        if order is None:
            order = inferred_order

        expanded = _as_bool(next_group.get('default_expanded'))
        if expanded is None:
            expanded = _as_bool(next_extra.get('default_expanded'))
        if expanded is None:
            expanded = inferred_expanded

        current_name_i18n = next_group.get('name_i18n')
        if isinstance(current_name_i18n, dict):
            merged_name_i18n = dict(_i18n_name(zh_name, en_name))
            merged_name_i18n.update(current_name_i18n)
            name_i18n = merged_name_i18n
        else:
            name_i18n = _i18n_name(zh_name, en_name)

        next_group.update(
            {
                'key': key,
                'order': order,
                'default_expanded': expanded,
                'name_i18n': name_i18n,
            }
        )
        next_extra['relation_group'] = next_group

        # Keep lightweight aliases for older consumers.
        next_extra['group_key'] = key
        next_extra['group_order'] = order
        next_extra['default_expanded'] = expanded

        if next_extra != (row.extra_config or {}):
            row.extra_config = next_extra
            row.save(update_fields=['extra_config', 'updated_at'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('system', '0030_seed_workflow_aux_closed_loop'),
    ]

    operations = [
        migrations.RunPython(seed_relation_group_metadata, noop_reverse),
    ]
