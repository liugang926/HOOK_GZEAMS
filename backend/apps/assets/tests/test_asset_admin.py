import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from apps.accounts.models import User
from apps.assets.admin import AssetAdmin, AssetAdminForm
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization


@pytest.mark.django_db
def test_asset_admin_uploads_append_system_file_ids():
    org = Organization.objects.create(name='Admin Upload Org', code='admin-upload-org')
    user = User.objects.create_user(
        username='admin-upload-user',
        email='admin-upload@example.com',
        password='secret',
        organization=org,
    )
    category = AssetCategory.objects.create(
        organization=org,
        code='ADMIN-CAT',
        name='Admin Category',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=org,
        asset_name='Admin Asset',
        asset_category=category,
        purchase_price='100.00',
        purchase_date='2026-03-01',
        images=['existing-image-id'],
        attachments=[],
        created_by=user,
    )

    admin_instance = AssetAdmin(Asset, AdminSite())
    admin_instance.message_user = Mock()

    request = RequestFactory().post('/admin/assets/asset/')
    request.user = user

    image_file = SimpleUploadedFile('photo.png', b'image-bytes', content_type='image/png')
    attachment_file = SimpleUploadedFile('manual.pdf', b'pdf-bytes', content_type='application/pdf')
    form = SimpleNamespace(
        cleaned_data={
            'image_uploads': [image_file],
            'attachment_uploads': [attachment_file],
        }
    )

    uploaded_image_id = str(uuid.uuid4())
    uploaded_attachment_id = str(uuid.uuid4())

    with patch('apps.system.services.file_storage.FileStorageService.save_file') as save_file:
        save_file.side_effect = [
            {'success': True, 'data': SimpleNamespace(id=uploaded_image_id)},
            {'success': True, 'data': SimpleNamespace(id=uploaded_attachment_id)},
        ]
        admin_instance.save_model(request, asset, form, change=True)

    asset.refresh_from_db()
    assert asset.images == ['existing-image-id', uploaded_image_id]
    assert asset.attachments == [uploaded_attachment_id]


@pytest.mark.django_db
def test_asset_admin_form_normalizes_single_file_id_strings():
    form = AssetAdminForm()
    form.cleaned_data = {
        'images': 'single-image-id',
        'attachments': ['attachment-a', {'id': 'attachment-b'}],
    }

    assert form.clean_images() == ['single-image-id']
    assert form.clean_attachments() == ['attachment-a', 'attachment-b']


@pytest.mark.django_db
def test_asset_admin_extracts_raw_string_file_ids_from_legacy_values():
    admin_instance = AssetAdmin(Asset, AdminSite())
    assert admin_instance._extract_file_ids('legacy-file-id') == ['legacy-file-id']
