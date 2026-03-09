"""
Object Registry - Central service for business object registration and management.

This service provides:
1. Auto-registration of standard business objects on app startup
2. Runtime metadata caching for fast object lookup
3. Mapping between object codes and their model/viewset classes
4. Field synchronization for hardcoded Django models
"""
from typing import Dict, Optional, Type, List
from django.core.cache import cache
from django.utils.module_loading import import_string
from apps.system.object_catalog import get_hardcoded_viewset_map
from apps.system.models import BusinessObject, FieldDefinition, ModelFieldDefinition
from apps.system.services.hardcoded_object_sync_service import HardcodedObjectSyncService


class ObjectMeta:
    """
    Business object metadata container.

    Attributes:
        code: Unique object code (e.g., 'Asset', 'AssetPickup')
        name: Human-readable object name
        model_class: Django model class (if hardcoded)
        viewset_class: DRF ViewSet class (if exists)
        is_hardcoded: Whether this is a hardcoded Django model
        django_model_path: Python path to Django model
    """

    def __init__(
        self,
        code: str,
        name: str,
        model_class: Optional[Type] = None,
        viewset_class: Optional[Type] = None,
        is_hardcoded: bool = False,
        django_model_path: Optional[str] = None,
    ):
        self.code = code
        self.name = name
        self.model_class = model_class
        self.viewset_class = viewset_class
        self.is_hardcoded = is_hardcoded
        self.django_model_path = django_model_path

    def __repr__(self):
        return f"ObjectMeta(code='{self.code}', name='{self.name}', hardcoded={self.is_hardcoded})"


class ObjectRegistry:
    """
    Central registry for all business objects in the system.

    This registry maintains a mapping of object codes to their metadata,
    enabling dynamic routing without hardcoded URL configurations.

    Usage:
        # Get object metadata
        meta = ObjectRegistry.get('Asset')

        # Get from database with caching
        meta = ObjectRegistry.get_or_create_from_db('Asset')
    """

    # In-memory registry for fast lookup
    _registry: Dict[str, ObjectMeta] = {}

    # ViewSet class path mapping for hardcoded objects
    _viewset_map: Dict[str, str] = get_hardcoded_viewset_map()

    @classmethod
    def register(cls, code: str, **metadata) -> ObjectMeta:
        """
        Register a business object in the in-memory registry.

        Args:
            code: Unique object code
            **metadata: Additional metadata (name, model_class, etc.)

        Returns:
            ObjectMeta instance
        """
        meta = ObjectMeta(code=code, **metadata)
        cls._registry[code] = meta
        return meta

    @classmethod
    def get(cls, code: str) -> Optional[ObjectMeta]:
        """
        Get object metadata from in-memory registry.

        Args:
            code: Object code

        Returns:
            ObjectMeta instance or None if not found
        """
        return cls._registry.get(code)

    @classmethod
    def get_viewset_class(cls, code: str) -> Optional[Type]:
        """
        Get ViewSet class for a given object code.

        Args:
            code: Object code

        Returns:
            ViewSet class or None if not configured
        """
        viewset_path = cls._viewset_map.get(code)
        if viewset_path:
            try:
                return import_string(viewset_path)
            except ImportError:
                pass
        return None

    @classmethod
    def get_or_create_from_db(cls, code: str) -> Optional[ObjectMeta]:
        """
        Get object metadata from database with caching.

        This method first checks the cache, then the database,
        creating ObjectMeta from BusinessObject record.

        Args:
            code: Object code

        Returns:
            ObjectMeta instance or None if BusinessObject doesn't exist
        """
        # Check cache first (with fallback for Redis unavailability)
        cache_key = f"object_meta:{code}"
        try:
            cached = cache.get(cache_key)
            if cached:
                # Hot-fix: viewset mappings evolve over time, but cached ObjectMeta may lag behind.
                # Refresh critical hardcoded bindings to avoid routing to MetadataDrivenViewSet by mistake.
                try:
                    mapped_viewset = cls.get_viewset_class(code)
                    if mapped_viewset:
                        # Hardcoded mappings take precedence over stale cache payloads.
                        # This prevents old cache entries (is_hardcoded=False) from breaking custom actions.
                        cached.is_hardcoded = True
                        cached.viewset_class = mapped_viewset

                    if getattr(cached, "is_hardcoded", False):
                        if getattr(cached, "viewset_class", None) is None:
                            cached.viewset_class = cls.get_viewset_class(code)
                        if getattr(cached, "model_class", None) is None and getattr(cached, "django_model_path", None):
                            cached.model_class = import_string(cached.django_model_path)
                except Exception:
                    pass
                return cached
        except Exception:
            # Redis unavailable, continue to database query
            pass

        # Query database - BusinessObject uses GlobalMetadataManager
        # which does NOT filter by organization (metadata is global)
        try:
            bo = BusinessObject.objects.get(code=code)
            meta = cls._build_meta_from_business_object(bo)
            # Try to cache for 1 hour (ignore failures)
            try:
                cache.set(cache_key, meta, timeout=3600)
            except Exception:
                pass
            return meta
        except BusinessObject.DoesNotExist:
            return None

    @classmethod
    def _build_meta_from_business_object(cls, bo: BusinessObject) -> ObjectMeta:
        """
        Build ObjectMeta from BusinessObject database record.

        Args:
            bo: BusinessObject instance

        Returns:
            ObjectMeta instance
        """
        model_class = None
        viewset_class = cls.get_viewset_class(bo.code)

        # Hardcoded status is derived from DB flag OR hardcoded viewset mapping.
        # This makes routing resilient when BusinessObject seed data has stale flags.
        is_hardcoded = bool(bo.is_hardcoded or viewset_class)

        # Import model class when it is a hardcoded object and model path is available.
        if is_hardcoded and bo.django_model_path:
            try:
                model_class = import_string(bo.django_model_path)
            except ImportError:
                pass

        return ObjectMeta(
            code=bo.code,
            name=bo.name,
            model_class=model_class,
            viewset_class=viewset_class,
            is_hardcoded=is_hardcoded,
            django_model_path=bo.django_model_path,
        )

    @classmethod
    def auto_register_standard_objects(cls) -> int:
        """
        Automatically register standard business objects on app startup.

        This ensures BusinessObject records exist for all hardcoded models,
        and syncs their field definitions to ModelFieldDefinition.

        Returns:
            Number of objects registered/updated
        """
        count = 0
        sync_service = HardcodedObjectSyncService()
        for result in sync_service.sync_catalog(overwrite_existing=True):
            business_object = result.business_object

            if business_object.is_hardcoded:
                cls._sync_model_fields(business_object)

            cls.register(
                business_object.code,
                name=business_object.name,
                is_hardcoded=business_object.is_hardcoded,
                django_model_path=business_object.django_model_path,
            )
            count += 1
        return count

    @classmethod
    def _sync_model_fields(cls, business_object: BusinessObject) -> int:
        """
        Sync Django model fields to ModelFieldDefinition.

        This ensures that hardcoded Django models have their fields
        exposed in the metadata system for layout configuration.

        Args:
            business_object: BusinessObject instance with is_hardcoded=True

        Returns:
            Number of fields synced
        """
        if not business_object.is_hardcoded or not business_object.django_model_path:
            return 0

        try:
            model_class = import_string(business_object.django_model_path)
        except ImportError:
            return 0

        count = 0
        existing_fields = set(
            ModelFieldDefinition.objects.filter(
                business_object=business_object
            ).values_list('field_name', flat=True)
        )

        for field in model_class._meta.get_fields():
            # Skip private fields and reverse relations
            if field.name.startswith('_'):
                continue

            # Skip auto-created reverse relations
            if field.auto_created:
                continue

            try:
                field_defaults = cls._model_field_to_dict(business_object, field)
                existing = ModelFieldDefinition.objects.filter(
                    business_object=business_object,
                    field_name=field.name,
                ).first()

                if existing:
                    existing.field_type = field_defaults['field_type']
                    existing.django_field_type = field_defaults['django_field_type']
                    existing.is_required = field_defaults['is_required']
                    existing.is_readonly = field_defaults['is_readonly']
                    existing.is_editable = field_defaults['is_editable']
                    existing.is_unique = field_defaults['is_unique']
                    existing.reference_model_path = field_defaults.get('reference_model_path', '')
                    existing.max_length = field_defaults.get('max_length')
                    existing.decimal_places = field_defaults.get('decimal_places')
                    existing.max_digits = field_defaults.get('max_digits')
                    if not existing.display_name:
                        existing.display_name = field_defaults['display_name']
                    if not existing.display_name_en:
                        existing.display_name_en = field_defaults.get('display_name_en', '')
                    existing.save(update_fields=[
                        'field_type',
                        'django_field_type',
                        'is_required',
                        'is_readonly',
                        'is_editable',
                        'is_unique',
                        'reference_model_path',
                        'max_length',
                        'decimal_places',
                        'max_digits',
                        'display_name',
                        'display_name_en',
                        'updated_at',
                    ])
                else:
                    # Create field definition when metadata row is missing.
                    ModelFieldDefinition.objects.create(
                        business_object=business_object,
                        field_name=field.name,
                        **field_defaults,
                    )

                # Create or update field definition
                count += 1
            except Exception:
                continue

        # Remove fields that no longer exist in model
        ModelFieldDefinition.objects.filter(
            business_object=business_object,
            field_name__in=existing_fields - set(
                f.name for f in model_class._meta.get_fields()
                if not f.name.startswith('_') and not f.auto_created
            )
        ).delete()

        return count

    @classmethod
    def _model_field_to_dict(cls, business_object: BusinessObject, field) -> dict:
        """
        Convert Django model field to ModelFieldDefinition dict.

        Args:
            business_object: BusinessObject instance
            field: Django model field instance

        Returns:
            Dictionary for ModelFieldDefinition creation
        """
        from apps.system.models import ModelFieldDefinition

        # Get verbose name
        display_name = getattr(field, 'verbose_name', field.name) or field.name

        # Map Django field type to metadata field type
        field_type = ModelFieldDefinition.get_metadata_field_type(field)

        # Check if required
        is_required = not field.null and not field.blank

        # Check if editable
        is_editable = getattr(field, 'editable', True)

        # Get max length for text fields
        max_length = getattr(field, 'max_length', None)

        return {
            'display_name': str(display_name),
            'display_name_en': '',
            'field_type': field_type,
            'django_field_type': field.__class__.__name__,
            'is_required': is_required,
            'is_readonly': not is_editable,
            'is_editable': is_editable,
            'is_unique': getattr(field, 'unique', False),
            'show_in_list': True,
            'show_in_detail': True,
            'show_in_form': is_editable,
            'sort_order': 0,
            'max_length': max_length,
            'decimal_places': getattr(field, 'decimal_places', None),
            'max_digits': getattr(field, 'max_digits', None),
        }

    @classmethod
    def invalidate_cache(cls, code: str) -> None:
        """
        Invalidate cached metadata for a specific object.

        Args:
            code: Object code
        """
        try:
            cache.delete(f"object_meta:{code}")
        except Exception:
            pass

    @classmethod
    def invalidate_all_cache(cls) -> None:
        """Invalidate all cached metadata."""
        # This would require cache key pattern deletion
        # For now, objects expire after 1 hour automatically
        pass

    @classmethod
    def get_all_codes(cls) -> List[str]:
        """
        Get list of all registered object codes.

        Returns:
            List of object codes
        """
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, code: str) -> bool:
        """
        Check if an object code is registered.

        Args:
            code: Object code

        Returns:
            True if registered, False otherwise
        """
        return code in cls._registry
