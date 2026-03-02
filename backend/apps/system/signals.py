"""
Signal handlers for the system app.

Handles cleanup tasks when objects are deleted, such as
removing associated translations.
"""
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from apps.system.models import Translation


# Define which models have translatable fields
# This attribute should be added to models that can have object translations
TRANSLATABLE_MODELS = {
    'BusinessObject',
    'DictionaryType',
    'DictionaryItem',
    'ModelFieldDefinition',
    'Department',
    'Asset',
    'AssetCategory',
    'Location',
    'Supplier',
}


@receiver(post_delete)
def cleanup_translations(sender, instance, **kwargs):
    """
    Delete translations when an object is deleted.

    Only processes models that have been explicitly marked as translatable
    by having their model class name in TRANSLATABLE_MODELS.

    The cleanup is done via Django's CASCADE behavior on the GenericForeignKey,
    but we also ensure soft-deleted objects have their translations soft-deleted.
    """
    # Check if this model type is translatable
    model_name = sender.__name__
    if model_name not in TRANSLATABLE_MODELS:
        return

    # For soft deletes (handled elsewhere), translations should be soft-deleted too
    # This signal handles hard deletes (physical deletion from database)
    try:
        content_type = ContentType.objects.get_for_model(sender, for_concrete_model=False)
        Translation.objects.filter(
            content_type=content_type,
            object_id=instance.pk
        ).delete()
    except Exception:
        # Silently fail - cleanup is not critical
        pass
