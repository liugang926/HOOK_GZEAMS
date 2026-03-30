"""Service tests for smart search fallback behavior."""
from decimal import Decimal

import pytest

from apps.assets.models import Asset, AssetCategory, Location, Supplier
from apps.search.models import SearchHistory, SearchSuggestion, SearchType
from apps.search.services import AssetSearchService


@pytest.fixture
def search_assets_dataset(user, organization):
    category = AssetCategory.objects.create(
        organization=organization,
        code='COMPUTER',
        name='Computer',
        created_by=user,
    )
    location = Location.objects.create(
        organization=organization,
        name='HQ Room 301',
        location_type='room',
        created_by=user,
    )
    supplier = Supplier.objects.create(
        organization=organization,
        code='SUP-001',
        name='Dell Supplier',
        created_by=user,
    )
    matched_asset = Asset.objects.create(
        organization=organization,
        created_by=user,
        asset_code='ASSET-LAPTOP-001',
        asset_name='Dell Laptop Pro',
        asset_category=category,
        specification='14 inch business laptop',
        brand='Dell',
        model='Latitude',
        serial_number='SN-LAPTOP-001',
        purchase_price=Decimal('12000.00'),
        current_value=Decimal('9800.00'),
        purchase_date='2026-01-15',
        location=location,
        supplier=supplier,
        asset_status='in_use',
    )
    other_asset = Asset.objects.create(
        organization=organization,
        created_by=user,
        asset_code='ASSET-PRINTER-001',
        asset_name='Office Printer',
        asset_category=category,
        specification='Laser printer',
        brand='HP',
        model='LaserJet',
        serial_number='SN-PRINTER-001',
        purchase_price=Decimal('3200.00'),
        current_value=Decimal('2700.00'),
        purchase_date='2026-02-01',
        location=location,
        supplier=supplier,
        asset_status='idle',
    )
    return {
        'category': category,
        'location': location,
        'supplier': supplier,
        'matched_asset': matched_asset,
        'other_asset': other_asset,
    }


@pytest.mark.django_db
def test_asset_search_service_fallback_returns_results_highlights_aggregations_and_history(
    user,
    organization,
    search_assets_dataset,
):
    service = AssetSearchService()

    result = service.search_assets(
        organization_id=str(organization.id),
        user=user,
        keyword='Laptop',
        filters={'status': 'in_use'},
        sort_by='relevance',
        sort_order='desc',
        page=1,
        page_size=20,
    )

    assert result['engine'] == 'database'
    assert result['total'] == 1
    assert result['results'][0]['id'] == str(search_assets_dataset['matched_asset'].id)
    assert '<em>Laptop</em>' in result['results'][0]['highlight']['asset_name'][0]
    assert result['aggregations']['status']['in_use'] == 1
    assert SearchHistory.objects.filter(user=user, keyword='Laptop').count() == 1
    assert SearchSuggestion.objects.filter(
        organization=organization,
        search_type=SearchType.ASSET,
        normalized_query='laptop',
    ).count() == 1


@pytest.mark.django_db
def test_asset_search_service_database_suggestions_merge_cached_queries_and_asset_values(
    user,
    organization,
    search_assets_dataset,
):
    SearchSuggestion.objects.create(
        organization=organization,
        search_type=SearchType.ASSET,
        query='Laptop Rollout',
        normalized_query='laptop rollout',
        frequency=8,
        created_by=user,
    )

    suggestions = AssetSearchService().get_suggestions(
        organization_id=str(organization.id),
        keyword='Lap',
        search_type=SearchType.ASSET,
        limit=10,
    )

    labels = [item['suggestion'] for item in suggestions]
    assert 'Laptop Rollout' in labels
    assert 'Dell Laptop Pro' in labels
