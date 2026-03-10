"""
GlobalSearchService - Cross-object search across all searchable BusinessObjects.

Performs icontains queries against each object's searchable fields,
returning grouped results with timeout protection.
"""
from __future__ import annotations

import logging
import signal
import time
from dataclasses import dataclass, field as dc_field
from typing import List, Optional

from django.db import models
from django.db.models import Q
from django.utils.module_loading import import_string

from apps.system.models import BusinessObject, FieldDefinition

logger = logging.getLogger(__name__)

# Searchable Django field types (text-like)
SEARCHABLE_DJANGO_FIELD_TYPES = (
    models.CharField,
    models.TextField,
    models.SlugField,
    models.EmailField,
    models.URLField,
)

# System fields to skip
SKIP_FIELDS = frozenset({
    'id', 'organization', 'organization_id',
    'created_by', 'updated_by', 'created_by_id', 'updated_by_id',
    'deleted_by', 'deleted_by_id',
    'created_at', 'updated_at', 'deleted_at',
    'is_deleted', 'custom_fields',
})


@dataclass
class SearchMatch:
    record_id: str
    display_name: str
    match_field: str
    match_value: str


@dataclass
class ObjectSearchResult:
    object_code: str
    object_name: str
    matches: List[SearchMatch] = dc_field(default_factory=list)


class GlobalSearchService:
    """
    Cross-object full-text search service.

    Searches across all active BusinessObjects, querying their
    `is_searchable=True` FieldDefinitions for matching records.
    """

    MAX_RESULTS_PER_OBJECT = 5
    MAX_TOTAL_TIME_MS = 3000
    MAX_PER_OBJECT_TIME_MS = 500

    def search(
        self,
        keyword: str,
        limit_per_object: int = 5,
        object_codes: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        Execute cross-object search.

        Args:
            keyword: Search term (minimum 2 chars)
            limit_per_object: Max results per object type
            object_codes: Optional list to restrict search scope

        Returns:
            List of dicts with object_code, object_name, matches[]
        """
        keyword = (keyword or '').strip()
        if len(keyword) < 2:
            return []

        limit = min(limit_per_object, self.MAX_RESULTS_PER_OBJECT)

        # Get all active business objects
        bo_qs = BusinessObject.objects.filter(is_active=True)
        if object_codes:
            bo_qs = bo_qs.filter(code__in=object_codes)

        business_objects = list(bo_qs.values('code', 'name', 'name_en', 'django_model_path', 'is_hardcoded'))

        results = []
        start_time = time.monotonic()

        for bo in business_objects:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            if elapsed_ms >= self.MAX_TOTAL_TIME_MS:
                logger.info(
                    'GlobalSearch: total timeout reached after %d ms, '
                    'searched %d/%d objects',
                    int(elapsed_ms), len(results), len(business_objects)
                )
                break

            try:
                result = self._search_single_object(
                    bo_code=bo['code'],
                    bo_name=bo['name'] or bo.get('name_en') or bo['code'],
                    model_path=bo.get('django_model_path') or '',
                    keyword=keyword,
                    limit=limit,
                )
                if result and result.matches:
                    results.append({
                        'object_code': result.object_code,
                        'object_name': result.object_name,
                        'matches': [
                            {
                                'record_id': m.record_id,
                                'display_name': m.display_name,
                                'match_field': m.match_field,
                                'match_value': m.match_value,
                            }
                            for m in result.matches
                        ],
                    })
            except Exception as exc:
                logger.warning(
                    'GlobalSearch: error searching %s: %s',
                    bo['code'], exc
                )
                continue

        return results

    def _search_single_object(
        self,
        bo_code: str,
        bo_name: str,
        model_path: str,
        keyword: str,
        limit: int,
    ) -> Optional[ObjectSearchResult]:
        """Search a single business object for matching records."""

        # Resolve model class
        model_class = self._resolve_model(bo_code, model_path)
        if model_class is None:
            return None

        # Get searchable field codes from FieldDefinition
        searchable_field_codes = self._get_searchable_fields(bo_code)

        # Determine which model fields are text-like and searchable
        search_q = Q()
        matched_field_names = []

        for field in model_class._meta.get_fields():
            if field.name in SKIP_FIELDS:
                continue
            if not hasattr(field, 'column'):
                continue

            # Use field if it's in the searchable list OR if no config exists
            # and the field is a text-like type
            is_configured_searchable = field.name in searchable_field_codes
            is_text_field = isinstance(field, SEARCHABLE_DJANGO_FIELD_TYPES)

            if searchable_field_codes:
                # If we have configured searchable fields, only use those
                if not is_configured_searchable or not is_text_field:
                    continue
            else:
                # Fallback: search all text-like fields
                if not is_text_field:
                    continue

            search_q |= Q(**{f'{field.name}__icontains': keyword})
            matched_field_names.append(field.name)

        if not matched_field_names:
            return None

        # Execute query with limit
        try:
            qs = model_class.objects.all()

            # Apply soft-delete filter if available
            if hasattr(model_class, 'is_deleted'):
                qs = qs.filter(is_deleted=False)

            records = list(qs.filter(search_q)[:limit])
        except Exception as exc:
            logger.debug('GlobalSearch: query failed for %s: %s', bo_code, exc)
            return None

        if not records:
            return None

        matches = []
        for record in records:
            display_name = self._resolve_display_name(record)
            match_field, match_value = self._find_match_context(
                record, matched_field_names, keyword
            )
            matches.append(SearchMatch(
                record_id=str(record.pk),
                display_name=display_name,
                match_field=match_field,
                match_value=match_value,
            ))

        return ObjectSearchResult(
            object_code=bo_code,
            object_name=bo_name,
            matches=matches,
        )

    def _resolve_model(self, bo_code: str, model_path: str):
        """Resolve Django model class from code or path."""
        if model_path:
            try:
                return import_string(model_path)
            except (ImportError, AttributeError):
                pass

        # Try ObjectRegistry
        from apps.system.services.object_registry import ObjectRegistry
        meta = ObjectRegistry.get_or_create_from_db(bo_code)
        if meta and meta.model_class:
            return meta.model_class

        return None

    def _get_searchable_fields(self, bo_code: str) -> set:
        """Get set of field codes marked as searchable for this object."""
        field_codes = FieldDefinition.objects.filter(
            object_code=bo_code,
            is_searchable=True,
            is_active=True,
        ).values_list('code', flat=True)
        return set(field_codes)

    def _resolve_display_name(self, record) -> str:
        """Extract readable display name from record."""
        for attr in ('name', 'code', 'title', 'data_no'):
            val = getattr(record, attr, None)
            if val:
                return str(val)
        return str(record.pk)

    def _find_match_context(
        self, record, field_names: list, keyword: str
    ) -> tuple:
        """Find which field matched and return field/value pair."""
        keyword_lower = keyword.lower()
        for name in field_names:
            val = getattr(record, name, None)
            if val and keyword_lower in str(val).lower():
                return name, str(val)
        # Fallback
        if field_names:
            val = getattr(record, field_names[0], '') or ''
            return field_names[0], str(val)
        return '', ''
