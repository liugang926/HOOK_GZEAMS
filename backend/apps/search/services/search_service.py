"""Service layer for smart asset search with optional Elasticsearch support."""
from __future__ import annotations

import hashlib
import html
import json
import logging
import re
from collections import OrderedDict
from typing import Any

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.paginator import EmptyPage, Paginator
from django.db import connection
from django.db.models import Count, F, FloatField, Prefetch, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext

from apps.assets.models import Asset, AssetTagRelation
from apps.common.services.base_crud import BaseCRUDService
from apps.search.models import SavedSearch, SearchHistory, SearchSuggestion, SearchType

logger = logging.getLogger(__name__)

ASSET_INDEX_SETTINGS: dict[str, Any] = {
    'settings': {
        'number_of_shards': 1,
        'number_of_replicas': 0,
        'analysis': {
            'analyzer': {
                'ik_max_word': {
                    'type': 'custom',
                    'tokenizer': 'ik_max_word',
                },
                'ik_smart': {
                    'type': 'custom',
                    'tokenizer': 'ik_smart',
                },
                'pinyin_analyzer': {
                    'type': 'custom',
                    'tokenizer': 'ik_max_word',
                    'filter': ['lowercase', 'pinyin'],
                },
            },
            'filter': {
                'pinyin': {
                    'type': 'pinyin',
                    'keep_separate_first_letter': False,
                    'keep_full_pinyin': True,
                    'keep_original': True,
                    'limit_first_letter_length': 32,
                }
            },
        },
    },
    'mappings': {
        'properties': {
            'asset_id': {'type': 'keyword'},
            'asset_code': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword'}},
                'analyzer': 'ik_max_word',
            },
            'asset_name': {
                'type': 'text',
                'analyzer': 'ik_max_word',
                'fields': {
                    'keyword': {'type': 'keyword'},
                    'pinyin': {'type': 'text', 'analyzer': 'pinyin_analyzer'},
                },
            },
            'specification': {'type': 'text', 'analyzer': 'ik_max_word'},
            'brand': {'type': 'text', 'analyzer': 'ik_max_word'},
            'model': {'type': 'text', 'analyzer': 'ik_max_word'},
            'serial_number': {'type': 'text', 'analyzer': 'ik_max_word'},
            'asset_category': {'type': 'keyword'},
            'asset_category_name': {
                'type': 'text',
                'analyzer': 'ik_max_word',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'asset_status': {'type': 'keyword'},
            'status_label': {'type': 'keyword'},
            'purchase_price': {'type': 'double'},
            'current_value': {'type': 'double'},
            'purchase_date': {'type': 'date'},
            'location': {'type': 'keyword'},
            'location_path': {
                'type': 'text',
                'analyzer': 'ik_max_word',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'department': {'type': 'keyword'},
            'department_name': {
                'type': 'text',
                'analyzer': 'ik_max_word',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'custodian': {'type': 'keyword'},
            'custodian_name': {
                'type': 'text',
                'analyzer': 'ik_max_word',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'supplier': {'type': 'keyword'},
            'supplier_name': {
                'type': 'text',
                'analyzer': 'ik_max_word',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'tags': {'type': 'keyword'},
            'tag_names': {
                'type': 'text',
                'analyzer': 'ik_max_word',
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'organization_id': {'type': 'keyword'},
            'is_deleted': {'type': 'boolean'},
            'created_at': {'type': 'date'},
            'updated_at': {'type': 'date'},
        }
    },
}

PRICE_RANGE_KEYS = OrderedDict([
    ('under_1k', Q(purchase_price__lt=1000)),
    ('1k_to_5k', Q(purchase_price__gte=1000, purchase_price__lt=5000)),
    ('5k_to_10k', Q(purchase_price__gte=5000, purchase_price__lt=10000)),
    ('10k_to_50k', Q(purchase_price__gte=10000, purchase_price__lt=50000)),
    ('over_50k', Q(purchase_price__gte=50000)),
])


def _fallback_asset_status_label(value: str) -> str:
    """Humanize asset status codes when dictionary metadata is unavailable."""
    if not value:
        return value
    return str(value).replace('_', ' ').title()


class SearchHistoryService(BaseCRUDService):
    """CRUD service for search history records."""

    def __init__(self):
        super().__init__(SearchHistory)


class SavedSearchService(BaseCRUDService):
    """CRUD service for saved search records."""

    def __init__(self):
        super().__init__(SavedSearch)


class AssetSearchService(BaseCRUDService):
    """Smart asset search service with Elasticsearch fallback support."""

    SEARCHABLE_FIELDS = (
        'asset_name',
        'asset_code',
        'specification',
        'brand',
        'model',
        'serial_number',
    )

    def __init__(self):
        super().__init__(Asset)
        self._es_client: Any | None = None
        self._es_client_initialized = False

    def search_assets(
        self,
        *,
        organization_id: str,
        user=None,
        keyword: str = '',
        filters: dict[str, Any] | None = None,
        sort_by: str = 'relevance',
        sort_order: str = 'desc',
        page: int = 1,
        page_size: int = 20,
        record_history: bool = True,
    ) -> dict[str, Any]:
        """Search assets with Elasticsearch when available, otherwise fallback to ORM."""
        normalized_keyword = self._normalize_query(keyword)
        active_filters = self._normalize_filters(filters or {})

        result: dict[str, Any]
        if self._is_elasticsearch_available():
            try:
                result = self._search_assets_elasticsearch(
                    organization_id=organization_id,
                    keyword=normalized_keyword,
                    filters=active_filters,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    page=page,
                    page_size=page_size,
                )
            except Exception as exc:
                logger.warning('Elasticsearch asset search failed, falling back to ORM: %s', exc)
                result = self._search_assets_fallback(
                    organization_id=organization_id,
                    keyword=normalized_keyword,
                    filters=active_filters,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    page=page,
                    page_size=page_size,
                )
        else:
            result = self._search_assets_fallback(
                organization_id=organization_id,
                keyword=normalized_keyword,
                filters=active_filters,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

        if record_history and user is not None and not getattr(user, 'is_anonymous', False):
            self.record_search(
                organization_id=organization_id,
                user=user,
                search_type=SearchType.ASSET,
                keyword=normalized_keyword,
                filters=active_filters,
                result_count=result['total'],
            )

        return result

    def get_suggestions(
        self,
        *,
        organization_id: str,
        keyword: str,
        search_type: str = SearchType.ASSET,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return ranked suggestions from Elasticsearch or database fallback."""
        normalized_keyword = self._normalize_query(keyword)
        if not normalized_keyword:
            return []

        if self._is_elasticsearch_available():
            try:
                suggestions = self._get_suggestions_elasticsearch(
                    organization_id=organization_id,
                    keyword=normalized_keyword,
                    search_type=search_type,
                    limit=limit,
                )
                if suggestions:
                    return suggestions
            except Exception as exc:
                logger.warning('Elasticsearch suggestions failed, falling back to ORM: %s', exc)

        return self._get_suggestions_fallback(
            organization_id=organization_id,
            keyword=normalized_keyword,
            search_type=search_type,
            limit=limit,
        )

    def record_search(
        self,
        *,
        organization_id: str,
        user,
        search_type: str,
        keyword: str,
        filters: dict[str, Any],
        result_count: int,
    ) -> SearchHistory:
        """Create or update a history record and refresh suggestion cache."""
        normalized_keyword = self._normalize_query(keyword)
        signature = self._build_signature(search_type, normalized_keyword, filters)
        lookup = {
            'organization_id': organization_id,
            'user': user,
            'search_type': search_type,
            'query_signature': signature,
        }
        defaults = {
            'keyword': keyword,
            'normalized_keyword': normalized_keyword,
            'filters': filters,
            'result_count': result_count,
            'created_by': user,
            'updated_by': user,
        }

        history = SearchHistory.all_objects.filter(is_deleted=False, **lookup).first()
        if history:
            history.keyword = keyword
            history.normalized_keyword = normalized_keyword
            history.filters = filters
            history.result_count = result_count
            history.search_count += 1
            history.updated_by = user
            history.last_searched_at = timezone.now()
            history.save(
                update_fields=[
                    'keyword',
                    'normalized_keyword',
                    'filters',
                    'result_count',
                    'search_count',
                    'updated_by',
                    'last_searched_at',
                    'updated_at',
                ]
            )
        else:
            history = SearchHistory.objects.create(
                query_signature=signature,
                organization_id=organization_id,
                user=user,
                search_type=search_type,
                keyword=keyword,
                normalized_keyword=normalized_keyword,
                filters=filters,
                result_count=result_count,
                created_by=user,
            )

        if normalized_keyword:
            self._record_suggestion(
                organization_id=organization_id,
                search_type=search_type,
                query=keyword,
                normalized_query=normalized_keyword,
                user=user,
            )

        return history

    def increment_saved_search_usage(self, saved_search: SavedSearch) -> SavedSearch:
        """Increment usage statistics for a saved search."""
        saved_search.use_count += 1
        saved_search.save(update_fields=['use_count', 'updated_at'])
        return saved_search

    def sync_asset_document(self, asset: Asset) -> bool:
        """Create or update the search document for a single asset."""
        if asset.is_deleted:
            return self.delete_asset_document(str(asset.id))

        client = self._get_es_client()
        if client is None:
            return False

        self.ensure_asset_index()
        document = self._build_asset_document(asset)
        client.index(
            index=self._get_asset_index_name(),
            id=str(asset.id),
            document=document,
            refresh='wait_for',
        )
        return True

    def delete_asset_document(self, asset_id: str) -> bool:
        """Delete the Elasticsearch document for an asset if present."""
        client = self._get_es_client()
        if client is None:
            return False

        try:
            client.delete(index=self._get_asset_index_name(), id=str(asset_id), refresh='wait_for')
            return True
        except Exception as exc:
            logger.debug('Delete asset document skipped for %s: %s', asset_id, exc)
            return False

    def ensure_asset_index(self) -> bool:
        """Create the Elasticsearch index when it does not exist yet."""
        client = self._get_es_client()
        if client is None:
            return False

        index_name = self._get_asset_index_name()
        try:
            if client.indices.exists(index=index_name):
                return True
            client.indices.create(
                index=index_name,
                settings=ASSET_INDEX_SETTINGS['settings'],
                mappings=ASSET_INDEX_SETTINGS['mappings'],
            )
            return True
        except Exception as exc:
            logger.warning('Failed to ensure search index %s: %s', index_name, exc)
            return False

    def rebuild_asset_index(self) -> bool:
        """Rebuild the asset index from scratch."""
        client = self._get_es_client()
        if client is None:
            return False

        index_name = self._get_asset_index_name()
        try:
            if client.indices.exists(index=index_name):
                client.indices.delete(index=index_name)
        except Exception as exc:
            logger.warning('Failed to delete asset index %s during rebuild: %s', index_name, exc)

        created = self.ensure_asset_index()
        if not created:
            return False
        return True

    def _search_assets_fallback(
        self,
        *,
        organization_id: str,
        keyword: str,
        filters: dict[str, Any],
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        """Run the ORM/PostgreSQL fallback search flow."""
        queryset = self._get_asset_queryset(organization_id)
        queryset = self._apply_filters(queryset, filters)
        queryset = self._apply_keyword_search(queryset, keyword)
        queryset = self._apply_sorting(queryset, keyword, sort_by, sort_order)

        total = queryset.count()
        paginator = Paginator(queryset, page_size)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages or 1)

        status_label_map = self._get_asset_status_label_map(organization_id)
        results = [
            self._serialize_asset_result(
                asset,
                keyword=keyword,
                score=float(getattr(asset, 'relevance_score', 0.0) or 0.0),
                status_label_map=status_label_map,
            )
            for asset in page_obj.object_list
        ]

        return {
            'total': total,
            'page': page_obj.number,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'results': results,
            'aggregations': self._build_aggregations(queryset),
            'engine': 'database',
        }

    def _search_assets_elasticsearch(
        self,
        *,
        organization_id: str,
        keyword: str,
        filters: dict[str, Any],
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        """Run the Elasticsearch search flow."""
        client = self._get_es_client()
        if client is None:
            raise RuntimeError('Elasticsearch client is unavailable.')

        self.ensure_asset_index()
        body = {
            'query': self._build_elasticsearch_query(
                organization_id=organization_id,
                keyword=keyword,
                filters=filters,
            ),
            'sort': self._build_elasticsearch_sort(
                keyword=keyword,
                sort_by=sort_by,
                sort_order=sort_order,
            ),
            'highlight': {
                'pre_tags': ['<em>'],
                'post_tags': ['</em>'],
                'fields': {
                    'asset_name': {},
                    'asset_code': {},
                    'specification': {},
                    'brand': {},
                    'model': {},
                },
            },
            'aggs': {
                'asset_category': {'terms': {'field': 'asset_category', 'size': 50}},
                'asset_status': {'terms': {'field': 'asset_status', 'size': 20}},
                'location': {'terms': {'field': 'location', 'size': 50}},
                'brand': {'terms': {'field': 'brand.keyword', 'size': 50}},
                'price_ranges': {
                    'range': {
                        'field': 'purchase_price',
                        'ranges': [
                            {'to': 1000, 'key': 'under_1k'},
                            {'from': 1000, 'to': 5000, 'key': '1k_to_5k'},
                            {'from': 5000, 'to': 10000, 'key': '5k_to_10k'},
                            {'from': 10000, 'to': 50000, 'key': '10k_to_50k'},
                            {'from': 50000, 'key': 'over_50k'},
                        ],
                    }
                },
            },
            'from': (page - 1) * page_size,
            'size': page_size,
        }

        response = client.search(index=self._get_asset_index_name(), body=body)
        hits = response.get('hits', {})
        total_value = int((hits.get('total') or {}).get('value', 0))
        results = []
        for hit in hits.get('hits', []):
            source = hit.get('_source', {})
            results.append({
                'id': source.get('asset_id'),
                'asset_code': source.get('asset_code') or '',
                'asset_name': source.get('asset_name') or '',
                'asset_category': source.get('asset_category'),
                'asset_category_name': source.get('asset_category_name') or '',
                'asset_status': source.get('asset_status') or '',
                'status_label': source.get('status_label') or '',
                'specification': source.get('specification') or '',
                'brand': source.get('brand') or '',
                'model': source.get('model') or '',
                'serial_number': source.get('serial_number') or '',
                'purchase_price': source.get('purchase_price'),
                'current_value': source.get('current_value'),
                'purchase_date': source.get('purchase_date'),
                'location': source.get('location'),
                'location_path': source.get('location_path') or '',
                'department': source.get('department'),
                'department_name': source.get('department_name') or '',
                'custodian': source.get('custodian'),
                'custodian_name': source.get('custodian_name') or '',
                'supplier': source.get('supplier'),
                'supplier_name': source.get('supplier_name') or '',
                'tags': source.get('tags') or [],
                'tag_names': source.get('tag_names') or [],
                'highlight': hit.get('highlight', {}),
                'score': float(hit.get('_score') or 0.0),
            })

        aggregations = {}
        for key, agg_payload in (response.get('aggregations') or {}).items():
            buckets = agg_payload.get('buckets', [])
            aggregations[key] = {
                str(bucket.get('key')): int(bucket.get('doc_count', 0))
                for bucket in buckets
                if bucket.get('key') not in (None, '')
            }

        total_pages = (total_value + page_size - 1) // page_size if total_value else 0
        return {
            'total': total_value,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'results': results,
            'aggregations': aggregations,
            'engine': 'elasticsearch',
        }

    def _get_suggestions_fallback(
        self,
        *,
        organization_id: str,
        keyword: str,
        search_type: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Build suggestions from cache and database content."""
        ranked: dict[str, int] = {}

        suggestion_rows = SearchSuggestion.objects.filter(
            organization_id=organization_id,
            search_type=search_type,
            normalized_query__icontains=keyword.lower(),
        ).values('query', 'frequency')[: limit * 2]
        for row in suggestion_rows:
            suggestion = str(row['query']).strip()
            if not suggestion:
                continue
            ranked[suggestion] = max(int(row['frequency']), ranked.get(suggestion, 0))

        if search_type == SearchType.ASSET:
            queryset = self._get_asset_queryset(organization_id)
            for field in ('asset_name', 'asset_code', 'specification', 'brand', 'model'):
                filter_key = f'{field}__icontains'
                rows = queryset.filter(**{filter_key: keyword}).exclude(**{field: ''}).values(field).annotate(
                    count=Count('id')
                ).order_by('-count', field)[:limit]
                for row in rows:
                    suggestion = str(row[field]).strip()
                    if not suggestion:
                        continue
                    ranked[suggestion] = max(int(row['count']), ranked.get(suggestion, 0))

        def sort_key(item: tuple[str, int]) -> tuple[int, int, str]:
            label, frequency = item
            prefix_priority = 0 if label.lower().startswith(keyword.lower()) else 1
            return (prefix_priority, -frequency, label.lower())

        return [
            {'suggestion': label, 'count': frequency}
            for label, frequency in sorted(ranked.items(), key=sort_key)[:limit]
        ]

    def _get_suggestions_elasticsearch(
        self,
        *,
        organization_id: str,
        keyword: str,
        search_type: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Query suggestion candidates from Elasticsearch."""
        client = self._get_es_client()
        if client is None:
            raise RuntimeError('Elasticsearch client is unavailable.')

        if search_type != SearchType.ASSET:
            return []

        response = client.search(
            index=self._get_asset_index_name(),
            body={
                'query': {
                    'bool': {
                        'filter': [
                            {'term': {'organization_id': organization_id}},
                            {'term': {'is_deleted': False}},
                        ],
                        'must': [
                            {
                                'multi_match': {
                                    'query': keyword,
                                    'fields': ['asset_name', 'asset_name.pinyin', 'asset_code', 'specification'],
                                    'type': 'bool_prefix',
                                }
                            }
                        ],
                    }
                },
                'aggs': {
                    'suggestions': {
                        'terms': {
                            'field': 'asset_name.keyword',
                            'size': limit,
                        }
                    }
                },
                'size': 0,
            },
        )

        suggestions = []
        for bucket in response.get('aggregations', {}).get('suggestions', {}).get('buckets', []):
            value = str(bucket.get('key', '')).strip()
            if not value:
                continue
            suggestions.append({'suggestion': value, 'count': int(bucket.get('doc_count', 0))})
        return suggestions

    def _build_asset_document(self, asset: Asset) -> dict[str, Any]:
        """Transform an asset into its indexable search document."""
        tag_relations = getattr(asset, 'prefetched_asset_tag_relations', None)
        if tag_relations is None:
            tag_relations = asset.asset_tag_relations.filter(
                is_deleted=False,
                tag__is_deleted=False,
            ).select_related('tag')

        tags = []
        tag_names = []
        for relation in tag_relations:
            tag = getattr(relation, 'tag', None)
            if not tag:
                continue
            tags.append(str(tag.id))
            tag_names.append(tag.name)

        custodian = asset.custodian
        custodian_name = ''
        if custodian is not None:
            custodian_name = custodian.get_full_name().strip() or custodian.username

        return {
            'asset_id': str(asset.id),
            'asset_code': asset.asset_code,
            'asset_name': asset.asset_name,
            'asset_category': str(asset.asset_category_id) if asset.asset_category_id else None,
            'asset_category_name': getattr(asset.asset_category, 'name', ''),
            'asset_status': asset.asset_status,
            'status_label': asset.get_status_label(),
            'specification': asset.specification or '',
            'brand': asset.brand or '',
            'model': asset.model or '',
            'serial_number': asset.serial_number or '',
            'purchase_price': float(asset.purchase_price) if asset.purchase_price is not None else None,
            'current_value': float(asset.current_value) if asset.current_value is not None else None,
            'purchase_date': asset.purchase_date.isoformat() if asset.purchase_date else None,
            'location': str(asset.location_id) if asset.location_id else None,
            'location_path': getattr(asset.location, 'path', '') or '',
            'department': str(asset.department_id) if asset.department_id else None,
            'department_name': getattr(asset.department, 'name', '') or '',
            'custodian': str(asset.custodian_id) if asset.custodian_id else None,
            'custodian_name': custodian_name,
            'supplier': str(asset.supplier_id) if asset.supplier_id else None,
            'supplier_name': getattr(asset.supplier, 'name', '') or '',
            'tags': tags,
            'tag_names': tag_names,
            'organization_id': str(asset.organization_id),
            'is_deleted': asset.is_deleted,
            'created_at': asset.created_at.isoformat(),
            'updated_at': asset.updated_at.isoformat(),
        }

    def _get_asset_queryset(self, organization_id: str):
        """Return the base queryset used by database search and suggestion flows."""
        return Asset.all_objects.filter(
            organization_id=organization_id,
            is_deleted=False,
        ).select_related(
            'asset_category',
            'department',
            'location',
            'custodian',
            'supplier',
        ).prefetch_related(
            Prefetch(
                'asset_tag_relations',
                queryset=AssetTagRelation.all_objects.filter(
                    is_deleted=False,
                    tag__is_deleted=False,
                    tag__is_active=True,
                ).select_related('tag'),
                to_attr='prefetched_asset_tag_relations',
            )
        )

    def _apply_filters(self, queryset, filters: dict[str, Any]):
        """Apply supported filters to an asset queryset."""
        if not filters:
            return queryset

        category = filters.get('category')
        if category:
            if isinstance(category, (list, tuple)):
                queryset = queryset.filter(asset_category_id__in=category)
            else:
                queryset = queryset.filter(asset_category_id=category)

        status = filters.get('status')
        if status:
            if isinstance(status, (list, tuple)):
                queryset = queryset.filter(asset_status__in=status)
            else:
                queryset = queryset.filter(asset_status=status)

        location = filters.get('location')
        if location:
            if isinstance(location, (list, tuple)):
                queryset = queryset.filter(location_id__in=location)
            else:
                queryset = queryset.filter(location_id=location)

        brand = filters.get('brand')
        if brand:
            queryset = queryset.filter(brand__icontains=brand)

        tags = filters.get('tags')
        if tags:
            queryset = queryset.filter(
                asset_tag_relations__is_deleted=False,
                asset_tag_relations__tag_id__in=list(tags),
            ).distinct()

        purchase_price_min = filters.get('purchase_price_min')
        if purchase_price_min not in (None, ''):
            queryset = queryset.filter(purchase_price__gte=purchase_price_min)

        purchase_price_max = filters.get('purchase_price_max')
        if purchase_price_max not in (None, ''):
            queryset = queryset.filter(purchase_price__lte=purchase_price_max)

        purchase_date_from = filters.get('purchase_date_from')
        if purchase_date_from:
            queryset = queryset.filter(purchase_date__gte=purchase_date_from)

        purchase_date_to = filters.get('purchase_date_to')
        if purchase_date_to:
            queryset = queryset.filter(purchase_date__lte=purchase_date_to)

        return queryset

    def _apply_keyword_search(self, queryset, keyword: str):
        """Apply keyword filters and ranking annotations."""
        if not keyword:
            return queryset.annotate(relevance_score=Value(0.0, output_field=FloatField()))

        keyword_filter = (
            Q(asset_name__icontains=keyword)
            | Q(asset_code__icontains=keyword)
            | Q(specification__icontains=keyword)
            | Q(brand__icontains=keyword)
            | Q(model__icontains=keyword)
            | Q(serial_number__icontains=keyword)
            | Q(asset_category__name__icontains=keyword)
            | Q(location__name__icontains=keyword)
            | Q(location__path__icontains=keyword)
            | Q(department__name__icontains=keyword)
            | Q(custodian__username__icontains=keyword)
            | Q(custodian__first_name__icontains=keyword)
            | Q(custodian__last_name__icontains=keyword)
            | Q(supplier__name__icontains=keyword)
        )

        manual_score = (
            self._weighted_match('asset_name__icontains', keyword, 8.0)
            + self._weighted_match('asset_code__icontains', keyword, 7.0)
            + self._weighted_match('specification__icontains', keyword, 5.0)
            + self._weighted_match('brand__icontains', keyword, 3.0)
            + self._weighted_match('model__icontains', keyword, 3.0)
            + self._weighted_match('serial_number__icontains', keyword, 2.0)
            + self._weighted_match('asset_category__name__icontains', keyword, 2.0)
            + self._weighted_match('location__path__icontains', keyword, 1.0)
        )

        if connection.vendor == 'postgresql':
            vector = (
                SearchVector('asset_name', weight='A')
                + SearchVector('asset_code', weight='A')
                + SearchVector('specification', weight='B')
                + SearchVector('brand', weight='C')
                + SearchVector('model', weight='C')
            )
            query = SearchQuery(keyword, search_type='plain')
            queryset = queryset.annotate(
                search_rank=SearchRank(vector, query),
            ).filter(keyword_filter | Q(search_rank__gt=0)).annotate(
                relevance_score=manual_score + Coalesce(
                    F('search_rank'),
                    Value(0.0),
                    output_field=FloatField(),
                ),
            )
            return queryset

        return queryset.filter(keyword_filter).annotate(
            relevance_score=manual_score,
        )

    def _apply_sorting(self, queryset, keyword: str, sort_by: str, sort_order: str):
        """Apply result ordering to a searched queryset."""
        order = '' if sort_order == 'asc' else '-'

        if sort_by == 'price':
            return queryset.order_by(f'{order}purchase_price', '-updated_at')
        if sort_by == 'date':
            return queryset.order_by(f'{order}purchase_date', '-updated_at')
        if sort_by == 'code':
            return queryset.order_by(f'{order}asset_code', '-updated_at')
        if sort_by == 'relevance' and keyword:
            return queryset.order_by('-relevance_score', '-updated_at')
        return queryset.order_by('-updated_at', '-created_at')

    def _build_aggregations(self, queryset) -> dict[str, Any]:
        """Build database aggregations for the active result set."""
        category_rows = queryset.values('asset_category_id', 'asset_category__name').annotate(
            count=Count('id')
        ).order_by('-count', 'asset_category__name')
        location_rows = queryset.values('location_id', 'location__path').annotate(
            count=Count('id')
        ).order_by('-count', 'location__path')
        status_rows = queryset.values('asset_status').annotate(count=Count('id')).order_by('-count', 'asset_status')
        brand_rows = queryset.exclude(brand='').values('brand').annotate(count=Count('id')).order_by('-count', 'brand')
        price_range_counts = queryset.aggregate(
            **{
                key: Count('id', filter=condition)
                for key, condition in PRICE_RANGE_KEYS.items()
            }
        )

        aggregations = {
            'category': {
                str(row['asset_category_id']): int(row['count'])
                for row in category_rows
                if row['asset_category_id'] is not None
            },
            'category_labels': {
                str(row['asset_category_id']): row['asset_category__name']
                for row in category_rows
                if row['asset_category_id'] is not None and row['asset_category__name']
            },
            'status': {
                str(row['asset_status']): int(row['count'])
                for row in status_rows
                if row['asset_status']
            },
            'location': {
                str(row['location_id']): int(row['count'])
                for row in location_rows
                if row['location_id'] is not None
            },
            'location_labels': {
                str(row['location_id']): row['location__path']
                for row in location_rows
                if row['location_id'] is not None and row['location__path']
            },
            'brand': {
                str(row['brand']): int(row['count'])
                for row in brand_rows
                if row['brand']
            },
            'price_ranges': {
                key: int(price_range_counts.get(key) or 0)
                for key, condition in PRICE_RANGE_KEYS.items()
            },
        }
        return aggregations

    def _serialize_asset_result(
        self,
        asset: Asset,
        *,
        keyword: str,
        score: float,
        status_label_map: dict[str, str],
    ) -> dict[str, Any]:
        """Serialize a search result row."""
        tag_relations = getattr(asset, 'prefetched_asset_tag_relations', None) or []
        tag_ids = []
        tag_names = []
        for relation in tag_relations:
            tag = getattr(relation, 'tag', None)
            if not tag:
                continue
            tag_ids.append(str(tag.id))
            tag_names.append(tag.name)

        custodian = asset.custodian
        custodian_name = ''
        if custodian is not None:
            custodian_name = custodian.get_full_name().strip() or custodian.username

        return {
            'id': str(asset.id),
            'asset_code': asset.asset_code,
            'asset_name': asset.asset_name,
            'asset_category': str(asset.asset_category_id) if asset.asset_category_id else None,
            'asset_category_name': getattr(asset.asset_category, 'name', ''),
            'asset_status': asset.asset_status,
            'status_label': self._resolve_asset_status_label(asset.asset_status, status_label_map),
            'specification': asset.specification or '',
            'brand': asset.brand or '',
            'model': asset.model or '',
            'serial_number': asset.serial_number or '',
            'purchase_price': asset.purchase_price,
            'current_value': asset.current_value,
            'purchase_date': asset.purchase_date,
            'location': str(asset.location_id) if asset.location_id else None,
            'location_path': getattr(asset.location, 'path', '') or '',
            'department': str(asset.department_id) if asset.department_id else None,
            'department_name': getattr(asset.department, 'name', '') or '',
            'custodian': str(asset.custodian_id) if asset.custodian_id else None,
            'custodian_name': custodian_name,
            'supplier': str(asset.supplier_id) if asset.supplier_id else None,
            'supplier_name': getattr(asset.supplier, 'name', '') or '',
            'tags': tag_ids,
            'tag_names': tag_names,
            'highlight': self._build_highlight_payload(asset, keyword),
            'score': round(score, 4),
        }

    def _get_asset_status_label_map(self, organization_id: str) -> dict[str, str]:
        """Resolve asset-status labels once per search execution to avoid per-row dictionary lookups."""
        try:
            from apps.system.services import DictionaryService

            return {
                str(item.get('code')): gettext(str(item.get('name') or ''))
                for item in DictionaryService.get_items('ASSET_STATUS', organization_id=organization_id)
                if item.get('code')
            }
        except Exception:
            return {}

    def _resolve_asset_status_label(self, asset_status: str, status_label_map: dict[str, str]) -> str:
        """Resolve the display label for an asset status without triggering additional queries."""
        return status_label_map.get(asset_status) or _fallback_asset_status_label(asset_status)

    def _build_highlight_payload(self, asset: Asset, keyword: str) -> dict[str, list[str]]:
        """Generate a highlight payload for database fallback results."""
        if not keyword:
            return {}

        field_values = {
            'asset_name': asset.asset_name,
            'asset_code': asset.asset_code,
            'specification': asset.specification,
            'brand': asset.brand,
            'model': asset.model,
            'serial_number': asset.serial_number,
            'asset_category_name': getattr(asset.asset_category, 'name', ''),
            'location_path': getattr(asset.location, 'path', ''),
        }

        payload: dict[str, list[str]] = {}
        for field_name, value in field_values.items():
            highlighted = self._highlight_text(value, keyword)
            if highlighted:
                payload[field_name] = [highlighted]
        return payload

    def _highlight_text(self, value: Any, keyword: str) -> str | None:
        """Wrap keyword matches with <em> while escaping user content."""
        if value in (None, '') or not keyword:
            return None

        raw_value = str(value)
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        cursor = 0
        segments: list[str] = []
        matched = False
        for match in pattern.finditer(raw_value):
            matched = True
            segments.append(html.escape(raw_value[cursor:match.start()]))
            segments.append(f'<em>{html.escape(match.group(0))}</em>')
            cursor = match.end()
        if not matched:
            return None
        segments.append(html.escape(raw_value[cursor:]))
        return ''.join(segments)

    def _weighted_match(self, lookup: str, keyword: str, weight: float):
        """Build a weighted score contribution expression."""
        from django.db.models import Case, When

        return Case(
            When(**{lookup: keyword}, then=Value(weight)),
            default=Value(0.0),
            output_field=FloatField(),
        )

    def _normalize_query(self, keyword: str | None) -> str:
        """Normalize free-text query input."""
        return re.sub(r'\s+', ' ', (keyword or '').strip())

    def _normalize_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Drop empty filter values while keeping supported structures intact."""
        normalized: dict[str, Any] = {}
        for key, value in filters.items():
            if value in (None, '', [], (), {}):
                continue
            normalized[key] = value
        return normalized

    def _build_signature(self, search_type: str, keyword: str, filters: dict[str, Any]) -> str:
        """Create a deterministic signature from a search payload."""
        payload = {
            'search_type': search_type,
            'keyword': keyword,
            'filters': filters,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode('utf-8')
        ).hexdigest()

    def _record_suggestion(
        self,
        *,
        organization_id: str,
        search_type: str,
        query: str,
        normalized_query: str,
        user,
    ) -> SearchSuggestion:
        """Create or update a suggestion cache record."""
        suggestion = SearchSuggestion.all_objects.filter(
            organization_id=organization_id,
            search_type=search_type,
            normalized_query=normalized_query,
            is_deleted=False,
        ).first()

        if suggestion:
            suggestion.query = query
            suggestion.frequency += 1
            suggestion.updated_by = user
            suggestion.last_used = timezone.now()
            suggestion.save(update_fields=['query', 'frequency', 'updated_by', 'last_used', 'updated_at'])
            return suggestion

        return SearchSuggestion.objects.create(
            organization_id=organization_id,
            search_type=search_type,
            query=query,
            normalized_query=normalized_query,
            created_by=user,
        )

    def _get_elasticsearch_config(self) -> dict[str, Any]:
        """Return the search engine configuration block from settings."""
        default_config = {
            'enabled': False,
            'hosts': ['http://localhost:9200'],
            'options': {},
            'index_prefix': 'gzeams',
        }
        return {
            **default_config,
            **getattr(settings, 'ELASTICSEARCH', default_config),
        }

    def _get_asset_index_name(self) -> str:
        """Build the index name for asset documents."""
        config = self._get_elasticsearch_config()
        prefix = str(config.get('index_prefix') or 'gzeams').strip() or 'gzeams'
        return f'{prefix}_asset'

    def _is_elasticsearch_available(self) -> bool:
        """Check whether Elasticsearch can be used safely."""
        return self._get_es_client() is not None

    def _get_es_client(self):
        """Lazy-load the Elasticsearch client when the dependency is installed."""
        if self._es_client_initialized:
            return self._es_client

        self._es_client_initialized = True
        config = self._get_elasticsearch_config()
        if not config.get('enabled'):
            self._es_client = None
            return None

        try:
            from elasticsearch import Elasticsearch
        except ImportError:
            logger.info('elasticsearch dependency is not installed; using database fallback.')
            self._es_client = None
            return None

        try:
            self._es_client = Elasticsearch(
                config.get('hosts') or ['http://localhost:9200'],
                **(config.get('options') or {}),
            )
        except Exception as exc:
            logger.warning('Failed to initialize Elasticsearch client: %s', exc)
            self._es_client = None
        return self._es_client

    def _build_elasticsearch_query(
        self,
        *,
        organization_id: str,
        keyword: str,
        filters: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the Elasticsearch query document."""
        must: list[dict[str, Any]] = []
        filter_clauses: list[dict[str, Any]] = [
            {'term': {'organization_id': organization_id}},
            {'term': {'is_deleted': False}},
        ]

        if keyword:
            must.append({
                'multi_match': {
                    'query': keyword,
                    'fields': [
                        'asset_name^4',
                        'asset_name.pinyin^2',
                        'asset_code^3',
                        'specification^2',
                        'brand',
                        'model',
                        'serial_number',
                        'asset_category_name',
                        'location_path',
                        'department_name',
                        'custodian_name',
                        'supplier_name',
                        'tag_names',
                    ],
                    'fuzziness': 'AUTO',
                    'operator': 'or',
                }
            })

        category = filters.get('category')
        if category:
            clause = {'terms' if isinstance(category, (list, tuple)) else 'term': {'asset_category': category}}
            filter_clauses.append(clause)

        status = filters.get('status')
        if status:
            clause = {'terms' if isinstance(status, (list, tuple)) else 'term': {'asset_status': status}}
            filter_clauses.append(clause)

        location = filters.get('location')
        if location:
            clause = {'terms' if isinstance(location, (list, tuple)) else 'term': {'location': location}}
            filter_clauses.append(clause)

        brand = filters.get('brand')
        if brand:
            filter_clauses.append({'match': {'brand': brand}})

        tags = filters.get('tags')
        if tags:
            filter_clauses.append({'terms': {'tags': list(tags)}})

        range_payload: dict[str, Any] = {}
        if filters.get('purchase_price_min') not in (None, ''):
            range_payload['gte'] = filters['purchase_price_min']
        if filters.get('purchase_price_max') not in (None, ''):
            range_payload['lte'] = filters['purchase_price_max']
        if range_payload:
            filter_clauses.append({'range': {'purchase_price': range_payload}})

        date_range: dict[str, Any] = {}
        if filters.get('purchase_date_from'):
            date_range['gte'] = filters['purchase_date_from']
        if filters.get('purchase_date_to'):
            date_range['lte'] = filters['purchase_date_to']
        if date_range:
            filter_clauses.append({'range': {'purchase_date': date_range}})

        return {
            'bool': {
                'must': must,
                'filter': filter_clauses,
            }
        }

    def _build_elasticsearch_sort(
        self,
        *,
        keyword: str,
        sort_by: str,
        sort_order: str,
    ) -> list[Any]:
        """Build Elasticsearch sort clauses."""
        order = 'asc' if sort_order == 'asc' else 'desc'
        if sort_by == 'price':
            return [{'purchase_price': {'order': order}}, {'updated_at': {'order': 'desc'}}]
        if sort_by == 'date':
            return [{'purchase_date': {'order': order}}, {'updated_at': {'order': 'desc'}}]
        if sort_by == 'code':
            return [{'asset_code.keyword': {'order': order}}]
        if sort_by == 'relevance' and keyword:
            return ['_score', {'updated_at': {'order': 'desc'}}]
        return [{'updated_at': {'order': 'desc'}}]
