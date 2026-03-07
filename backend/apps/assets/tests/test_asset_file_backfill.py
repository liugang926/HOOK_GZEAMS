import importlib
import uuid

import pytest
from django.apps import apps as django_apps

from apps.accounts.models import User
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.system.models import SystemFile


def _create_asset_with_org():
    org = Organization.objects.create(name='Backfill Org', code=f'backfill-org-{uuid.uuid4().hex[:8]}')
    user = User.objects.create_user(
        username=f'backfill-user-{uuid.uuid4().hex[:8]}',
        email=f'backfill-{uuid.uuid4().hex[:8]}@example.com',
        password='secret',
        organization=org,
    )
    category = AssetCategory.objects.create(
        organization=org,
        code=f'BACKFILL-{uuid.uuid4().hex[:6]}',
        name='Backfill Category',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=org,
        asset_name='Backfill Asset',
        asset_category=category,
        purchase_price='100.00',
        purchase_date='2026-03-01',
        created_by=user,
    )
    return org, asset


@pytest.mark.django_db
def test_backfill_asset_systemfile_links_sets_blank_linkage():
    migration = importlib.import_module('apps.assets.migrations.0008_backfill_asset_systemfile_links')

    org, asset = _create_asset_with_org()
    system_file = SystemFile.all_objects.create(
        organization=org,
        file_name='legacy-image.png',
        file_path='uploads/legacy-image.png',
        file_size=123,
        file_type='image/png',
        field_code='images',
    )
    asset.images = [str(system_file.id)]
    asset.save(update_fields=['images'])

    migration.backfill_asset_systemfile_links(django_apps, None)

    system_file.refresh_from_db()
    assert system_file.object_code == 'Asset'
    assert str(system_file.instance_id) == str(asset.id)
    assert system_file.field_code == 'images'


@pytest.mark.django_db
def test_backfill_asset_systemfile_links_does_not_override_existing_binding():
    migration = importlib.import_module('apps.assets.migrations.0008_backfill_asset_systemfile_links')

    org, asset = _create_asset_with_org()
    existing_instance_id = uuid.uuid4()
    system_file = SystemFile.all_objects.create(
        organization=org,
        file_name='bound-file.pdf',
        file_path='uploads/bound-file.pdf',
        file_size=456,
        file_type='application/pdf',
        object_code='Contract',
        instance_id=existing_instance_id,
        field_code='attachments',
    )
    asset.attachments = [str(system_file.id)]
    asset.save(update_fields=['attachments'])

    migration.backfill_asset_systemfile_links(django_apps, None)

    system_file.refresh_from_db()
    assert system_file.object_code == 'Contract'
    assert system_file.instance_id == existing_instance_id
    assert system_file.field_code == 'attachments'
