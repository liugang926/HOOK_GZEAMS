"""
Tests for pagination consistency across ViewSets.

Tests that:
- deleted() endpoint uses consistent pagination format
- Standard DRF pagination is used
- BaseResponse format is maintained
"""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.accounts.models import User
from apps.assets.models import Asset


@pytest.mark.django_db
class TestPaginationConsistency:
    """Test pagination consistency across all endpoints."""

    def test_deleted_endpoint_pagination_format(self, auth_client, asset):
        """Test that deleted endpoint uses standard pagination format."""
        # Soft delete the asset
        asset.soft_delete()

        url = reverse('asset-deleted')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check BaseResponse format
        assert 'success' in response.data or 'data' in response.data

        # Check pagination structure
        if 'data' in response.data:
            assert 'count' in response.data['data']
            assert 'results' in response.data['data']

    def test_list_endpoint_pagination_format(self, auth_client, asset):
        """Test that list endpoint uses standard pagination format."""
        url = reverse('asset-list')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check BaseResponse format
        assert 'success' in response.data or 'data' in response.data or 'results' in response.data

    def test_pagination_with_page_size(self, auth_client, organization):
        """Test pagination with custom page size."""
        # Create multiple assets
        for i in range(25):
            Asset.objects.create(
                organization=organization,
                asset_code=f'TEST{i:03d}',
                asset_name=f'Test Asset {i}',
                asset_category_id=None,
                original_value=1000.00
            )

        url = reverse('asset-list')
        response = auth_client.get(url, {'page_size': 10})

        assert response.status_code == status.HTTP_200_OK

    def test_pagination_page_parameter(self, auth_client, organization):
        """Test pagination with page parameter."""
        # Create multiple assets
        for i in range(25):
            Asset.objects.create(
                organization=organization,
                asset_code=f'TEST{i:03d}',
                asset_name=f'Test Asset {i}',
                asset_category_id=None,
                original_value=1000.00
            )

        url = reverse('asset-list')
        response = auth_client.get(url, {'page': 2, 'page_size': 10})

        assert response.status_code == status.HTTP_200_OK
