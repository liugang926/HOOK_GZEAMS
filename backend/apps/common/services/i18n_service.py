"""
Translation service for internationalization (i18n).

Provides:
- Unified translation interface
- Translation caching
- Language pack generation
- Missing translation tracking
"""
from typing import Dict, Optional, Any, List
from django.core.cache import cache
import threading


# Thread-local storage for current language
_thread_locals = threading.local()


def get_current_language() -> str:
    """Get current language from thread-local storage."""
    return getattr(_thread_locals, 'language', 'zh-CN')


def set_current_language(lang_code: str) -> None:
    """Set current language in thread-local storage."""
    _thread_locals.language = lang_code


def clear_current_language() -> None:
    """Clear current language from thread-local storage."""
    if hasattr(_thread_locals, 'language'):
        del _thread_locals.language


class TranslationCache:
    """
    Cache manager for translations.
    """

    CACHE_PREFIX = 'i18n'
    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def _make_key(cls, *parts: str) -> str:
        """Generate cache key from parts."""
        return f'{cls.CACHE_PREFIX}:{":".join(str(p) for p in parts)}'

    @classmethod
    def get_translation(
        cls,
        namespace: str,
        key: str,
        lang_code: str
    ) -> Optional[str]:
        """Get single translation from cache."""
        cache_key = cls._make_key('text', namespace, key, lang_code)
        return cache.get(cache_key)

    @classmethod
    def set_translation(
        cls,
        namespace: str,
        key: str,
        lang_code: str,
        text: str
    ) -> None:
        """Set single translation in cache."""
        cache_key = cls._make_key('text', namespace, key, lang_code)
        cache.set(cache_key, text, cls.CACHE_TIMEOUT)

    @classmethod
    def get_namespace(
        cls,
        namespace: str,
        lang_code: str
    ) -> Optional[Dict[str, str]]:
        """Get all translations for a namespace."""
        cache_key = cls._make_key('ns', namespace, lang_code)
        return cache.get(cache_key)

    @classmethod
    def set_namespace(
        cls,
        namespace: str,
        lang_code: str,
        translations: Dict[str, str]
    ) -> None:
        """Set all translations for a namespace."""
        cache_key = cls._make_key('ns', namespace, lang_code)
        cache.set(cache_key, translations, cls.CACHE_TIMEOUT)

    @classmethod
    def get_language_pack(cls, lang_code: str) -> Optional[Dict]:
        """Get full language pack from cache."""
        cache_key = cls._make_key('pack', lang_code)
        return cache.get(cache_key)

    @classmethod
    def set_language_pack(cls, lang_code: str, pack: Dict) -> None:
        """Set full language pack in cache."""
        cache_key = cls._make_key('pack', lang_code)
        cache.set(cache_key, pack, cls.CACHE_TIMEOUT)

    @classmethod
    def invalidate_namespace(cls, namespace: str) -> None:
        """Clear cache for a namespace."""
        # Note: Pattern deletion only works with Redis
        try:
            from django_redis import get_redis_connection
            conn = get_redis_connection('default')
            pattern = cls._make_key('*', namespace, '*')
            keys = conn.keys(pattern)
            if keys:
                conn.delete(*keys)
        except Exception:
            pass

    @classmethod
    def invalidate_language(cls, lang_code: str) -> None:
        """Clear cache for a language."""
        cache.delete(cls._make_key('pack', lang_code))

    @classmethod
    def invalidate_all(cls) -> None:
        """Clear all translation caches."""
        try:
            from django_redis import get_redis_connection
            conn = get_redis_connection('default')
            pattern = f'{cls.CACHE_PREFIX}:*'
            keys = conn.keys(pattern)
            if keys:
                conn.delete(*keys)
        except Exception:
            pass


class TranslationService:
    """
    Centralized translation service.

    Provides static methods for:
    - Getting translations
    - Getting language packs
    - Translating model instances
    """

    DEFAULT_LANGUAGE = 'zh-CN'
    SUPPORTED_LANGUAGES = ['zh-CN', 'en-US', 'ja-JP']

    @staticmethod
    def get_current_language() -> str:
        """Get current language code."""
        return get_current_language()

    @staticmethod
    def set_current_language(lang_code: str) -> None:
        """Set current language code."""
        set_current_language(lang_code)

    @staticmethod
    def get_text(
        namespace: str,
        key: str,
        lang_code: Optional[str] = None,
        default: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Get translated text.

        Args:
            namespace: Translation namespace (e.g., 'asset', 'common')
            key: Translation key (e.g., 'status.idle')
            lang_code: Language code (default: current language)
            default: Default value if translation not found
            use_cache: Whether to use cache

        Returns:
            Translated text or default
        """
        lang_code = lang_code or get_current_language()
        default = default if default is not None else key

        # Check cache
        if use_cache:
            cached = TranslationCache.get_translation(namespace, key, lang_code)
            if cached is not None:
                return cached

        # Query database
        try:
            from apps.system.models import Translation
            translation = Translation.objects.filter(
                namespace=namespace,
                key=key,
                language_code=lang_code,
                is_deleted=False
            ).first()

            if translation:
                text = translation.text
                if use_cache:
                    TranslationCache.set_translation(namespace, key, lang_code, text)
                return text
        except Exception:
            pass

        return default

    @staticmethod
    def get_text_auto(
        key: str,
        lang_code: Optional[str] = None,
        default: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Get translation with auto-parsed namespace.

        Key format: 'namespace.key' (e.g., 'asset.status.idle')
        """
        parts = key.split('.', 1)
        if len(parts) == 2:
            namespace, actual_key = parts
        else:
            namespace, actual_key = 'common', key

        return TranslationService.get_text(
            namespace, actual_key, lang_code, default, use_cache
        )

    @staticmethod
    def get_namespace(
        namespace: str,
        lang_code: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, str]:
        """
        Get all translations for a namespace.

        Args:
            namespace: Namespace to get
            lang_code: Language code
            use_cache: Whether to use cache

        Returns:
            Dict mapping keys to translated text
        """
        lang_code = lang_code or get_current_language()

        # Check cache
        if use_cache:
            cached = TranslationCache.get_namespace(namespace, lang_code)
            if cached is not None:
                return cached

        # Query database
        translations = {}
        try:
            from apps.system.models import Translation
            qs = Translation.objects.filter(
                namespace=namespace,
                language_code=lang_code,
                is_deleted=False
            ).values('key', 'text')

            for item in qs:
                translations[item['key']] = item['text']

            if use_cache and translations:
                TranslationCache.set_namespace(namespace, lang_code, translations)
        except Exception:
            pass

        return translations

    @staticmethod
    def get_language_pack(
        lang_code: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Dict[str, str]]:
        """
        Get full language pack for frontend.

        Returns nested dict: {namespace: {key: text}}
        """
        lang_code = lang_code or get_current_language()

        # Check cache
        if use_cache:
            cached = TranslationCache.get_language_pack(lang_code)
            if cached is not None:
                return cached

        # Build language pack
        pack = {}
        try:
            from apps.system.models import Translation
            qs = Translation.objects.filter(
                language_code=lang_code,
                is_deleted=False
            ).values('namespace', 'key', 'text')

            for item in qs:
                ns = item['namespace']
                key = item['key']
                text = item['text']

                if ns not in pack:
                    pack[ns] = {}

                # Support nested keys (e.g., 'status.idle')
                TranslationService._set_nested(pack[ns], key, text)

            if use_cache and pack:
                TranslationCache.set_language_pack(lang_code, pack)
        except Exception:
            pass

        return pack

    @staticmethod
    def _set_nested(d: Dict, key: str, value: Any) -> None:
        """Set nested dict value for dotted key."""
        parts = key.split('.')
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value

    @staticmethod
    def translate_object(
        instance,
        lang_code: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Translate model instance fields.

        Args:
            instance: Model instance
            lang_code: Target language
            fields: Fields to translate (default: all *_translations fields)

        Returns:
            Dict with translated field values
        """
        lang_code = lang_code or get_current_language()
        result = {}

        # Find translatable fields
        for field_name in dir(instance):
            if fields and field_name not in fields:
                continue

            if field_name.endswith('_translations'):
                base_field = field_name.replace('_translations', '')
                translations = getattr(instance, field_name, None)

                if isinstance(translations, dict):
                    # Get translation for current language
                    translated = translations.get(lang_code)
                    if not translated:
                        # Fallback to default language
                        translated = translations.get(TranslationService.DEFAULT_LANGUAGE)
                    if not translated:
                        # Fallback to any available translation
                        translated = next(iter(translations.values()), None)

                    result[f'{base_field}_i18n'] = translated
                    result[base_field] = getattr(instance, base_field, None)

        return result

    @staticmethod
    def create_translation(
        namespace: str,
        key: str,
        translations: Dict[str, str],
        context: Optional[str] = None,
        translation_type: str = 'label',
        default_text: Optional[str] = None
    ) -> Any:
        """
        Create or update translations.

        Args:
            namespace: Namespace
            key: Translation key
            translations: {lang_code: text} dict
            context: Optional context for disambiguation
            translation_type: 'label', 'message', or 'enum'
            default_text: Default text

        Returns:
            Created/updated Translation instance
        """
        try:
            from apps.system.models import Translation

            created_translations = []
            for lang_code, text in translations.items():
                trans, created = Translation.objects.update_or_create(
                    namespace=namespace,
                    key=key,
                    language_code=lang_code,
                    defaults={
                        'text': text,
                        'context': context,
                        'type': translation_type,
                        'default_text': default_text or text,
                    }
                )
                created_translations.append(trans)

                # Invalidate cache
                TranslationCache.invalidate_namespace(namespace)
                TranslationCache.invalidate_language(lang_code)

            return created_translations[0] if created_translations else None
        except Exception as e:
            raise ValueError(f"Failed to create translation: {e}")

    @staticmethod
    def get_available_languages() -> List[Dict[str, Any]]:
        """
        Get list of available languages.

        Returns:
            List of language info dicts
        """
        return [
            {
                'code': 'zh-CN',
                'name': 'Chinese (Simplified)',
                'native_name': '简体中文',
                'flag': '🇨🇳',
                'is_default': True
            },
            {
                'code': 'en-US',
                'name': 'English (US)',
                'native_name': 'English',
                'flag': '🇺🇸',
                'is_default': False
            },
            {
                'code': 'ja-JP',
                'name': 'Japanese',
                'native_name': '日本語',
                'flag': '🇯🇵',
                'is_default': False
            },
        ]

    # =========================================================================
    # GenericForeignKey Translation Methods
    # =========================================================================

    @staticmethod
    def get_object_translation(
        obj,
        field_name: str,
        lang_code: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Get translation for a dynamic object field via GenericForeignKey.

        Args:
            obj: Model instance to translate
            field_name: Field name being translated (e.g., 'name', 'description')
            lang_code: Target language code
            use_cache: Whether to use cache

        Returns:
            Translated text or None if not found
        """
        from django.contrib.contenttypes.models import ContentType
        from apps.system.models import Translation

        lang_code = lang_code or get_current_language()
        content_type = ContentType.objects.get_for_model(obj)

        # Check cache
        if use_cache:
            cache_key = TranslationCache._make_key(
                'gfk', content_type.model, obj.pk, field_name, lang_code
            )
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        # Query database
        try:
            translation = Translation.objects.filter(
                content_type=content_type,
                object_id=obj.pk,
                field_name=field_name,
                language_code=lang_code,
                is_deleted=False
            ).first()

            if translation:
                text = translation.text
                if use_cache:
                    cache.set(cache_key, text, TranslationCache.CACHE_TIMEOUT)
                return text
        except Exception:
            pass

        return None

    @staticmethod
    def get_localized_value(
        obj,
        field_name: str,
        lang_code: Optional[str] = None,
        fallback_to_original: bool = True
    ) -> str:
        """
        Get localized value for an object field.

        Priority:
        1. Translation from Translation table (GenericForeignKey)
        2. Field-specific translation (e.g., name_en for 'name' field in English)
        3. Original field value

        Args:
            obj: Model instance
            field_name: Field name to translate
            lang_code: Target language code
            fallback_to_original: Whether to fallback to original value

        Returns:
            Localized value or empty string
        """
        lang_code = lang_code or get_current_language()

        # Try GenericForeignKey translation first
        translation = TranslationService.get_object_translation(obj, field_name, lang_code)
        if translation:
            return translation

        # Try field-specific translation (e.g., name_en)
        if lang_code == 'en-US' or lang_code.startswith('en'):
            en_field = f'{field_name}_en'
            en_value = getattr(obj, en_field, None)
            if en_value:
                return en_value

        # Fallback to original value
        if fallback_to_original:
            original_value = getattr(obj, field_name, '')
            return original_value if original_value else ''

        return ''

    @staticmethod
    def get_object_translations(
        obj,
        lang_code: Optional[str] = None,
        field_names: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Get all translations for an object.

        Args:
            obj: Model instance
            lang_code: Target language code
            field_names: Specific fields to translate (default: all available)

        Returns:
            Dict mapping field names to translated values
        """
        from django.contrib.contenttypes.models import ContentType
        from apps.system.models import Translation

        lang_code = lang_code or get_current_language()
        content_type = ContentType.objects.get_for_model(obj)

        result = {}

        # Query all translations for this object
        try:
            qs = Translation.objects.filter(
                content_type=content_type,
                object_id=obj.pk,
                language_code=lang_code,
                is_deleted=False
            )

            if field_names:
                qs = qs.filter(field_name__in=field_names)

            for trans in qs:
                result[trans.field_name] = trans.text
        except Exception:
            pass

        return result

    @staticmethod
    def set_object_translation(
        obj,
        field_name: str,
        text: str,
        lang_code: str,
        context: Optional[str] = None
    ) -> Any:
        """
        Set translation for an object field.

        Args:
            obj: Model instance
            field_name: Field name being translated
            text: Translated text
            lang_code: Target language code
            context: Optional context

        Returns:
            Created or updated Translation instance
        """
        from django.contrib.contenttypes.models import ContentType
        from apps.system.models import Translation

        content_type = ContentType.objects.get_for_model(obj)

        translation, created = Translation.objects.update_or_create(
            content_type=content_type,
            object_id=obj.pk,
            field_name=field_name,
            language_code=lang_code,
            defaults={
                'text': text,
                'context': context or '',
                'type': 'object_field',
            }
        )

        # Invalidate cache
        TranslationCache.invalidate_all()

        return translation

    @staticmethod
    def delete_object_translations(
        obj,
        field_names: Optional[List[str]] = None
    ) -> int:
        """
        Delete translations for an object.

        Args:
            obj: Model instance
            field_names: Specific fields to delete (default: all)

        Returns:
            Number of translations deleted
        """
        from django.contrib.contenttypes.models import ContentType
        from apps.system.models import Translation

        content_type = ContentType.objects.get_for_model(obj)

        qs = Translation.objects.filter(
            content_type=content_type,
            object_id=obj.pk
        )

        if field_names:
            qs = qs.filter(field_name__in=field_names)

        count = qs.count()
        qs.delete()

        # Invalidate cache
        TranslationCache.invalidate_all()

        return count

    @staticmethod
    def bulk_get_object_translations(
        objects: List,
        field_name: str,
        lang_code: Optional[str] = None
    ) -> Dict[int, str]:
        """
        Bulk get translations for multiple objects (N+1 query optimization).

        Args:
            objects: List of model instances
            field_name: Field name to translate
            lang_code: Target language code

        Returns:
            Dict mapping object IDs to translated values
        """
        from django.contrib.contenttypes.models import ContentType
        from apps.system.models import Translation

        if not objects:
            return {}

        lang_code = lang_code or get_current_language()
        first_obj = objects[0]
        content_type = ContentType.objects.get_for_model(first_obj)

        # Get all object IDs
        object_ids = [obj.pk for obj in objects]

        # Query all translations in one go
        result = {}
        try:
            qs = Translation.objects.filter(
                content_type=content_type,
                object_id__in=object_ids,
                field_name=field_name,
                language_code=lang_code,
                is_deleted=False
            )

            for trans in qs:
                result[trans.object_id] = trans.text
        except Exception:
            pass

        return result


class TranslatedFieldMixin:
    """
    Mixin for serializers to auto-translate fields.

    Usage:
        class AssetSerializer(TranslatedFieldMixin, ModelSerializer):
            class Meta:
                model = Asset
                fields = ['id', 'name', 'status']
    """

    def __init__(self, *args, **kwargs):
        self._lang_code = kwargs.pop('lang_code', None)
        super().__init__(*args, **kwargs)

    def get_language_from_context(self) -> str:
        """Get language from request context or default."""
        if self._lang_code:
            return self._lang_code

        request = self.context.get('request')
        if request:
            # Check Accept-Language header
            lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            if lang and lang in TranslationService.SUPPORTED_LANGUAGES:
                return lang

            # Check query parameter
            lang = request.query_params.get('lang')
            if lang and lang in TranslationService.SUPPORTED_LANGUAGES:
                return lang

        return TranslationService.DEFAULT_LANGUAGE

    def to_representation(self, instance):
        """Add translated fields to output."""
        data = super().to_representation(instance)
        lang_code = self.get_language_from_context()

        # Add translated fields
        translations = TranslationService.translate_object(instance, lang_code)
        data.update(translations)

        return data

    # Delegate GenericForeignKey translation methods to TranslationService
    @staticmethod
    def get_object_translation(obj, field_name: str, lang_code: Optional[str] = None, use_cache: bool = True) -> Optional[str]:
        """Get object field translation (delegates to TranslationService)."""
        return TranslationService.get_object_translation(obj, field_name, lang_code, use_cache)

    @staticmethod
    def get_localized_value(obj, field_name: str, lang_code: Optional[str] = None, fallback_to_original: bool = True) -> str:
        """Get localized value (delegates to TranslationService)."""
        return TranslationService.get_localized_value(obj, field_name, lang_code, fallback_to_original)

    @staticmethod
    def get_object_translations(obj, lang_code: Optional[str] = None, field_names: Optional[List[str]] = None) -> Dict[str, str]:
        """Get all object translations (delegates to TranslationService)."""
        return TranslationService.get_object_translations(obj, lang_code, field_names)

    @staticmethod
    def set_object_translation(obj, field_name: str, text: str, lang_code: str, context: Optional[str] = None) -> Any:
        """Set object translation (delegates to TranslationService)."""
        return TranslationService.set_object_translation(obj, field_name, text, lang_code, context)

    @staticmethod
    def delete_object_translations(obj, field_names: Optional[List[str]] = None) -> int:
        """Delete object translations (delegates to TranslationService)."""
        return TranslationService.delete_object_translations(obj, field_names)

    @staticmethod
    def bulk_get_object_translations(objects: List, field_name: str, lang_code: Optional[str] = None) -> Dict[int, str]:
        """Bulk get object translations (delegates to TranslationService)."""
        return TranslationService.bulk_get_object_translations(objects, field_name, lang_code)


# Alias for backward compatibility
I18nService = TranslationService
