import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.organizations.models import Organization
from apps.system.services.file_storage import FileStorageService
from apps.system.services.image_processor import ImageProcessorService


@pytest.mark.django_db
def test_save_image_without_compression_does_not_raise_bytesio_error(settings, tmp_path, monkeypatch):
    settings.MEDIA_ROOT = str(tmp_path)
    org = Organization.objects.create(name='Upload Test Org', code='upload-test-org')

    # Force image branch and non-compressed processing path.
    monkeypatch.setattr(
        ImageProcessorService,
        'is_image_file',
        classmethod(lambda cls, filename, mime_type=None: True),
    )
    monkeypatch.setattr(
        ImageProcessorService,
        'process_uploaded_image',
        classmethod(
            lambda cls, file_obj, filename, file_size, generate_thumbnail=True: {
                'width': 100,
                'height': 100,
                'is_compressed': False,
                'thumbnail_data': b'thumb-bytes',
                'thumbnail_ext': '.jpg',
            }
        ),
    )

    uploaded = SimpleUploadedFile(
        'test.png',
        b'fake-image-content',
        content_type='image/png',
    )

    service = FileStorageService()
    result = service.save_file(uploaded, str(org.id), object_code='Asset', field_code='images')

    assert result['success'] is True
    assert result['data'].id is not None
