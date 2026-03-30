"""API tests for smart search endpoints."""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserOrganization
from apps.assets.models import Asset, AssetCategory, Location, Supplier
from apps.search.models import SavedSearch


def build_client(user, organization):
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    return client


@pytest.fixture
def api_search_setup(user, organization):
    category = AssetCategory.objects.create(
        organization=organization,
        code='EQUIPMENT',
        name='Equipment',
        created_by=user,
    )
    location = Location.objects.create(
        organization=organization,
        name='Main Warehouse',
        location_type='warehouse',
        created_by=user,
    )
    supplier = Supplier.objects.create(
        organization=organization,
        code='SUP-API',
        name='Supplier API',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=organization,
        created_by=user,
        asset_code='API-ASSET-001',
        asset_name='Laptop For API Search',
        asset_category=category,
        specification='API regression laptop',
        brand='Lenovo',
        model='ThinkPad',
        serial_number='API-SN-001',
        purchase_price=Decimal('8800.00'),
        current_value=Decimal('7600.00'),
        purchase_date='2026-01-10',
        location=location,
        supplier=supplier,
        asset_status='in_use',
    )
    return {
        'category': category,
        'location': location,
        'supplier': supplier,
        'asset': asset,
    }


@pytest.mark.django_db
def test_post_search_endpoint_returns_asset_results_and_records_history(user, organization, api_search_setup):
    client = build_client(user, organization)

    response = client.post(
        '/api/search/',
        {
            'keyword': 'Laptop',
            'filters': {'status': 'in_use'},
            'sort_by': 'relevance',
            'page': 1,
            'page_size': 20,
        },
        format='json',
    )

    assert response.status_code == 200
    assert response.data['success'] is True
    assert response.data['data']['total'] == 1
    assert response.data['data']['results'][0]['asset_code'] == 'API-ASSET-001'

    history_response = client.get('/api/search/history/')
    assert history_response.status_code == 200
    assert history_response.data['data']['count'] == 1


@pytest.mark.django_db
def test_suggestion_endpoint_returns_typeahead_matches(user, organization, api_search_setup):
    client = build_client(user, organization)

    response = client.get('/api/search/suggestions/', {'keyword': 'Lap', 'type': 'asset'})

    assert response.status_code == 200
    assert response.data['success'] is True
    assert any(item['suggestion'] == 'Laptop For API Search' for item in response.data['data'])


@pytest.mark.django_db
def test_saved_search_endpoints_support_create_list_and_use(user, organization):
    client = build_client(user, organization)

    create_response = client.post(
        '/api/search/saved/',
        {
            'name': 'High Value Laptops',
            'search_type': 'asset',
            'keyword': 'Laptop',
            'filters': {'purchase_price_min': 8000},
            'is_shared': True,
        },
        format='json',
    )

    assert create_response.status_code == 201
    saved_id = create_response.data['data']['id']

    list_response = client.get('/api/search/saved/', {'type': 'asset'})
    assert list_response.status_code == 200
    assert list_response.data['data']['count'] == 1

    use_response = client.post(f'/api/search/saved/{saved_id}/use/', format='json')
    assert use_response.status_code == 200
    assert use_response.data['data']['name'] == 'High Value Laptops'
    assert use_response.data['data']['is_shared'] is True


@pytest.mark.django_db
def test_shared_saved_search_is_visible_to_other_users_in_same_org(user, organization):
    other_user = User.objects.create_user(
        username='search-other-user',
        email='search-other-user@example.com',
        password='pass123456',
        organization=organization,
    )
    UserOrganization.objects.create(
        user=other_user,
        organization=organization,
        role='member',
        is_primary=True,
    )
    SavedSearch.objects.create(
        organization=organization,
        user=user,
        name='Shared Search',
        search_type='asset',
        keyword='Laptop',
        filters={'status': 'in_use'},
        is_shared=True,
        created_by=user,
    )

    client = build_client(other_user, organization)
    response = client.get('/api/search/saved/', {'type': 'asset'})

    assert response.status_code == 200
    assert response.data['data']['count'] == 1
    assert response.data['data']['results'][0]['name'] == 'Shared Search'
