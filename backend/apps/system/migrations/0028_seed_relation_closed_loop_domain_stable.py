from django.db import migrations


def _i18n_name(zh_cn: str, en_us: str) -> dict:
    return {
        'zh-CN': zh_cn,
        'en-US': en_us,
        'default': zh_cn,
    }


def seed_relation_closed_loop_domain_stable(apps, schema_editor):
    ObjectRelationDefinition = apps.get_model('system', 'ObjectRelationDefinition')

    rows = [
        # Asset category
        {
            'parent_object_code': 'AssetCategory',
            'relation_code': 'assets',
            'target_object_code': 'Asset',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'asset_category',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '分类资产',
            'relation_name_en': 'Category Assets',
        },
        {
            'parent_object_code': 'AssetCategory',
            'relation_code': 'receipt_documents',
            'target_object_code': 'AssetReceipt',
            'relation_kind': 'through_line_item',
            'through_object_code': 'AssetReceiptItem',
            'through_parent_fk_field': 'asset_category',
            'through_target_fk_field': 'asset_receipt',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '入库单据',
            'relation_name_en': 'Receipt Documents',
        },
        {
            'parent_object_code': 'AssetCategory',
            'relation_code': 'software_catalog',
            'target_object_code': 'Software',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'category',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
            'relation_name': '软件目录',
            'relation_name_en': 'Software Catalog',
        },
        {
            'parent_object_code': 'AssetCategory',
            'relation_code': 'consumables',
            'target_object_code': 'Consumable',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'category',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
            'relation_name': '耗材',
            'relation_name_en': 'Consumables',
        },

        # Asset receipt
        {
            'parent_object_code': 'AssetReceipt',
            'relation_code': 'purchase_request_card',
            'target_object_code': 'PurchaseRequest',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'purchase_request_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '采购申请',
            'relation_name_en': 'Purchase Request',
        },
        {
            'parent_object_code': 'AssetReceipt',
            'relation_code': 'asset_categories',
            'target_object_code': 'AssetCategory',
            'relation_kind': 'through_line_item',
            'through_object_code': 'AssetReceiptItem',
            'through_parent_fk_field': 'asset_receipt',
            'through_target_fk_field': 'asset_category',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '入库分类',
            'relation_name_en': 'Receipt Categories',
        },

        # Asset status log
        {
            'parent_object_code': 'AssetStatusLog',
            'relation_code': 'asset_card',
            'target_object_code': 'Asset',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'asset_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '资产卡片',
            'relation_name_en': 'Asset Card',
        },

        # Depreciation config
        {
            'parent_object_code': 'DepreciationConfig',
            'relation_code': 'asset_category_card',
            'target_object_code': 'AssetCategory',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'category_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '资产分类',
            'relation_name_en': 'Asset Category',
        },

        # IT software domain
        {
            'parent_object_code': 'ITSoftware',
            'relation_code': 'software_licenses',
            'target_object_code': 'ITSoftwareLicense',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'software',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '软件许可',
            'relation_name_en': 'Software Licenses',
        },
        {
            'parent_object_code': 'ITSoftwareLicense',
            'relation_code': 'software_card',
            'target_object_code': 'ITSoftware',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'software_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '软件信息',
            'relation_name_en': 'Software',
        },
        {
            'parent_object_code': 'ITSoftwareLicense',
            'relation_code': 'license_allocations',
            'target_object_code': 'ITLicenseAllocation',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'license',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '许可分配',
            'relation_name_en': 'License Allocations',
        },

        # Insurance company
        {
            'parent_object_code': 'InsuranceCompany',
            'relation_code': 'insurance_policies',
            'target_object_code': 'InsurancePolicy',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'company',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '保险保单',
            'relation_name_en': 'Insurance Policies',
        },

        # Inventory snapshot
        {
            'parent_object_code': 'InventorySnapshot',
            'relation_code': 'task_card',
            'target_object_code': 'InventoryTask',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'task_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '盘点任务',
            'relation_name_en': 'Inventory Task',
        },
        {
            'parent_object_code': 'InventorySnapshot',
            'relation_code': 'asset_card',
            'target_object_code': 'Asset',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'asset_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '资产卡片',
            'relation_name_en': 'Asset Card',
        },

        # Software license domain (software_licenses app)
        {
            'parent_object_code': 'Software',
            'relation_code': 'software_licenses',
            'target_object_code': 'SoftwareLicense',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'software',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '软件许可',
            'relation_name_en': 'Software Licenses',
        },
        {
            'parent_object_code': 'Software',
            'relation_code': 'asset_category_card',
            'target_object_code': 'AssetCategory',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'category_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '资产分类',
            'relation_name_en': 'Asset Category',
        },
        {
            'parent_object_code': 'SoftwareLicense',
            'relation_code': 'software_card',
            'target_object_code': 'Software',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'software_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '软件信息',
            'relation_name_en': 'Software',
        },
        {
            'parent_object_code': 'SoftwareLicense',
            'relation_code': 'vendor_card',
            'target_object_code': 'Supplier',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'vendor_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '供应商',
            'relation_name_en': 'Vendor',
        },
        {
            'parent_object_code': 'SoftwareLicense',
            'relation_code': 'license_allocations',
            'target_object_code': 'LicenseAllocation',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'license',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
            'relation_name': '许可分配',
            'relation_name_en': 'License Allocations',
        },
        {
            'parent_object_code': 'LicenseAllocation',
            'relation_code': 'software_license_card',
            'target_object_code': 'SoftwareLicense',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'license_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '软件许可',
            'relation_name_en': 'Software License',
        },
        {
            'parent_object_code': 'LicenseAllocation',
            'relation_code': 'asset_card',
            'target_object_code': 'Asset',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'asset_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '资产卡片',
            'relation_name_en': 'Asset Card',
        },

        # Maintenance plan / task
        {
            'parent_object_code': 'MaintenancePlan',
            'relation_code': 'maintenance_tasks',
            'target_object_code': 'MaintenanceTask',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'plan',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '维保任务',
            'relation_name_en': 'Maintenance Tasks',
        },
        {
            'parent_object_code': 'MaintenanceTask',
            'relation_code': 'maintenance_plan_card',
            'target_object_code': 'MaintenancePlan',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'plan_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '维保计划',
            'relation_name_en': 'Maintenance Plan',
        },
        {
            'parent_object_code': 'MaintenanceTask',
            'relation_code': 'asset_card',
            'target_object_code': 'Asset',
            'relation_kind': 'derived_query',
            'derived_parent_key_field': 'asset_id',
            'derived_target_key_field': 'id',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '资产卡片',
            'relation_name_en': 'Asset Card',
        },

        # Organization / department
        {
            'parent_object_code': 'Organization',
            'relation_code': 'child_organizations',
            'target_object_code': 'Organization',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'parent',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '下级组织',
            'relation_name_en': 'Child Organizations',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'departments',
            'target_object_code': 'Department',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'relation_name': '部门',
            'relation_name_en': 'Departments',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'users',
            'target_object_code': 'User',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 30,
            'relation_name': '用户',
            'relation_name_en': 'Users',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'assets',
            'target_object_code': 'Asset',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'department',
            'display_mode': 'inline_readonly',
            'sort_order': 40,
            'relation_name': '组织资产',
            'relation_name_en': 'Organization Assets',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'consumable_issues',
            'target_object_code': 'ConsumableIssue',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'department',
            'display_mode': 'inline_readonly',
            'sort_order': 50,
            'relation_name': '耗材领用',
            'relation_name_en': 'Consumable Issues',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'purchase_requests',
            'target_object_code': 'PurchaseRequest',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'department',
            'display_mode': 'inline_readonly',
            'sort_order': 60,
            'relation_name': '采购申请',
            'relation_name_en': 'Purchase Requests',
        },
        {
            'parent_object_code': 'Organization',
            'relation_code': 'disposal_requests',
            'target_object_code': 'DisposalRequest',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'department',
            'display_mode': 'inline_readonly',
            'sort_order': 70,
            'relation_name': '处置申请',
            'relation_name_en': 'Disposal Requests',
        },
        {
            'parent_object_code': 'Department',
            'relation_code': 'child_departments',
            'target_object_code': 'Department',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'parent',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '下级部门',
            'relation_name_en': 'Child Departments',
        },
        {
            'parent_object_code': 'Department',
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

        # Purchase request
        {
            'parent_object_code': 'PurchaseRequest',
            'relation_code': 'asset_receipts',
            'target_object_code': 'AssetReceipt',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'purchase_request',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'relation_name': '入库单据',
            'relation_name_en': 'Asset Receipts',
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
        ('system', '0027_seed_relation_closed_loop_inventory_consumables'),
    ]

    operations = [
        migrations.RunPython(seed_relation_closed_loop_domain_stable, noop_reverse),
    ]
