"""
Internationalization (i18n) ViewSets - API endpoints for translations and languages.

Provides:
- Language management (CRUD + set default)
- Translation management (CRUD + bulk operations)
- Object-scoped translations
- Translation export/import
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from apps.common.viewsets import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.system.models import Translation, Language
from apps.system.serializers import (
    LanguageSerializer,
    LanguageListSerializer,
    TranslationSerializer,
    TranslationListSerializer,
    TranslationCreateSerializer,
    TranslationBulkSerializer,
    ObjectTranslationSerializer,
)
from apps.system.filters import TranslationFilter, LanguageFilter


class LanguageViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Language model.

    Provides CRUD operations for language configuration.
    Uses GlobalMetadataManager - languages are shared across organizations.
    """

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LanguageFilter
    search_fields = ['code', 'name', 'native_name']
    ordering = ['sort_order', 'code']

    def get_serializer_class(self):
        """Use lightweight serializer for list actions."""
        if self.action == 'list':
            return LanguageListSerializer
        return LanguageSerializer

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """
        Get all active languages.

        Returns languages with is_active=True, ordered by sort_order.
        """
        languages = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(languages, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='set-default')
    def set_default(self, request, pk=None):
        """
        Set a language as the default language.

        Only one language can be default at a time.
        This will unset is_default on all other languages.
        """
        language = self.get_object()

        # Unset default on all languages
        Language.objects.all().update(is_default=False)

        # Set this language as default
        language.is_default = True
        language.save()

        # Clear translation cache
        from apps.common.services.i18n_service import TranslationCache
        TranslationCache.invalidate_all()

        serializer = self.get_serializer(language)
        return Response({
            'success': True,
            'message': f'{language.name} set as default language.',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='default')
    def get_default(self, request):
        """
        Get the default language.
        """
        language = self.get_queryset().filter(is_default=True).first()
        if not language:
            # Fallback to zh-CN if no default set
            language = self.get_queryset().filter(code='zh-CN').first()

        if language:
            serializer = self.get_serializer(language)
            return Response({
                'success': True,
                'data': serializer.data
            })

        return Response({
            'success': False,
            'error': 'No default language configured'
        }, status=status.HTTP_404_NOT_FOUND)


class TranslationViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Translation model.

    Provides CRUD operations for translations.
    Supports both namespace/key and GenericForeignKey patterns.
    Uses GlobalMetadataManager - translations are shared metadata.
    """

    queryset = Translation.objects.select_related('content_type').all()
    serializer_class = TranslationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TranslationFilter
    search_fields = ['key', 'text', 'context']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use lightweight serializer for list actions."""
        if self.action == 'list':
            return TranslationListSerializer
        return TranslationSerializer

    def get_locale(self):
        """
        Get locale from request headers or query parameters.

        Priority:
        1. Accept-Language header
        2. locale query parameter
        3. Default to 'zh-CN'
        """
        request = self.context.get('request') if hasattr(self, 'context') else self.request
        if request:
            # Check Accept-Language header
            locale = request.headers.get('Accept-Language', '')
            if locale:
                return locale.split(',')[0].strip()
            # Check query parameter
            locale = request.query_params.get('locale', '')
            if locale:
                return locale
        return 'zh-CN'

    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk(self, request):
        """
        Bulk create or update translations.

        Request body:
        {
            "translations": [
                {
                    "namespace": "asset",
                    "key": "status.idle",
                    "language_code": "en-US",
                    "text": "Idle"
                },
                ...
            ]
        }

        Response:
        {
            "success": true,
            "summary": {
                "total": 10,
                "created": 5,
                "updated": 5,
                "failed": 0
            },
            "results": [...]
        }
        """
        serializer = TranslationBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        translations_data = serializer.validated_data['translations']
        results = []
        created_count = 0
        updated_count = 0
        failed_count = 0

        for trans_data in translations_data:
            try:
                # Handle content_type string to model conversion
                content_type = None
                if trans_data.get('content_type'):
                    app_label, model = trans_data['content_type'].split('.')
                    content_type = ContentType.objects.get(
                        app_label=app_label,
                        model=model.lower()
                    )

                # Build lookup kwargs
                lookup_kwargs = {
                    'language_code': trans_data['language_code'],
                    'is_deleted': False
                }

                if trans_data.get('namespace') and trans_data.get('key'):
                    lookup_kwargs.update({
                        'namespace': trans_data['namespace'],
                        'key': trans_data['key'],
                    })
                else:
                    lookup_kwargs.update({
                        'content_type': content_type,
                        'object_id': trans_data['object_id'],
                        'field_name': trans_data.get('field_name', ''),
                    })

                # Try to get existing translation
                translation = Translation.objects.filter(**lookup_kwargs).first()

                if translation:
                    # Update existing
                    translation.text = trans_data['text']
                    translation.context = trans_data.get('context', '')
                    translation.type = trans_data.get('type', 'label')
                    translation.updated_by = request.user
                    translation.save()
                    updated_count += 1
                    results.append({
                        'id': str(translation.id),
                        'action': 'updated',
                        'success': True
                    })
                else:
                    # Create new
                    translation = Translation.objects.create(
                        namespace=trans_data.get('namespace', ''),
                        key=trans_data.get('key', ''),
                        content_type=content_type,
                        object_id=trans_data.get('object_id'),
                        field_name=trans_data.get('field_name', ''),
                        language_code=trans_data['language_code'],
                        text=trans_data['text'],
                        context=trans_data.get('context', ''),
                        type=trans_data.get('type', 'label'),
                        created_by=request.user,
                        updated_by=request.user
                    )
                    created_count += 1
                    results.append({
                        'id': str(translation.id),
                        'action': 'created',
                        'success': True
                    })

            except Exception as e:
                failed_count += 1
                results.append({
                    'action': 'failed',
                    'success': False,
                    'error': str(e)
                })

        # Clear cache
        from apps.common.services.i18n_service import TranslationCache
        TranslationCache.invalidate_all()

        return Response({
            'success': True,
            'message': f'Bulk operation completed: {created_count} created, {updated_count} updated, {failed_count} failed.',
            'summary': {
                'total': len(translations_data),
                'created': created_count,
                'updated': updated_count,
                'failed': failed_count
            },
            'results': results
        })

    @action(detail=False, methods=['get'], url_path='namespace/(?P<namespace>[^/]+)')
    def by_namespace(self, request, namespace=None):
        """
        Get all translations for a specific namespace.

        Returns translations grouped by key for the given namespace.
        Optionally filter by language_code.
        """
        queryset = self.get_queryset().filter(namespace=namespace)

        language_code = request.query_params.get('language_code')
        if language_code:
            queryset = queryset.filter(language_code=language_code)

        serializer = self.get_serializer(queryset, many=True)

        # Group by key
        grouped = {}
        for item in serializer.data:
            key = item['key']
            if key not in grouped:
                grouped[key] = {}
            grouped[key][item['language_code']] = item['text']

        return Response({
            'success': True,
            'data': {
                'namespace': namespace,
                'translations': grouped
            }
        })

    @action(detail=False, methods=['get'], url_path='object/(?P<content_type>[^/]+)/(?P<object_id>[^/]+)')
    def by_object(self, request, content_type=None, object_id=None):
        """
        Get all translations for a specific object.

        URL format: /api/system/translations/object/{app_model}/{object_id}/
        Example: /api/system/translations/object/system.BusinessObject/123/

        Returns all translations grouped by field and language.
        """
        try:
            app_label, model = content_type.split('.')
            ct = ContentType.objects.get(app_label=app_label, model=model.lower())
        except (ValueError, ContentType.DoesNotExist):
            return Response({
                'success': False,
                'error': f'Invalid content_type: {content_type}'
            }, status=status.HTTP_400_BAD_REQUEST)

        translations = self.get_queryset().filter(
            content_type=ct,
            object_id=object_id
        )

        serializer = self.get_serializer(translations, many=True)

        # Group by field_name and language_code
        grouped = {}
        for item in serializer.data:
            field = item['field_name']
            lang = item['language_code']
            if field not in grouped:
                grouped[field] = {}
            grouped[field][lang] = item['text']

        return Response({
            'success': True,
            'data': {
                'content_type': content_type,
                'object_id': object_id,
                'translations': grouped
            }
        })

    @action(detail=False, methods=['put'], url_path='object/(?P<content_type>[^/]+)/(?P<object_id>[^/]+)')
    def set_object_translations(self, request, content_type=None, object_id=None):
        """
        Set translations for a specific object.

        URL format: /api/system/translations/object/{app_model}/{object_id}/
        Method: PUT

        Request body:
        {
            "translations": {
                "en-US": {
                    "name": "Asset",
                    "description": "Fixed asset"
                },
                "ja-JP": {
                    "name": "資産"
                }
            }
        }
        """
        serializer = ObjectTranslationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            app_label, model = content_type.split('.')
            ct = ContentType.objects.get(app_label=app_label, model=model.lower())
        except (ValueError, ContentType.DoesNotExist):
            return Response({
                'success': False,
                'error': f'Invalid content_type: {content_type}'
            }, status=status.HTTP_400_BAD_REQUEST)

        translations_data = serializer.validated_data['translations']
        results = []

        for locale, fields in translations_data.items():
            for field_name, text in fields.items():
                # Update or create translation
                translation, created = Translation.objects.update_or_create(
                    content_type=ct,
                    object_id=object_id,
                    field_name=field_name,
                    language_code=locale,
                    defaults={
                        'text': text,
                        'type': 'object_field',
                        'updated_by': request.user,
                    }
                )

                if created:
                    translation.created_by = request.user
                    translation.save()

                results.append({
                    'locale': locale,
                    'field': field_name,
                    'text': text,
                    'action': 'created' if created else 'updated'
                })

        # Clear cache
        from apps.common.services.i18n_service import TranslationCache
        TranslationCache.invalidate_all()

        return Response({
            'success': True,
            'message': f'Updated {len(results)} translations.',
            'data': {
                'content_type': content_type,
                'object_id': object_id,
                'results': results
            }
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """
        Export translations to CSV format.

        Query parameters:
        - namespace: Filter by namespace
        - language_code: Filter by language (required)
        - content_type: Filter by content type model
        """
        language_code = request.query_params.get('language_code')
        if not language_code:
            return Response({
                'success': False,
                'error': 'language_code query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(language_code=language_code)

        namespace = request.query_params.get('namespace')
        if namespace:
            queryset = queryset.filter(namespace=namespace)

        content_type_model = request.query_params.get('content_type')
        if content_type_model:
            queryset = queryset.filter(content_type__model=content_type_model)

        serializer = self.get_serializer(queryset, many=True)

        # Build CSV data
        import csv
        from io import StringIO
        from django.http import HttpResponse

        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)

        # Header
        writer.writerow([
            'namespace', 'key', 'content_type', 'object_id',
            'field_name', 'language_code', 'text', 'type', 'context'
        ])

        # Rows
        for item in serializer.data:
            writer.writerow([
                item.get('namespace', ''),
                item.get('key', ''),
                item.get('content_type_model', ''),
                item.get('object_id', ''),
                item.get('field_name', ''),
                item['language_code'],
                item['text'],
                item.get('type', ''),
                item.get('context', ''),
            ])

        # Create response
        response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="translations_{language_code}.csv"'
        response.write('\ufeff')  # UTF-8 BOM
        return response

    @action(detail=False, methods=['post'], url_path='import')
    def import_translations(self, request):
        """
        Import translations from CSV file.

        Request: multipart/form-data with 'file' field

        Expected CSV format:
        namespace,key,content_type,object_id,field_name,language_code,text,type,context
        """
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No file uploaded. Please provide a CSV file.'
            }, status=status.HTTP_400_BAD_REQUEST)

        csv_file = request.FILES['file']

        # Check file extension
        if not csv_file.name.endswith('.csv'):
            return Response({
                'success': False,
                'error': 'Only CSV files are supported.'
            }, status=status.HTTP_400_BAD_REQUEST)

        import csv
        from io import TextIOWrapper

        # Read CSV
        csv_file = TextIOWrapper(csv_file, encoding='utf-8-sig')
        reader = csv.DictReader(csv_file)

        results = {
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Get or create content_type
                content_type = None
                object_id = None

                if row.get('content_type'):
                    try:
                        app_label, model = row['content_type'].split('.')
                        content_type = ContentType.objects.get(
                            app_label=app_label,
                            model=model.lower()
                        )
                        object_id = int(row['object_id']) if row.get('object_id') else None
                    except (ValueError, ContentType.DoesNotExist):
                        results['errors'].append({
                            'row': row_num,
                            'error': f'Invalid content_type: {row.get("content_type")}'
                        })
                        results['failed'] += 1
                        continue

                # Determine lookup fields
                if row.get('namespace') and row.get('key'):
                    lookup_kwargs = {
                        'namespace': row['namespace'],
                        'key': row['key'],
                        'language_code': row['language_code'],
                        'is_deleted': False
                    }
                else:
                    if not content_type or not object_id:
                        results['errors'].append({
                            'row': row_num,
                            'error': 'Must provide either namespace/key or content_type/object_id'
                        })
                        results['failed'] += 1
                        continue

                    lookup_kwargs = {
                        'content_type': content_type,
                        'object_id': object_id,
                        'field_name': row.get('field_name', ''),
                        'language_code': row['language_code'],
                        'is_deleted': False
                    }

                # Create or update
                translation, created = Translation.objects.update_or_create(
                    defaults={
                        'text': row['text'],
                        'context': row.get('context', ''),
                        'type': row.get('type', 'label'),
                        'updated_by': request.user,
                    },
                    **lookup_kwargs
                )

                if created:
                    translation.created_by = request.user
                    translation.save()
                    results['created'] += 1
                else:
                    results['updated'] += 1

            except Exception as e:
                results['errors'].append({
                    'row': row_num,
                    'error': str(e)
                })
                results['failed'] += 1

        # Clear cache
        from apps.common.services.i18n_service import TranslationCache
        TranslationCache.invalidate_all()

        total = results['created'] + results['updated'] + results['failed']
        return Response({
            'success': True,
            'message': f'Import completed: {results["created"]} created, {results["updated"]} updated, {results["failed"]} failed.',
            'data': {
                'total': total,
                'summary': results
            }
        })

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Get translation statistics.

        Returns:
        - Total translations by language
        - Coverage by namespace
        - System vs user translations
        """
        from django.db.models import Count, Q

        # Total by language
        by_language = list(
            Translation.objects.filter(is_deleted=False)
            .values('language_code')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # By namespace
        by_namespace = list(
            Translation.objects.filter(
                is_deleted=False,
                namespace__gt=''
            )
            .values('namespace')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # By type
        by_type = list(
            Translation.objects.filter(is_deleted=False)
            .values('type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # System vs user
        system_count = Translation.objects.filter(
            is_deleted=False,
            is_system=True
        ).count()

        user_count = Translation.objects.filter(
            is_deleted=False,
            is_system=False
        ).count()

        return Response({
            'success': True,
            'data': {
                'total': {
                    'by_language': by_language,
                    'by_namespace': by_namespace,
                    'by_type': by_type,
                    'system_vs_user': {
                        'system': system_count,
                        'user': user_count
                    }
                }
            }
        })
