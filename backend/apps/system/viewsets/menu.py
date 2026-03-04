"""
Dynamic Menu ViewSet - Generates menu structure from BusinessObject metadata.

This ViewSet provides a completely dynamic menu system where menu items
are generated from BusinessObject records with menu_config metadata.
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action

from apps.common.responses.base import BaseResponse
from apps.system.models import BusinessObject


class MenuViewSet(viewsets.GenericViewSet):
    """
    Dynamic Menu ViewSet.

    Provides menu structure for the frontend navigation based on
    BusinessObject metadata. No hardcoded menu items - everything
    is dynamically generated from the database.

    Endpoints:
        GET /api/system/menu/ - Get full menu structure
        GET /api/system/menu/flat/ - Get flat menu item list
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Get BusinessObjects that should appear in menu.

        BusinessObject uses GlobalMetadataManager (no organization filtering)
        since metadata is system-level and available to all organizations.
        """
        return BusinessObject.objects.filter(
            menu_config__show_in_menu=True
        )

    def list(self, request, *args, **kwargs):
        """
        Get dynamic menu structure grouped by category.

        Menu config format in BusinessObject.menu_config:
        {
            "show_in_menu": true,           # Whether to show in menu
            "group": "资产管理",             # Menu group name
            "group_order": 10,              # Group display order
            "item_order": 1,                # Item order within group
            "icon": "Asset",                # Icon name (Element Plus or custom)
            "badge": null                   # Optional badge config
        }

        Response format:
        {
            "success": true,
            "data": {
                "groups": [
                    {
                        "name": "资产管理",
                        "order": 10,
                        "icon": "FolderOpened",
                        "items": [
                            {
                                "code": "Asset",
                                "name": "资产列表",
                                "url": "/objects/Asset",
                                "icon": "Document",
                                "order": 1
                            },
                            ...
                        ]
                    }
                ],
                "items": [...]  # Flat list for easier rendering
            }
        }
        """
        queryset = self.get_queryset()

        # Group items by menu_config.group
        groups = {}
        flat_items = []

        for obj in queryset:
            menu_config = obj.menu_config or {}

            # Skip if not configured to show in menu
            if not menu_config.get('show_in_menu'):
                continue

            # Get menu configuration
            group_name = menu_config.get('group', 'Other')
            group_code = menu_config.get('group_code') or str(group_name).strip().lower().replace(' ', '_')
            group_order = menu_config.get('group_order', 999)
            item_order = menu_config.get('item_order', 999)
            icon = menu_config.get('icon', 'Document')

            # Support custom URL in menu_config (for system pages)
            custom_url = menu_config.get('url')
            menu_item = {
                'code': obj.code,
                'name': obj.name,
                'name_en': obj.name_en,
                'url': custom_url if custom_url else f"/objects/{obj.code}",
                'icon': icon,
                'order': item_order,
                'group': group_name,
                'group_code': group_code,
                'badge': menu_config.get('badge')
            }

            # Add to group
            if group_name not in groups:
                groups[group_name] = {
                    'code': group_code,
                    'name': group_name,
                    'order': group_order,
                    'icon': menu_config.get('group_icon', 'Folder'),
                    'items': []
                }

            groups[group_name]['items'].append(menu_item)
            flat_items.append(menu_item)

        # Sort items within each group
        for group in groups.values():
            group['items'].sort(key=lambda x: x['order'])

        # Convert groups dict to sorted list
        grouped_list = sorted(
            groups.values(),
            key=lambda x: x['order']
        )

        # ── Static Lifecycle Group ──────────────────────────────────────────
        # These pages use custom /assets/lifecycle/ URLs and are not
        # represented as BusinessObjects, so they are injected statically.
        lifecycle_group = {
            'code': 'lifecycle',
            'name': '资产生命周期',
            'name_en': 'Asset Lifecycle',
            'order': 25,
            'icon': 'Refresh',
            'items': [
                {
                    'code': 'PurchaseRequest',
                    'name': '采购申请',
                    'name_en': 'Purchase Requests',
                    'url': '/assets/lifecycle/purchase-requests',
                    'icon': 'ShoppingCart',
                    'order': 1,
                    'group': '资产生命周期',
                    'group_code': 'lifecycle',
                    'badge': None,
                },
                {
                    'code': 'AssetReceipt',
                    'name': '入库验收',
                    'name_en': 'Asset Receipts',
                    'url': '/assets/lifecycle/asset-receipts',
                    'icon': 'Box',
                    'order': 2,
                    'group': '资产生命周期',
                    'group_code': 'lifecycle',
                    'badge': None,
                },
                {
                    'code': 'MaintenanceOrder',
                    'name': '维修工单',
                    'name_en': 'Maintenance Orders',
                    'url': '/assets/lifecycle/maintenance',
                    'icon': 'Tools',
                    'order': 3,
                    'group': '资产生命周期',
                    'group_code': 'lifecycle',
                    'badge': None,
                },
                {
                    'code': 'MaintenancePlan',
                    'name': '维保计划',
                    'name_en': 'Maintenance Plans',
                    'url': '/assets/lifecycle/maintenance-plans',
                    'icon': 'Calendar',
                    'order': 4,
                    'group': '资产生命周期',
                    'group_code': 'lifecycle',
                    'badge': None,
                },
                {
                    'code': 'MaintenanceTask',
                    'name': '维保任务',
                    'name_en': 'Maintenance Tasks',
                    'url': '/assets/lifecycle/maintenance-tasks',
                    'icon': 'Finished',
                    'order': 5,
                    'group': '资产生命周期',
                    'group_code': 'lifecycle',
                    'badge': None,
                },
                {
                    'code': 'DisposalRequest',
                    'name': '报废申请',
                    'name_en': 'Disposal Requests',
                    'url': '/assets/lifecycle/disposal-requests',
                    'icon': 'Delete',
                    'order': 6,
                    'group': '资产生命周期',
                    'group_code': 'lifecycle',
                    'badge': None,
                },
            ]
        }

        # Insert lifecycle group at the correct position (after asset operations)
        grouped_list_with_lifecycle = []
        lifecycle_inserted = False
        insurance_inserted = False
        leasing_inserted = False

        insurance_group = {
            'code': 'insurance',
            'name': '保险管理',
            'name_en': 'Insurance',
            'order': 35,
            'icon': 'Umbrella',
            'items': [
                {
                    'code': 'InsuranceDashboard',
                    'name': '保险概览',
                    'name_en': 'Insurance Overview',
                    'url': '/insurance/dashboard',
                    'icon': 'DataLine',
                    'order': 1,
                    'group': '保险管理',
                    'group_code': 'insurance',
                    'badge': None,
                },
                {
                    'code': 'InsurancePolicy',
                    'name': '保险保单',
                    'name_en': 'Insurance Policies',
                    'url': '/objects/InsurancePolicy',
                    'icon': 'Document',
                    'order': 2,
                    'group': '保险管理',
                    'group_code': 'insurance',
                    'badge': None,
                },
                {
                    'code': 'ClaimRecord',
                    'name': '理赔管理',
                    'name_en': 'Claim Management',
                    'url': '/insurance/claims',
                    'icon': 'Tickets',
                    'order': 3,
                    'group': '保险管理',
                    'group_code': 'insurance',
                    'badge': None,
                },
            ]
        }

        leasing_group = {
            'code': 'leasing',
            'name': '租赁管理',
            'name_en': 'Leasing',
            'order': 45,
            'icon': 'Key',
            'items': [
                {
                    'code': 'LeasingDashboard',
                    'name': '租赁概览',
                    'name_en': 'Leasing Overview',
                    'url': '/leasing/dashboard',
                    'icon': 'DataLine',
                    'order': 1,
                    'group': '租赁管理',
                    'group_code': 'leasing',
                    'badge': None,
                },
                {
                    'code': 'LeasingContract',
                    'name': '租赁合同',
                    'name_en': 'Lease Contracts',
                    'url': '/objects/LeasingContract',
                    'icon': 'Document',
                    'order': 2,
                    'group': '租赁管理',
                    'group_code': 'leasing',
                    'badge': None,
                },
                {
                    'code': 'RentPayment',
                    'name': '租金管理',
                    'name_en': 'Rent Payments',
                    'url': '/leasing/payments',
                    'icon': 'Wallet',
                    'order': 3,
                    'group': '租赁管理',
                    'group_code': 'leasing',
                    'badge': None,
                },
            ]
        }

        for group in grouped_list:
            if not lifecycle_inserted and group.get('order', 0) >= 25:
                grouped_list_with_lifecycle.append(lifecycle_group)
                lifecycle_inserted = True
            if not insurance_inserted and group.get('order', 0) >= 35:
                grouped_list_with_lifecycle.append(insurance_group)
                insurance_inserted = True
            if not leasing_inserted and group.get('order', 0) >= 45:
                grouped_list_with_lifecycle.append(leasing_group)
                leasing_inserted = True
            grouped_list_with_lifecycle.append(group)

        if not lifecycle_inserted:
            grouped_list_with_lifecycle.append(lifecycle_group)
        if not insurance_inserted:
            grouped_list_with_lifecycle.append(insurance_group)
        if not leasing_inserted:
            grouped_list_with_lifecycle.append(leasing_group)

        # Reports group — always appended at the end
        reports_group = {
            'code': 'reports',
            'name': '报表中心',
            'name_en': 'Reports',
            'order': 90,
            'icon': 'DataAnalysis',
            'items': [
                {
                    'code': 'ReportCenter',
                    'name': '报表中心',
                    'name_en': 'Report Center',
                    'url': '/reports/center',
                    'icon': 'DataAnalysis',
                    'order': 1,
                    'group': '报表中心',
                    'group_code': 'reports',
                    'badge': None,
                },
            ]
        }
        grouped_list_with_lifecycle.append(reports_group)

        return BaseResponse.success({
            'groups': grouped_list_with_lifecycle,
            'items': flat_items
        })


    @action(detail=False, methods=['get'], url_path='flat')
    def flat(self, request, *args, **kwargs):
        """
        Get flat menu item list.

        Simpler format for components that don't need grouping.

        GET /api/system/menu/flat/

        Response:
        {
            "success": true,
            "data": [
                {
                    "code": "Asset",
                    "name": "资产列表",
                    "url": "/objects/Asset",
                    "icon": "Document",
                    "group": "资产管理",
                    "order": 1
                },
                ...
            ]
        }
        """
        result = self.list(request, *args, **kwargs)
        return BaseResponse.success(result.data['items'])

    @action(detail=False, methods=['get'], url_path='config')
    def config(self, request, *args, **kwargs):
        """
        Get menu configuration schema.

        Returns the schema for menu_config field, useful for
        frontend form builders or admin panels.

        GET /api/system/menu/config/
        """
        schema = {
            'menu_config': {
                'show_in_menu': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Whether to show in menu'
                },
                'group': {
                    'type': 'string',
                    'default': '其他',
                    'description': 'Menu group name'
                },
                'group_order': {
                    'type': 'integer',
                    'default': 999,
                    'description': 'Group display order'
                },
                'item_order': {
                    'type': 'integer',
                    'default': 999,
                    'description': 'Menu item display order'
                },
                'icon': {
                    'type': 'string',
                    'default': 'Document',
                    'description': 'Icon name (Element Plus)'
                },
                'group_icon': {
                    'type': 'string',
                    'default': 'Folder',
                    'description': 'Group icon name'
                },
                'url': {
                    'type': 'string',
                    'default': None,
                    'description': 'Custom URL (default: /objects/{code})'
                },
                'badge': {
                    'type': 'object',
                    'default': None,
                    'description': 'Badge config (e.g., {"type": "dot", "value": 5})'
                }
            }
        }

        return BaseResponse.success({
            'schema': schema,
            'common_groups': [
                {'code': 'dashboard', 'name': 'Dashboard', 'order': 1, 'icon': 'Odometer'},
                {'code': 'asset', 'name': 'Asset Management', 'order': 10, 'icon': 'FolderOpened'},
                {'code': 'asset_operation', 'name': 'Asset Operations', 'order': 20, 'icon': 'Operation'},
                {'code': 'consumable', 'name': 'Consumables', 'order': 30, 'icon': 'Box'},
                {'code': 'purchase', 'name': 'Procurement', 'order': 40, 'icon': 'ShoppingCart'},
                {'code': 'maintenance', 'name': 'Maintenance', 'order': 50, 'icon': 'Tools'},
                {'code': 'inventory', 'name': 'Inventory', 'order': 60, 'icon': 'Document'},
                {'code': 'organization', 'name': 'Organization', 'order': 70, 'icon': 'OfficeBuilding'},
                {'code': 'finance', 'name': 'Finance', 'order': 80, 'icon': 'Wallet'},
                {'code': 'workflow', 'name': 'Workflow Management', 'order': 90, 'icon': 'Connection'},
                {'code': 'system', 'name': 'System', 'order': 100, 'icon': 'Setting'},
                {'code': 'other', 'name': 'Other', 'order': 999, 'icon': 'More'}
            ],
            'common_icons': [
                'Document', 'Folder', 'FolderOpened', 'Menu', 'Setting',
                'Odometer', 'Goods', 'Box', 'Wallet', 'User', 'Tickets',
                'Calendar', 'Clock', 'Bell', 'ChatDotRound', 'Message',
                'DataLine', 'PieChart', 'TrendCharts', 'Monitor'
            ]
        })
