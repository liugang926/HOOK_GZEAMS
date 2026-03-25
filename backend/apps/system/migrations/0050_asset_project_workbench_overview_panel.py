from copy import deepcopy

from django.db import migrations


OVERVIEW_PANEL = {
    "code": "project_overview",
    "title_key": "projects.panels.overview",
    "component": "asset-project-overview",
}


def seed_asset_project_workbench_overview_panel(apps, schema_editor):
    BusinessObject = apps.get_model("system", "BusinessObject")

    business_object = BusinessObject.objects.filter(code="AssetProject").first()
    if business_object is None:
        return

    menu_config = deepcopy(business_object.menu_config or {})
    workbench = dict(menu_config.get("workbench") or {})
    detail_panels = list(workbench.get("detail_panels") or workbench.get("detailPanels") or [])
    filtered_panels = [
        dict(panel)
        for panel in detail_panels
        if str(panel.get("code") or "").strip() != OVERVIEW_PANEL["code"]
    ]

    workbench["detail_panels"] = [dict(OVERVIEW_PANEL)] + filtered_panels
    menu_config["workbench"] = workbench

    business_object.menu_config = menu_config
    business_object.save(update_fields=["menu_config", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("system", "0049_asset_project_workbench_return_history_panel"),
    ]

    operations = [
        migrations.RunPython(seed_asset_project_workbench_overview_panel, migrations.RunPython.noop),
    ]
