# Generated manually for complete menu configuration

from django.db import migrations


def init_complete_menu_config(apps, schema_editor):
    """Initialize complete menu configuration for all business objects."""
    BusinessObject = apps.get_model('system', 'BusinessObject')

    # Complete menu configuration for all business objects
    menu_configs = {
        # ============================================================
        # ASSET MANAGEMENT GROUP (资产管理) - order: 10
        # ============================================================
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
            'item_order': 10,
            'icon': 'Folder',
            'group_icon': 'FolderOpened'
        },
        'Supplier': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 11,
            'icon': 'OfficeBuilding',
            'group_icon': 'FolderOpened'
        },
        'Location': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 12,
            'icon': 'Place',
            'group_icon': 'FolderOpened'
        },
        'AssetStatusLog': {
            'show_in_menu': True,
            'group': '资产管理',
            'group_order': 10,
            'item_order': 13,
            'icon': 'Notebook',
            'group_icon': 'FolderOpened'
        },

        # ============================================================
        # INVENTORY MANAGEMENT GROUP (库存管理) - order: 20
        # ============================================================
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
        'InventoryItem': {
            'show_in_menu': False,  # Usually accessed via InventoryTask
            'group': '库存管理',
            'group_order': 20,
            'item_order': 3,
            'icon': 'Box',
            'group_icon': 'Goods'
        },

        # ============================================================
        # CONSUMABLE MANAGEMENT GROUP (耗材管理) - order: 30
        # ============================================================
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

        # ============================================================
        # MAINTENANCE MANAGEMENT GROUP (维护管理) - order: 40
        # ============================================================
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
        'MaintenanceTask': {
            'show_in_menu': True,
            'group': '维护管理',
            'group_order': 40,
            'item_order': 3,
            'icon': 'Checked',
            'group_icon': 'Tools'
        },

        # ============================================================
        # FINANCE MANAGEMENT GROUP (财务管理) - order: 50
        # ============================================================
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
        'FinanceVoucher': {
            'show_in_menu': True,
            'group': '财务管理',
            'group_order': 50,
            'item_order': 4,
            'icon': 'Document',
            'group_icon': 'Wallet'
        },
        'DepreciationRecord': {
            'show_in_menu': True,
            'group': '财务管理',
            'group_order': 50,
            'item_order': 5,
            'icon': 'TrendCharts',
            'group_icon': 'Wallet'
        },

        # ============================================================
        # IT ASSET MANAGEMENT GROUP (IT资产管理) - order: 60
        # ============================================================
        'ITAsset': {
            'show_in_menu': True,
            'group': 'IT资产管理',
            'group_order': 60,
            'item_order': 1,
            'icon': 'Monitor',
            'group_icon': 'Monitor'
        },

        # ============================================================
        # SOFTWARE LICENSES GROUP (软件许可) - order: 70
        # ============================================================
        'SoftwareLicense': {
            'show_in_menu': True,
            'group': '软件许可',
            'group_order': 70,
            'item_order': 1,
            'icon': 'Document',
            'group_icon': 'Tickets'
        },

        # ============================================================
        # LEASING MANAGEMENT GROUP (租赁管理) - order: 80
        # ============================================================
        'LeasingContract': {
            'show_in_menu': True,
            'group': '租赁管理',
            'group_order': 80,
            'item_order': 1,
            'icon': 'Document',
            'group_icon': 'Document'
        },

        # ============================================================
        # INSURANCE MANAGEMENT GROUP (保险管理) - order: 85
        # ============================================================
        'InsurancePolicy': {
            'show_in_menu': True,
            'group': '保险管理',
            'group_order': 85,
            'item_order': 1,
            'icon': 'Shield',
            'group_icon': 'Shield'
        },

        # ============================================================
        # ORGANIZATION MANAGEMENT GROUP (组织管理) - order: 90
        # ============================================================
        'Department': {
            'show_in_menu': True,
            'group': '组织管理',
            'group_order': 90,
            'item_order': 1,
            'icon': 'OfficeBuilding',
            'group_icon': 'OfficeBuilding'
        },
        'Organization': {
            'show_in_menu': False,  # Usually managed via admin panel
            'group': '组织管理',
            'group_order': 90,
            'item_order': 2,
            'icon': 'OfficeBuilding',
            'group_icon': 'OfficeBuilding'
        },
        'User': {
            'show_in_menu': False,  # Usually managed via admin panel
            'group': '组织管理',
            'group_order': 90,
            'item_order': 3,
            'icon': 'User',
            'group_icon': 'OfficeBuilding'
        },
        'Role': {
            'show_in_menu': False,  # Usually managed via admin panel
            'group': '组织管理',
            'group_order': 90,
            'item_order': 4,
            'icon': 'UserFilled',
            'group_icon': 'OfficeBuilding'
        },

        # ============================================================
        # WORKFLOW MANAGEMENT GROUP (工作流管理) - order: 95
        # ============================================================
        'WorkflowDefinition': {
            'show_in_menu': False,  # Usually managed via admin panel
            'group': '工作流管理',
            'group_order': 95,
            'item_order': 1,
            'icon': 'Connection',
            'group_icon': 'Connection'
        },
        'WorkflowInstance': {
            'show_in_menu': False,  # Usually accessed via task center
            'group': '工作流管理',
            'group_order': 95,
            'item_order': 2,
            'icon': 'CircleCheck',
            'group_icon': 'Connection'
        },
    }

    # Update menu_config for all business objects
    updated_count = 0
    for obj in BusinessObject.objects.filter(is_deleted=False):
        if obj.code in menu_configs:
            obj.menu_config = menu_configs[obj.code]
            obj.save(update_fields=['menu_config'])
            updated_count += 1

    print(f'Updated menu_config for {updated_count} business objects')


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0012_init_menu_config'),
    ]

    operations = [
        migrations.RunPython(init_complete_menu_config, migrations.RunPython.noop),
    ]
