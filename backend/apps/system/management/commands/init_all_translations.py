# Management command to initialize comprehensive translation data
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from apps.system.models import (
    Translation, BusinessObject, DictionaryType, DictionaryItem,
    ModelFieldDefinition
)


class Command(BaseCommand):
    help = 'Initialize comprehensive translation data for all objects'

    def handle(self, *args, **options):
        self.stdout.write('Initializing comprehensive translation data...')

        # Get content types
        business_object_ct = ContentType.objects.get_for_model(BusinessObject, for_concrete_model=False)
        dict_type_ct = ContentType.objects.get_for_model(DictionaryType, for_concrete_model=False)
        dict_item_ct = ContentType.objects.get_for_model(DictionaryItem, for_concrete_model=False)
        field_def_ct = ContentType.objects.get_for_model(ModelFieldDefinition, for_concrete_model=False)

        translations_to_create = []

        # ========================================================================
        # 1. Static Translations (namespace/key pattern)
        # ========================================================================
        self.stdout.write('  Adding static translations...')

        static_translations = {
            # Actions
            'button.save': {'zh-CN': '保存', 'en-US': 'Save'},
            'button.cancel': {'zh-CN': '取消', 'en-US': 'Cancel'},
            'button.confirm': {'zh-CN': '确定', 'en-US': 'Confirm'},
            'button.add': {'zh-CN': '添加', 'en-US': 'Add'},
            'button.edit': {'zh-CN': '编辑', 'en-US': 'Edit'},
            'button.delete': {'zh-CN': '删除', 'en-US': 'Delete'},
            'button.export': {'zh-CN': '导出', 'en-US': 'Export'},
            'button.import': {'zh-CN': '导入', 'en-US': 'Import'},
            'button.search': {'zh-CN': '查询', 'en-US': 'Search'},
            'button.reset': {'zh-CN': '重置', 'en-US': 'Reset'},
            'button.submit': {'zh-CN': '提交', 'en-US': 'Submit'},
            'button.approve': {'zh-CN': '通过', 'en-US': 'Approve'},
            'button.reject': {'zh-CN': '拒绝', 'en-US': 'Reject'},
            'button.back': {'zh-CN': '返回', 'en-US': 'Back'},
            'button.close': {'zh-CN': '关闭', 'en-US': 'Close'},
            'button.refresh': {'zh-CN': '刷新', 'en-US': 'Refresh'},
            'button.download': {'zh-CN': '下载', 'en-US': 'Download'},
            'button.upload': {'zh-CN': '上传', 'en-US': 'Upload'},
            'button.print': {'zh-CN': '打印', 'en-US': 'Print'},
            'button.view': {'zh-CN': '查看', 'en-US': 'View'},
            'button.create': {'zh-CN': '新建', 'en-US': 'Create'},
            'button.update': {'zh-CN': '更新', 'en-US': 'Update'},

            # Status
            'status.active': {'zh-CN': '启用', 'en-US': 'Active'},
            'status.inactive': {'zh-CN': '停用', 'en-US': 'Inactive'},
            'status.enabled': {'zh-CN': '启用', 'en-US': 'Enabled'},
            'status.disabled': {'zh-CN': '禁用', 'en-US': 'Disabled'},
            'status.idle': {'zh-CN': '空闲', 'en-US': 'Idle'},
            'status.in_use': {'zh-CN': '使用中', 'en-US': 'In Use'},
            'status.maintenance': {'zh-CN': '维护中', 'en-US': 'Maintenance'},
            'status.pending': {'zh-CN': '待审批', 'en-US': 'Pending'},
            'status.approved': {'zh-CN': '已审批', 'en-US': 'Approved'},
            'status.rejected': {'zh-CN': '已拒绝', 'en-US': 'Rejected'},
            'status.draft': {'zh-CN': '草稿', 'en-US': 'Draft'},
            'status.completed': {'zh-CN': '已完成', 'en-US': 'Completed'},
            'status.cancelled': {'zh-CN': '已取消', 'en-US': 'Cancelled'},
            'status.in_progress': {'zh-CN': '进行中', 'en-US': 'In Progress'},
            'status.locked': {'zh-CN': '锁定', 'en-US': 'Locked'},
            'status.archived': {'zh-CN': '已归档', 'en-US': 'Archived'},

            # Common labels
            'label.yes': {'zh-CN': '是', 'en-US': 'Yes'},
            'label.no': {'zh-CN': '否', 'en-US': 'No'},
            'label.all': {'zh-CN': '全部', 'en-US': 'All'},
            'label.name': {'zh-CN': '名称', 'en-US': 'Name'},
            'label.code': {'zh-CN': '编码', 'en-US': 'Code'},
            'label.description': {'zh-CN': '描述', 'en-US': 'Description'},
            'label.remark': {'zh-CN': '备注', 'en-US': 'Remark'},
            'label.notes': {'zh-CN': '备注', 'en-US': 'Notes'},
            'label.created_at': {'zh-CN': '创建时间', 'en-US': 'Created At'},
            'label.updated_at': {'zh-CN': '更新时间', 'en-US': 'Updated At'},
            'label.created_by': {'zh-CN': '创建人', 'en-US': 'Created By'},
            'label.updated_by': {'zh-CN': '更新人', 'en-US': 'Updated By'},
            'label.actions': {'zh-CN': '操作', 'en-US': 'Actions'},
            'label.status': {'zh-CN': '状态', 'en-US': 'Status'},
            'label.type': {'zh-CN': '类型', 'en-US': 'Type'},
            'label.category': {'zh-CN': '分类', 'en-US': 'Category'},
            'label.quantity': {'zh-CN': '数量', 'en-US': 'Quantity'},
            'label.amount': {'zh-CN': '金额', 'en-US': 'Amount'},
            'label.price': {'zh-CN': '价格', 'en-US': 'Price'},
            'label.date': {'zh-CN': '日期', 'en-US': 'Date'},
            'label.time': {'zh-CN': '时间', 'en-US': 'Time'},
            'label.user': {'zh-CN': '用户', 'en-US': 'User'},
            'label.department': {'zh-CN': '部门', 'en-US': 'Department'},
            'label.location': {'zh-CN': '位置', 'en-US': 'Location'},
            'label.address': {'zh-CN': '地址', 'en-US': 'Address'},
            'label.phone': {'zh-CN': '电话', 'en-US': 'Phone'},
            'label.email': {'zh-CN': '邮箱', 'en-US': 'Email'},
            'label.attachment': {'zh-CN': '附件', 'en-US': 'Attachment'},
            'label.image': {'zh-CN': '图片', 'en-US': 'Image'},
            'label.file': {'zh-CN': '文件', 'en-US': 'File'},
        }

        for key, texts in static_translations.items():
            namespace, key = key.split('.', 1)
            for lang_code, text in texts.items():
                if not Translation.objects.filter(
                    namespace=namespace,
                    key=key,
                    language_code=lang_code,
                    is_deleted=False
                ).exists():
                    translations_to_create.append(
                        Translation(
                            namespace=namespace,
                            key=key,
                            language_code=lang_code,
                            text=text,
                            type='label',
                            is_system=True
                        )
                    )

        # ========================================================================
        # 2. BusinessObject Translations
        # ========================================================================
        self.stdout.write('  Adding BusinessObject translations...')

        business_object_translations = {
            'Asset': {'zh-CN': '固定资产', 'en-US': 'Fixed Asset'},
            'AssetCategory': {'zh-CN': '资产分类', 'en-US': 'Asset Category'},
            'Location': {'zh-CN': '存放位置', 'en-US': 'Storage Location'},
            'Supplier': {'zh-CN': '供应商', 'en-US': 'Supplier'},
            'AssetPickup': {'zh-CN': '资产领用', 'en-US': 'Asset Pickup'},
            'AssetTransfer': {'zh-CN': '资产调拨', 'en-US': 'Asset Transfer'},
            'AssetReturn': {'zh-CN': '资产退库', 'en-US': 'Asset Return'},
            'AssetLoan': {'zh-CN': '资产借用', 'en-US': 'Asset Loan'},
            'Consumable': {'zh-CN': '耗材', 'en-US': 'Consumable'},
            'ConsumableCategory': {'zh-CN': '耗材分类', 'en-US': 'Consumable Category'},
            'ConsumableStock': {'zh-CN': '耗材库存', 'en-US': 'Consumable Stock'},
            'ConsumablePurchase': {'zh-CN': '耗材采购', 'en-US': 'Consumable Purchase'},
            'ConsumableIssue': {'zh-CN': '耗材领用', 'en-US': 'Consumable Issue'},
            'PurchaseRequest': {'zh-CN': '采购申请', 'en-US': 'Purchase Request'},
            'InventoryTask': {'zh-CN': '盘点任务', 'en-US': 'Inventory Task'},
            'InventorySnapshot': {'zh-CN': '资产快照', 'en-US': 'Asset Snapshot'},
            'InventoryItem': {'zh-CN': '盘点明细', 'en-US': 'Inventory Item'},
            'Maintenance': {'zh-CN': '维修记录', 'en-US': 'Maintenance Record'},
            'MaintenanceTask': {'zh-CN': '维修任务', 'en-US': 'Maintenance Task'},
            'DisposalRequest': {'zh-CN': '报废申请', 'en-US': 'Disposal Request'},
            'Voucher': {'zh-CN': '财务凭证', 'en-US': 'Finance Voucher'},
            'VoucherTemplate': {'zh-CN': '凭证模板', 'en-US': 'Voucher Template'},
            'DepreciationConfig': {'zh-CN': '折旧配置', 'en-US': 'Depreciation Config'},
            'DepreciationRecord': {'zh-CN': '折旧记录', 'en-US': 'Depreciation Record'},
            'ITAsset': {'zh-CN': 'IT资产', 'en-US': 'IT Asset'},
            'ITMaintenanceRecord': {'zh-CN': 'IT维护记录', 'en-US': 'IT Maintenance Record'},
            'ConfigurationChange': {'zh-CN': '配置变更', 'en-US': 'Configuration Change'},
            'Software': {'zh-CN': '软件目录', 'en-US': 'Software Catalog'},
            'SoftwareLicense': {'zh-CN': '软件许可', 'en-US': 'Software License'},
            'LicenseAllocation': {'zh-CN': '许可证分配', 'en-US': 'License Allocation'},
            'LeasingContract': {'zh-CN': '租赁合同', 'en-US': 'Leasing Contract'},
            'LeaseItem': {'zh-CN': '租赁明细', 'en-US': 'Lease Item'},
            'LeaseExtension': {'zh-CN': '租赁展期', 'en-US': 'Lease Extension'},
            'LeaseReturn': {'zh-CN': '租赁归还', 'en-US': 'Lease Return'},
            'RentPayment': {'zh-CN': '租金支付', 'en-US': 'Rent Payment'},
            'InsuranceCompany': {'zh-CN': '保险公司', 'en-US': 'Insurance Company'},
            'InsurancePolicy': {'zh-CN': '保险保单', 'en-US': 'Insurance Policy'},
            'InsuredAsset': {'zh-CN': '参保资产', 'en-US': 'Insured Asset'},
            'PremiumPayment': {'zh-CN': '保费支付', 'en-US': 'Premium Payment'},
            'ClaimRecord': {'zh-CN': '理赔记录', 'en-US': 'Claim Record'},
            'PolicyRenewal': {'zh-CN': '保单续保', 'en-US': 'Policy Renewal'},
            'WorkflowDefinition': {'zh-CN': '工作流定义', 'en-US': 'Workflow Definition'},
            'WorkflowInstance': {'zh-CN': '工作流实例', 'en-US': 'Workflow Instance'},
            'WorkflowTask': {'zh-CN': '工作流任务', 'en-US': 'Workflow Task'},
        }

        for obj_code, translations in business_object_translations.items():
            try:
                obj = BusinessObject.objects.get(code=obj_code, is_deleted=False)
                for lang_code, text in translations.items():
                    # Skip if name_en exists and matches for en-US
                    if lang_code == 'en-US' and obj.name_en == text:
                        continue
                    if not Translation.objects.filter(
                        content_type=business_object_ct,
                        object_id=obj.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=business_object_ct,
                                object_id=obj.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except BusinessObject.DoesNotExist:
                self.stdout.write(f'    Warning: BusinessObject "{obj_code}" not found')

        # ========================================================================
        # 3. DictionaryType Translations
        # ========================================================================
        self.stdout.write('  Adding DictionaryType translations...')

        dict_type_translations = {
            'ASSET_STATUS': {'zh-CN': '资产状态', 'en-US': 'Asset Status'},
            'ASSET_TYPE': {'zh-CN': '资产类型', 'en-US': 'Asset Type'},
            'ASSET_CATEGORY': {'zh-CN': '资产分类', 'en-US': 'Asset Category'},
            'UNIT': {'zh-CN': '计量单位', 'en-US': 'Unit'},
            'ASSET_BRAND': {'zh-CN': '资产品牌', 'en-US': 'Asset Brand'},
            'DEPRECIATION_METHOD': {'zh-CN': '折旧方法', 'en-US': 'Depreciation Method'},
            'INVENTORY_DISCREPANCY_TYPE': {'zh-CN': '盘点差异类型', 'en-US': 'Inventory Discrepancy Type'},
            'INVENTORY_STATUS': {'zh-CN': '盘点状态', 'en-US': 'Inventory Status'},
            'INVENTORY_TYPE': {'zh-CN': '盘点类型', 'en-US': 'Inventory Type'},
            'MAINTENANCE_TYPE': {'zh-CN': '维护类型', 'en-US': 'Maintenance Type'},
            'MAINTENANCE_STATUS': {'zh-CN': '维护状态', 'en-US': 'Maintenance Status'},
            'CONSUMABLE_TYPE': {'zh-CN': '耗材类型', 'en-US': 'Consumable Type'},
            'CONSUMIBLE_CATEGORY': {'zh-CN': '耗材分类', 'en-US': 'Consumable Category'},
            'VOUCHER_STATUS': {'zh-CN': '凭证状态', 'en-US': 'Voucher Status'},
            'VOUCHER_TYPE': {'zh-CN': '凭证类型', 'en-US': 'Voucher Type'},
            'SOFTWARE_TYPE': {'zh-CN': '软件类型', 'en-US': 'Software Type'},
            'LICENSE_TYPE': {'zh-CN': '许可类型', 'en-US': 'License Type'},
            'LICENSE_STATUS': {'zh-CN': '许可状态', 'en-US': 'License Status'},
            'ALLOCATION_STATUS': {'zh-CN': '分配状态', 'en-US': 'Allocation Status'},
            'LEASE_STATUS': {'zh-CN': '租赁状态', 'en-US': 'Lease Status'},
            'INSURANCE_TYPE': {'zh-CN': '保险类型', 'en-US': 'Insurance Type'},
            'CLAIM_STATUS': {'zh-CN': '理赔状态', 'en-US': 'Claim Status'},
            'WORKFLOW_STATUS': {'zh-CN': '流程状态', 'en-US': 'Workflow Status'},
            'TASK_STATUS': {'zh-CN': '任务状态', 'en-US': 'Task Status'},
            'APPROVAL_RESULT': {'zh-CN': '审批结果', 'en-US': 'Approval Result'},
            'PAYMENT_STATUS': {'zh-CN': '支付状态', 'en-US': 'Payment Status'},
            'CONTRACT_STATUS': {'zh-CN': '合同状态', 'en-US': 'Contract Status'},
            'POLICY_STATUS': {'zh-CN': '保单状态', 'en-US': 'Policy Status'},
            'OS_TYPE': {'zh-CN': '操作系统', 'en-US': 'OS Type'},
            'ASSET_SOURCE': {'zh-CN': '资产来源', 'en-US': 'Asset Source'},
            'USAGE_STATUS': {'zh-CN': '使用状态', 'en-US': 'Usage Status'},
        }

        for dict_code, translations in dict_type_translations.items():
            try:
                obj = DictionaryType.objects.get(code=dict_code, is_deleted=False)
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_type_ct,
                        object_id=obj.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_type_ct,
                                object_id=obj.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryType.DoesNotExist:
                self.stdout.write(f'    Warning: DictionaryType "{dict_code}" not found')

        # ========================================================================
        # 4. DictionaryItem Translations (Asset Status)
        # ========================================================================
        self.stdout.write('  Adding DictionaryItem translations...')

        # Asset Status items
        asset_status_items = {
            'IDLE': {'zh-CN': '空闲', 'en-US': 'Idle'},
            'IN_USE': {'zh-CN': '使用中', 'en-US': 'In Use'},
            'MAINTENANCE': {'zh-CN': '维护中', 'en-US': 'Maintenance'},
            'REPAIR': {'zh-CN': '维修中', 'en-US': 'Under Repair'},
            'SCRAPPED': {'zh-CN': '已报废', 'en-US': 'Scrapped'},
            'LOST': {'zh-CN': '已丢失', 'en-US': 'Lost'},
            'RETIRE': {'zh-CN': '已退役', 'en-US': 'Retired'},
            'BORROWED': {'zh-CN': '借用中', 'en-US': 'Borrowed'},
            'PICKUP_PENDING': {'zh-CN': '待领用', 'en-US': 'Pickup Pending'},
            'TRANSFER_PENDING': {'zh-CN': '待调拨', 'en-US': 'Transfer Pending'},
            'RETURN_PENDING': {'zh-CN': '待退库', 'en-US': 'Return Pending'},
            'ON_LOAN': {'zh-CN': '借出', 'en-US': 'On Loan'},
            'DISPOSAL': {'zh-CN': '报废', 'en-US': 'Disposal'},
        }

        for item_code, translations in asset_status_items.items():
            try:
                item = DictionaryItem.objects.get(
                    dictionary_type__code='ASSET_STATUS',
                    code=item_code,
                    is_deleted=False
                )
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_item_ct,
                        object_id=item.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_item_ct,
                                object_id=item.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryItem.DoesNotExist:
                pass  # Item may not exist

        # Inventory Status items
        inventory_status_items = {
            'PENDING': {'zh-CN': '待开始', 'en-US': 'Pending'},
            'IN_PROGRESS': {'zh-CN': '进行中', 'en-US': 'In Progress'},
            'COMPLETED': {'zh-CN': '已完成', 'en-US': 'Completed'},
            'CANCELLED': {'zh-CN': '已取消', 'en-US': 'Cancelled'},
        }

        for item_code, translations in inventory_status_items.items():
            try:
                item = DictionaryItem.objects.get(
                    dictionary_type__code='INVENTORY_STATUS',
                    code=item_code,
                    is_deleted=False
                )
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_item_ct,
                        object_id=item.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_item_ct,
                                object_id=item.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryItem.DoesNotExist:
                pass

        # Inventory Type items
        inventory_type_items = {
            'FULL': {'zh-CN': '全盘', 'en-US': 'Full Inventory'},
            'RANDOM': {'zh-CN': '抽盘', 'en-US': 'Random'},
            'DYNAMIC': {'zh-CN': '动盘', 'en-US': 'Dynamic'},
            'PARTIAL': {'zh-CN': '部分盘点', 'en-US': 'Partial'},
            'DEPARTMENT': {'zh-CN': '部门盘点', 'en-US': 'Department'},
        }

        for item_code, translations in inventory_type_items.items():
            try:
                item = DictionaryItem.objects.get(
                    dictionary_type__code='INVENTORY_TYPE',
                    code=item_code,
                    is_deleted=False
                )
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_item_ct,
                        object_id=item.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_item_ct,
                                object_id=item.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryItem.DoesNotExist:
                pass

        # Maintenance Type items
        maintenance_type_items = {
            'PREVENTIVE': {'zh-CN': '预防性维护', 'en-US': 'Preventive'},
            'CORRECTIVE': {'zh-CN': '纠正性维护', 'en-US': 'Corrective'},
            'UPGRADE': {'zh-CN': '升级', 'en-US': 'Upgrade'},
            'REPLACEMENT': {'zh-CN': '更换', 'en-US': 'Replacement'},
            'INSPECTION': {'zh-CN': '巡检', 'en-US': 'Inspection'},
            'CLEANING': {'zh-CN': '清洁', 'en-US': 'Cleaning'},
            'OTHER': {'zh-CN': '其他', 'en-US': 'Other'},
        }

        for item_code, translations in maintenance_type_items.items():
            try:
                item = DictionaryItem.objects.get(
                    dictionary_type__code='MAINTENANCE_TYPE',
                    code=item_code,
                    is_deleted=False
                )
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_item_ct,
                        object_id=item.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_item_ct,
                                object_id=item.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryItem.DoesNotExist:
                pass

        # Workflow Status items
        workflow_status_items = {
            'DRAFT': {'zh-CN': '草稿', 'en-US': 'Draft'},
            'ACTIVE': {'zh-CN': '生效中', 'en-US': 'Active'},
            'INACTIVE': {'zh-CN': '已停用', 'en-US': 'Inactive'},
            'ARCHIVED': {'zh-CN': '已归档', 'en-US': 'Archived'},
        }

        for item_code, translations in workflow_status_items.items():
            try:
                item = DictionaryItem.objects.get(
                    dictionary_type__code='WORKFLOW_STATUS',
                    code=item_code,
                    is_deleted=False
                )
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_item_ct,
                        object_id=item.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_item_ct,
                                object_id=item.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryItem.DoesNotExist:
                pass

        # Task Status items
        task_status_items = {
            'PENDING': {'zh-CN': '待处理', 'en-US': 'Pending'},
            'IN_PROGRESS': {'zh-CN': '处理中', 'en-US': 'In Progress'},
            'COMPLETED': {'zh-CN': '已完成', 'en-US': 'Completed'},
            'CANCELLED': {'zh-CN': '已取消', 'en-US': 'Cancelled'},
            'RETURNED': {'zh-CN': '已退回', 'en-US': 'Returned'},
        }

        for item_code, translations in task_status_items.items():
            try:
                item = DictionaryItem.objects.get(
                    dictionary_type__code='TASK_STATUS',
                    code=item_code,
                    is_deleted=False
                )
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_item_ct,
                        object_id=item.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_item_ct,
                                object_id=item.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryItem.DoesNotExist:
                pass

        # Approval Result items
        approval_result_items = {
            'APPROVED': {'zh-CN': '同意', 'en-US': 'Approved'},
            'REJECTED': {'zh-CN': '拒绝', 'en-US': 'Rejected'},
            'RETURNED': {'zh-CN': '退回', 'en-US': 'Returned'},
            'CANCELLED': {'zh-CN': '撤销', 'en-US': 'Cancelled'},
        }

        for item_code, translations in approval_result_items.items():
            try:
                item = DictionaryItem.objects.get(
                    dictionary_type__code='APPROVAL_RESULT',
                    code=item_code,
                    is_deleted=False
                )
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_item_ct,
                        object_id=item.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_item_ct,
                                object_id=item.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryItem.DoesNotExist:
                pass

        # Voucher Status items
        voucher_status_items = {
            'DRAFT': {'zh-CN': '草稿', 'en-US': 'Draft'},
            'PENDING': {'zh-CN': '待审批', 'en-US': 'Pending'},
            'APPROVED': {'zh-CN': '已审批', 'en-US': 'Approved'},
            'POSTED': {'zh-CN': '已入账', 'en-US': 'Posted'},
            'REJECTED': {'zh-CN': '已驳回', 'en-US': 'Rejected'},
        }

        for item_code, translations in voucher_status_items.items():
            try:
                item = DictionaryItem.objects.get(
                    dictionary_type__code='VOUCHER_STATUS',
                    code=item_code,
                    is_deleted=False
                )
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_item_ct,
                        object_id=item.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_item_ct,
                                object_id=item.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryItem.DoesNotExist:
                pass

        # Software Type items
        software_type_items = {
            'OS': {'zh-CN': '操作系统', 'en-US': 'Operating System'},
            'OFFICE': {'zh-CN': '办公软件', 'en-US': 'Office Software'},
            'PROFESSIONAL': {'zh-CN': '专业软件', 'en-US': 'Professional'},
            'DEVELOPMENT': {'zh-CN': '开发工具', 'en-US': 'Development Tool'},
            'SECURITY': {'zh-CN': '安全软件', 'en-US': 'Security Software'},
            'DATABASE': {'zh-CN': '数据库', 'en-US': 'Database'},
            'OTHER': {'zh-CN': '其他', 'en-US': 'Other'},
        }

        for item_code, translations in software_type_items.items():
            try:
                item = DictionaryItem.objects.get(
                    dictionary_type__code='SOFTWARE_TYPE',
                    code=item_code,
                    is_deleted=False
                )
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_item_ct,
                        object_id=item.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_item_ct,
                                object_id=item.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryItem.DoesNotExist:
                pass

        # License Status items
        license_status_items = {
            'ACTIVE': {'zh-CN': '生效中', 'en-US': 'Active'},
            'EXPIRED': {'zh-CN': '已过期', 'en-US': 'Expired'},
            'SUSPENDED': {'zh-CN': '暂停', 'en-US': 'Suspended'},
            'REVOKED': {'zh-CN': '撤销', 'en-US': 'Revoked'},
        }

        for item_code, translations in license_status_items.items():
            try:
                item = DictionaryItem.objects.get(
                    dictionary_type__code='LICENSE_STATUS',
                    code=item_code,
                    is_deleted=False
                )
                for lang_code, text in translations.items():
                    if not Translation.objects.filter(
                        content_type=dict_item_ct,
                        object_id=item.pk,
                        field_name='name',
                        language_code=lang_code,
                        is_deleted=False
                    ).exists():
                        translations_to_create.append(
                            Translation(
                                content_type=dict_item_ct,
                                object_id=item.pk,
                                field_name='name',
                                language_code=lang_code,
                                text=text,
                                type='object_field',
                                is_system=True
                            )
                        )
            except DictionaryItem.DoesNotExist:
                pass

        # ========================================================================
        # 5. Bulk Create
        # ========================================================================
        if translations_to_create:
            Translation.objects.bulk_create(translations_to_create, batch_size=500)
            count = len(translations_to_create)
            self.stdout.write(self.style.SUCCESS(f'Created {count} translations.'))
        else:
            self.stdout.write(self.style.WARNING('No new translations to create.'))

        self.stdout.write(self.style.SUCCESS('Translation initialization complete.'))
