import logging
from urllib.parse import urlencode

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.common.responses.base import BaseResponse
from apps.system.services.object_registry import ObjectRegistry
from apps.system.services.object_history_aggregation_service import ObjectHistoryAggregationService
from apps.system.services.relation_query_service import RelationQueryService

logger = logging.getLogger(__name__)


class ObjectRouterRelationActionsMixin:
    def history(self, request, *args, **kwargs):
        """
        Get unified history entries for a single record.

        GET /api/system/objects/{code}/{id}/history/
        """
        error_response = self._ensure_object_meta_loaded(kwargs)
        if error_response is not None:
            return error_response

        record_id = kwargs.get("id")
        if not record_id:
            return BaseResponse.error(
                "VALIDATION_ERROR",
                "common.messages.badRequest",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        self._set_delegate_lookup_pk(kwargs)
        instance = self._load_delegate_instance(record_id)
        if instance is None:
            return BaseResponse.error(
                "NOT_FOUND",
                "common.messages.resourceNotFound",
                http_status=status.HTTP_404_NOT_FOUND,
            )

        service = ObjectHistoryAggregationService()
        items = service.build_history(
            object_code=self._object_meta.code,
            instance=instance,
        )

        page = self._parse_positive_int(request.query_params.get("page"), default=1)
        page_size = self._parse_positive_int(request.query_params.get("page_size"), default=20, maximum=100)
        start = (page - 1) * page_size
        end = start + page_size

        return BaseResponse.paginated(
            count=len(items),
            next_url=self._build_page_url(request, page + 1, page_size) if end < len(items) else None,
            previous_url=self._build_page_url(request, page - 1, page_size) if page > 1 else None,
            results=items[start:end],
        )

    def relations(self, request, *args, **kwargs):
        """
        Get relation definitions for current object.

        GET /api/system/objects/{code}/relations/
        """
        error_response = self._ensure_object_meta_loaded(kwargs)
        if error_response is not None:
            return error_response

        request_locale = self._get_request_locale(request)
        service = RelationQueryService()
        relations = service.list_relations(self._object_meta.code, locale=request_locale)
        return Response(
            {
                'success': True,
                'data': {
                    'object_code': self._object_meta.code,
                    'relations': relations,
                    'locale': request_locale,
                }
            },
            status=status.HTTP_200_OK,
        )

    def relation_counts(self, request, *args, **kwargs):
        """
        Get record counts for all relations of a parent record.

        GET /api/system/objects/{code}/{id}/relation-counts/
        """
        error_response = self._ensure_object_meta_loaded(kwargs)
        if error_response is not None:
            return error_response

        parent_id = kwargs.get('id')
        if not parent_id:
            return BaseResponse.error(
                'VALIDATION_ERROR',
                'common.messages.badRequest',
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        service = RelationQueryService()
        try:
            counts = service.count_relations(
                parent_object_code=self._object_meta.code,
                parent_id=str(parent_id),
                organization_id=str(getattr(request, 'organization_id', '') or '') or None,
            )
        except Exception as exc:
            logger.warning(
                "relation_counts failed. code=%s id=%s error=%s",
                self._object_meta.code,
                parent_id,
                exc,
            )
            counts = {}

        return Response(
            {
                'success': True,
                'data': {
                    'object_code': self._object_meta.code,
                    'parent_id': str(parent_id),
                    'counts': counts,
                }
            },
            status=status.HTTP_200_OK,
        )

    def compact_detail(self, request, *args, **kwargs):
        """
        Get compact summary fields for a single record (used by hover cards).

        GET /api/system/objects/{code}/{id}/compact/
        """
        error_response = self._ensure_object_meta_loaded(kwargs)
        if error_response is not None:
            return error_response

        record_id = kwargs.get('id')
        if not record_id:
            return BaseResponse.error(
                'VALIDATION_ERROR',
                'common.messages.badRequest',
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        instance = None
        try:
            if self._delegate_viewset and hasattr(self._delegate_viewset, 'get_queryset'):
                queryset = self._delegate_viewset.get_queryset()
            else:
                model_path = getattr(self._object_meta, 'django_model_path', '') or ''
                if '.' not in model_path:
                    return BaseResponse.error(
                        code='NOT_FOUND',
                        message='common.messages.resourceNotFound',
                        http_status=status.HTTP_404_NOT_FOUND,
                    )

                from django.apps import apps

                parts = model_path.rsplit('.', 1)
                app_label = parts[0].replace('apps.', '').split('.')[0]
                model_name = parts[-1]
                try:
                    model_class = apps.get_model(app_label, model_name)
                except LookupError:
                    return BaseResponse.error(
                        code='NOT_FOUND',
                        message='common.messages.resourceNotFound',
                        http_status=status.HTTP_404_NOT_FOUND,
                    )
                queryset = model_class.objects.all()

            instance = queryset.filter(pk=record_id).first()
        except Exception:
            instance = None

        if not instance:
            return BaseResponse.error(
                code='NOT_FOUND',
                message='common.messages.resourceNotFound',
                http_status=status.HTTP_404_NOT_FOUND,
            )

        request_locale = self._get_request_locale(request)
        compact_fields = self._resolve_compact_fields(instance, request_locale)

        return Response(
            {
                'success': True,
                'data': {
                    'object_code': self._object_meta.code,
                    'record_id': str(record_id),
                    'fields': compact_fields,
                }
            },
            status=status.HTTP_200_OK,
        )

    def _resolve_compact_fields(self, instance, locale: str) -> list:
        """Build compact summary field list from instance (max 6 fields)."""
        max_compact_fields = 6
        skip_fields = {
            'id', 'organization', 'organization_id', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'is_deleted', 'deleted_at',
            'name', 'code', 'is_active',
        }

        model_class = type(instance)
        fields = []

        for field in model_class._meta.fields:
            if field.name in skip_fields:
                continue
            if not field.editable:
                continue

            value = getattr(instance, field.name, None)
            if value is None:
                continue

            display_value = value
            field_type = 'text'
            if getattr(field, 'is_relation', False):
                field_type = 'reference'
                display_value = str(value) if value else ''
            elif hasattr(field, 'choices') and field.choices:
                field_type = 'select'
                display_value = str(dict(field.choices).get(value, value))
            else:
                display_value = str(value) if value is not None else ''

            label = str(getattr(field, 'verbose_name', field.name) or field.name)

            fields.append({
                'field_code': field.name,
                'label': label,
                'value': display_value,
                'field_type': field_type,
            })

            if len(fields) >= max_compact_fields:
                break

        return fields

    def relationship_graph(self, request, *args, **kwargs):
        """
        Get relationship overview for a record - all relations with counts
        and sample records.

        GET /api/system/objects/{code}/{id}/relationship-graph/
        """
        error_response = self._ensure_object_meta_loaded(kwargs)
        if error_response is not None:
            return error_response

        parent_id = kwargs.get('id')
        if not parent_id:
            return BaseResponse.error(
                'VALIDATION_ERROR',
                'common.messages.badRequest',
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        locale = request.headers.get('Accept-Language', 'zh')

        try:
            service = RelationQueryService()
            counts = service.count_relations(
                parent_object_code=self._object_meta.code,
                parent_record_id=str(parent_id),
            )
            relations_list = service.list_relations(
                parent_object_code=self._object_meta.code,
                locale=locale,
            )

            graph = []
            for relation in relations_list:
                relation_code = relation.get('relation_code', '')
                count = counts.get(relation_code, 0)

                sample_records = []
                if count > 0:
                    try:
                        resolution = service.resolve(
                            parent_object_code=self._object_meta.code,
                            relation_code=relation_code,
                            parent_record_id=str(parent_id),
                        )
                        if resolution and resolution.target_queryset is not None:
                            sample_qs = resolution.target_queryset[:3]
                            for record in sample_qs:
                                sample_records.append({
                                    'id': str(record.pk),
                                    'display_name': str(
                                        getattr(record, 'name', None)
                                        or getattr(record, 'code', None)
                                        or record.pk
                                    ),
                                })
                    except Exception:
                        pass

                graph.append({
                    'relation_code': relation_code,
                    'relation_name': relation.get('label', relation_code),
                    'target_object_code': relation.get('target_object_code', ''),
                    'relation_kind': relation.get('relation_kind', ''),
                    'display_tier': relation.get('display_tier', 'L2'),
                    'count': count,
                    'sample_records': sample_records,
                })

            return BaseResponse.create_success_response(
                data={
                    'object_code': self._object_meta.code,
                    'record_id': str(parent_id),
                    'relations': graph,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return BaseResponse.error(
                code='INTERNAL_ERROR',
                message=str(exc),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @staticmethod
    def _parse_positive_int(value, *, default: int, maximum: int | None = None) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        if parsed < 1:
            parsed = default
        if maximum is not None:
            parsed = min(parsed, maximum)
        return parsed

    @staticmethod
    def _build_page_url(request, page: int, page_size: int) -> str:
        query = request.query_params.copy()
        query["page"] = page
        query["page_size"] = page_size
        return request.build_absolute_uri(f"{request.path}?{urlencode(query, doseq=True)}")

    def related(self, request, *args, **kwargs):
        """
        Get related object records by relation code.

        GET /api/system/objects/{code}/{id}/related/{relation_code}/
        """
        error_response = self._ensure_object_meta_loaded(kwargs)
        if error_response is not None:
            return error_response

        parent_id = kwargs.get('id')
        relation_code = kwargs.get('relation_code')
        if not parent_id:
            return BaseResponse.error(
                'VALIDATION_ERROR',
                'common.messages.badRequest',
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        if not relation_code:
            return BaseResponse.error(
                'VALIDATION_ERROR',
                'common.messages.badRequest',
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        service = RelationQueryService()
        try:
            resolution = service.resolve_related_queryset(
                parent_object_code=self._object_meta.code,
                parent_id=str(parent_id),
                relation_code=str(relation_code),
                organization_id=str(getattr(request, 'organization_id', '') or '') or None,
            )
        except (ValidationError, DjangoValidationError):
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message='common.messages.badRequest',
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        target_meta = ObjectRegistry.get_or_create_from_db(resolution.target_object_code)
        if not target_meta:
            return BaseResponse.error(
                code='NOT_FOUND',
                message='common.messages.resourceNotFound',
                http_status=status.HTTP_404_NOT_FOUND,
            )

        delegate = self._create_delegate_viewset(target_meta, request)
        delegate.action = 'list'
        delegate.kwargs = {'code': resolution.target_object_code}
        delegate.request = request

        queryset = resolution.target_queryset
        if hasattr(delegate, 'filter_queryset'):
            queryset = delegate.filter_queryset(queryset)
        queryset = self._apply_delegate_default_ordering(queryset, delegate)

        page = delegate.paginate_queryset(queryset) if hasattr(delegate, 'paginate_queryset') else None
        if page is not None:
            serializer = delegate.get_serializer(page, many=True)
            page_response = delegate.get_paginated_response(serializer.data)
            page_payload = page_response.data
            if isinstance(page_payload, dict) and page_payload.get('success') is True:
                page_payload = page_payload.get('data', {}) or {}
            if not isinstance(page_payload, dict) or 'results' not in page_payload:
                page_payload = {
                    'count': len(serializer.data),
                    'next': None,
                    'previous': None,
                    'results': serializer.data,
                }
        else:
            serializer = delegate.get_serializer(queryset, many=True)
            page_payload = {
                'count': len(serializer.data),
                'next': None,
                'previous': None,
                'results': serializer.data,
            }

        relation = resolution.relation
        relation_payload = {
            'relation_code': relation.relation_code,
            'relation_kind': relation.relation_kind,
            'target_object_code': relation.target_object_code,
            'display_mode': relation.display_mode,
            'sort_order': relation.sort_order,
        }

        return Response(
            {
                'success': True,
                'data': {
                    **page_payload,
                    'relation': relation_payload,
                    'parent_object_code': self._object_meta.code,
                    'parent_id': str(parent_id),
                    'target_object_code': resolution.target_object_code,
                }
            },
            status=status.HTTP_200_OK,
        )
