# Generated manually for system management menu configuration

from django.db import migrations


def add_system_management_menu(apps, schema_editor):
    """Add menu configuration for system management pages."""
    BusinessObject = apps.get_model('system', 'BusinessObject')

    # System Management Group (系统管理) - order: 100
    # These are special system pages that use custom URLs, not /objects/{code}
    system_menu_configs = {
        'BusinessObject': {
            'show_in_menu': True,
            'group': '系统管理',
            'group_order': 100,
            'item_order': 1,
            'icon': 'Grid',
            'group_icon': 'Setting',
            'url': '/system/business-objects'
        },
        'FieldDefinition': {
            'show_in_menu': True,
            'group': '系统管理',
            'group_order': 100,
            'item_order': 2,
            'icon': 'List',
            'group_icon': 'Setting',
            'url': '/system/field-definitions'
        },
        'PageLayout': {
            'show_in_menu': True,
            'group': '系统管理',
            'group_order': 100,
            'item_order': 3,
            'icon': 'Notebook',
            'group_icon': 'Setting',
            'url': '/system/page-layouts'
        },
        'DictionaryType': {
            'show_in_menu': True,
            'group': '系统管理',
            'group_order': 100,
            'item_order': 4,
            'icon': 'Notebook',
            'group_icon': 'Setting',
            'url': '/system/dictionary-types'
        },
        'SequenceRule': {
            'show_in_menu': True,
            'group': '系统管理',
            'group_order': 100,
            'item_order': 5,
            'icon': 'Sort',
            'group_icon': 'Setting',
            'url': '/system/sequence-rules'
        },
        'BusinessRule': {
            'show_in_menu': True,
            'group': '系统管理',
            'group_order': 100,
            'item_order': 6,
            'icon': 'MagicStick',
            'group_icon': 'Setting',
            'url': '/system/business-rules'
        },
        'ConfigPackage': {
            'show_in_menu': True,
            'group': '系统管理',
            'group_order': 100,
            'item_order': 7,
            'icon': 'Box',
            'group_icon': 'Setting',
            'url': '/system/config-packages'
        },
        'SystemConfig': {
            'show_in_menu': True,
            'group': '系统管理',
            'group_order': 100,
            'item_order': 8,
            'icon': 'Setting',
            'group_icon': 'Setting',
            'url': '/system/config'
        },
        'SystemFile': {
            'show_in_menu': True,
            'group': '系统管理',
            'group_order': 100,
            'item_order': 9,
            'icon': 'Folder',
            'group_icon': 'Setting',
            'url': '/system/files'
        },
    }

    # Update menu_config for system management business objects
    updated_count = 0
    for obj in BusinessObject.objects.filter(is_deleted=False):
        if obj.code in system_menu_configs:
            existing_config = obj.menu_config or {}
            # Merge with existing config, but system menu config takes precedence
            merged_config = {**existing_config, **system_menu_configs[obj.code]}
            obj.menu_config = merged_config
            obj.save(update_fields=['menu_config'])
            updated_count += 1

    print(f'Updated menu_config for {updated_count} system management business objects')


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0018_add_metadata_layout_extensions'),
    ]

    operations = [
        migrations.RunPython(add_system_management_menu, migrations.RunPython.noop),
    ]
