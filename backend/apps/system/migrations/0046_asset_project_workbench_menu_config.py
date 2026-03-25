from copy import deepcopy

from django.db import migrations


ASSET_PROJECT_WORKBENCH = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/AssetProject",
    "toolbar": {
        "primary_actions": [
            {
                "code": "refresh_rollups",
                "label_key": "projects.actions.refreshRollups",
                "action_path": "refresh_rollups",
                "button_type": "primary",
            }
        ],
        "secondary_actions": [],
    },
    "detail_panels": [
        {
            "code": "project_assets",
            "title_key": "projects.panels.assets",
            "component": "asset-project-assets",
        },
        {
            "code": "project_members",
            "title_key": "projects.panels.members",
            "component": "asset-project-members",
        },
    ],
    "async_indicators": [],
}


def merge_nested_config(base, overrides):
    merged = deepcopy(base or {})
    if not isinstance(overrides, dict):
        return merged

    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_nested_config(merged[key], value)
            continue
        merged[key] = deepcopy(value)

    return merged


def seed_asset_project_workbench(apps, schema_editor):
    BusinessObject = apps.get_model("system", "BusinessObject")
    asset_project = BusinessObject.objects.filter(code="AssetProject").first()
    if asset_project is None:
        return

    menu_config = dict(asset_project.menu_config or {})
    workbench = merge_nested_config(ASSET_PROJECT_WORKBENCH, menu_config.get("workbench") or {})

    menu_config.update(
        {
            "url": "/objects/AssetProject",
            "show_in_menu": True,
            "workbench": workbench,
        }
    )

    asset_project.menu_config = menu_config
    asset_project.save(update_fields=["menu_config"])


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0045_finance_voucher_workbench_menu_config"),
    ]

    operations = [
        migrations.RunPython(seed_asset_project_workbench, migrations.RunPython.noop),
    ]
