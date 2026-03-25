from django.db import migrations


def seed_layout_object_i18n_feature_flags(apps, schema_editor):
    """
    Seed global feature flags for layout/object runtime i18n rollout.

    Keys:
    - runtime_i18n_enabled
    - layout_merge_unified_enabled
    - field_code_strict_mode
    """
    SystemConfig = apps.get_model('system', 'SystemConfig')

    feature_flags = [
        {
            'config_key': 'runtime_i18n_enabled',
            'config_value': 'true',
            'value_type': 'boolean',
            'name': 'Runtime i18n Enabled',
            'category': 'feature_flag',
            'description': 'Enable runtime localization for object/layout metadata.',
        },
        {
            'config_key': 'layout_merge_unified_enabled',
            'config_value': 'true',
            'value_type': 'boolean',
            'name': 'Layout Merge Unified Enabled',
            'category': 'feature_flag',
            'description': 'Enable unified runtime layout merge and normalization path.',
        },
        {
            'config_key': 'field_code_strict_mode',
            'config_value': 'false',
            'value_type': 'boolean',
            'name': 'Field Code Strict Mode',
            'category': 'feature_flag',
            'description': 'Return field_code only and stop emitting legacy code key.',
        },
    ]

    for item in feature_flags:
        SystemConfig.objects.get_or_create(
            config_key=item['config_key'],
            organization_id=None,
            defaults={
                'config_value': item['config_value'],
                'value_type': item['value_type'],
                'name': item['name'],
                'category': item['category'],
                'description': item['description'],
                'is_system': True,
            },
        )


def reverse_seed_layout_object_i18n_feature_flags(apps, schema_editor):
    # Keep seeded system feature flags on rollback to avoid accidental prod behavior change.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('system', '0023_activitylog'),
    ]

    operations = [
        migrations.RunPython(
            seed_layout_object_i18n_feature_flags,
            reverse_seed_layout_object_i18n_feature_flags,
        ),
    ]

