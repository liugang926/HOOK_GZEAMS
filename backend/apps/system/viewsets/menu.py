"""
Dynamic Menu ViewSet - Generates menu structure from BusinessObject metadata.

This ViewSet provides a completely dynamic menu system where menu items
are generated from BusinessObject records with menu_config metadata.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Value, F

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
            group_name = menu_config.get('group', '其他')
            group_order = menu_config.get('group_order', 999)
            item_order = menu_config.get('item_order', 999)
            icon = menu_config.get('icon', 'Document')

            menu_item = {
                'code': obj.code,
                'name': obj.name,
                'name_en': obj.name_en,
                'url': f"/objects/{obj.code}",
                'icon': icon,
                'order': item_order,
                'group': group_name,
                'badge': menu_config.get('badge')
            }

            # Add to group
            if group_name not in groups:
                groups[group_name] = {
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

        return BaseResponse.success({
            'groups': grouped_list,
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
                    'description': '是否在菜单中显示'
                },
                'group': {
                    'type': 'string',
                    'default': '其他',
                    'description': '菜单分组名称'
                },
                'group_order': {
                    'type': 'integer',
                    'default': 999,
                    'description': '分组显示顺序'
                },
                'item_order': {
                    'type': 'integer',
                    'default': 999,
                    'description': '菜单项显示顺序'
                },
                'icon': {
                    'type': 'string',
                    'default': 'Document',
                    'description': '图标名称'
                },
                'group_icon': {
                    'type': 'string',
                    'default': 'Folder',
                    'description': '分组图标名称'
                },
                'badge': {
                    'type': 'object',
                    'default': None,
                    'description': '徽章配置 (e.g., {"type": "dot", "value": 5})'
                }
            }
        }

        return BaseResponse.success({
            'schema': schema,
            'common_groups': [
                {'name': '工作台', 'order': 1, 'icon': 'Odometer'},
                {'name': '资产管理', 'order': 10, 'icon': 'FolderOpened'},
                {'name': '库存管理', 'order': 20, 'icon': 'Goods'},
                {'name': '耗材管理', 'order': 30, 'icon': 'Box'},
                {'name': '财务管理', 'order': 40, 'icon': 'Wallet'},
                {'name': '系统管理', 'order': 100, 'icon': 'Setting'},
                {'name': '其他', 'order': 999, 'icon': 'More'}
            ],
            'common_icons': [
                'Document', 'Folder', 'FolderOpened', 'Menu', 'Setting',
                'Odometer', 'Goods', 'Box', 'Wallet', 'User', 'Tickets',
                'Calendar', 'Clock', 'Bell', 'ChatDotRound', 'Message',
                'DataLine', 'PieChart', 'TrendCharts', 'Monitor'
            ]
        })
