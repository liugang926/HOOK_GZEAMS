"""Signal handlers for keeping the search index in sync."""
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.assets.models import Asset, AssetCategory, AssetTag, AssetTagRelation, Location
from apps.search.tasks import (
    delete_asset_from_search_index,
    sync_asset_to_search_index,
    sync_assets_for_category,
    sync_assets_for_location,
    sync_assets_for_tag,
)


def run_after_commit(callback):
    """Schedule a callable after the current transaction commits."""
    try:
        transaction.on_commit(callback)
    except RuntimeError:
        callback()


@receiver(post_save, sender=Asset)
def sync_asset_after_save(sender, instance: Asset, **kwargs):
    """Sync the asset document after save and soft-delete operations."""
    run_after_commit(lambda: sync_asset_to_search_index.delay(str(instance.id)))


@receiver(post_delete, sender=Asset)
def remove_asset_after_delete(sender, instance: Asset, **kwargs):
    """Delete the asset document after a hard delete."""
    run_after_commit(lambda: delete_asset_from_search_index.delay(str(instance.id)))


@receiver(post_save, sender=AssetTagRelation)
def sync_asset_after_tag_relation_save(sender, instance: AssetTagRelation, **kwargs):
    """Sync the linked asset after tag assignment changes."""
    run_after_commit(lambda: sync_asset_to_search_index.delay(str(instance.asset_id)))


@receiver(post_delete, sender=AssetTagRelation)
def sync_asset_after_tag_relation_delete(sender, instance: AssetTagRelation, **kwargs):
    """Sync the linked asset after tag assignment deletion."""
    run_after_commit(lambda: sync_asset_to_search_index.delay(str(instance.asset_id)))


@receiver(post_save, sender=AssetCategory)
def sync_assets_after_category_save(sender, instance: AssetCategory, **kwargs):
    """Sync assets affected by category metadata changes."""
    run_after_commit(lambda: sync_assets_for_category.delay(str(instance.id)))


@receiver(post_save, sender=Location)
def sync_assets_after_location_save(sender, instance: Location, **kwargs):
    """Sync assets affected by location metadata changes."""
    run_after_commit(lambda: sync_assets_for_location.delay(str(instance.id)))


@receiver(post_save, sender=AssetTag)
def sync_assets_after_tag_save(sender, instance: AssetTag, **kwargs):
    """Sync assets affected by tag metadata changes."""
    run_after_commit(lambda: sync_assets_for_tag.delay(str(instance.id)))
