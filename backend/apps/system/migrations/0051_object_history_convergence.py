from django.db import migrations


AUDIT_OBJECT_CODES = ("AssetStatusLog", "ConfigurationChange")
HISTORY_RELATIONS = (
    ("Asset", "configuration_changes", "configuration_change"),
    ("ITAsset", "configuration_changes", "configuration_change"),
)


def apply_object_history_convergence(apps, schema_editor):
    BusinessObject = apps.get_model("system", "BusinessObject")
    ObjectRelationDefinition = apps.get_model("system", "ObjectRelationDefinition")

    BusinessObject.objects.filter(
        code__in=AUDIT_OBJECT_CODES,
        is_deleted=False,
    ).update(
        is_menu_hidden=True,
        object_role="log",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
    )

    for parent_object_code, relation_code, history_source_type in HISTORY_RELATIONS:
        relations = ObjectRelationDefinition.objects.filter(
            parent_object_code=parent_object_code,
            relation_code=relation_code,
            is_deleted=False,
        )
        for relation in relations:
            next_extra = dict(relation.extra_config or {})
            next_extra["presentation_zone"] = "history"
            next_extra["history_source_type"] = history_source_type
            if next_extra != (relation.extra_config or {}):
                relation.extra_config = next_extra
                relation.save(update_fields=["extra_config", "updated_at"])


def revert_object_history_convergence(apps, schema_editor):
    BusinessObject = apps.get_model("system", "BusinessObject")
    ObjectRelationDefinition = apps.get_model("system", "ObjectRelationDefinition")

    BusinessObject.objects.filter(
        code__in=AUDIT_OBJECT_CODES,
        is_deleted=False,
    ).update(
        is_menu_hidden=False,
        object_role="root",
        is_top_level_navigable=True,
        allow_standalone_query=True,
        allow_standalone_route=True,
    )

    for parent_object_code, relation_code, _history_source_type in HISTORY_RELATIONS:
        relations = ObjectRelationDefinition.objects.filter(
            parent_object_code=parent_object_code,
            relation_code=relation_code,
            is_deleted=False,
        )
        for relation in relations:
            next_extra = dict(relation.extra_config or {})
            next_extra.pop("presentation_zone", None)
            next_extra.pop("history_source_type", None)
            if next_extra != (relation.extra_config or {}):
                relation.extra_config = next_extra
                relation.save(update_fields=["extra_config", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("system", "0050_asset_project_workbench_overview_panel"),
    ]

    operations = [
        migrations.RunPython(
            apply_object_history_convergence,
            revert_object_history_convergence,
        ),
    ]
