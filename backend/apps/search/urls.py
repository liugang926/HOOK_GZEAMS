"""URL configuration for smart search APIs."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.search.viewsets import (
    AssetSearchAPIView,
    SavedSearchViewSet,
    SearchHistoryViewSet,
    SearchSuggestionAPIView,
)

router = DefaultRouter()
router.register(r'history', SearchHistoryViewSet, basename='search-history')
router.register(r'saved', SavedSearchViewSet, basename='saved-search')

app_name = 'search'

urlpatterns = [
    path('', AssetSearchAPIView.as_view(), name='asset-search'),
    path('assets/', AssetSearchAPIView.as_view(), name='asset-search-legacy'),
    path('suggestions/', SearchSuggestionAPIView.as_view(), name='search-suggestions'),
    path('', include(router.urls)),
]
