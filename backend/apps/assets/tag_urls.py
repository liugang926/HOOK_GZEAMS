"""
Compatibility URL patterns for Phase 7.3 asset tag endpoints.
"""
from django.urls import path

from apps.assets.viewsets import AssetTagViewSet, AssetViewSet, TagGroupViewSet


urlpatterns = [
    path(
        'tags/groups/',
        TagGroupViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='asset-tag-group-list',
    ),
    path(
        'tags/groups/<uuid:pk>/',
        TagGroupViewSet.as_view(
            {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}
        ),
        name='asset-tag-group-detail',
    ),
    path(
        'tags/',
        AssetTagViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='asset-tag-list',
    ),
    path(
        'tags/statistics/',
        AssetTagViewSet.as_view({'get': 'statistics'}),
        name='asset-tag-statistics',
    ),
    path(
        'tags/batch-add/',
        AssetTagViewSet.as_view({'post': 'batch_add'}),
        name='asset-tag-batch-add',
    ),
    path(
        'tags/batch-remove/',
        AssetTagViewSet.as_view({'post': 'batch_remove'}),
        name='asset-tag-batch-remove',
    ),
    path(
        'tags/<uuid:pk>/',
        AssetTagViewSet.as_view(
            {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}
        ),
        name='asset-tag-detail',
    ),
    path(
        'assets/by-tags/',
        AssetViewSet.as_view({'post': 'by_tags'}),
        name='asset-by-tags',
    ),
    path(
        'assets/<uuid:pk>/tags/',
        AssetViewSet.as_view({'get': 'tags', 'post': 'tags'}),
        name='asset-tags',
    ),
    path(
        'assets/<uuid:pk>/tags/<uuid:tag_id>/',
        AssetViewSet.as_view({'delete': 'remove_tag'}),
        name='asset-tag-remove',
    ),
]
