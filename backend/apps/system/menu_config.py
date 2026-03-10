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

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional

from apps.system.models import BusinessObject, MenuEntry, MenuGroup


MenuConfig = Dict[str, Any]
MenuManagementSettings = Dict[str, Any]


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
        "code": "MenuManagement",
        "translation_key": "menu.routes.menuManagement",
        "url": "/system/menu-management",
        "group_code": "system",
        "item_order": 102,
        "icon": "Grid",
    },
    {
        "code": "SystemBranding",
        "translation_key": "menu.routes.systemBranding",
        "url": "/system/branding",
        "group_code": "system",
        "item_order": 105,
        "icon": "Brush",
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


def get_menu_item_identity(source_type: str, code: str) -> str:
    return f"{source_type}:{code}"


def is_default_business_object(code: str, is_hardcoded: bool = False) -> bool:
    return bool(is_hardcoded or code in DEFAULT_OBJECT_MENU_RULES)


def _humanize_group_code(code: str) -> str:
    return str(code or "").replace("_", " ").strip().title() or "Other"


def _get_default_group_definitions() -> Dict[str, Dict[str, Any]]:
    return {
        code: {
            "code": code,
            "name": _humanize_group_code(code),
            "translation_key": group["translation_key"],
            "order": int(group["order"]),
            "icon": group["icon"],
            "is_visible": True,
            "is_default": True,
            "is_locked": False,
        }
        for code, group in MENU_GROUPS.items()
    }


def _normalize_route_path(value: Optional[str], fallback: str) -> str:
    path = str(value or fallback or "").strip()
    if not path:
        return fallback
    if path.startswith("/"):
        return path
    return f"/{path.lstrip('/')}"


def sync_menu_registry_models() -> Dict[str, Any]:
    default_groups = _get_default_group_definitions()
    groups_by_code: Dict[str, MenuGroup] = {}
    created_groups: List[str] = []
    created_entries: List[str] = []
    updated_entries: List[str] = []

    def ensure_group(code: str) -> MenuGroup:
        spec = default_groups.get(code, {})
        group = groups_by_code.get(code)
        if group is None:
            group = MenuGroup.all_objects.filter(code=code).first()
        created = group is None
        if group is None:
            group = MenuGroup(
                code=code,
                name=str(spec.get("name") or _humanize_group_code(code)),
                translation_key=str(spec.get("translation_key") or ""),
                icon=str(spec.get("icon") or "Menu"),
                sort_order=int(spec.get("order") or 999),
                is_visible=bool(spec.get("is_visible", True)),
                is_locked=False,
                is_system=code in default_groups,
            )
            group.save()
        changed_fields: List[str] = []
        if group.is_deleted:
            group.is_deleted = False
            group.deleted_at = None
            group.deleted_by = None
            changed_fields.extend(["is_deleted", "deleted_at", "deleted_by"])
        desired_translation_key = str(spec.get("translation_key") or "")
        if group.translation_key != desired_translation_key:
            group.translation_key = desired_translation_key
            changed_fields.append("translation_key")
        if group.is_locked:
            group.is_locked = False
            changed_fields.append("is_locked")
        desired_is_system = code in default_groups
        if group.is_system != desired_is_system:
            group.is_system = desired_is_system
            changed_fields.append("is_system")
        desired_name = str(spec.get("name") or _humanize_group_code(code))
        if not group.name or group.name == desired_translation_key or group.name.startswith("menu."):
            group.name = desired_name
            changed_fields.append("name")
        if created:
            created_groups.append(code)
        elif changed_fields:
            group.save(update_fields=changed_fields)
        groups_by_code[code] = group
        return group

    existing_groups = MenuGroup.all_objects.all()
    groups_by_code.update({group.code: group for group in existing_groups})
    ensure_group("other")

    for item in deepcopy(STATIC_MENU_ITEMS):
        default_group = ensure_group(item["group_code"])
        entry = MenuEntry.all_objects.filter(source_type="static", source_code=item["code"]).first()
        created = entry is None
        if entry is None:
            entry = MenuEntry(
                source_type="static",
                source_code=item["code"],
                code=item["code"],
                name=item["code"],
                name_en=item["code"],
                translation_key=item["translation_key"],
                route_path=item["url"],
                icon=item["icon"],
                sort_order=int(item["item_order"]),
                is_visible=True,
                is_locked=False,
                is_system=True,
                menu_group=default_group,
            )
            entry.save()
        changed_fields: List[str] = []
        if entry.is_deleted:
            entry.is_deleted = False
            entry.deleted_at = None
            entry.deleted_by = None
            changed_fields.extend(["is_deleted", "deleted_at", "deleted_by"])
        desired_path = _normalize_route_path(item["url"], item["url"])
        if entry.code != item["code"]:
            entry.code = item["code"]
            changed_fields.append("code")
        if entry.name != item["code"]:
            entry.name = item["code"]
            changed_fields.append("name")
        if entry.name_en != item["code"]:
            entry.name_en = item["code"]
            changed_fields.append("name_en")
        if entry.translation_key != item["translation_key"]:
            entry.translation_key = item["translation_key"]
            changed_fields.append("translation_key")
        if entry.route_path != desired_path:
            entry.route_path = desired_path
            changed_fields.append("route_path")
        if entry.icon != item["icon"]:
            entry.icon = item["icon"]
            changed_fields.append("icon")
        if entry.is_locked:
            entry.is_locked = False
            changed_fields.append("is_locked")
        if entry.is_system is not True:
            entry.is_system = True
            changed_fields.append("is_system")
        if entry.menu_group_id is None or getattr(entry.menu_group, "is_deleted", False):
            entry.menu_group = default_group
            changed_fields.append("menu_group")
        if created:
            created_entries.append(entry.code)
        elif changed_fields:
            entry.save(update_fields=changed_fields)

    object_entries = {
        entry.source_code: entry
        for entry in MenuEntry.all_objects.filter(source_type="business_object").select_related("menu_group")
    }
    active_object_codes: set[str] = set()
    seed_group_definitions = _get_default_group_definitions()

    for obj in BusinessObject.objects.filter(is_deleted=False).order_by("code"):
        active_object_codes.add(obj.code)
        legacy_menu = build_menu_config_for_object(
            obj.code,
            obj.menu_config or {},
            group_definitions=seed_group_definitions,
        )
        group_code = str(legacy_menu.get("group_code") or "other")
        group = ensure_group(group_code)
        entry = object_entries.get(obj.code)
        if entry is None:
            entry = MenuEntry.objects.create(
                source_type="business_object",
                source_code=obj.code,
                code=obj.code,
                name=obj.name,
                name_en=obj.name_en or "",
                translation_key=str(legacy_menu.get("translation_key") or get_object_translation_key(obj.code)),
                route_path=_normalize_route_path(legacy_menu.get("url"), f"/objects/{obj.code}"),
                icon=str(legacy_menu.get("icon") or "Document"),
                sort_order=int(legacy_menu.get("item_order") or 999),
                is_visible=bool(legacy_menu.get("show_in_menu", True)),
                is_locked=is_default_business_object(obj.code, obj.is_hardcoded),
                is_system=is_default_business_object(obj.code, obj.is_hardcoded),
                menu_group=group,
                business_object=obj,
            )
            created_entries.append(entry.code)
            continue

        changed_fields: List[str] = []
        if entry.is_deleted:
            entry.is_deleted = False
            entry.deleted_at = None
            entry.deleted_by = None
            changed_fields.extend(["is_deleted", "deleted_at", "deleted_by"])
        if entry.code != obj.code:
            entry.code = obj.code
            changed_fields.append("code")
        if entry.name != obj.name:
            entry.name = obj.name
            changed_fields.append("name")
        desired_name_en = obj.name_en or ""
        if entry.name_en != desired_name_en:
            entry.name_en = desired_name_en
            changed_fields.append("name_en")
        desired_translation_key = str(legacy_menu.get("translation_key") or get_object_translation_key(obj.code))
        if entry.translation_key != desired_translation_key:
            entry.translation_key = desired_translation_key
            changed_fields.append("translation_key")
        if entry.business_object_id != obj.id:
            entry.business_object = obj
            changed_fields.append("business_object")
        desired_locked = is_default_business_object(obj.code, obj.is_hardcoded)
        if entry.is_locked != desired_locked:
            entry.is_locked = desired_locked
            changed_fields.append("is_locked")
        if entry.is_system != desired_locked:
            entry.is_system = desired_locked
            changed_fields.append("is_system")
        if entry.menu_group_id is None or getattr(entry.menu_group, "is_deleted", False):
            entry.menu_group = group
            changed_fields.append("menu_group")
        if changed_fields:
            entry.save(update_fields=changed_fields)
            updated_entries.append(entry.code)

    for source_code, entry in object_entries.items():
        if source_code in active_object_codes:
            continue
        if not entry.is_deleted:
            entry.soft_delete()

    return {
        "created_groups": created_groups,
        "created_entries": created_entries,
        "updated_entries": updated_entries,
    }


def get_menu_group_definitions(settings: Optional[MenuManagementSettings] = None) -> Dict[str, Dict[str, Any]]:
    sync_menu_registry_models()
    definitions: Dict[str, Dict[str, Any]] = {}
    for group in MenuGroup.objects.filter(is_deleted=False).order_by("sort_order", "code"):
        definitions[group.code] = {
            "code": group.code,
            "name": group.name,
            "translation_key": group.translation_key,
            "order": int(group.sort_order),
            "icon": group.icon,
            "is_visible": bool(group.is_visible),
            "is_default": bool(group.is_system),
            "is_locked": bool(group.is_locked),
        }
    if "other" not in definitions:
        definitions["other"] = _get_default_group_definitions()["other"]
    return definitions


def get_menu_group_definition(
    group_code: str,
    group_definitions: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    definitions = group_definitions or get_menu_group_definitions()
    return definitions.get(group_code, definitions.get("other", _get_default_group_definitions()["other"]))


def get_static_menu_items(settings: Optional[MenuManagementSettings] = None) -> List[Dict[str, Any]]:
    sync_menu_registry_models()
    items: List[Dict[str, Any]] = []
    for entry in (
        MenuEntry.objects
        .filter(source_type="static", is_deleted=False)
        .select_related("menu_group")
        .order_by("menu_group__sort_order", "sort_order", "code")
    ):
        items.append({
            "code": entry.code,
            "translation_key": entry.translation_key,
            "url": entry.route_path,
            "group_code": entry.menu_group.code,
            "item_order": int(entry.sort_order),
            "icon": entry.icon,
            "show_in_menu": bool(entry.is_visible),
        })
    return items


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

    return _get_default_group_definitions().get(group_code, _get_default_group_definitions()["other"])["icon"] or "Document"


def build_menu_config_for_object(
    object_code: str,
    old_config: Optional[MenuConfig] = None,
    group_definitions: Optional[Dict[str, Dict[str, Any]]] = None,
) -> MenuConfig:
    existing = old_config or {}
    explicit = DEFAULT_OBJECT_MENU_RULES.get(object_code, {})
    group_code = explicit.get("group_code") or _infer_group_code(object_code, existing)
    group = (group_definitions or _get_default_group_definitions()).get(
        group_code,
        (group_definitions or _get_default_group_definitions()).get("other", _get_default_group_definitions()["other"]),
    )
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
    group_definitions = get_menu_group_definitions()
    updated_codes: List[str] = []
    unchanged_codes: List[str] = []

    for obj in objects:
        new_config = build_menu_config_for_object(
            obj.code,
            obj.menu_config or {},
            group_definitions=group_definitions,
        )
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
