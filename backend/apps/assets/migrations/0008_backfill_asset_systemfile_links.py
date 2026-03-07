from collections import defaultdict

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


def backfill_asset_systemfile_links(apps, schema_editor):
    Asset = apps.get_model('assets', 'Asset')
    SystemFile = apps.get_model('system', 'SystemFile')
    asset_qs = getattr(Asset, 'all_objects', Asset.objects)
    system_file_qs = getattr(SystemFile, 'all_objects', SystemFile.objects)

    file_refs = defaultdict(list)
    for asset in asset_qs.all().only('id', 'images', 'attachments'):
        for field_name in ('images', 'attachments'):
            for file_id in _normalize_file_value(getattr(asset, field_name)):
                file_refs[str(file_id)].append((str(asset.id), field_name))

    for file_id, refs in file_refs.items():
        if len(refs) != 1:
            continue

        asset_id, field_name = refs[0]
        try:
            system_file = system_file_qs.get(pk=file_id)
        except SystemFile.DoesNotExist:
            continue

        if system_file.object_code not in ('', None):
            continue
        if system_file.instance_id is not None:
            continue
        if system_file.field_code not in ('', None, field_name):
            continue

        system_file.object_code = 'Asset'
        system_file.instance_id = asset_id
        system_file.field_code = field_name
        system_file.save(update_fields=['object_code', 'instance_id', 'field_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0028_seed_relation_closed_loop_domain_stable'),
        ('assets', '0007_normalize_asset_file_fields'),
    ]

    operations = [
        migrations.RunPython(backfill_asset_systemfile_links, migrations.RunPython.noop),
    ]
