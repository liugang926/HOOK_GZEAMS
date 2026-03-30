"""Celery tasks for asynchronous search-index synchronization."""
from celery import shared_task

from apps.assets.models import Asset
from apps.search.services import AssetSearchService


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def sync_asset_to_search_index(self, asset_id: str):
    """Synchronize a single asset document into the search index."""
    asset = Asset.all_objects.select_related(
        'asset_category',
        'department',
        'location',
        'custodian',
        'supplier',
    ).filter(pk=asset_id).first()
    if asset is None:
        return {'synced': False, 'reason': 'asset_not_found'}

    synced = AssetSearchService().sync_asset_document(asset)
    return {'synced': synced, 'asset_id': asset_id}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def delete_asset_from_search_index(self, asset_id: str):
    """Delete an asset document from the search index."""
    deleted = AssetSearchService().delete_asset_document(asset_id)
    return {'deleted': deleted, 'asset_id': asset_id}


@shared_task
def sync_assets_for_category(category_id: str):
    """Re-sync all assets affected by a category update."""
    asset_ids = list(
        Asset.all_objects.filter(asset_category_id=category_id).values_list('id', flat=True)
    )
    for asset_id in asset_ids:
        sync_asset_to_search_index.delay(str(asset_id))
    return {'queued': len(asset_ids), 'scope': 'category', 'id': category_id}


@shared_task
def sync_assets_for_location(location_id: str):
    """Re-sync all assets affected by a location update."""
    asset_ids = list(
        Asset.all_objects.filter(location_id=location_id).values_list('id', flat=True)
    )
    for asset_id in asset_ids:
        sync_asset_to_search_index.delay(str(asset_id))
    return {'queued': len(asset_ids), 'scope': 'location', 'id': location_id}


@shared_task
def sync_assets_for_tag(tag_id: str):
    """Re-sync all assets affected by a tag update."""
    asset_ids = list(
        Asset.all_objects.filter(
            asset_tag_relations__tag_id=tag_id
        ).values_list('id', flat=True).distinct()
    )
    for asset_id in asset_ids:
        sync_asset_to_search_index.delay(str(asset_id))
    return {'queued': len(asset_ids), 'scope': 'tag', 'id': tag_id}


@shared_task
def sync_all_assets_to_search_index(batch_size: int = 500):
    """Queue synchronization for every asset record."""
    queryset = Asset.all_objects.order_by('id').values_list('id', flat=True)
    queued = 0
    for asset_id in queryset.iterator(chunk_size=batch_size):
        sync_asset_to_search_index.delay(str(asset_id))
        queued += 1
    return {'queued': queued, 'batch_size': batch_size}


@shared_task
def rebuild_asset_search_index():
    """Rebuild the asset search index and queue a full backfill."""
    rebuilt = AssetSearchService().rebuild_asset_index()
    if rebuilt:
        sync_all_assets_to_search_index.delay()
    return {'rebuilt': rebuilt}
