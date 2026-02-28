"""
Update BusinessObject.menu_config for dynamic frontend menu rendering.

This command makes sure every business object has a stable menu configuration,
including legacy modules that were migrated to object-router endpoints.
"""
from django.core.management.base import BaseCommand

from apps.system.models import BusinessObject


class Command(BaseCommand):
    help = "Synchronize menu_config for all BusinessObjects"

    MENU_GROUPS = {
        "dashboard": {"name": "Dashboard", "order": 1, "icon": "Odometer"},
        "asset": {"name": "Asset Management", "order": 10, "icon": "FolderOpened"},
        "asset_operation": {"name": "Asset Operations", "order": 20, "icon": "Operation"},
        "consumable": {"name": "Consumables", "order": 30, "icon": "Box"},
        "purchase": {"name": "Procurement", "order": 40, "icon": "ShoppingCart"},
        "maintenance": {"name": "Maintenance", "order": 50, "icon": "Tools"},
        "inventory": {"name": "Inventory", "order": 60, "icon": "Document"},
        "organization": {"name": "Organization", "order": 70, "icon": "OfficeBuilding"},
        "finance": {"name": "Finance", "order": 80, "icon": "Wallet"},
        "workflow": {"name": "Workflow Management", "order": 90, "icon": "Connection"},
        "system": {"name": "System", "order": 100, "icon": "Setting"},
        "other": {"name": "Other", "order": 999, "icon": "More"},
    }

    OBJECT_MENU_CONFIG = {
        # Dashboard
        "Dashboard": {"group": "dashboard", "order": 1, "icon": "DataLine"},

        # Asset Management
        "Asset": {"group": "asset", "order": 1, "icon": "Document"},
        "AssetCategory": {"group": "asset", "order": 2, "icon": "Folder"},
        "Location": {"group": "asset", "order": 3, "icon": "Location"},
        "Supplier": {"group": "asset", "order": 4, "icon": "Van"},
        "AssetStatusLog": {"group": "asset", "order": 5, "icon": "Clock"},
        "ITAsset": {"group": "asset", "order": 20, "icon": "Monitor"},
        "InsuredAsset": {"group": "asset", "order": 21, "icon": "DocumentChecked"},

        # Asset Operations
        "AssetPickup": {"group": "asset_operation", "order": 1, "icon": "Upload"},
        "AssetTransfer": {"group": "asset_operation", "order": 2, "icon": "Switch"},
        "AssetReturn": {"group": "asset_operation", "order": 3, "icon": "Download"},
        "AssetLoan": {"group": "asset_operation", "order": 4, "icon": "Connection"},

        # Consumable Management
        "Consumable": {"group": "consumable", "order": 1, "icon": "Box"},
        "ConsumableCategory": {"group": "consumable", "order": 2, "icon": "Folder"},
        "ConsumableStock": {"group": "consumable", "order": 3, "icon": "Goods"},
        "ConsumablePurchase": {"group": "consumable", "order": 4, "icon": "ShoppingCart"},
        "ConsumableIssue": {"group": "consumable", "order": 5, "icon": "Sell"},

        # Purchase Management
        "PurchaseRequest": {"group": "purchase", "order": 1, "icon": "Document"},
        "AssetReceipt": {"group": "purchase", "order": 2, "icon": "Inbox"},

        # Maintenance Management
        "Maintenance": {"group": "maintenance", "order": 1, "icon": "Tools"},
        "MaintenanceTask": {"group": "maintenance", "order": 2, "icon": "List"},
        "MaintenancePlan": {"group": "maintenance", "order": 3, "icon": "Calendar"},
        "ITMaintenanceRecord": {"group": "maintenance", "order": 4, "icon": "Setting"},
        "DisposalRequest": {"group": "maintenance", "order": 5, "icon": "Delete"},

        # Inventory Management
        "InventoryTask": {"group": "inventory", "order": 1, "icon": "Clipboard"},
        "InventorySnapshot": {"group": "inventory", "order": 2, "icon": "Camera"},
        "InventoryItem": {"group": "inventory", "order": 3, "icon": "Document"},

        # Organization Management
        "Organization": {"group": "organization", "order": 1, "icon": "OfficeBuilding"},
        "Department": {"group": "organization", "order": 2, "icon": "Guide"},

        # Finance / Depreciation / Insurance / Leasing / Software
        "FinanceVoucher": {"group": "finance", "order": 1, "icon": "Tickets"},
        "VoucherTemplate": {"group": "finance", "order": 2, "icon": "Files"},
        "DepreciationConfig": {"group": "finance", "order": 3, "icon": "Setting"},
        "DepreciationRun": {"group": "finance", "order": 4, "icon": "VideoPlay"},
        "DepreciationRecord": {"group": "finance", "order": 5, "icon": "Histogram"},
        "InsuranceCompany": {"group": "finance", "order": 10, "icon": "OfficeBuilding"},
        "InsurancePolicy": {"group": "finance", "order": 11, "icon": "Document"},
        "PolicyRenewal": {"group": "finance", "order": 12, "icon": "Refresh"},
        "PremiumPayment": {"group": "finance", "order": 13, "icon": "Wallet"},
        "ClaimRecord": {"group": "finance", "order": 14, "icon": "Warning"},
        "LeasingContract": {"group": "finance", "order": 20, "icon": "Files"},
        "LeaseItem": {"group": "finance", "order": 21, "icon": "List"},
        "LeaseExtension": {"group": "finance", "order": 22, "icon": "Clock"},
        "LeaseReturn": {"group": "finance", "order": 23, "icon": "Back"},
        "RentPayment": {"group": "finance", "order": 24, "icon": "Wallet"},
        "Software": {"group": "finance", "order": 30, "icon": "Monitor"},
        "SoftwareLicense": {"group": "finance", "order": 31, "icon": "Key"},
        "LicenseAllocation": {"group": "finance", "order": 32, "icon": "Share"},
        "ITSoftware": {"group": "finance", "order": 33, "icon": "Monitor"},
        "ITSoftwareLicense": {"group": "finance", "order": 34, "icon": "Key"},
        "ITLicenseAllocation": {"group": "finance", "order": 35, "icon": "Share"},

        # System Management
        "User": {"group": "system", "order": 1, "icon": "User"},
        "ConfigurationChange": {"group": "system", "order": 2, "icon": "Edit"},

        # Workflow Management
        "WorkflowDefinition": {"group": "workflow", "order": 1, "icon": "Connection"},
        "WorkflowInstance": {"group": "workflow", "order": 2, "icon": "List"},
    }

    def _infer_config(self, code: str) -> dict:
        normalized = (code or "").lower()

        if normalized.startswith("workflow"):
            return {"group": "workflow", "order": 900, "icon": "Connection"}
        if "inventory" in normalized:
            return {"group": "inventory", "order": 900, "icon": "Document"}
        if "consumable" in normalized:
            return {"group": "consumable", "order": 900, "icon": "Box"}
        if "maintenance" in normalized:
            return {"group": "maintenance", "order": 900, "icon": "Tools"}
        if any(token in normalized for token in ("organization", "department")):
            return {"group": "organization", "order": 900, "icon": "OfficeBuilding"}
        if any(token in normalized for token in ("asset", "location", "supplier")):
            return {"group": "asset", "order": 900, "icon": "Document"}
        if any(token in normalized for token in (
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
        )):
            return {"group": "finance", "order": 900, "icon": "Wallet"}

        return {"group": "other", "order": 999, "icon": "Document"}

    def handle(self, *args, **options):
        queryset = BusinessObject.objects.filter(is_deleted=False).order_by("code")
        total = queryset.count()
        updated = 0
        unchanged = 0

        self.stdout.write(f"Found {total} BusinessObjects")

        for obj in queryset:
            config = self.OBJECT_MENU_CONFIG.get(obj.code, self._infer_config(obj.code))
            group_code = config["group"]
            group_info = self.MENU_GROUPS.get(group_code, self.MENU_GROUPS["other"])
            old_config = obj.menu_config or {}

            menu_config = {
                "show_in_menu": True,
                "group": group_info["name"],
                "group_code": group_code,
                "group_order": group_info["order"],
                "group_icon": group_info["icon"],
                "item_order": int(config.get("order", 999)),
                "icon": config.get("icon", "Document"),
            }

            # Keep existing custom URL/badge if present.
            if old_config.get("url"):
                menu_config["url"] = old_config["url"]
            if old_config.get("badge"):
                menu_config["badge"] = old_config["badge"]

            if old_config == menu_config:
                unchanged += 1
                continue

            obj.menu_config = menu_config
            obj.save(update_fields=["menu_config"])
            updated += 1
            self.stdout.write(
                f"  UPDATED {obj.code:30s} -> {group_info['name']} ({menu_config['item_order']})"
            )

        self.stdout.write(f"\nDone. updated={updated}, unchanged={unchanged}, total={total}")

        self.stdout.write("\nMenu groups summary:")
        for group in sorted(self.MENU_GROUPS.values(), key=lambda item: item["order"]):
            count = queryset.filter(menu_config__group=group["name"]).count()
            if count:
                self.stdout.write(f"  {group['name']:20s} {count}")
