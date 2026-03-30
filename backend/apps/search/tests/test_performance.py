"""Performance regression tests for the smart-search module."""
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.assets.models import Asset, AssetCategory, Location, Supplier
from apps.search.models import SavedSearch, SearchHistory, SearchType
from apps.search.serializers import SavedSearchSerializer, SearchHistorySerializer
from apps.search.services import AssetSearchService
from apps.search.viewsets import SavedSearchViewSet, SearchHistoryViewSet


def _serialize_and_count_queries(serializer_class, queryset) -> int:
    """Measure serializer query count for the provided queryset."""
    with CaptureQueriesContext(connection) as captured_queries:
        serializer_class(queryset, many=True).data
    return len(captured_queries)


@pytest.mark.django_db
def test_search_history_queryset_does_not_add_row_level_user_queries(user, organization):
    records = [
        SearchHistory.objects.create(
            organization=organization,
            user=user,
            search_type=SearchType.ASSET,
            keyword=f'Laptop {index}',
            normalized_keyword=f'laptop {index}',
            query_signature=f'signature-{index}',
            filters={'status': 'in_use'},
            result_count=index,
            created_by=user,
            updated_by=user,
        )
        for index in range(1, 4)
    ]

    single_queryset = SearchHistoryViewSet.queryset.filter(pk=records[0].pk)
    multi_queryset = SearchHistoryViewSet.queryset.filter(pk__in=[record.pk for record in records])

    single_queries = _serialize_and_count_queries(SearchHistorySerializer, single_queryset)
    multi_queries = _serialize_and_count_queries(SearchHistorySerializer, multi_queryset)

    # Adding more rows should not trigger extra nested-user queries.
    assert multi_queries <= single_queries + 1


@pytest.mark.django_db
def test_saved_search_queryset_does_not_add_row_level_user_queries(user, organization):
    records = [
        SavedSearch.objects.create(
            organization=organization,
            user=user,
            name=f'Saved Search {index}',
            search_type=SearchType.ASSET,
            keyword=f'Laptop {index}',
            filters={'status': 'in_use'},
            is_shared=index % 2 == 0,
            created_by=user,
            updated_by=user,
        )
        for index in range(1, 4)
    ]

    single_queryset = SavedSearchViewSet.queryset.filter(pk=records[0].pk)
    multi_queryset = SavedSearchViewSet.queryset.filter(pk__in=[record.pk for record in records])

    single_queries = _serialize_and_count_queries(SavedSearchSerializer, single_queryset)
    multi_queries = _serialize_and_count_queries(SavedSearchSerializer, multi_queryset)

    # The eager-loaded queryset should keep serialization cost almost constant.
    assert multi_queries <= single_queries + 1


@pytest.mark.django_db
def test_asset_search_query_count_is_stable_as_page_size_grows(user, organization):
    category = AssetCategory.objects.create(
        organization=organization,
        code='PERF-LAPTOP',
        name='Performance Laptop',
        created_by=user,
    )
    location = Location.objects.create(
        organization=organization,
        name='Performance Lab',
        location_type='room',
        created_by=user,
    )
    supplier = Supplier.objects.create(
        organization=organization,
        code='SUP-PERF',
        name='Performance Supplier',
        created_by=user,
    )

    for index in range(1, 4):
        Asset.objects.create(
            organization=organization,
            created_by=user,
            asset_code=f'PERF-LAPTOP-{index:03d}',
            asset_name=f'Performance Laptop {index}',
            asset_category=category,
            specification='Performance regression device',
            brand='ThinkPad',
            model=f'P{index}',
            serial_number=f'PERF-SN-{index:03d}',
            purchase_price=Decimal('12000.00') + index,
            current_value=Decimal('9000.00'),
            purchase_date='2026-01-15',
            location=location,
            supplier=supplier,
            asset_status='in_use',
        )

    service = AssetSearchService()

    with CaptureQueriesContext(connection) as single_page_queries:
        single_page = service.search_assets(
            organization_id=str(organization.id),
            user=user,
            keyword='Performance Laptop',
            filters={'status': 'in_use'},
            sort_by='relevance',
            sort_order='desc',
            page=1,
            page_size=1,
            record_history=False,
        )

    with CaptureQueriesContext(connection) as multi_page_queries:
        multi_page = service.search_assets(
            organization_id=str(organization.id),
            user=user,
            keyword='Performance Laptop',
            filters={'status': 'in_use'},
            sort_by='relevance',
            sort_order='desc',
            page=1,
            page_size=3,
            record_history=False,
        )

    assert single_page['total'] == 3
    assert multi_page['total'] == 3
    assert len(multi_page['results']) == 3

    # Larger pages should reuse eager-loaded relations and status-label lookup
    # rather than adding a query per result row.
    assert len(multi_page_queries) <= len(single_page_queries) + 1
