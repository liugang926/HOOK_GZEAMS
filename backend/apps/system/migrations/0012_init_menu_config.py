# Generated manually for dynamic menu system

from django.db import migrations


def init_menu_config(apps, schema_editor):
    """Initialize menu_config for existing business objects."""
    BusinessObject = apps.get_model('system', 'BusinessObject')

    # Define menu configurations for common business objects
    menu_configs = {
        # Asset Management Group (order: 10)
        'Asset': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 1,
            'icon': 'Document',
            'group_icon': 'FolderOpened'
        },
        'AssetPickup': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 2,
            'icon': 'Upload',
            'group_icon': 'FolderOpened'
        },
        'AssetTransfer': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 3,
            'icon': 'Switch',
            'group_icon': 'FolderOpened'
        },
        'AssetReturn': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 4,
            'icon': 'Download',
            'group_icon': 'FolderOpened'
        },
        'AssetLoan': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 5,
            'icon': 'Pointer',
            'group_icon': 'FolderOpened'
        },
        'AssetCategory': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 6,
            'icon': 'Folder',
            'group_icon': 'FolderOpened'
        },
        'Supplier': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 7,
            'icon': 'OfficeBuilding',
            'group_icon': 'FolderOpened'
        },
        'Location': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 8,
            'icon': 'Place',
            'group_icon': 'FolderOpened'
        },
        'AssetStatusLog': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 9,
            'icon': 'Notebook',
            'group_icon': 'FolderOpened'
        },

        # Inventory Management Group (order: 20)
        'InventoryTask': {
            'show_in_menu': True,
            'group': '库存管理',
            'group_order': 20,
            'item_order': 1,
            'icon': 'List',
            'group_icon': 'Goods'
        },
        'InventorySnapshot': {
            'show_in_menu': False,  # Usually accessed via InventoryTask
            'group': '库存管理',
            'group_order': 20,
            'item_order': 2,
            'icon': 'Camera',
            'group_icon': 'Goods'
        },

        # Consumable Management Group (order: 30)
        'Consumable': {
            'show_in_menu': True,
            'group': '耗材管理',
            'group_order': 30,
            'item_order': 1,
            'icon': 'Box',
            'group_icon': 'Box'
        },
        'ConsumableCategory': {
            'show_in_menu': True,
            'group': '耗材管理',
            'group_order': 30,
            'item_order': 2,
            'icon': 'FolderOpened',
            'group_icon': 'Box'
        },
        'ConsumableStock': {
            'show_in_menu': True,
            'group': '耗材管理',
            'group_order': 30,
            'item_order': 3,
            'icon': 'Goods',
            'group_icon': 'Box'
        },
        'ConsumablePurchase': {
            'show_in_menu': True,
            'group': '耗材管理',
            'group_order': 30,
            'item_order': 4,
            'icon': 'ShoppingCart',
            'group_icon': 'Box'
        },
        'ConsumableIssue': {
            'show_in_menu': True,
            'group': '耗材管理',
            'group_order': 30,
            'item_order': 5,
            'icon': 'Sell',
            'group_icon': 'Box'
        },

        # Maintenance Management Group (order: 40)
        'Maintenance': {
            'show_in_menu': True,
            'group': '维护管理',
            'group_order': 40,
            'item_order': 1,
            'icon': 'Tools',
            'group_icon': 'Tools'
        },
        'MaintenancePlan': {
            'show_in_menu': True,
            'group': '维护管理',
            'group_order': 40,
            'item_order': 2,
            'icon': 'Calendar',
            'group_icon': 'Tools'
        },

        # Finance Management Group (order: 50)
        'PurchaseRequest': {
            'show_in_menu': True,
            'group': '财务管理',
            'group_order': 50,
            'item_order': 1,
            'icon': 'Wallet',
            'group_icon': 'Wallet'
        },
        'AssetReceipt': {
            'show_in_menu': True,
            'group': '财务管理',
            'group_order': 50,
            'item_order': 2,
            'icon': 'Tickets',
            'group_icon': 'Wallet'
        },
        'DisposalRequest': {
            'show_in_menu': True,
            'group': '财务管理',
            'group_order': 50,
            'item_order': 3,
            'icon': 'DeleteFilled',
            'group_icon': 'Wallet'
        },

        # System Management Group (order: 100)
        'Department': {
            'show_in_menu': True,
            'group': '系统管理',
            'group_order': 100,
            'item_order': 1,
            'icon': 'OfficeBuilding',
            'group_icon': 'Setting'
        },
        'User': {
            'show_in_menu': False,  # Usually managed via admin panel
            'group': '系统管理',
            'group_order': 100,
            'item_order': 2,
            'icon': 'User',
            'group_icon': 'Setting'
        },
        'Organization': {
            'show_in_menu': False,  # Usually managed via admin panel
            'group': '系统管理',
            'group_order': 100,
            'item_order': 3,
            'icon': 'OfficeBuilding',
            'group_icon': 'Setting'
        },

        # Workflow Management Group (order: 90)
        'WorkflowDefinition': {
            'show_in_menu': False,  # Usually managed via admin panel
            'group': '工作流管理',
            'group_order': 90,
            'item_order': 1,
            'icon': 'Connection',
            'group_icon': 'Connection'
        },
        'WorkflowInstance': {
            'show_in_menu': False,  # Usually accessed via task center
            'group': '工作流管理',
            'group_order': 90,
            'item_order': 2,
            'icon': 'CircleCheck',
            'group_icon': 'Connection'
        },
    }

    # Update menu_config for existing business objects
    for obj in BusinessObject.objects.filter(is_deleted=False):
        if obj.code in menu_configs:
            obj.menu_config = menu_configs[obj.code]
            obj.save(update_fields=['menu_config'])


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0011_menu_config'),
    ]

    operations = [
        migrations.RunPython(init_menu_config, migrations.RunPython.noop),
    ]
