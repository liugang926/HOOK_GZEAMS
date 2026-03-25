from copy import deepcopy

from django.db import migrations


RETURN_HISTORY_PANEL = {
    "code": "project_return_history",
    "title_key": "projects.panels.returnHistory",
    "component": "asset-project-return-history",
}


def seed_asset_project_workbench_return_history_panel(apps, schema_editor):
    BusinessObject = apps.get_model("system", "BusinessObject")

    business_object = BusinessObject.objects.filter(code="AssetProject").first()
    if business_object is None:
        return

    menu_config = deepcopy(business_object.menu_config or {})
    workbench = dict(menu_config.get("workbench") or {})
    detail_panels = list(workbench.get("detail_panels") or workbench.get("detailPanels") or [])

    if any(str(panel.get("code") or "").strip() == RETURN_HISTORY_PANEL["code"] for panel in detail_panels):
        return

    detail_panels.append(dict(RETURN_HISTORY_PANEL))
    workbench["detail_panels"] = detail_panels
    menu_config["workbench"] = workbench

    business_object.menu_config = menu_config
    business_object.save(update_fields=["menu_config", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("system", "0048_asset_project_workbench_returns_panel"),
    ]

    operations = [
        migrations.RunPython(seed_asset_project_workbench_return_history_panel, migrations.RunPython.noop),
    ]
