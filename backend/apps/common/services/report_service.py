"""
Report service for metadata-driven reporting.

Provides:
- Dynamic report data generation
- Aggregation calculations
- Report caching
- Chart data formatting
"""
from typing import Dict, List, Any, Optional, Type
from django.db.models import Sum, Count, Avg, Max, Min, F, Q, QuerySet
from django.core.cache import cache
import json
import hashlib


class ReportService:
    """
    Metadata-driven report service.

    Generates report data based on ReportLayout configuration.
    """

    AGGREGATION_FUNCTIONS = {
        'sum': Sum,
        'avg': Avg,
        'count': Count,
        'max': Max,
        'min': Min,
    }

    def __init__(self, report_layout):
        """
        Initialize report service.

        Args:
            report_layout: ReportLayout instance
        """
        self.report_layout = report_layout
        self.aggregation_config = report_layout.aggregation_config or {}
        self.chart_config = report_layout.chart_config or {}
        self.filter_config = report_layout.filter_config or {}
        self.cache_key_prefix = f'report:{report_layout.code}'

    def generate_report_data(
        self,
        filters: Optional[Dict] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate report data.

        Args:
            filters: User-provided filter values
            organization_id: Organization ID for data isolation

        Returns:
            Dict with metadata, data, and chart_config
        """
        # Check cache
        cache_key = self._get_cache_key(filters, organization_id)
        if self.report_layout.cache_enabled:
            cached = cache.get(cache_key)
            if cached:
                return cached

        # Get model class
        model_class = self._get_model_class()

        # Build queryset with filters
        queryset = self._build_queryset(model_class, filters, organization_id)

        # Execute aggregation
        aggregated_data = self._execute_aggregation(queryset)

        # Format result
        result = {
            'metadata': {
                'report_name': self.report_layout.name,
                'report_code': self.report_layout.code,
                'report_type': self.report_layout.report_type,
                'chart_type': self.chart_config.get('chart_type', 'bar'),
            },
            'data': aggregated_data,
            'chart_config': self._build_chart_options(aggregated_data),
            'filter_config': self.filter_config,
        }

        # Cache result
        if self.report_layout.cache_enabled:
            cache.set(cache_key, result, self.report_layout.cache_ttl or 300)

        return result

    def _get_model_class(self) -> Type:
        """Get Django model class for the business object."""
        # Model mapping based on business object code
        model_mapping = {
            'Asset': 'apps.assets.models.Asset',
            'Consumable': 'apps.consumables.models.Consumable',
            'InventoryTask': 'apps.inventory.models.InventoryTask',
            'Maintenance': 'apps.lifecycle.models.Maintenance',
            'DynamicData': 'apps.system.models.DynamicData',
        }

        bo_code = self.report_layout.business_object.code
        model_path = model_mapping.get(bo_code, 'apps.system.models.DynamicData')

        from django.utils.module_loading import import_string
        return import_string(model_path)

    def _build_queryset(
        self,
        model_class: Type,
        filters: Optional[Dict] = None,
        organization_id: Optional[str] = None
    ) -> QuerySet:
        """Build filtered queryset."""
        queryset = model_class.objects.filter(is_deleted=False)

        # Apply organization filter
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        # Apply config-defined static filters
        config_filters = self.aggregation_config.get('filters', {})
        queryset = self._apply_filters(queryset, config_filters)

        # Apply user-provided dynamic filters
        if filters:
            queryset = self._apply_filters(queryset, filters)

        return queryset

    def _apply_filters(
        self,
        queryset: QuerySet,
        filters: Dict[str, Any]
    ) -> QuerySet:
        """Apply filter conditions to queryset."""
        for field, value in filters.items():
            if value is None or value == '':
                continue

            if isinstance(value, dict):
                # Handle operators: $gte, $lte, $in, $like, $ne
                for op, val in value.items():
                    if op == '$gte':
                        queryset = queryset.filter(**{f'{field}__gte': val})
                    elif op == '$lte':
                        queryset = queryset.filter(**{f'{field}__lte': val})
                    elif op == '$gt':
                        queryset = queryset.filter(**{f'{field}__gt': val})
                    elif op == '$lt':
                        queryset = queryset.filter(**{f'{field}__lt': val})
                    elif op == '$in':
                        queryset = queryset.filter(**{f'{field}__in': val})
                    elif op == '$like':
                        queryset = queryset.filter(**{f'{field}__icontains': val})
                    elif op == '$ne':
                        queryset = queryset.exclude(**{field: val})
            else:
                queryset = queryset.filter(**{field: value})

        return queryset

    def _execute_aggregation(self, queryset: QuerySet) -> List[Dict]:
        """Execute data aggregation."""
        dimensions = self.aggregation_config.get('dimensions', [])
        metrics = self.aggregation_config.get('metrics', [])
        order_by = self.aggregation_config.get('order_by', [])
        limit = self.aggregation_config.get('limit', 100)

        if not metrics:
            # No metrics defined, return raw data
            return list(queryset.values()[:limit])

        # Build aggregation annotations
        annotations = {}
        for metric in metrics:
            field = metric['field']
            agg_func_name = metric.get('agg', 'count')
            alias = metric.get('alias', f'{field}_{agg_func_name}')

            AggFunc = self.AGGREGATION_FUNCTIONS.get(agg_func_name, Count)
            annotations[alias] = AggFunc(field)

        if dimensions:
            # Grouped aggregation
            result = queryset.values(*dimensions).annotate(**annotations)

            # Apply ordering
            for order_item in order_by:
                field = order_item.get('field')
                direction = '-' if order_item.get('dir') == 'desc' else ''
                result = result.order_by(f'{direction}{field}')

            return list(result[:limit])
        else:
            # Total aggregation (no grouping)
            result = queryset.aggregate(**annotations)
            return [result]

    def _build_chart_options(self, data: List[Dict]) -> Dict[str, Any]:
        """Build ECharts-compatible chart options."""
        chart_type = self.chart_config.get('chart_type', 'bar')
        x_axis = self.chart_config.get('x_axis', {})
        y_axis = self.chart_config.get('y_axis', [])
        title = self.chart_config.get('title', self.report_layout.name)

        # Build x-axis categories from dimension
        x_field = x_axis.get('field')
        categories = [str(item.get(x_field, '')) for item in data] if x_field else []

        # Build series data
        series = []
        for y_config in y_axis:
            y_field = y_config.get('field')
            y_label = y_config.get('label', y_field)
            values = [item.get(y_field, 0) for item in data]

            series.append({
                'name': y_label,
                'type': chart_type,
                'data': values,
            })

        return {
            'title': {'text': title},
            'xAxis': {
                'type': 'category',
                'data': categories,
                'name': x_axis.get('label', ''),
            },
            'yAxis': {
                'type': 'value',
            },
            'series': series,
            'tooltip': {'trigger': 'axis'},
            'legend': {
                'data': [s['name'] for s in series]
            },
        }

    def _get_cache_key(
        self,
        filters: Optional[Dict] = None,
        organization_id: Optional[str] = None
    ) -> str:
        """Generate cache key."""
        key_parts = [
            self.cache_key_prefix,
            organization_id or 'all',
        ]
        if filters:
            filter_hash = hashlib.md5(
                json.dumps(filters, sort_keys=True, default=str).encode()
            ).hexdigest()[:8]
            key_parts.append(filter_hash)

        return ':'.join(key_parts)

    def clear_cache(self, filters: Optional[Dict] = None) -> None:
        """Clear report cache."""
        # Clear specific cache or all caches for this report
        try:
            from django_redis import get_redis_connection
            conn = get_redis_connection('default')
            pattern = f'{self.cache_key_prefix}:*'
            keys = conn.keys(pattern)
            if keys:
                conn.delete(*keys)
        except Exception:
            # For non-Redis, clear specific key
            if filters:
                cache_key = self._get_cache_key(filters)
                cache.delete(cache_key)

    @staticmethod
    def execute_query(
        model_class: Type,
        dimensions: List[str],
        metrics: List[Dict],
        filters: Optional[Dict] = None,
        order_by: Optional[List[Dict]] = None,
        limit: int = 100,
        organization_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Static method to execute ad-hoc queries.

        Args:
            model_class: Django model class
            dimensions: Group-by fields
            metrics: Aggregation metrics
            filters: Filter conditions
            order_by: Ordering config
            limit: Result limit
            organization_id: Organization filter

        Returns:
            List of aggregated results
        """
        queryset = model_class.objects.filter(is_deleted=False)

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        if filters:
            for field, value in filters.items():
                if value:
                    queryset = queryset.filter(**{field: value})

        # Build annotations
        annotations = {}
        for metric in metrics:
            field = metric['field']
            agg = metric.get('agg', 'count')
            alias = metric.get('alias', f'{field}_{agg}')

            AggFunc = ReportService.AGGREGATION_FUNCTIONS.get(agg, Count)
            annotations[alias] = AggFunc(field)

        if dimensions:
            result = queryset.values(*dimensions).annotate(**annotations)
        else:
            result = [queryset.aggregate(**annotations)]

        # Apply ordering
        if order_by:
            for item in order_by:
                field = item.get('field')
                direction = '-' if item.get('dir') == 'desc' else ''
                result = result.order_by(f'{direction}{field}')

        return list(result[:limit])
