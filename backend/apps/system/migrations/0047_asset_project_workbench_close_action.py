from copy import deepcopy

from django.db import migrations


CLOSE_PROJECT_ACTION = {
    "code": "close_project",
    "label_key": "projects.actions.closeProject",
    "action_path": "close",
    "button_type": "warning",
    "confirm_message_key": "projects.messages.confirmCloseProject",
    "visible_when": {
        "status_in": ["active", "suspended"],
    },
}


def upsert_action(actions, action_definition):
    normalized_actions = []
    target_code = str((action_definition or {}).get("code") or "").strip()

    for action in actions or []:
        if not isinstance(action, dict):
            continue
        if target_code and str(action.get("code") or "").strip() == target_code:
            normalized_actions.append(deepcopy(action_definition))
        else:
            normalized_actions.append(deepcopy(action))

    if target_code and not any(str(item.get("code") or "").strip() == target_code for item in normalized_actions):
        normalized_actions.append(deepcopy(action_definition))

    return normalized_actions


def seed_asset_project_workbench_close_action(apps, schema_editor):
    BusinessObject = apps.get_model("system", "BusinessObject")
    asset_project = BusinessObject.objects.filter(code="AssetProject").first()
    if asset_project is None:
        return

    menu_config = dict(asset_project.menu_config or {})
    workbench = dict(menu_config.get("workbench") or {})
    toolbar = dict(workbench.get("toolbar") or {})
    secondary_actions = toolbar.get("secondary_actions") or []

    toolbar["secondary_actions"] = upsert_action(secondary_actions, CLOSE_PROJECT_ACTION)
    workbench["toolbar"] = toolbar
    menu_config["workbench"] = workbench

    asset_project.menu_config = menu_config
    asset_project.save(update_fields=["menu_config"])


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0046_asset_project_workbench_menu_config"),
    ]

    operations = [
        migrations.RunPython(seed_asset_project_workbench_close_action, migrations.RunPython.noop),
    ]
