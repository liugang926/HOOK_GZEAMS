"""
Standard menu configuration for metadata-driven navigation.

This module is the single runtime source of truth for:
- standard menu groups
- default menu placement for registered business objects
- static system pages that belong in the main navigation

No localized labels are stored here. Runtime consumers must resolve
`translation_key` fields through the i18n layer.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from apps.system.models import BusinessObject


MenuConfig = Dict[str, Any]


MENU_GROUPS: Dict[str, Dict[str, Any]] = {
    "asset_master": {
        "order": 10,
        "icon": "FolderOpened",
        "translation_key": "menu.categories.asset_master",
    },
    "asset_operation": {
        "order": 20,
        "icon": "Operation",
        "translation_key": "menu.categories.asset_operation",
    },
    "lifecycle": {
        "order": 30,
        "icon": "Refresh",
        "translation_key": "menu.categories.lifecycle",
    },
    "consumable": {
        "order": 40,
        "icon": "Box",
        "translation_key": "menu.categories.consumable",
    },
    "inventory": {
        "order": 50,
        "icon": "Box",
        "translation_key": "menu.categories.inventory",
    },
    "finance": {
        "order": 60,
        "icon": "Wallet",
        "translation_key": "menu.categories.finance",
    },
    "organization": {
        "order": 70,
        "icon": "OfficeBuilding",
        "translation_key": "menu.categories.organization",
    },
    "workflow": {
        "order": 80,
        "icon": "Connection",
        "translation_key": "menu.categories.workflow",
    },
    "system": {
        "order": 90,
        "icon": "Setting",
        "translation_key": "menu.categories.system",
    },
    "reports": {
        "order": 100,
        "icon": "DataAnalysis",
        "translation_key": "menu.categories.reports",
    },
    "other": {
        "order": 999,
        "icon": "Menu",
        "translation_key": "menu.categories.other",
    },
}


OBJECT_ROUTE_KEY_MAP: Dict[str, str] = {
    "Asset": "assetList",
    "AssetCategory": "assetCategory",
    "Location": "location",
    "Supplier": "supplier",
    "AssetStatusLog": "assetStatusLog",
    "AssetPickup": "assetPickup",
    "AssetTransfer": "assetTransfer",
    "AssetReturn": "assetReturn",
    "AssetLoan": "assetLoan",
    "Consumable": "consumable",
    "ConsumableCategory": "consumableCategory",
    "ConsumableStock": "consumableStock",
    "ConsumablePurchase": "consumablePurchase",
    "ConsumableIssue": "consumableIssue",
    "PurchaseRequest": "purchaseRequest",
    "AssetReceipt": "assetReceipt",
    "Maintenance": "maintenance",
    "MaintenanceTask": "maintenanceTask",
    "MaintenancePlan": "maintenancePlan",
    "DisposalRequest": "disposalRequest",
    "InventoryTask": "inventoryTask",
    "InventorySnapshot": "inventorySnapshot",
    "InventoryItem": "inventoryItem",
    "Organization": "organization",
    "Department": "department",
    "User": "users",
    "WorkflowDefinition": "workflowDefinitions",
    "WorkflowInstance": "workflowInstances",
    "FinanceVoucher": "financeVoucher",
    "VoucherTemplate": "voucherTemplate",
    "DepreciationConfig": "depreciationConfig",
    "DepreciationRecord": "depreciationRecord",
    "DepreciationRun": "depreciationRun",
    "ITAsset": "itAsset",
    "ITMaintenanceRecord": "itMaintenanceRecord",
    "ConfigurationChange": "configurationChange",
    "ITSoftware": "itSoftware",
    "ITSoftwareLicense": "itSoftwareLicense",
    "ITLicenseAllocation": "itLicenseAllocation",
    "Software": "software",
    "SoftwareLicense": "softwareLicense",
    "LicenseAllocation": "licenseAllocation",
    "LeasingContract": "leasingContract",
    "LeaseItem": "leaseItem",
    "LeaseExtension": "leaseExtension",
    "LeaseReturn": "leaseReturn",
    "RentPayment": "rentPayment",
    "InsuranceCompany": "insuranceCompany",
    "InsurancePolicy": "insurancePolicy",
    "InsuredAsset": "insuredAsset",
    "PremiumPayment": "premiumPayment",
    "ClaimRecord": "claimRecord",
    "PolicyRenewal": "policyRenewal",
}


DEFAULT_OBJECT_MENU_RULES: Dict[str, Dict[str, Any]] = {
    "Asset": {"group_code": "asset_master", "item_order": 10, "icon": "Document"},
    "AssetCategory": {"group_code": "asset_master", "item_order": 20, "icon": "Folder"},
    "Location": {"group_code": "asset_master", "item_order": 30, "icon": "Location"},
    "Supplier": {"group_code": "asset_master", "item_order": 40, "icon": "OfficeBuilding"},
    "AssetStatusLog": {"group_code": "asset_master", "item_order": 50, "icon": "Clock"},
    "ITAsset": {"group_code": "asset_master", "item_order": 60, "icon": "Monitor"},
    "InsuredAsset": {"group_code": "asset_master", "item_order": 70, "icon": "DocumentChecked"},
    "AssetPickup": {"group_code": "asset_operation", "item_order": 10, "icon": "Upload"},
    "AssetTransfer": {"group_code": "asset_operation", "item_order": 20, "icon": "Switch"},
    "AssetReturn": {"group_code": "asset_operation", "item_order": 30, "icon": "Download"},
    "AssetLoan": {"group_code": "asset_operation", "item_order": 40, "icon": "Connection"},
    "PurchaseRequest": {"group_code": "lifecycle", "item_order": 10, "icon": "ShoppingCart"},
    "AssetReceipt": {"group_code": "lifecycle", "item_order": 20, "icon": "Box"},
    "Maintenance": {"group_code": "lifecycle", "item_order": 30, "icon": "Tools"},
    "MaintenancePlan": {"group_code": "lifecycle", "item_order": 40, "icon": "Calendar"},
    "MaintenanceTask": {"group_code": "lifecycle", "item_order": 50, "icon": "List"},
    "DisposalRequest": {"group_code": "lifecycle", "item_order": 60, "icon": "Delete"},
    "Consumable": {"group_code": "consumable", "item_order": 10, "icon": "Box"},
    "ConsumableCategory": {"group_code": "consumable", "item_order": 20, "icon": "Folder"},
    "ConsumableStock": {"group_code": "consumable", "item_order": 30, "icon": "Goods"},
    "ConsumablePurchase": {"group_code": "consumable", "item_order": 40, "icon": "ShoppingCart"},
    "ConsumableIssue": {"group_code": "consumable", "item_order": 50, "icon": "Sell"},
    "InventoryTask": {"group_code": "inventory", "item_order": 10, "icon": "Clipboard"},
    "InventorySnapshot": {
        "group_code": "inventory",
        "item_order": 20,
        "icon": "Camera",
        "show_in_menu": False,
    },
    "InventoryItem": {
        "group_code": "inventory",
        "item_order": 30,
        "icon": "Document",
        "show_in_menu": False,
    },
    "FinanceVoucher": {"group_code": "finance", "item_order": 10, "icon": "Tickets"},
    "VoucherTemplate": {"group_code": "finance", "item_order": 20, "icon": "Files"},
    "DepreciationConfig": {"group_code": "finance", "item_order": 30, "icon": "Setting"},
    "DepreciationRun": {"group_code": "finance", "item_order": 40, "icon": "VideoPlay"},
    "DepreciationRecord": {"group_code": "finance", "item_order": 50, "icon": "Histogram"},
    "InsuranceCompany": {"group_code": "finance", "item_order": 60, "icon": "OfficeBuilding"},
    "InsurancePolicy": {"group_code": "finance", "item_order": 70, "icon": "Shield"},
    "PremiumPayment": {"group_code": "finance", "item_order": 80, "icon": "Wallet"},
    "ClaimRecord": {"group_code": "finance", "item_order": 90, "icon": "Warning"},
    "PolicyRenewal": {"group_code": "finance", "item_order": 100, "icon": "Refresh"},
    "LeasingContract": {"group_code": "finance", "item_order": 110, "icon": "Files"},
    "LeaseItem": {"group_code": "finance", "item_order": 120, "icon": "List"},
    "LeaseExtension": {"group_code": "finance", "item_order": 130, "icon": "Clock"},
    "LeaseReturn": {"group_code": "finance", "item_order": 140, "icon": "Back"},
    "RentPayment": {"group_code": "finance", "item_order": 150, "icon": "Wallet"},
    "Software": {"group_code": "finance", "item_order": 160, "icon": "Monitor"},
    "SoftwareLicense": {"group_code": "finance", "item_order": 170, "icon": "Key"},
    "LicenseAllocation": {"group_code": "finance", "item_order": 180, "icon": "Share"},
    "ITSoftware": {"group_code": "finance", "item_order": 190, "icon": "Monitor"},
    "ITSoftwareLicense": {"group_code": "finance", "item_order": 200, "icon": "Key"},
    "ITLicenseAllocation": {"group_code": "finance", "item_order": 210, "icon": "Share"},
    "Organization": {
        "group_code": "organization",
        "item_order": 10,
        "icon": "OfficeBuilding",
        "show_in_menu": False,
    },
    "Department": {"group_code": "organization", "item_order": 20, "icon": "Guide"},
    "User": {"group_code": "organization", "item_order": 30, "icon": "User", "show_in_menu": False},
    "Role": {
        "group_code": "organization",
        "item_order": 40,
        "icon": "UserFilled",
        "show_in_menu": False,
    },
    "WorkflowDefinition": {
        "group_code": "workflow",
        "item_order": 10,
        "icon": "Connection",
        "show_in_menu": False,
    },
    "WorkflowInstance": {
        "group_code": "workflow",
        "item_order": 20,
        "icon": "List",
        "show_in_menu": False,
    },
    "ConfigurationChange": {
        "group_code": "system",
        "item_order": 10,
        "icon": "Edit",
        "show_in_menu": False,
    },
}


STATIC_MENU_ITEMS: List[Dict[str, Any]] = [
    {
        "code": "VoucherList",
        "translation_key": "menu.routes.vouchers",
        "url": "/finance/vouchers",
        "group_code": "finance",
        "item_order": 1,
        "icon": "Tickets",
    },
    {
        "code": "DepreciationList",
        "translation_key": "menu.routes.depreciation",
        "url": "/finance/depreciation",
        "group_code": "finance",
        "item_order": 2,
        "icon": "TrendCharts",
    },
    {
        "code": "InsuranceDashboard",
        "translation_key": "menu.routes.insuranceDashboard",
        "url": "/insurance/dashboard",
        "group_code": "finance",
        "item_order": 3,
        "icon": "DataLine",
    },
    {
        "code": "ClaimList",
        "translation_key": "menu.routes.claimList",
        "url": "/insurance/claims",
        "group_code": "finance",
        "item_order": 4,
        "icon": "Tickets",
    },
    {
        "code": "LeasingDashboard",
        "translation_key": "menu.routes.leasingDashboard",
        "url": "/leasing/dashboard",
        "group_code": "finance",
        "item_order": 5,
        "icon": "DataLine",
    },
    {
        "code": "RentPaymentList",
        "translation_key": "menu.routes.rentPayments",
        "url": "/leasing/payments",
        "group_code": "finance",
        "item_order": 6,
        "icon": "Wallet",
    },
    {
        "code": "TaskCenter",
        "translation_key": "menu.routes.taskCenter",
        "url": "/workflow/tasks",
        "group_code": "workflow",
        "item_order": 10,
        "icon": "List",
    },
    {
        "code": "MyApprovals",
        "translation_key": "menu.routes.myApprovals",
        "url": "/workflow/my-approvals",
        "group_code": "workflow",
        "item_order": 20,
        "icon": "CircleCheck",
    },
    {
        "code": "WorkflowList",
        "translation_key": "menu.routes.workflowList",
        "url": "/admin/workflows",
        "group_code": "workflow",
        "item_order": 30,
        "icon": "Connection",
    },
    {
        "code": "PermissionManagement",
        "translation_key": "menu.routes.permissions",
        "url": "/admin/permissions",
        "group_code": "workflow",
        "item_order": 40,
        "icon": "Lock",
    },
    {
        "code": "BusinessObjectList",
        "translation_key": "menu.routes.businessObjects",
        "url": "/system/business-objects",
        "group_code": "system",
        "item_order": 10,
        "icon": "Grid",
    },
    {
        "code": "FieldDefinitionList",
        "translation_key": "menu.routes.fieldDefinitions",
        "url": "/system/field-definitions",
        "group_code": "system",
        "item_order": 20,
        "icon": "List",
    },
    {
        "code": "PageLayoutList",
        "translation_key": "menu.routes.pageLayouts",
        "url": "/system/page-layouts",
        "group_code": "system",
        "item_order": 30,
        "icon": "Files",
    },
    {
        "code": "LanguageList",
        "translation_key": "menu.routes.languages",
        "url": "/system/languages",
        "group_code": "system",
        "item_order": 40,
        "icon": "ChatDotRound",
    },
    {
        "code": "TranslationList",
        "translation_key": "menu.routes.translations",
        "url": "/system/translations",
        "group_code": "system",
        "item_order": 50,
        "icon": "DocumentCopy",
    },
    {
        "code": "BusinessRuleList",
        "translation_key": "menu.routes.businessRules",
        "url": "/system/business-rules",
        "group_code": "system",
        "item_order": 60,
        "icon": "Connection",
    },
    {
        "code": "ConfigPackageList",
        "translation_key": "menu.routes.configPackages",
        "url": "/system/config-packages",
        "group_code": "system",
        "item_order": 70,
        "icon": "Box",
    },
    {
        "code": "DictionaryTypeList",
        "translation_key": "menu.routes.dictionaryTypes",
        "url": "/system/dictionary-types",
        "group_code": "system",
        "item_order": 80,
        "icon": "Collection",
    },
    {
        "code": "SequenceRuleList",
        "translation_key": "menu.routes.sequenceRules",
        "url": "/system/sequence-rules",
        "group_code": "system",
        "item_order": 90,
        "icon": "Sort",
    },
    {
        "code": "SystemConfigList",
        "translation_key": "menu.routes.systemConfig",
        "url": "/system/config",
        "group_code": "system",
        "item_order": 100,
        "icon": "Tools",
    },
    {
        "code": "SystemFileList",
        "translation_key": "menu.routes.systemFiles",
        "url": "/system/files",
        "group_code": "system",
        "item_order": 110,
        "icon": "FolderOpened",
    },
    {
        "code": "ModuleWorkbench",
        "translation_key": "menu.routes.moduleWorkbench",
        "url": "/system/module-workbench",
        "group_code": "system",
        "item_order": 120,
        "icon": "Operation",
    },
    {
        "code": "SSOConfigPage",
        "translation_key": "menu.routes.ssoConfig",
        "url": "/system/sso",
        "group_code": "system",
        "item_order": 130,
        "icon": "Key",
    },
    {
        "code": "OrganizationTree",
        "translation_key": "menu.routes.organizationTree",
        "url": "/system/organization-tree",
        "group_code": "system",
        "item_order": 140,
        "icon": "Share",
    },
    {
        "code": "IntegrationConfigList",
        "translation_key": "menu.routes.integrationConfigs",
        "url": "/integration/configs",
        "group_code": "system",
        "item_order": 150,
        "icon": "Link",
    },
    {
        "code": "ReportCenter",
        "translation_key": "menu.routes.reportCenter",
        "url": "/reports/center",
        "group_code": "reports",
        "item_order": 10,
        "icon": "DataAnalysis",
    },
]


def get_menu_group_definition(group_code: str) -> Dict[str, Any]:
    return MENU_GROUPS.get(group_code, MENU_GROUPS["other"])


def get_object_translation_key(object_code: str) -> str:
    mapped = OBJECT_ROUTE_KEY_MAP.get(object_code, object_code)
    return f"menu.routes.{mapped}"


def _infer_group_code(object_code: str, old_config: Optional[MenuConfig] = None) -> str:
    legacy_group_code = str((old_config or {}).get("group_code") or "").strip()
    if legacy_group_code in MENU_GROUPS:
        return legacy_group_code

    normalized = str(object_code or "").lower()

    if normalized.startswith("workflow"):
        return "workflow"
    if "inventory" in normalized:
        return "inventory"
    if "consumable" in normalized:
        return "consumable"
    if any(token in normalized for token in ("purchase", "receipt", "maintenance", "disposal")):
        return "lifecycle"
    if any(token in normalized for token in ("organization", "department", "user", "role")):
        return "organization"
    if any(token in normalized for token in ("asset", "location", "supplier")):
        return "asset_master"
    if any(
        token in normalized
        for token in (
            "finance",
            "voucher",
            "depreciation",
            "insurance",
            "policy",
            "premium",
            "claim",
            "lease",
            "rent",
            "software",
            "license",
        )
    ):
        return "finance"

    return "other"


def _infer_icon(object_code: str, group_code: str) -> str:
    normalized = str(object_code or "").lower()

    if group_code == "asset_operation":
        if "pickup" in normalized:
            return "Upload"
        if "transfer" in normalized:
            return "Switch"
        if "return" in normalized:
            return "Download"
        if "loan" in normalized:
            return "Connection"
        return "Operation"

    if group_code == "lifecycle":
        if "purchase" in normalized:
            return "ShoppingCart"
        if "receipt" in normalized:
            return "Box"
        if "plan" in normalized:
            return "Calendar"
        if "task" in normalized:
            return "List"
        if "maintenance" in normalized:
            return "Tools"
        if "disposal" in normalized:
            return "Delete"

    return get_menu_group_definition(group_code)["icon"] or "Document"


def build_menu_config_for_object(object_code: str, old_config: Optional[MenuConfig] = None) -> MenuConfig:
    existing = old_config or {}
    explicit = DEFAULT_OBJECT_MENU_RULES.get(object_code, {})
    group_code = explicit.get("group_code") or _infer_group_code(object_code, existing)
    group = get_menu_group_definition(group_code)
    inferred_icon = _infer_icon(object_code, group_code)

    show_in_menu = explicit.get("show_in_menu")
    if show_in_menu is None:
        show_in_menu = bool(existing.get("show_in_menu", True))

    item_order = explicit.get("item_order")
    if item_order is None:
        item_order = int(existing.get("item_order") or 999)

    menu_config: MenuConfig = {
        "show_in_menu": show_in_menu,
        "group_code": group_code,
        "group_translation_key": group["translation_key"],
        "group_order": int(group["order"]),
        "group_icon": group["icon"],
        "item_order": int(item_order),
        "icon": explicit.get("icon") or existing.get("icon") or inferred_icon or "Document",
        "translation_key": explicit.get("translation_key")
        or existing.get("translation_key")
        or get_object_translation_key(object_code),
    }

    if explicit.get("url"):
        menu_config["url"] = explicit["url"]
    elif existing.get("url"):
        menu_config["url"] = existing["url"]

    if existing.get("badge") is not None:
        menu_config["badge"] = existing["badge"]

    return menu_config


def sync_business_object_menu_configs(
    queryset: Optional[Iterable[BusinessObject]] = None,
) -> Dict[str, Any]:
    if queryset is None:
        queryset = BusinessObject.objects.filter(is_deleted=False).order_by("code")
    objects = list(queryset)
    updated_codes: List[str] = []
    unchanged_codes: List[str] = []

    for obj in objects:
        new_config = build_menu_config_for_object(obj.code, obj.menu_config or {})
        if (obj.menu_config or {}) == new_config:
            unchanged_codes.append(obj.code)
            continue

        obj.menu_config = new_config
        obj.save(update_fields=["menu_config"])
        updated_codes.append(obj.code)

    return {
        "total": len(objects),
        "updated": updated_codes,
        "unchanged": unchanged_codes,
    }
