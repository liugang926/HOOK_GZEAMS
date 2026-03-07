from django.db import migrations


def _normalize_file_value(value):
    if value in (None, '', []):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        candidate = value.get('id') or value.get('fileId') or value.get('value')
        return [candidate] if isinstance(candidate, str) and candidate else []
    if isinstance(value, list):
        normalized = []
        for item in value:
            if isinstance(item, str) and item and item not in normalized:
                normalized.append(item)
                continue
            if isinstance(item, dict):
                candidate = item.get('id') or item.get('fileId') or item.get('value')
                if isinstance(candidate, str) and candidate and candidate not in normalized:
                    normalized.append(candidate)
        return normalized
    return []


def normalize_asset_file_fields(apps, schema_editor):
    Asset = apps.get_model('assets', 'Asset')

    for asset in Asset.objects.all().only('id', 'images', 'attachments'):
        next_images = _normalize_file_value(asset.images)
        next_attachments = _normalize_file_value(asset.attachments)

        updates = {}
        if asset.images != next_images:
            updates['images'] = next_images
        if asset.attachments != next_attachments:
            updates['attachments'] = next_attachments

        if updates:
            Asset.objects.filter(pk=asset.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0006_migrate_unit_data'),
    ]

    operations = [
        migrations.RunPython(normalize_asset_file_fields, migrations.RunPython.noop),
    ]
