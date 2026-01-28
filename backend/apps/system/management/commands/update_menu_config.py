"""
Update BusinessObject menu_config to make all objects visible in menu.

This command sets show_in_menu=True for all business objects with appropriate
group configurations so they appear in the frontend menu.
"""
from django.core.management.base import BaseCommand

from apps.system.models import BusinessObject


class Command(BaseCommand):
    help = 'Update menu_config for all BusinessObjects to make them visible in menu'

    # Define menu groups with order and icon
    MENU_GROUPS = {
        'dashboard': {'name': '工作台', 'order': 1, 'icon': 'Odometer'},
        'asset': {'name': '资产管理', 'order': 10, 'icon': 'FolderOpened'},
        'asset_operation': {'name': '资产作业', 'order': 20, 'icon': 'Operation'},
        'consumable': {'name': '耗材管理', 'order': 30, 'icon': 'Box'},
        'purchase': {'name': '采购管理', 'order': 40, 'icon': 'ShoppingCart'},
        'maintenance': {'name': '维保管理', 'order': 50, 'icon': 'Tools'},
        'inventory': {'name': '盘点管理', 'order': 60, 'icon': 'Document'},
        'organization': {'name': '组织管理', 'order': 70, 'icon': 'OfficeBuilding'},
        'system': {'name': '系统管理', 'order': 100, 'icon': 'Setting'},
        'workflow': {'name': '流程管理', 'order': 90, 'icon': 'Connection'},
    }

    # Object to menu group mapping
    OBJECT_MENU_CONFIG = {
        # Dashboard
        'Dashboard': {'group': 'dashboard', 'order': 1, 'icon': 'DataLine'},

        # Asset Management
        'Asset': {'group': 'asset', 'order': 1, 'icon': 'Document'},
        'AssetCategory': {'group': 'asset', 'order': 2, 'icon': 'Folder'},
        'Location': {'group': 'asset', 'order': 3, 'icon': 'Location'},
        'Supplier': {'group': 'asset', 'order': 4, 'icon': 'Supplier'},
        'AssetStatusLog': {'group': 'asset', 'order': 5, 'icon': 'Clock'},

        # Asset Operations
        'AssetPickup': {'group': 'asset_operation', 'order': 1, 'icon': 'Upload'},
        'AssetTransfer': {'group': 'asset_operation', 'order': 2, 'icon': 'Switch'},
        'AssetReturn': {'group': 'asset_operation', 'order': 3, 'icon': 'Download'},
        'AssetLoan': {'group': 'asset_operation', 'order': 4, 'icon': 'Borrow'},

        # Consumable Management
        'Consumable': {'group': 'consumable', 'order': 1, 'icon': 'Box'},
        'ConsumableCategory': {'group': 'consumable', 'order': 2, 'icon': 'Folder'},
        'ConsumableStock': {'group': 'consumable', 'order': 3, 'icon': 'Goods'},
        'ConsumablePurchase': {'group': 'consumable', 'order': 4, 'icon': 'ShoppingCart'},
        'ConsumableIssue': {'group': 'consumable', 'order': 5, 'icon': 'Sell'},

        # Purchase Management
        'PurchaseRequest': {'group': 'purchase', 'order': 1, 'icon': 'Document'},
        'AssetReceipt': {'group': 'purchase', 'order': 2, 'icon': 'Inbox'},

        # Maintenance Management
        'Maintenance': {'group': 'maintenance', 'order': 1, 'icon': 'Tools'},
        'MaintenancePlan': {'group': 'maintenance', 'order': 2, 'icon': 'Calendar'},
        'DisposalRequest': {'group': 'maintenance', 'order': 3, 'icon': 'Delete'},

        # Inventory Management
        'InventoryTask': {'group': 'inventory', 'order': 1, 'icon': 'Clipboard'},
        'InventorySnapshot': {'group': 'inventory', 'order': 2, 'icon': 'Camera'},

        # Organization Management
        'Organization': {'group': 'organization', 'order': 1, 'icon': 'OfficeBuilding'},
        'Department': {'group': 'organization', 'order': 2, 'icon': 'Guide'},

        # System Management
        'User': {'group': 'system', 'order': 1, 'icon': 'User'},

        # Workflow Management
        'WorkflowDefinition': {'group': 'workflow', 'order': 1, 'icon': 'Connection'},
        'WorkflowInstance': {'group': 'workflow', 'order': 2, 'icon': 'List'},
    }

    def handle(self, *args, **options):
        """Update menu_config for all BusinessObjects."""
        # BusinessObject uses GlobalMetadataManager (is_deleted filter handled automatically)
        queryset = BusinessObject.objects.all()
        total = queryset.count()
        updated = 0

        self.stdout.write(f'Found {total} BusinessObjects')

        for obj in queryset:
            code = obj.code
            config = self.OBJECT_MENU_CONFIG.get(code)

            if not config:
                self.stdout.write(f'  ⚠️  No config for {code}, skipping')
                continue

            group_info = self.MENU_GROUPS.get(config['group'])

            if not group_info:
                self.stdout.write(f'  ⚠️  No group info for {config["group"]}, skipping')
                continue

            # Build menu_config
            menu_config = {
                'show_in_menu': True,
                'group': group_info['name'],
                'group_order': group_info['order'],
                'group_icon': group_info['icon'],
                'item_order': config['order'],
                'icon': config['icon'],
            }

            # Update the object
            old_config = obj.menu_config or {}
            obj.menu_config = menu_config
            obj.save(update_fields=['menu_config'])
            updated += 1

            self.stdout.write(
                f'  ✅ {code:30s} -> {group_info["name"]:15s} (order: {config["order"]})'
            )

        self.stdout.write(f'\n✅ Updated {updated}/{total} BusinessObjects')

        # Show summary
        self.stdout.write('\n📊 Menu Groups Summary:')
        for group_key, group_info in self.MENU_GROUPS.items():
            count = queryset.filter(
                is_deleted=False,
                menu_config__group=group_info['name']
            ).count()
            if count > 0:
                self.stdout.write(f'  {group_info["name"]:15s}: {count} objects')
