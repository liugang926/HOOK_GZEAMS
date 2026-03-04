"""
Object Router ViewSet - Unified dynamic routing for all business objects.

This ViewSet provides a single entry point (/api/objects/{code}/) for all
business objects, routing requests to the appropriate ViewSet based on the
object code.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied
from typing import Any, List, Optional
import inspect
import re
import logging
from django.db.models import Q

from apps.system.services.object_registry import ObjectRegistry
from apps.system.services.layout_runtime_normalizer import normalize_layout_config_for_runtime
from apps.common.viewsets.metadata_driven import MetadataDrivenViewSet
from apps.common.responses.base import BaseResponse
from apps.common.services.i18n_service import TranslationService, get_current_language

logger = logging.getLogger(__name__)


class ObjectRouterViewSet(viewsets.ViewSet):
    """
    Unified dynamic object router ViewSet.

    URL Pattern: /api/objects/{code}/

    This ViewSet dynamically routes requests to the appropriate business object
    based on the object_code in the URL. It supports both hardcoded Django models
    (with existing ViewSets) and dynamic metadata-driven objects.

    Examples:
        GET /api/objects/Asset/              # List assets
        POST /api/objects/Asset/             # Create asset
        GET /api/objects/Asset/{id}/         # Get asset detail
        GET /api/objects/Asset/metadata/     # Get asset metadata

    Standard objects automatically supported:
        - Asset, AssetCategory, AssetPickup, AssetTransfer, AssetReturn, AssetLoan
        - Consumable, ConsumableCategory, ConsumableStock
        - PurchaseRequest, AssetReceipt, Maintenance, DisposalRequest
        - InventoryTask, InventorySnapshot
        - And many more...
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._delegate_viewset: Optional[viewsets.ModelViewSet] = None
        self._object_meta = None
        self._feature_flag_cache = {}
        self._legacy_field_code_warned = False

    _IMMUTABLE_SYSTEM_FIELD_CODES = {
        'id',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'deleted_at',
        'deleted_by',
        'is_deleted',
        'version',
        'organization',
        'organization_id',
        'tenant_id',
    }

    def initial(self, request, *args, **kwargs):
        """
        Initialize ViewSet by loading object metadata and creating delegate.

        This method is called before any action to set up the appropriate
        ViewSet based on the object_code in the URL.
        """
        super().initial(request, *args, **kwargs)

        object_code = kwargs.get('code')
        if not object_code:
            raise ValidationError({"code": ["object_code is required"]})

        # Get object metadata from registry or database
        self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
        if not self._object_meta:
            raise NotFound(f"Business object '{object_code}' not found")

        # Create the delegate ViewSet that will handle the actual request
        self._delegate_viewset = self._create_delegate_viewset(
            self._object_meta, request
        )

    def _create_delegate_viewset(self, meta, request):
        """
        Create the delegate ViewSet based on object type.

        For hardcoded objects, uses the existing ViewSet.
        For dynamic objects, uses MetadataDrivenViewSet.

        Args:
            meta: ObjectMeta instance
            request: Current HTTP request

        Returns:
            ViewSet instance configured for this object
        """
        if meta.is_hardcoded and meta.viewset_class:
            return self._get_hardcoded_viewset(meta, request)
        else:
            return self._get_dynamic_viewset(meta, request)

    def _get_hardcoded_viewset(self, meta, request):
        """
        Get ViewSet for hardcoded Django models.

        Args:
            meta: ObjectMeta with is_hardcoded=True
            request: Current HTTP request

        Returns:
            Configured ViewSet instance
        """
        viewset_class = meta.viewset_class
        if not viewset_class:
            # Fallback to dynamic viewset if no viewset configured
            return self._get_dynamic_viewset(meta, request)

        # Instantiate and configure the ViewSet
        viewset = viewset_class()
        # Rebuild queryset per request to avoid stale tenant-scoped filters that can
        # be baked into class-level queryset during module import.
        template_queryset = getattr(viewset_class, 'queryset', None)
        viewset.queryset = self._build_request_scoped_queryset(template_queryset, request)
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = getattr(self, 'action', None)
        # Set kwargs for DRF's get_object() method to access URL parameters
        viewset.kwargs = self.kwargs
        viewset.args = self.args

        # Initialize the ViewSet
        if hasattr(viewset, 'initial'):
            viewset.initial(request, *self.args, **self.kwargs)

        return viewset

    def _build_request_scoped_queryset(self, template_queryset, request):
        """
        Build a deterministic queryset for delegated hardcoded ViewSets.

        Class-level querysets can accidentally capture stale organization filters.
        This rebuilds from `all_objects`/default manager and applies request-scoped
        organization + soft-delete constraints explicitly.
        """
        if template_queryset is None:
            return None

        model_class = getattr(template_queryset, 'model', None)
        if model_class is None:
            return template_queryset

        manager = getattr(model_class, 'all_objects', None) or model_class._default_manager
        queryset = manager.all()

        field_names = {f.name for f in model_class._meta.fields}
        request_org_id = getattr(request, 'organization_id', None)

        if 'organization' in field_names and request_org_id:
            queryset = queryset.filter(organization_id=request_org_id)
        elif 'organization' in field_names and not request_org_id:
            # Avoid accidental cross-organization leakage when org context is absent.
            queryset = queryset.none()

        if 'is_deleted' in field_names:
            queryset = queryset.filter(is_deleted=False)

        try:
            select_related = getattr(template_queryset.query, 'select_related', None)
            if select_related is True:
                queryset = queryset.select_related()
            elif isinstance(select_related, dict) and select_related:
                queryset = queryset.select_related(*select_related.keys())
        except Exception:
            pass

        try:
            prefetch_related = tuple(getattr(template_queryset, '_prefetch_related_lookups', ()) or ())
            if prefetch_related:
                queryset = queryset.prefetch_related(*prefetch_related)
        except Exception:
            pass

        try:
            order_by = tuple(getattr(template_queryset.query, 'order_by', ()) or ())
            if order_by:
                queryset = queryset.order_by(*order_by)
        except Exception:
            pass

        return queryset

    def _get_dynamic_viewset(self, meta, request):
        """
        Get ViewSet for dynamic metadata-driven objects.

        Args:
            meta: ObjectMeta
            request: Current HTTP request

        Returns:
            Configured MetadataDrivenViewSet instance
        """
        viewset = MetadataDrivenViewSet()
        viewset.business_object_code = meta.code
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = getattr(self, 'action', None)
        # Set kwargs for DRF's get_object() method to access URL parameters
        viewset.kwargs = self.kwargs
        viewset.args = self.args
        viewset.initial(request, *self.args, **self.kwargs)
        return viewset

    # Delegate all standard CRUD methods to the delegate ViewSet

    def list(self, request, *args, **kwargs):
        """
        List objects with pagination, filtering, and search.

        GET /api/objects/{code}/
        """
        resp = self._delegate_viewset.list(request, *args, **kwargs)

        # Normalize list response shapes:
        # - The low-code frontend expects the standard paginated DTO (wrapped by BaseResponse):
        #   `{ success: true, data: { count, next, previous, results } }`
        # - Some legacy viewsets return `{ success: true, data: [] }`
        # - Some DRF viewsets may return plain list or plain paginated dict.
        try:
            if isinstance(resp, Response) and isinstance(getattr(resp, "data", None), dict):
                payload = resp.data
                if payload.get("success") is True:
                    # Legacy `{ success, data: [] }` -> paginated DTO
                    if isinstance(payload.get("data"), list):
                        items = payload.get("data") or []
                        resp.data = {
                            "success": True,
                            "data": {
                                "count": len(items),
                                "next": None,
                                "previous": None,
                                "results": items,
                            },
                        }
                    # Plain paginated dict under `data` is already acceptable.
                    return resp

                # Plain paginated dict -> wrap
                if "count" in payload and "results" in payload:
                    resp.data = {"success": True, "data": payload}
        except Exception:
            pass

        try:
            # Plain list -> wrap
            if isinstance(resp, Response) and isinstance(getattr(resp, "data", None), list):
                items = resp.data or []
                resp.data = {
                    "success": True,
                    "data": {
                        "count": len(items),
                        "next": None,
                        "previous": None,
                        "results": items,
                    },
                }
        except Exception:
            pass

        return resp

    def retrieve(self, request, *args, **kwargs):
        """
        Get a single object by ID.

        GET /api/objects/{code}/{id}/
        """
        # Map 'id' to 'pk' for DRF ViewSet compatibility
        # URL pattern uses <uuid:id> but ViewSet.retrieve() expects 'pk' parameter
        # We need to update the delegate's kwargs attribute directly because
        # DRF's get_object() method accesses self.kwargs, not the function kwargs
        if 'id' in kwargs:
            # Update delegate's kwargs with mapped value
            self._delegate_viewset.kwargs = {
                **self._delegate_viewset.kwargs,
                'pk': kwargs['id']
            }
        return self._delegate_viewset.retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Create a new object.

        POST /api/objects/{code}/
        """
        return self._delegate_viewset.create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Full update of an object.

        PUT /api/objects/{code}/{id}/
        """
        # Map 'id' to 'pk' for DRF ViewSet compatibility
        if 'id' in kwargs:
            self._delegate_viewset.kwargs = {
                **self._delegate_viewset.kwargs,
                'pk': kwargs['id']
            }
        return self._delegate_viewset.update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Partial update of an object.

        PATCH /api/objects/{code}/{id}/
        """
        # Map 'id' to 'pk' for DRF ViewSet compatibility
        if 'id' in kwargs:
            self._delegate_viewset.kwargs = {
                **self._delegate_viewset.kwargs,
                'pk': kwargs['id']
            }
        return self._delegate_viewset.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete (soft delete) an object.

        DELETE /api/objects/{code}/{id}/
        """
        # Map 'id' to 'pk' for DRF ViewSet compatibility
        if 'id' in kwargs:
            self._delegate_viewset.kwargs = {
                **self._delegate_viewset.kwargs,
                'pk': kwargs['id']
            }
        return self._delegate_viewset.destroy(request, *args, **kwargs)

    def _resolve_custom_action(self, action_path: str, request_method: str, detail: bool):
        """
        Resolve custom action handler on delegated ViewSet.

        Priority:
        1) Match DRF @action `url_path` (supports regex + nested path segments)
        2) Fallback to normalized method name (e.g. `batch-post` -> `batch_post`)
        """
        normalized_path = (action_path or '').strip('/')
        if not normalized_path:
            return None, (), {}

        method_lower = request_method.lower()
        delegate = self._delegate_viewset

        # 1) Match action-decorated handlers by url_path.
        for attr_name in dir(delegate):
            handler = getattr(delegate, attr_name, None)
            if not callable(handler):
                continue

            url_path = getattr(handler, 'url_path', None)
            if not url_path:
                continue

            handler_detail = getattr(handler, 'detail', None)
            if handler_detail is not None and bool(handler_detail) != bool(detail):
                continue

            mapping = getattr(handler, 'mapping', None)
            if mapping and method_lower not in mapping:
                continue

            try:
                match = re.fullmatch(url_path, normalized_path)
            except re.error:
                continue

            if match:
                route_kwargs = {
                    key: value
                    for key, value in match.groupdict().items()
                    if value is not None
                }
                return handler, (), route_kwargs

        # 2) Fallback by method name.
        normalized_full = normalized_path.replace('-', '_').replace('/', '_')
        segments = [seg for seg in normalized_path.split('/') if seg]
        normalized_head = segments[0].replace('-', '_') if segments else normalized_full

        for candidate_name, extra_args in (
            (normalized_full, ()),
            (normalized_head, tuple(segments[1:])),
        ):
            handler = getattr(delegate, candidate_name, None)
            if not callable(handler):
                continue

            handler_detail = getattr(handler, 'detail', None)
            if handler_detail is not None and bool(handler_detail) != bool(detail):
                continue

            mapping = getattr(handler, 'mapping', None)
            if mapping and method_lower not in mapping:
                continue

            return handler, extra_args, {}

        return None, (), {}

    def _invoke_custom_action(self, request, *, action_path: str, detail: bool, object_id=None):
        """Invoke resolved custom action on delegated ViewSet."""
        handler, route_args, route_kwargs = self._resolve_custom_action(
            action_path=action_path,
            request_method=request.method,
            detail=detail,
        )
        if not handler:
            try:
                delegate_name = type(self._delegate_viewset).__name__
            except Exception:
                delegate_name = 'unknown'
            logger.warning(
                "Object router custom action not resolved. code=%s detail=%s action_path=%s method=%s delegate=%s",
                getattr(self._object_meta, 'code', None),
                detail,
                action_path,
                request.method,
                delegate_name,
            )
            return BaseResponse.not_found(
                f"Action '{action_path}' for object '{self._object_meta.code}'"
            )

        if object_id is not None:
            self._delegate_viewset.kwargs = {
                **self._delegate_viewset.kwargs,
                'pk': object_id
            }

        old_action = getattr(self._delegate_viewset, 'action', None)
        self._delegate_viewset.action = getattr(handler, '__name__', old_action)
        from apps.common.middleware import get_current_organization, set_current_organization, clear_current_organization
        previous_org_id = get_current_organization()
        request_org_id = getattr(request, 'organization_id', None)

        try:
            # Keep tenant context deterministic for delegated custom actions.
            # Some test/runtime paths may miss middleware-bound thread-local org.
            if request_org_id:
                set_current_organization(str(request_org_id))

            params = inspect.signature(handler).parameters
            accepts_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
            invoke_kwargs = {}

            if object_id is not None and ('pk' in params or accepts_var_kw):
                invoke_kwargs['pk'] = object_id

            for key, value in route_kwargs.items():
                if key in params or accepts_var_kw:
                    invoke_kwargs[key] = value

            return handler(request, *route_args, **invoke_kwargs)
        finally:
            self._delegate_viewset.action = old_action
            if previous_org_id:
                set_current_organization(previous_org_id)
            else:
                clear_current_organization()

    def collection_action(self, request, *args, **kwargs):
        """
        Route collection-level custom actions.

        Examples:
        - /api/system/objects/FinanceVoucher/batch_push/
        - /api/system/objects/FinanceVoucher/generate/asset-purchase/
        - /api/system/objects/DepreciationConfig/categories/{category_id}/
        """
        return self._invoke_custom_action(
            request,
            action_path=kwargs.get('action_path', ''),
            detail=False,
        )

    def detail_action(self, request, *args, **kwargs):
        """
        Route detail-level custom actions.

        Examples:
        - /api/system/objects/FinanceVoucher/{id}/submit/
        - /api/system/objects/FinanceVoucher/{id}/integration-logs/
        """
        return self._invoke_custom_action(
            request,
            action_path=kwargs.get('action_path', ''),
            detail=True,
            object_id=kwargs.get('id'),
        )

    @action(detail=False, methods=['post'], url_path='batch-get')
    def batch_get(self, request, *args, **kwargs):
        """
        Batch get objects by ids (for reference field resolution).

        POST /api/system/objects/{code}/batch-get/
        Body: { "ids": ["uuid1", "uuid2", ...] }

        Returns serialized objects in the input order (when possible).
        """
        if not self._object_meta:
            object_code = kwargs.get('code')
            if not object_code:
                return BaseResponse.error('VALIDATION_ERROR', 'object_code is required', http_status=status.HTTP_400_BAD_REQUEST)

            self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
            if not self._object_meta:
                return BaseResponse.not_found(f"Business object '{object_code}' not found")

            self._delegate_viewset = self._create_delegate_viewset(self._object_meta, request)

        ids = request.data.get('ids') if isinstance(request.data, dict) else None
        if not isinstance(ids, list):
            return BaseResponse.error('VALIDATION_ERROR', 'ids must be a list', http_status=status.HTTP_400_BAD_REQUEST)

        # Normalize and cap to prevent abuse.
        normalized_ids = [str(v) for v in ids if v not in (None, '')]
        if len(normalized_ids) == 0:
            return BaseResponse.success({'results': [], 'missing_ids': []})
        if len(normalized_ids) > 200:
            return BaseResponse.error('VALIDATION_ERROR', 'ids too large (max 200)', http_status=status.HTTP_400_BAD_REQUEST)

        try:
            if hasattr(self._delegate_viewset, 'get_queryset'):
                qs = self._delegate_viewset.get_queryset()
            else:
                qs = getattr(self._delegate_viewset, 'queryset', None)

            if qs is None:
                return BaseResponse.success({'results': [], 'missing_ids': normalized_ids})

            base_qs = qs
            if hasattr(self._delegate_viewset, 'filter_queryset'):
                try:
                    qs = self._delegate_viewset.filter_queryset(qs)
                except Exception:
                    qs = base_qs

            qs = qs.filter(pk__in=normalized_ids)

            # Some viewsets override list/retrieve and do not use filter backends.
            # If filtering removed everything, fall back to the raw queryset.
            if not qs.exists():
                qs = base_qs.filter(pk__in=normalized_ids)

            results = []
            if hasattr(self._delegate_viewset, 'get_serializer'):
                try:
                    serializer = self._delegate_viewset.get_serializer(qs, many=True)
                    results = serializer.data
                except Exception:
                    # Some viewsets have a richer retrieve serializer that may be misconfigured.
                    # Prefer list serializer for reference resolution (id/name/code is enough).
                    old_action = getattr(self._delegate_viewset, 'action', None)
                    try:
                        self._delegate_viewset.action = 'list'
                        serializer = self._delegate_viewset.get_serializer(qs, many=True)
                        results = serializer.data
                    except Exception:
                        results = [{'id': str(obj.pk), 'name': str(obj)} for obj in qs]
                    finally:
                        self._delegate_viewset.action = old_action
            else:
                # Fallback: minimal representation
                results = [{'id': str(obj.pk), 'name': str(obj)} for obj in qs]

            by_id = {}
            for item in results:
                if isinstance(item, dict):
                    item_id = item.get('id') or item.get('pk')
                    if item_id is not None:
                        by_id[str(item_id)] = item

            ordered = [by_id[i] for i in normalized_ids if i in by_id]
            missing = [i for i in normalized_ids if i not in by_id]

            return BaseResponse.success({'results': ordered, 'missing_ids': missing})
        except Exception as e:
            # Never fail the entire page rendering because of a label-resolve helper.
            import logging
            logging.getLogger(__name__).warning(f"batch_get failed for {self._object_meta.code}: {e}")
            return BaseResponse.success({'results': [], 'missing_ids': normalized_ids})

    @action(detail=False, methods=['get'], url_path='metadata')
    def metadata(self, request, *args, **kwargs):
        """
        Get object metadata for frontend dynamic rendering.

        GET /api/objects/{code}/metadata/

        Returns field definitions, layout configurations,
        permissions, and other metadata needed for the frontend
        to dynamically render forms and lists.

        Response structure:
        {
            "success": true,
            "data": {
                "code": "Asset",
                "name": "资产卡片",
                "is_hardcoded": true,
                "fields": [...],
                "layouts": {
                    "form": {...},
                    "list": {...}
                },
                "permissions": {...}
            }
        }
        """
        # Initialize object_meta if not already done
        # This is needed because as_view() doesn't call initial() for custom actions
        if not self._object_meta:
            object_code = kwargs.get('code')

            if not object_code:
                return BaseResponse.error('VALIDATION_ERROR', 'object_code is required', http_status=status.HTTP_400_BAD_REQUEST)

            self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
            if not self._object_meta:
                return BaseResponse.not_found(f"Business object '{object_code}' not found")

        from apps.system.models import FieldDefinition, ModelFieldDefinition, PageLayout

        # Get field definitions from both sources:
        # 1. FieldDefinition for low-code custom fields
        # 2. ModelFieldDefinition for hardcoded Django model fields
        request_locale = self._get_request_locale(request)
        runtime_i18n_enabled = self._is_feature_enabled(
            'runtime_i18n_enabled',
            default=True,
            request=request,
        )
        fields = []

        # For hardcoded objects, get fields from ModelFieldDefinition
        if self._object_meta.is_hardcoded:
            model_fields = ModelFieldDefinition.objects.filter(
                business_object__code=self._object_meta.code
            ).order_by('sort_order')

            for fd in model_fields:
                fields.append(
                    self._format_model_field(
                        fd,
                        context='form',
                        locale=request_locale,
                        localize=runtime_i18n_enabled,
                    )
                )
        else:
            # For dynamic objects, get fields from FieldDefinition
            # FieldDefinition uses GlobalMetadataManager (no org filtering)
            fields_query = FieldDefinition.objects.filter(
                business_object__code=self._object_meta.code
            ).order_by('sort_order')

            for fd in fields_query:
                fields.append(
                    self._format_field_definition(
                        fd,
                        context='form',
                        locale=request_locale,
                        localize=runtime_i18n_enabled,
                    )
                )

        # Get layouts - auto-generate from field definitions if not exist
        from apps.system.services.layout_generator import LayoutGenerator
        from apps.system.validators import get_default_layout_config
        from apps.system.models import BusinessObject

        layouts = {}
        # Get BusinessObject for layout generation
        bo = BusinessObject.objects.filter(code=self._object_meta.code).first()

        if bo:
            # Auto-generate layouts using LayoutGenerator
            # This will return existing PageLayout configs or generate defaults
            layout_types = ['list', 'form', 'detail']
            for layout_type in layout_types:
                try:
                    layouts[layout_type] = LayoutGenerator.get_or_generate_layout(bo, layout_type)
                except Exception as layout_err:
                    logger.warning(
                        "metadata layout generation failed. code=%s layout_type=%s error=%s",
                        self._object_meta.code,
                        layout_type,
                        layout_err,
                    )
                    layouts[layout_type] = get_default_layout_config(layout_type)
        else:
            # Fallback to PageLayout query for backward compatibility
            try:
                layout_records = PageLayout.objects.filter(
                    business_object__code=self._object_meta.code
                )
                for layout in layout_records:
                    layouts[layout.layout_type] = layout.layout_config
            except Exception as layout_query_err:
                logger.warning(
                    "metadata layout query failed. code=%s error=%s",
                    self._object_meta.code,
                    layout_query_err,
                )

        # Ensure core layout keys always exist to avoid frontend null checks exploding.
        for layout_type in ['list', 'form', 'detail']:
            if layout_type not in layouts or not layouts.get(layout_type):
                layouts[layout_type] = get_default_layout_config(layout_type)

        # Get permissions for current user
        permissions = self._get_user_permissions(request.user, self._object_meta.code)

        object_name = self._object_meta.name
        if runtime_i18n_enabled and bo:
            object_name = self._localize_field_value(bo, 'name', request_locale, bo.name)

        return BaseResponse.success({
            'code': self._object_meta.code,
            'name': object_name,
            'is_hardcoded': self._object_meta.is_hardcoded,
            'django_model_path': self._object_meta.django_model_path,
            'enable_workflow': self._get_business_object_flag('enable_workflow'),
            'enable_version': self._get_business_object_flag('enable_version'),
            'fields': fields,
            'layouts': layouts,
            'permissions': permissions,
        })

    def _get_business_object_flag(self, flag_name: str) -> bool:
        """Get a flag value from the BusinessObject."""
        try:
            from apps.system.models import BusinessObject
            # BusinessObject uses GlobalMetadataManager (no org filtering)
            bo = BusinessObject.objects.filter(code=self._object_meta.code).first()
            if not bo:
                return False
            return getattr(bo, flag_name, False)
        except Exception:
            return False

    def _coerce_bool(self, value: Any, default: bool) -> bool:
        """Coerce config value to boolean safely."""
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {'true', '1', 'yes', 'y', 'on'}:
                return True
            if normalized in {'false', '0', 'no', 'n', 'off'}:
                return False
        return default

    def _is_feature_enabled(self, config_key: str, *, default: bool, request=None) -> bool:
        """
        Resolve feature flag from SystemConfig with org > global fallback.

        Cached per viewset instance to avoid repeated lookups.
        """
        request_obj = request or getattr(self, 'request', None)
        org_id = getattr(request_obj, 'organization_id', None)
        cache_key = (config_key, str(org_id) if org_id else 'global')
        if cache_key in self._feature_flag_cache:
            return self._feature_flag_cache[cache_key]

        resolved = default
        try:
            from apps.system.models import SystemConfig

            query = SystemConfig.objects.filter(config_key=config_key)
            config = None
            if org_id:
                config = query.filter(organization_id=org_id).order_by('-updated_at', '-created_at').first()
            if not config:
                config = query.filter(organization__isnull=True).order_by('-updated_at', '-created_at').first()
            if config:
                resolved = self._coerce_bool(config.get_typed_value(), default)
        except Exception:
            resolved = default

        self._feature_flag_cache[cache_key] = resolved
        return resolved

    def _build_field_identifier_payload(self, field_code: str, *, force_strict: bool = False) -> dict:
        """
        Build field identity payload with strict/compat mode.

        strict: only field_code
        compat: field_code + legacy code
        """
        strict_mode = force_strict or self._is_feature_enabled(
            'field_code_strict_mode',
            default=False,
        )
        payload = {'field_code': field_code}
        if not strict_mode:
            payload['code'] = field_code
            if not self._legacy_field_code_warned:
                logger.info(
                    "Legacy `code` key is still emitted for compatibility. "
                    "Enable field_code_strict_mode to return field_code only."
                )
                self._legacy_field_code_warned = True
        return payload

    def _get_user_permissions(self, user, object_code: str) -> dict:
        """
        Get user permissions for this object.

        Args:
            user: Current user
            object_code: Business object code

        Returns:
            Dictionary of permission flags
        """
        # Build permission codes
        permissions = {
            'view': self._check_user_permission(user, object_code, 'view'),
            'add': self._check_user_permission(user, object_code, 'add'),
            'change': self._check_user_permission(user, object_code, 'change'),
            'delete': self._check_user_permission(user, object_code, 'delete'),
        }

        return permissions

    def _check_user_permission(self, user, object_code: str, action: str) -> bool:
        """
        Check if user has permission for an action on an object.

        Args:
            user: User instance
            object_code: Business object code
            action: Action name (view, add, change, delete)

        Returns:
            True if user has permission, False otherwise
        """
        if user.is_superuser:
            return True

        perm_code = f"{object_code.lower()}_{action}"
        return user.has_perm(perm_code)

    def _get_request_locale(self, request) -> str:
        """Resolve locale with runtime-safe priority: query > header > profile > context/default."""

        def _normalize_locale(raw_locale: Any) -> str:
            if not raw_locale:
                return ''
            locale = str(raw_locale).strip()
            if not locale:
                return ''
            if locale in TranslationService.SUPPORTED_LANGUAGES:
                return locale

            lowered = locale.lower().replace('_', '-')
            if lowered.startswith('zh'):
                return 'zh-CN'
            if lowered.startswith('en'):
                return 'en-US'
            if lowered.startswith('ja'):
                return 'ja-JP'
            return ''

        def _parse_accept_language(raw_header: str) -> List[str]:
            if not raw_header:
                return []
            candidates: List[tuple[str, float]] = []
            for chunk in raw_header.split(','):
                part = chunk.strip()
                if not part:
                    continue
                lang = part
                quality = 1.0
                if ';' in part:
                    pieces = [p.strip() for p in part.split(';') if p.strip()]
                    lang = pieces[0]
                    for piece in pieces[1:]:
                        if piece.startswith('q='):
                            try:
                                quality = float(piece.split('=', 1)[1])
                            except (ValueError, TypeError):
                                quality = 0.0
                            break
                candidates.append((lang, quality))
            candidates.sort(key=lambda item: item[1], reverse=True)
            return [lang for lang, _ in candidates]

        query_locale = request.query_params.get('locale') or request.query_params.get('lang')
        normalized_query_locale = _normalize_locale(query_locale)
        if normalized_query_locale:
            return normalized_query_locale

        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        for candidate in _parse_accept_language(accept_language):
            normalized_header_locale = _normalize_locale(candidate)
            if normalized_header_locale:
                return normalized_header_locale

        user = getattr(request, 'user', None)
        preferred_language = getattr(user, 'preferred_language', None) if user and user.is_authenticated else None
        normalized_preferred_language = _normalize_locale(preferred_language)
        if normalized_preferred_language:
            return normalized_preferred_language

        context_locale = (
            getattr(request, 'language_code', None)
            or getattr(request, 'locale', None)
            or get_current_language()
        )
        normalized_context_locale = _normalize_locale(context_locale)
        if normalized_context_locale:
            return normalized_context_locale
        return TranslationService.DEFAULT_LANGUAGE

    def _localize_field_value(self, obj, field_name: str, locale: str, default_value: Any = '') -> Any:
        """Localize a model field via TranslationService with safe fallback."""
        try:
            value = TranslationService.get_localized_value(
                obj,
                field_name,
                lang_code=locale,
                fallback_to_original=True,
            )
            if value not in (None, ''):
                return value
        except Exception:
            pass
        return default_value

    def _pick_locale_text(self, localized_map: Any, locale: str) -> str:
        """Pick a localized text from a locale map."""
        if not isinstance(localized_map, dict):
            return ''
        if locale in localized_map and localized_map.get(locale):
            return str(localized_map.get(locale))
        short_locale = locale.split('-', 1)[0]
        if short_locale in localized_map and localized_map.get(short_locale):
            return str(localized_map.get(short_locale))
        if 'zh-CN' in localized_map and localized_map.get('zh-CN'):
            return str(localized_map.get('zh-CN'))
        if 'en-US' in localized_map and localized_map.get('en-US'):
            return str(localized_map.get('en-US'))
        for _, value in localized_map.items():
            if value:
                return str(value)
        return ''

    def _localize_options(self, options: Any, locale: str) -> Any:
        """Localize option labels while preserving original option structure."""
        if not options:
            return options

        if isinstance(options, list):
            localized_options = []
            for option in options:
                if not isinstance(option, dict):
                    localized_options.append(option)
                    continue

                normalized_option = dict(option)
                localized_label = self._pick_locale_text(normalized_option.get('label_i18n'), locale)
                if not localized_label and locale.startswith('en') and normalized_option.get('label_en'):
                    localized_label = str(normalized_option.get('label_en'))
                if localized_label:
                    normalized_option['label'] = localized_label
                localized_options.append(normalized_option)
            return localized_options

        if isinstance(options, dict):
            # For dict-style options, value is usually the visible label.
            # Keep shape intact and localize only map values when they are locale maps.
            localized_options = {}
            for key, value in options.items():
                if isinstance(value, dict):
                    localized_text = self._pick_locale_text(value, locale)
                    localized_options[key] = localized_text or value
                else:
                    localized_options[key] = value
            return localized_options

        return options

    @action(detail=False, methods=['post'], url_path='batch-delete')
    def batch_delete(self, request, *args, **kwargs):
        """
        Batch delete objects.

        POST /api/objects/{code}/batch-delete/

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }
        """
        return self._delegate_viewset.batch_delete(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='batch-restore')
    def batch_restore(self, request, *args, **kwargs):
        """
        Batch restore soft-deleted objects.

        POST /api/objects/{code}/batch-restore/
        """
        return self._delegate_viewset.batch_restore(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='batch-update')
    def batch_update(self, request, *args, **kwargs):
        """
        Batch update objects.

        POST /api/objects/{code}/batch-update/
        """
        return self._delegate_viewset.batch_update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='deleted')
    def deleted(self, request, *args, **kwargs):
        """
        List soft-deleted objects.

        GET /api/objects/{code}/deleted/
        """
        return self._delegate_viewset.deleted(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='restore')
    def restore(self, request, *args, **kwargs):
        """
        Restore a soft-deleted object.

        POST /api/objects/{code}/{id}/restore/
        """
        # Map 'id' to 'pk' for DRF ViewSet compatibility
        if 'id' in kwargs:
            self._delegate_viewset.kwargs = {
                **self._delegate_viewset.kwargs,
                'pk': kwargs['id']
            }
        return self._delegate_viewset.restore(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='fields')
    def fields(self, request, *args, **kwargs):
        """
        Get field definitions with context-aware filtering.

        GET /api/objects/{code}/fields/?context={context}&include_relations={true|false}

        Query Parameters:
            context: Rendering context - 'form' | 'detail' | 'list' (default: 'form')
            include_relations: Include reverse relations - 'true' | 'false' (default: 'false')

        Response structure:
        {
            "success": true,
            "data": {
                "editable_fields": [...],
                "reverse_relations": [...]
            }
        }
        """
        # Initialize object_meta if not already done
        if not self._object_meta:
            object_code = kwargs.get('code')
            if not object_code:
                return BaseResponse.error('VALIDATION_ERROR', 'object_code is required', http_status=status.HTTP_400_BAD_REQUEST)

            self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
            if not self._object_meta:
                return BaseResponse.not_found(f"Business object '{object_code}' not found")

        # Get query parameters
        context = request.query_params.get('context', 'form')
        include_relations = request.query_params.get('include_relations', 'false').lower() == 'true'
        request_locale = self._get_request_locale(request)
        runtime_i18n_enabled = self._is_feature_enabled(
            'runtime_i18n_enabled',
            default=True,
            request=request,
        )

        # Validate context parameter
        valid_contexts = ['form', 'detail', 'list']
        if context not in valid_contexts:
            return BaseResponse.error(
                'VALIDATION_ERROR',
                f'Invalid context. Must be one of: {", ".join(valid_contexts)}',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        from apps.system.models import FieldDefinition, ModelFieldDefinition

        editable_fields = []
        reverse_relations = []

        if self._object_meta.is_hardcoded:
            # For hardcoded objects, get fields from ModelFieldDefinition
            model_fields = ModelFieldDefinition.objects.filter(
                business_object__code=self._object_meta.code
            ).order_by('sort_order')

            for fd in model_fields:
                field_data = self._format_model_field(
                    fd,
                    context,
                    request_locale,
                    localize=runtime_i18n_enabled,
                )
                # Check if this is a reverse relation (sub_table type)
                if fd.field_type == 'sub_table':
                    if include_relations:
                        reverse_relations.append(field_data)
                else:
                    # Apply context filtering
                    if self._should_show_field(fd, context, is_model_field=True):
                        editable_fields.append(field_data)
        else:
            # For dynamic objects, get fields from FieldDefinition
            fields_query = FieldDefinition.objects.filter(
                business_object__code=self._object_meta.code
            ).order_by('sort_order')

            for fd in fields_query:
                field_data = self._format_field_definition(
                    fd,
                    context,
                    request_locale,
                    localize=runtime_i18n_enabled,
                )

                # Check if this is a reverse relation
                if fd.is_reverse_relation:
                    if include_relations:
                        reverse_relations.append(field_data)
                else:
                    # Apply context filtering
                    if self._should_show_field(fd, context, is_model_field=False):
                        editable_fields.append(field_data)

        # Safety fallback: if detail view ends up with zero fields, show all non-relation fields.
        # This prevents blank detail pages when show_in_detail is misconfigured across the board.
        if context == 'detail' and not editable_fields:
            if self._object_meta.is_hardcoded:
                for fd in model_fields:
                    if fd.field_type == 'sub_table':
                        continue
                    editable_fields.append(
                        self._format_model_field(
                            fd,
                            context,
                            request_locale,
                            localize=runtime_i18n_enabled,
                        )
                    )
            else:
                for fd in fields_query:
                    if fd.is_reverse_relation:
                        continue
                    editable_fields.append(
                        self._format_field_definition(
                            fd,
                            context,
                            request_locale,
                            localize=runtime_i18n_enabled,
                        )
                    )

        return BaseResponse.success({
            'editable_fields': editable_fields,
            'reverse_relations': reverse_relations,
            'context': context,
            'locale': request_locale,
        })

    @action(detail=False, methods=['get'], url_path='runtime')
    def runtime(self, request, *args, **kwargs):
        """
        Get runtime metadata (fields + active layout) for frontend rendering.

        GET /api/system/objects/{code}/runtime/?mode={edit|readonly|list|search}&include_relations={true|false}

        This endpoint is intentionally "frontend-friendly":
        - One request returns everything needed to render a page (fields + layout).
        - It mirrors the selection rules used by `page-layouts/get_active_layout`.
        - It mirrors the context filtering rules used by `objects/{code}/fields`.
        """
        if not self._object_meta:
            object_code = kwargs.get('code')
            if not object_code:
                return BaseResponse.error('VALIDATION_ERROR', 'object_code is required', http_status=status.HTTP_400_BAD_REQUEST)

            self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
            if not self._object_meta:
                return BaseResponse.not_found(f"Business object '{object_code}' not found")

        mode = request.query_params.get('mode', 'edit')
        include_relations = request.query_params.get('include_relations', 'true').lower() == 'true'
        request_locale = self._get_request_locale(request)
        runtime_i18n_enabled = self._is_feature_enabled(
            'runtime_i18n_enabled',
            default=True,
            request=request,
        )
        layout_merge_unified_enabled = self._is_feature_enabled(
            'layout_merge_unified_enabled',
            default=True,
            request=request,
        )

        # Single-layout model:
        # - readonly/detail/search pages reuse edit/form field model for consistency.
        # - only list uses list context.
        if mode in ['list']:
            context = 'list'
        else:
            context = 'form'

        # Build fields payload (same logic as `fields()`).
        # Duplicated here to keep `runtime` independent from action dispatch plumbing.
        from apps.system.models import FieldDefinition, ModelFieldDefinition, BusinessObject, PageLayout
        from apps.system.serializers import PageLayoutSerializer

        editable_fields = []
        reverse_relations = []

        if self._object_meta.is_hardcoded:
            model_fields = ModelFieldDefinition.objects.filter(
                business_object__code=self._object_meta.code
            ).order_by('sort_order')

            for fd in model_fields:
                field_data = self._format_model_field(
                    fd,
                    context,
                    request_locale,
                    localize=runtime_i18n_enabled,
                    strict_identifier=True,
                )
                if fd.field_type == 'sub_table':
                    if include_relations:
                        reverse_relations.append(field_data)
                else:
                    if self._should_show_field(fd, context, is_model_field=True):
                        editable_fields.append(field_data)
        else:
            fields_query = FieldDefinition.objects.filter(
                business_object__code=self._object_meta.code
            ).order_by('sort_order')

            for fd in fields_query:
                field_data = self._format_field_definition(
                    fd,
                    context,
                    request_locale,
                    localize=runtime_i18n_enabled,
                    strict_identifier=True,
                )
                if fd.is_reverse_relation:
                    if include_relations:
                        reverse_relations.append(field_data)
                else:
                    if self._should_show_field(fd, context, is_model_field=False):
                        editable_fields.append(field_data)

        # Safety fallback: if form/detail-equivalent view ends up with zero fields,
        # show all non-relation fields to avoid blank pages.
        if context in ['form', 'detail'] and not editable_fields:
            if self._object_meta.is_hardcoded:
                for fd in model_fields:
                    if fd.field_type == 'sub_table':
                        continue
                    editable_fields.append(
                        self._format_model_field(
                            fd,
                            context,
                            request_locale,
                            localize=runtime_i18n_enabled,
                            strict_identifier=True,
                        )
                    )
            else:
                for fd in fields_query:
                    if fd.is_reverse_relation:
                        continue
                    editable_fields.append(
                        self._format_field_definition(
                            fd,
                            context,
                            request_locale,
                            localize=runtime_i18n_enabled,
                            strict_identifier=True,
                        )
                    )

        # Resolve active layout (custom > default > generated config).
        # Single-layout model: readonly/detail/search reuses shared form layout.
        layout_type = mode
        if mode in ['edit', 'form', 'readonly', 'detail', 'search']:
            layout_type = 'form'

        business_object = BusinessObject.objects.filter(code=self._object_meta.code).first()
        if not business_object:
            return BaseResponse.not_found(f"Business object '{self._object_meta.code}' not found")

        # List runtime uses a shared column model derived from field metadata,
        # with optional user column-preference overrides.
        if mode == 'list':
            from apps.system.services.column_config_service import ColumnConfigService
            from apps.system.services.layout_generator import LayoutGenerator

            generated = LayoutGenerator.generate_list_layout(business_object) or {}
            user_column_config = {}
            try:
                if request.user and request.user.is_authenticated:
                    user_column_config = ColumnConfigService.get_column_config(request.user, self._object_meta.code) or {}
            except Exception:
                user_column_config = {}

            columns = user_column_config.get('columns')
            if not isinstance(columns, list) or not columns:
                columns = generated.get('columns') if isinstance(generated.get('columns'), list) else []

            layout_payload = {
                'layout_type': 'list',
                'layout_config': {
                    'columns': columns,
                    'columnOrder': user_column_config.get('columnOrder') if isinstance(user_column_config.get('columnOrder'), list) else [],
                    'rowSelection': bool(generated.get('rowSelection', True)),
                    'pagination': bool(generated.get('pagination', True)),
                    'pageSize': int(generated.get('pageSize', 20)),
                },
                'is_template': True,
                'source': user_column_config.get('source', 'default'),
            }
            layout_source = user_column_config.get('source', 'default')
            if layout_merge_unified_enabled:
                layout_layers = ['user', 'default'] if layout_source == 'user' else ['default']
            else:
                layout_layers = ['default']
            return BaseResponse.success({
                'runtime_version': 1,
                'object_code': self._object_meta.code,
                'mode': mode,
                'context': context,
                'locale': request_locale,
                'layout_source': layout_source,
                'layout_layers': layout_layers,
                'layout_id': layout_payload.get('id'),
                'permissions': self._get_user_permissions(request.user, self._object_meta.code),
                'fields': {
                    'editable_fields': editable_fields,
                    'reverse_relations': reverse_relations,
                    'context': context,
                    'locale': request_locale,
                },
                'layout': layout_payload,
                'is_default': user_column_config.get('source', 'default') != 'user',
            })

        org_id = getattr(request, 'organization_id', None)
        base_filters = {
            'business_object': business_object,
            'layout_type': layout_type,
            'is_active': True
        }

        base_qs = PageLayout.objects.filter(**base_filters, is_deleted=False)

        def _scope_custom(qs):
            if org_id:
                return qs.filter(organization_id=org_id)
            return qs

        def _scope_default(qs):
            if org_id:
                return qs.filter(Q(organization_id=org_id) | Q(organization__isnull=True))
            return qs

        # Runtime pages should prefer published layouts first.
        # Draft layouts are fallback only when nothing published exists.
        layout_source = 'default'
        layout = None
        layout_candidates = [
            ('org', _scope_custom(base_qs.filter(is_default=False, status='published'))),
            ('default', _scope_default(base_qs.filter(is_default=True, status='published'))),
            ('org', _scope_custom(base_qs.filter(is_default=False))),
            ('default', _scope_default(base_qs.filter(is_default=True))),
        ]
        for candidate_source, candidate_qs in layout_candidates:
            layout = candidate_qs.order_by('-updated_at', '-created_at').first()
            if layout:
                layout_source = candidate_source
                if candidate_source == 'org' and getattr(layout, 'organization_id', None) is None:
                    layout_source = 'global'
                break

        if layout:
            layout_payload = PageLayoutSerializer(layout).data
            raw_layout_config = layout_payload.get('layout_config')
            if layout_merge_unified_enabled and isinstance(raw_layout_config, dict):
                normalized_layout_config = normalize_layout_config_for_runtime(
                    business_object,
                    raw_layout_config
                )
                layout_payload['layout_config'] = normalized_layout_config
                if 'layoutConfig' in layout_payload:
                    layout_payload['layoutConfig'] = normalized_layout_config
            is_default = bool(layout.is_default)
        else:
            from apps.system.services.layout_generator import LayoutGenerator
            from apps.system.validators import get_default_layout_config

            if layout_type in ['form', 'list']:
                layout_config = LayoutGenerator.get_or_generate_layout(business_object, layout_type)
            else:
                layout_config = get_default_layout_config(layout_type)
            if layout_merge_unified_enabled:
                layout_config = normalize_layout_config_for_runtime(business_object, layout_config)

            layout_payload = {
                'layout_type': layout_type,
                'layout_config': layout_config,
                'is_template': True
            }
            is_default = True
            layout_source = 'default'

        if layout_merge_unified_enabled:
            layout_layers = ['user', 'role', 'org', 'global', 'default']
        else:
            layout_layers = ['default']

        return BaseResponse.success({
            'runtime_version': 1,
            'object_code': self._object_meta.code,
            'mode': mode,
            'context': context,
            'locale': request_locale,
            'layout_source': layout_source,
            'layout_layers': layout_layers,
            'layout_id': layout_payload.get('id') if isinstance(layout_payload, dict) else None,
            'permissions': self._get_user_permissions(request.user, self._object_meta.code),
            'fields': {
                'editable_fields': editable_fields,
                'reverse_relations': reverse_relations,
                'context': context,
                'locale': request_locale,
            },
            'layout': layout_payload,
            'is_default': is_default,
        })

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request, *args, **kwargs):
        """
        Current user endpoint under the unified object router.

        GET /api/system/objects/User/me/

        This exists to eliminate frontend dependencies on legacy `/api/auth/users/me/`.
        """
        if not request.user or not request.user.is_authenticated:
            return BaseResponse.unauthorized()

        object_code = (kwargs.get('code') or '').strip()
        if not object_code and self._object_meta:
            object_code = self._object_meta.code
        if not object_code:
            return BaseResponse.error('VALIDATION_ERROR', 'object_code is required', http_status=status.HTTP_400_BAD_REQUEST)
        if object_code != 'User':
            return BaseResponse.not_found(f"Endpoint only exists for 'User' (got '{object_code}')")

        from apps.accounts.serializers import UserDetailSerializer
        serializer = UserDetailSerializer(request.user)
        return BaseResponse.success(serializer.data)

    def me_profile(self, request, *args, **kwargs):
        """
        Update current user's profile under the unified object router.

        PUT/PATCH /api/system/objects/User/me/profile/
        """
        if not request.user or not request.user.is_authenticated:
            return BaseResponse.unauthorized()

        object_code = (kwargs.get('code') or '').strip()
        if not object_code and self._object_meta:
            object_code = self._object_meta.code
        if not object_code:
            return BaseResponse.error('VALIDATION_ERROR', 'object_code is required', http_status=status.HTTP_400_BAD_REQUEST)
        if object_code != 'User':
            return BaseResponse.not_found(f"Endpoint only exists for 'User' (got '{object_code}')")

        from apps.accounts.serializers import UserUpdateSerializer, UserDetailSerializer

        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        out = UserDetailSerializer(request.user).data
        return BaseResponse.success(out, message='Profile updated successfully.')

    @action(detail=False, methods=['post'], url_path='me/change-password')
    def me_change_password(self, request, *args, **kwargs):
        """
        Change current user's password under the unified object router.

        POST /api/system/objects/User/me/change-password/
        Body: { oldPassword, newPassword } (camelCase accepted by parser)
        """
        if not request.user or not request.user.is_authenticated:
            return BaseResponse.unauthorized()

        object_code = (kwargs.get('code') or '').strip()
        if not object_code and self._object_meta:
            object_code = self._object_meta.code
        if not object_code:
            return BaseResponse.error('VALIDATION_ERROR', 'object_code is required', http_status=status.HTTP_400_BAD_REQUEST)
        if object_code != 'User':
            return BaseResponse.not_found(f"Endpoint only exists for 'User' (got '{object_code}')")

        from django.contrib.auth.hashers import make_password
        from apps.accounts.serializers import ChangePasswordSerializer

        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        request.user.password = make_password(serializer.validated_data['new_password'])
        request.user.save()
        return BaseResponse.success(message='Password changed successfully.')

    def _should_show_field(self, field, context: str, is_model_field: bool = False) -> bool:
        """
        Determine if a field should be shown in the given context.

        Args:
            field: FieldDefinition or ModelFieldDefinition instance
            context: 'form', 'detail', or 'list'
            is_model_field: True if field is ModelFieldDefinition

        Returns:
            True if field should be shown in this context
        """
        if is_model_field:
            # ModelFieldDefinition has show_in_form, show_in_detail, show_in_list
            if context == 'form':
                # Check if reverse relation (sub_table) - don't show in editable fields
                if field.field_type == 'sub_table':
                    return False
                return getattr(field, 'show_in_form', True)
            elif context == 'detail':
                if field.field_type == 'sub_table':
                    return False
                return getattr(field, 'show_in_detail', True)
            elif context == 'list':
                if field.field_type == 'sub_table':
                    return False
                return getattr(field, 'show_in_list', False)
        else:
            # FieldDefinition has show_in_form, show_in_detail, show_in_list
            if context == 'form':
                if field.is_reverse_relation:
                    return False
                return getattr(field, 'show_in_form', True)
            elif context == 'detail':
                if field.is_reverse_relation:
                    return False
                return getattr(field, 'show_in_detail', True)
            elif context == 'list':
                if field.is_reverse_relation:
                    return False
                return getattr(field, 'show_in_list', False)

        return True

    @classmethod
    def _is_builtin_system_field_code(cls, code: str) -> bool:
        normalized = str(code or '').strip().lower()
        if not normalized:
            return False
        if normalized in cls._IMMUTABLE_SYSTEM_FIELD_CODES:
            return True
        # camelCase compatibility
        if normalized in {'createdat', 'createdby', 'createdbyid', 'updatedat', 'updatedby', 'updatedbyid', 'deletedat', 'deletedby', 'deletedbyid'}:
            return True
        return False

    def _format_field_definition(
        self,
        fd,
        context: str,
        locale: Optional[str] = None,
        *,
        localize: bool = True,
        strict_identifier: bool = False,
    ) -> dict:
        """Format FieldDefinition instance for API response."""
        resolved_locale = locale or TranslationService.DEFAULT_LANGUAGE
        if localize:
            localized_name = self._localize_field_value(fd, 'name', resolved_locale, fd.name)
            localized_placeholder = self._localize_field_value(fd, 'placeholder', resolved_locale, fd.placeholder)
            localized_options = self._localize_options(fd.options, resolved_locale)
        else:
            localized_name = fd.name
            localized_placeholder = fd.placeholder
            localized_options = fd.options

        return {
            **self._build_field_identifier_payload(fd.code, force_strict=strict_identifier),
            'name': localized_name,
            'label': localized_name,
            'field_type': fd.field_type,
            'is_required': fd.is_required,
            'is_readonly': fd.is_readonly,
            'is_system': fd.is_system,
            'is_searchable': fd.is_searchable,
            'sortable': fd.sortable,
            'show_in_filter': fd.show_in_filter,
            'show_in_list': fd.show_in_list,
            'show_in_detail': fd.show_in_detail,
            'show_in_form': getattr(fd, 'show_in_form', True),
            'sort_order': fd.sort_order,
            'column_width': fd.column_width,
            'min_column_width': fd.min_column_width,
            'fixed': fd.fixed,
            'options': localized_options,
            'placeholder': localized_placeholder,
            'default_value': fd.default_value,
            'reference_object': fd.reference_object,
            # Reverse relation fields
            'is_reverse_relation': getattr(fd, 'is_reverse_relation', False),
            'reverse_relation_model': getattr(fd, 'reverse_relation_model', ''),
            'reverse_relation_field': getattr(fd, 'reverse_relation_field', ''),
            'relation_display_mode': getattr(fd, 'relation_display_mode', 'tab_readonly'),
            'locale': resolved_locale,
        }

    def _format_model_field(
        self,
        fd,
        context: str,
        locale: Optional[str] = None,
        *,
        localize: bool = True,
        strict_identifier: bool = False,
    ) -> dict:
        """Format ModelFieldDefinition instance for API response."""
        resolved_locale = locale or TranslationService.DEFAULT_LANGUAGE
        # Try to get field choices from the actual Django model
        options = self._get_model_field_choices(fd)
        if localize:
            options = self._localize_options(options, resolved_locale)

        # Determine field type - if has choices, it should be rendered as select
        field_type = fd.field_type
        if options and field_type == 'text':
            field_type = 'select'
        if localize:
            localized_display_name = self._localize_field_value(
                fd,
                'display_name',
                resolved_locale,
                fd.display_name or fd.field_name,
            )
            if resolved_locale.startswith('en') and getattr(fd, 'display_name_en', None):
                localized_display_name = fd.display_name_en
        else:
            localized_display_name = fd.display_name or fd.field_name

        is_system_field = bool(
            not getattr(fd, 'is_editable', True)
            or self._is_builtin_system_field_code(getattr(fd, 'field_name', ''))
        )

        return {
            **self._build_field_identifier_payload(fd.field_name, force_strict=strict_identifier),
            'name': localized_display_name,
            'label': localized_display_name,
            'field_type': field_type,
            'is_required': fd.is_required,
            'is_readonly': fd.is_readonly,
            'is_system': is_system_field,
            'is_searchable': True,
            'sortable': True,
            'show_in_filter': False,
            'show_in_list': fd.show_in_list,
            'show_in_detail': fd.show_in_detail,
            'show_in_form': getattr(fd, 'show_in_form', True),
            'sort_order': fd.sort_order,
            'column_width': None,
            'min_column_width': None,
            'fixed': False,
            'options': options,  # Now includes choices from Django model
            'placeholder': None,
            'default_value': None,
            'reference_object': fd.reference_model_path if fd.field_type == 'reference' else None,
            # Reverse relation fields
            'is_reverse_relation': fd.field_type == 'sub_table',
            'reverse_relation_model': '',
            'reverse_relation_field': '',
            'relation_display_mode': 'tab_readonly',
            'locale': resolved_locale,
        }

    def _get_model_field_choices(self, fd) -> list:
        """
        Extract field choices from Django model for select-type fields.
        
        Args:
            fd: ModelFieldDefinition instance
            
        Returns:
            List of options in format [{'value': 'v', 'label': 'Label'}, ...]
        """
        try:
            # Get the actual Django model class
            model_class = self._object_meta.get_django_model() if hasattr(self._object_meta, 'get_django_model') else None
            if not model_class:
                # Fallback: try to get model from BusinessObject
                from apps.system.models import BusinessObject
                bo = BusinessObject.objects.filter(code=self._object_meta.code).first()
                if bo and bo.django_model_path:
                    from django.utils.module_loading import import_string
                    model_class = import_string(bo.django_model_path)
            
            if not model_class:
                return None
                
            # Get the field from the model
            try:
                field = model_class._meta.get_field(fd.field_name)
            except Exception:
                return None
            
            # Check if field has choices
            if hasattr(field, 'choices') and field.choices:
                choices = field.choices
                # Handle both tuple and list formats
                # Format: [(value, label), ...] or [('value', 'Label'), ...]
                if isinstance(choices, (list, tuple)) and len(choices) > 0:
                    return [
                        {'value': choice[0], 'label': str(choice[1])}
                        for choice in choices
                    ]
            
            return None
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logging.getLogger(__name__).warning(f"Failed to get choices for field {fd.field_name}: {e}")
            return None

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request, *args, **kwargs):
        """
        Get JSON Schema for the business object.

        GET /api/objects/{code}/schema/

        Returns a JSON Schema suitable for frontend form validation.
        """
        # Initialize object_meta if not already done
        if not self._object_meta:
            object_code = kwargs.get('code')
            if not object_code:
                return BaseResponse.error('VALIDATION_ERROR', 'object_code is required', http_status=status.HTTP_400_BAD_REQUEST)

            self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
            if not self._object_meta:
                return BaseResponse.not_found(f"Business object '{object_code}' not found")

        from apps.system.models import FieldDefinition

        fields = FieldDefinition.objects.filter(
            business_object__code=self._object_meta.code,
            is_deleted=False
        )

        properties = {}
        required = []

        type_mapping = {
            'text': 'string',
            'textarea': 'string',
            'number': 'number',
            'currency': 'number',
            'percent': 'number',
            'integer': 'integer',
            'float': 'number',
            'boolean': 'boolean',
            'date': 'string',
            'datetime': 'string',
            'email': 'string',
            'url': 'string',
            'select': 'string',
            'multi_select': 'array',
            'radio': 'string',
            'checkbox': 'boolean',
            'user': 'string',
            'department': 'string',
            'reference': 'string',
            'asset': 'string',
            'formula': 'number',
            'file': 'string',
            'image': 'string',
            'qr_code': 'string',
            'barcode': 'string',
            'location': 'object',
            'json': 'object',
        }

        for fd in fields:
            prop = {
                'type': type_mapping.get(fd.field_type, 'string'),
                'title': fd.name,
            }

            if fd.description:
                prop['description'] = fd.description

            if fd.max_length:
                prop['maxLength'] = fd.max_length

            if fd.min_value is not None:
                prop['minimum'] = float(fd.min_value)

            if fd.max_value is not None:
                prop['maximum'] = float(fd.max_value)

            if fd.field_type in ['select', 'multi_select'] and fd.options:
                if isinstance(fd.options, dict):
                    prop['enum'] = list(fd.options.keys())
                elif isinstance(fd.options, list):
                    prop['enum'] = fd.options

            if fd.field_type == 'multi_select':
                prop['items'] = {'type': 'string'}
                if 'enum' in prop:
                    prop['items']['enum'] = prop.pop('enum')

            properties[fd.code] = prop

            if fd.is_required:
                required.append(fd.code)

        return BaseResponse.success({
            'type': 'object',
            'properties': properties,
            'required': required,
        })
