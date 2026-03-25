"""
Canonical catalog for hardcoded business objects.

This module is the single configuration source for built-in objects that still
map to handwritten Django models and DRF viewsets. Runtime metadata continues
to live in BusinessObject rows; this catalog only provides bootstrap defaults
and fallbacks.
"""
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple


@dataclass(frozen=True)
class HardcodedObjectDefinition:
    code: str
    name: str
    name_en: str
    django_model_path: str
    viewset_path: str = ""
    icon: str = "document"
    menu_category: str = ""
    is_menu_hidden: bool = False
    object_role: str = "root"
    is_top_level_navigable: bool = True
    allow_standalone_query: bool = True
    allow_standalone_route: bool = True
    inherit_permissions: bool = False
    inherit_workflow: bool = False
    inherit_status: bool = False
    inherit_lifecycle: bool = False

    @property
    def app_label(self) -> str:
        parts = self.django_model_path.split(".")
        if len(parts) >= 2 and parts[0] == "apps":
            return parts[1]
        if len(parts) >= 3:
            return parts[-3]
        return ""

    @property
    def name_pair(self) -> Tuple[str, str]:
        return (self.name, self.name_en)


HARDCODED_OBJECTS: Tuple[HardcodedObjectDefinition, ...] = (
    HardcodedObjectDefinition(
        code="Asset",
        name="资产",
        name_en="Asset",
        django_model_path="apps.assets.models.Asset",
        viewset_path="apps.assets.viewsets.AssetViewSet",
        icon="box",
    ),
    HardcodedObjectDefinition(
        code="AssetCategory",
        name="资产分类",
        name_en="Asset Category",
        django_model_path="apps.assets.models.AssetCategory",
        viewset_path="apps.assets.viewsets.AssetCategoryViewSet",
        icon="folder",
    ),
    HardcodedObjectDefinition(
        code="Supplier",
        name="供应商",
        name_en="Supplier",
        django_model_path="apps.assets.models.Supplier",
        viewset_path="apps.assets.viewsets.SupplierViewSet",
        icon="office-building",
    ),
    HardcodedObjectDefinition(
        code="Location",
        name="位置",
        name_en="Location",
        django_model_path="apps.assets.models.Location",
        viewset_path="apps.assets.viewsets.LocationViewSet",
        icon="location",
    ),
    HardcodedObjectDefinition(
        code="AssetStatusLog",
        name="资产状态日志",
        name_en="Asset Status Log",
        django_model_path="apps.assets.models.AssetStatusLog",
        viewset_path="apps.assets.viewsets.AssetStatusLogViewSet",
    ),
    HardcodedObjectDefinition(
        code="AssetPickup",
        name="资产领用",
        name_en="Asset Pickup",
        django_model_path="apps.assets.models.AssetPickup",
        viewset_path="apps.assets.viewsets.AssetPickupViewSet",
        icon="hand",
    ),
    HardcodedObjectDefinition(
        code="PickupItem",
        name="领用明细",
        name_en="Pickup Item",
        django_model_path="apps.assets.models.PickupItem",
        viewset_path="apps.assets.viewsets.PickupItemViewSet",
        icon="list",
        menu_category="asset_operation",
        is_menu_hidden=True,
        object_role="detail",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_workflow=True,
        inherit_status=True,
        inherit_lifecycle=True,
    ),
    HardcodedObjectDefinition(
        code="AssetTransfer",
        name="资产调拨",
        name_en="Asset Transfer",
        django_model_path="apps.assets.models.AssetTransfer",
        viewset_path="apps.assets.viewsets.AssetTransferViewSet",
        icon="switch",
    ),
    HardcodedObjectDefinition(
        code="TransferItem",
        name="调拨明细",
        name_en="Transfer Item",
        django_model_path="apps.assets.models.TransferItem",
        viewset_path="apps.assets.viewsets.TransferItemViewSet",
        icon="list",
        menu_category="asset_operation",
        is_menu_hidden=True,
        object_role="detail",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_workflow=True,
        inherit_status=True,
        inherit_lifecycle=True,
    ),
    HardcodedObjectDefinition(
        code="AssetReturn",
        name="资产归还",
        name_en="Asset Return",
        django_model_path="apps.assets.models.AssetReturn",
        viewset_path="apps.assets.viewsets.AssetReturnViewSet",
        icon="back",
    ),
    HardcodedObjectDefinition(
        code="ReturnItem",
        name="归还明细",
        name_en="Return Item",
        django_model_path="apps.assets.models.ReturnItem",
        viewset_path="apps.assets.viewsets.ReturnItemViewSet",
        icon="list",
        menu_category="asset_operation",
        is_menu_hidden=True,
        object_role="detail",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_workflow=True,
        inherit_status=True,
        inherit_lifecycle=True,
    ),
    HardcodedObjectDefinition(
        code="AssetLoan",
        name="资产借用",
        name_en="Asset Loan",
        django_model_path="apps.assets.models.AssetLoan",
        viewset_path="apps.assets.viewsets.AssetLoanViewSet",
    ),
    HardcodedObjectDefinition(
        code="LoanItem",
        name="借用明细",
        name_en="Loan Item",
        django_model_path="apps.assets.models.LoanItem",
        viewset_path="apps.assets.viewsets.LoanItemViewSet",
        icon="list",
        menu_category="asset_operation",
        is_menu_hidden=True,
        object_role="detail",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_workflow=True,
        inherit_status=True,
        inherit_lifecycle=True,
    ),
    HardcodedObjectDefinition(
        code="Consumable",
        name="耗材",
        name_en="Consumable",
        django_model_path="apps.consumables.models.Consumable",
        viewset_path="apps.consumables.viewsets.ConsumableViewSet",
        icon="files",
    ),
    HardcodedObjectDefinition(
        code="ConsumableCategory",
        name="耗材分类",
        name_en="Consumable Category",
        django_model_path="apps.consumables.models.ConsumableCategory",
        viewset_path="apps.consumables.viewsets.ConsumableCategoryViewSet",
        icon="folder",
    ),
    HardcodedObjectDefinition(
        code="ConsumableStock",
        name="耗材库存",
        name_en="Consumable Stock",
        django_model_path="apps.consumables.models.ConsumableStock",
        viewset_path="apps.consumables.viewsets.ConsumableStockViewSet",
    ),
    HardcodedObjectDefinition(
        code="ConsumablePurchase",
        name="耗材采购",
        name_en="Consumable Purchase",
        django_model_path="apps.consumables.models.ConsumablePurchase",
        viewset_path="apps.consumables.viewsets.ConsumablePurchaseViewSet",
    ),
    HardcodedObjectDefinition(
        code="ConsumableIssue",
        name="耗材领用",
        name_en="Consumable Issue",
        django_model_path="apps.consumables.models.ConsumableIssue",
        viewset_path="apps.consumables.viewsets.ConsumableIssueViewSet",
    ),
    HardcodedObjectDefinition(
        code="PurchaseRequest",
        name="采购申请",
        name_en="Purchase Request",
        django_model_path="apps.lifecycle.models.PurchaseRequest",
        viewset_path="apps.lifecycle.viewsets.PurchaseRequestViewSet",
        icon="document",
    ),
    HardcodedObjectDefinition(
        code="PurchaseRequestItem",
        name="\u91c7\u8d2d\u7533\u8bf7\u660e\u7ec6",
        name_en="Purchase Request Item",
        django_model_path="apps.lifecycle.models.PurchaseRequestItem",
        icon="list",
        menu_category="lifecycle",
        is_menu_hidden=True,
        object_role="detail",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_workflow=True,
        inherit_status=True,
        inherit_lifecycle=True,
    ),
    HardcodedObjectDefinition(
        code="AssetReceipt",
        name="资产入库",
        name_en="Asset Receipt",
        django_model_path="apps.lifecycle.models.AssetReceipt",
        viewset_path="apps.lifecycle.viewsets.AssetReceiptViewSet",
    ),
    HardcodedObjectDefinition(
        code="AssetReceiptItem",
        name="\u8d44\u4ea7\u5165\u5e93\u660e\u7ec6",
        name_en="Asset Receipt Item",
        django_model_path="apps.lifecycle.models.AssetReceiptItem",
        icon="list",
        menu_category="lifecycle",
        is_menu_hidden=True,
        object_role="detail",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_workflow=True,
        inherit_status=True,
        inherit_lifecycle=True,
    ),
    HardcodedObjectDefinition(
        code="Maintenance",
        name="维修记录",
        name_en="Maintenance",
        django_model_path="apps.lifecycle.models.Maintenance",
        viewset_path="apps.lifecycle.viewsets.MaintenanceViewSet",
        icon="tools",
    ),
    HardcodedObjectDefinition(
        code="MaintenanceTask",
        name="维修任务",
        name_en="Maintenance Task",
        django_model_path="apps.lifecycle.models.MaintenanceTask",
        viewset_path="apps.lifecycle.viewsets.MaintenanceTaskViewSet",
    ),
    HardcodedObjectDefinition(
        code="MaintenancePlan",
        name="维修计划",
        name_en="Maintenance Plan",
        django_model_path="apps.lifecycle.models.MaintenancePlan",
        viewset_path="apps.lifecycle.viewsets.MaintenancePlanViewSet",
    ),
    HardcodedObjectDefinition(
        code="DisposalRequest",
        name="报废申请",
        name_en="Disposal Request",
        django_model_path="apps.lifecycle.models.DisposalRequest",
        viewset_path="apps.lifecycle.viewsets.DisposalRequestViewSet",
    ),
    HardcodedObjectDefinition(
        code="DisposalItem",
        name="\u62a5\u5e9f\u660e\u7ec6",
        name_en="Disposal Item",
        django_model_path="apps.lifecycle.models.DisposalItem",
        icon="list",
        menu_category="lifecycle",
        is_menu_hidden=True,
        object_role="detail",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_workflow=True,
        inherit_status=True,
        inherit_lifecycle=True,
    ),
    HardcodedObjectDefinition(
        code="InventoryTask",
        name="盘点任务",
        name_en="Inventory Task",
        django_model_path="apps.inventory.models.InventoryTask",
        viewset_path="apps.inventory.viewsets.InventoryTaskViewSet",
        icon="clipboard",
    ),
    HardcodedObjectDefinition(
        code="InventorySnapshot",
        name="资产快照",
        name_en="Inventory Snapshot",
        django_model_path="apps.inventory.models.InventorySnapshot",
        viewset_path="apps.inventory.viewsets.InventorySnapshotViewSet",
    ),
    HardcodedObjectDefinition(
        code="InventoryItem",
        name="盘点明细",
        name_en="Inventory Item",
        django_model_path="apps.inventory.models.InventoryDifference",
        viewset_path="apps.inventory.viewsets.InventoryDifferenceViewSet",
    ),
    HardcodedObjectDefinition(
        code="Organization",
        name="组织",
        name_en="Organization",
        django_model_path="apps.organizations.models.Organization",
        viewset_path="apps.organizations.viewsets.OrganizationViewSet",
        icon="office-building",
    ),
    HardcodedObjectDefinition(
        code="Department",
        name="部门",
        name_en="Department",
        django_model_path="apps.organizations.models.Department",
        viewset_path="apps.organizations.viewsets.DepartmentViewSet",
        icon="office-building",
    ),
    HardcodedObjectDefinition(
        code="User",
        name="用户",
        name_en="User",
        django_model_path="apps.accounts.models.User",
        viewset_path="apps.accounts.viewsets.UserViewSet",
        icon="user",
    ),
    HardcodedObjectDefinition(
        code="WorkflowDefinition",
        name="工作流定义",
        name_en="Workflow Definition",
        django_model_path="apps.workflows.models.WorkflowDefinition",
        viewset_path="apps.workflows.viewsets.WorkflowDefinitionViewSet",
    ),
    HardcodedObjectDefinition(
        code="WorkflowTemplate",
        name="工作流模板",
        name_en="Workflow Template",
        django_model_path="apps.workflows.models.WorkflowTemplate",
        viewset_path="apps.workflows.viewsets.WorkflowTemplateViewSet",
    ),
    HardcodedObjectDefinition(
        code="WorkflowInstance",
        name="工作流实例",
        name_en="Workflow Instance",
        django_model_path="apps.workflows.models.WorkflowInstance",
        viewset_path="apps.workflows.viewsets.WorkflowInstanceViewSet",
    ),
    HardcodedObjectDefinition(
        code="WorkflowTask",
        name="工作流任务",
        name_en="Workflow Task",
        django_model_path="apps.workflows.models.WorkflowTask",
        viewset_path="apps.workflows.viewsets.WorkflowTaskViewSet",
    ),
    HardcodedObjectDefinition(
        code="WorkflowApproval",
        name="工作流审批记录",
        name_en="Workflow Approval",
        django_model_path="apps.workflows.models.WorkflowApproval",
        viewset_path="apps.workflows.viewsets.WorkflowApprovalViewSet",
    ),
    HardcodedObjectDefinition(
        code="WorkflowOperationLog",
        name="工作流操作日志",
        name_en="Workflow Operation Log",
        django_model_path="apps.workflows.models.WorkflowOperationLog",
        viewset_path="apps.workflows.viewsets.WorkflowOperationLogViewSet",
    ),
    HardcodedObjectDefinition(
        code="FinanceVoucher",
        name="财务凭证",
        name_en="Finance Voucher",
        django_model_path="apps.finance.models.FinanceVoucher",
        viewset_path="apps.finance.viewsets.FinanceVoucherViewSet",
    ),
    HardcodedObjectDefinition(
        code="VoucherTemplate",
        name="凭证模板",
        name_en="Voucher Template",
        django_model_path="apps.finance.models.VoucherTemplate",
        viewset_path="apps.finance.viewsets.VoucherTemplateViewSet",
    ),
    HardcodedObjectDefinition(
        code="DepreciationConfig",
        name="折旧配置",
        name_en="Depreciation Config",
        django_model_path="apps.depreciation.models.DepreciationConfig",
        viewset_path="apps.depreciation.viewsets.DepreciationConfigViewSet",
    ),
    HardcodedObjectDefinition(
        code="DepreciationRecord",
        name="折旧记录",
        name_en="Depreciation Record",
        django_model_path="apps.depreciation.models.DepreciationRecord",
        viewset_path="apps.depreciation.viewsets.DepreciationRecordViewSet",
    ),
    HardcodedObjectDefinition(
        code="DepreciationRun",
        name="折旧运行",
        name_en="Depreciation Run",
        django_model_path="apps.depreciation.models.DepreciationRun",
        viewset_path="apps.depreciation.viewsets.DepreciationRunViewSet",
    ),
    HardcodedObjectDefinition(
        code="ITAsset",
        name="IT资产",
        name_en="IT Asset",
        django_model_path="apps.it_assets.models.ITAssetInfo",
        viewset_path="apps.it_assets.viewsets.ITAssetInfoViewSet",
    ),
    HardcodedObjectDefinition(
        code="ITMaintenanceRecord",
        name="IT维护记录",
        name_en="IT Maintenance Record",
        django_model_path="apps.it_assets.models.ITMaintenanceRecord",
        viewset_path="apps.it_assets.viewsets.ITMaintenanceRecordViewSet",
    ),
    HardcodedObjectDefinition(
        code="ConfigurationChange",
        name="配置变更",
        name_en="Configuration Change",
        django_model_path="apps.it_assets.models.ConfigurationChange",
        viewset_path="apps.it_assets.viewsets.ConfigurationChangeViewSet",
    ),
    HardcodedObjectDefinition(
        code="ITSoftware",
        name="IT软件目录",
        name_en="IT Software Catalog",
        django_model_path="apps.it_assets.models.Software",
        viewset_path="apps.it_assets.viewsets.SoftwareViewSet",
    ),
    HardcodedObjectDefinition(
        code="ITSoftwareLicense",
        name="IT软件许可",
        name_en="IT Software License",
        django_model_path="apps.it_assets.models.SoftwareLicense",
        viewset_path="apps.it_assets.viewsets.SoftwareLicenseViewSet",
    ),
    HardcodedObjectDefinition(
        code="ITLicenseAllocation",
        name="IT许可证分配",
        name_en="IT License Allocation",
        django_model_path="apps.it_assets.models.LicenseAllocation",
        viewset_path="apps.it_assets.viewsets.LicenseAllocationViewSet",
    ),
    HardcodedObjectDefinition(
        code="Software",
        name="软件目录",
        name_en="Software Catalog",
        django_model_path="apps.software_licenses.models.Software",
        viewset_path="apps.software_licenses.viewsets.SoftwareViewSet",
    ),
    HardcodedObjectDefinition(
        code="SoftwareLicense",
        name="软件许可",
        name_en="Software License",
        django_model_path="apps.software_licenses.models.SoftwareLicense",
        viewset_path="apps.software_licenses.viewsets.SoftwareLicenseViewSet",
    ),
    HardcodedObjectDefinition(
        code="LicenseAllocation",
        name="许可证分配",
        name_en="License Allocation",
        django_model_path="apps.software_licenses.models.LicenseAllocation",
        viewset_path="apps.software_licenses.viewsets.LicenseAllocationViewSet",
    ),
    HardcodedObjectDefinition(
        code="LeasingContract",
        name="租赁合同",
        name_en="Lease Contract",
        django_model_path="apps.leasing.models.LeaseContract",
        viewset_path="apps.leasing.viewsets.LeaseContractViewSet",
    ),
    HardcodedObjectDefinition(
        code="LeaseItem",
        name="租赁明细",
        name_en="Lease Item",
        django_model_path="apps.leasing.models.LeaseItem",
        viewset_path="apps.leasing.viewsets.LeaseItemViewSet",
    ),
    HardcodedObjectDefinition(
        code="RentPayment",
        name="租金支付",
        name_en="Rent Payment",
        django_model_path="apps.leasing.models.RentPayment",
        viewset_path="apps.leasing.viewsets.RentPaymentViewSet",
    ),
    HardcodedObjectDefinition(
        code="LeaseReturn",
        name="租赁归还",
        name_en="Lease Return",
        django_model_path="apps.leasing.models.LeaseReturn",
        viewset_path="apps.leasing.viewsets.LeaseReturnViewSet",
    ),
    HardcodedObjectDefinition(
        code="LeaseExtension",
        name="租赁续租",
        name_en="Lease Extension",
        django_model_path="apps.leasing.models.LeaseExtension",
        viewset_path="apps.leasing.viewsets.LeaseExtensionViewSet",
    ),
    HardcodedObjectDefinition(
        code="InsuranceCompany",
        name="保险公司",
        name_en="Insurance Company",
        django_model_path="apps.insurance.models.InsuranceCompany",
        viewset_path="apps.insurance.viewsets.InsuranceCompanyViewSet",
    ),
    HardcodedObjectDefinition(
        code="InsurancePolicy",
        name="保险保单",
        name_en="Insurance Policy",
        django_model_path="apps.insurance.models.InsurancePolicy",
        viewset_path="apps.insurance.viewsets.InsurancePolicyViewSet",
    ),
    HardcodedObjectDefinition(
        code="InsuredAsset",
        name="投保资产",
        name_en="Insured Asset",
        django_model_path="apps.insurance.models.InsuredAsset",
        viewset_path="apps.insurance.viewsets.InsuredAssetViewSet",
    ),
    HardcodedObjectDefinition(
        code="PremiumPayment",
        name="保费支付",
        name_en="Premium Payment",
        django_model_path="apps.insurance.models.PremiumPayment",
        viewset_path="apps.insurance.viewsets.PremiumPaymentViewSet",
    ),
    HardcodedObjectDefinition(
        code="ClaimRecord",
        name="理赔记录",
        name_en="Claim Record",
        django_model_path="apps.insurance.models.ClaimRecord",
        viewset_path="apps.insurance.viewsets.ClaimRecordViewSet",
    ),
    HardcodedObjectDefinition(
        code="PolicyRenewal",
        name="保单续保",
        name_en="Policy Renewal",
        django_model_path="apps.insurance.models.PolicyRenewal",
        viewset_path="apps.insurance.viewsets.PolicyRenewalViewSet",
    ),
    HardcodedObjectDefinition(
        code="AssetProject",
        name="资产项目",
        name_en="Asset Project",
        django_model_path="apps.projects.models.AssetProject",
        viewset_path="apps.projects.viewsets.AssetProjectViewSet",
        icon="collection",
        menu_category="lifecycle",
    ),
    HardcodedObjectDefinition(
        code="ProjectAsset",
        name="项目资产分配",
        name_en="Project Asset",
        django_model_path="apps.projects.models.ProjectAsset",
        viewset_path="apps.projects.viewsets.ProjectAssetViewSet",
        icon="link",
        menu_category="lifecycle",
        is_menu_hidden=True,
        object_role="detail",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_status=True,
        inherit_lifecycle=True,
    ),
    HardcodedObjectDefinition(
        code="ProjectMember",
        name="项目成员",
        name_en="Project Member",
        django_model_path="apps.projects.models.ProjectMember",
        viewset_path="apps.projects.viewsets.ProjectMemberViewSet",
        icon="user-filled",
        menu_category="lifecycle",
        is_menu_hidden=True,
        object_role="detail",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_status=True,
        inherit_lifecycle=True,
    ),
)

HARDCODED_OBJECTS_BY_CODE: Dict[str, HardcodedObjectDefinition] = {
    definition.code: definition for definition in HARDCODED_OBJECTS
}
HARDCODED_MODEL_PATHS: Dict[str, str] = {
    definition.code: definition.django_model_path for definition in HARDCODED_OBJECTS
}
HARDCODED_VIEWSET_PATHS: Dict[str, str] = {
    definition.code: definition.viewset_path
    for definition in HARDCODED_OBJECTS
    if definition.viewset_path
}
HARDCODED_OBJECT_NAMES: Dict[str, Tuple[str, str]] = {
    definition.code: definition.name_pair for definition in HARDCODED_OBJECTS
}
HARDCODED_OBJECT_CODES_BY_MODEL_PATH: Dict[str, str] = {
    definition.django_model_path: definition.code for definition in HARDCODED_OBJECTS
}


def iter_hardcoded_object_definitions() -> Iterable[HardcodedObjectDefinition]:
    return HARDCODED_OBJECTS


def get_hardcoded_object_definition(code: str) -> Optional[HardcodedObjectDefinition]:
    return HARDCODED_OBJECTS_BY_CODE.get(code)


def get_hardcoded_model_map() -> Dict[str, str]:
    return dict(HARDCODED_MODEL_PATHS)


def get_hardcoded_viewset_map() -> Dict[str, str]:
    return dict(HARDCODED_VIEWSET_PATHS)


def get_hardcoded_object_names() -> Dict[str, Tuple[str, str]]:
    return dict(HARDCODED_OBJECT_NAMES)


def get_object_code_by_model_path(model_path: str) -> Optional[str]:
    return HARDCODED_OBJECT_CODES_BY_MODEL_PATH.get(model_path)
