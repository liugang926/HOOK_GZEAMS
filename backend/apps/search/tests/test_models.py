"""Model tests for smart search records."""
import pytest
from django.db import IntegrityError

from apps.search.models import SavedSearch, SearchHistory, SearchSuggestion, SearchType


@pytest.mark.django_db
def test_search_history_supports_soft_delete_and_org_scoping(user, organization, second_organization):
    history = SearchHistory.objects.create(
        organization=organization,
        user=user,
        search_type=SearchType.ASSET,
        keyword='Laptop',
        normalized_keyword='laptop',
        query_signature='sig-1',
        filters={'status': 'in_use'},
        result_count=3,
        created_by=user,
    )

    assert SearchHistory.objects.filter(user=user).count() == 1
    assert SearchHistory.objects.filter(organization=second_organization).count() == 0

    history.soft_delete(user=user)
    history.refresh_from_db()

    assert history.is_deleted is True
    assert SearchHistory.objects.filter(user=user).count() == 0


@pytest.mark.django_db
def test_saved_search_name_must_be_unique_per_user_and_organization(user, organization):
    SavedSearch.objects.create(
        organization=organization,
        user=user,
        name='High Value Assets',
        search_type=SearchType.ASSET,
        keyword='Laptop',
        filters={'purchase_price_min': 10000},
        created_by=user,
    )

    with pytest.raises(IntegrityError):
        SavedSearch.objects.create(
            organization=organization,
            user=user,
            name='High Value Assets',
            search_type=SearchType.ASSET,
            keyword='Printer',
            created_by=user,
        )


@pytest.mark.django_db
def test_search_suggestion_is_deduplicated_by_org_and_type(user, organization):
    SearchSuggestion.objects.create(
        organization=organization,
        search_type=SearchType.ASSET,
        query='Laptop',
        normalized_query='laptop',
        created_by=user,
    )

    with pytest.raises(IntegrityError):
        SearchSuggestion.objects.create(
            organization=organization,
            search_type=SearchType.ASSET,
            query='Laptop',
            normalized_query='laptop',
            created_by=user,
        )
