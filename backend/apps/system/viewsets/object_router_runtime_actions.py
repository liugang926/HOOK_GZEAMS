from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action

from apps.common.responses.base import BaseResponse
from apps.system.services.layout_runtime_normalizer import normalize_layout_config_for_runtime
from apps.system.services.object_registry import ObjectRegistry
from apps.system.services.relation_query_service import RelationQueryService


class ObjectRouterRuntimeActionsMixin:
    _VALID_FIELD_CONTEXTS = ('form', 'detail', 'list')
    _FORM_LAYOUT_RUNTIME_MODES = {'edit', 'form', 'readonly', 'detail', 'search'}

    def _ensure_object_meta_loaded(self, kwargs):
        if self._object_meta:
            return None

        object_code = kwargs.get('code')
        if not object_code:
            return BaseResponse.error(
                'VALIDATION_ERROR',
                'object_code is required',
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
        if not self._object_meta:
            return BaseResponse.not_found(f"Business object '{object_code}' not found")

        return None

    def _resolve_runtime_context(self, mode: str) -> str:
        return 'list' if mode == 'list' else 'form'

    def _resolve_runtime_layout_type(self, mode: str) -> str:
        return 'form' if mode in self._FORM_LAYOUT_RUNTIME_MODES else mode

    def _get_workbench_config_value(self, payload: dict, *keys, default=None):
        if not isinstance(payload, dict):
            return default
        for key in keys:
            if key in payload and payload[key] is not None:
                return payload[key]
        return default

    def _normalize_workbench_aliases(self, value) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    def _extract_layout_workbench(self, layout_bundle: dict) -> dict:
        if not isinstance(layout_bundle, dict):
            return {}

        layout_payload = layout_bundle.get('layout')
        if not isinstance(layout_payload, dict):
            return {}

        layout_config = layout_payload.get('layout_config') or layout_payload.get('layoutConfig')
        if isinstance(layout_config, dict):
            workbench = layout_config.get('workbench')
            if isinstance(workbench, dict):
                return workbench

        workbench = layout_payload.get('workbench')
        if isinstance(workbench, dict):
            return workbench

        return {}

    def _apply_workbench_overrides(self, target: dict, source: dict):
        if not isinstance(source, dict):
            return target

        workspace_mode = self._get_workbench_config_value(
            source,
            'workspace_mode',
            'workspaceMode',
        )
        if workspace_mode:
            target['workspace_mode'] = str(workspace_mode)

        primary_entry_route = self._get_workbench_config_value(
            source,
            'primary_entry_route',
            'primaryEntryRoute',
        )
        if primary_entry_route:
            target['primary_entry_route'] = str(primary_entry_route)

        legacy_aliases = self._get_workbench_config_value(
            source,
            'legacy_aliases',
            'legacyAliases',
        )
        if isinstance(legacy_aliases, list):
            target['legacy_aliases'] = self._normalize_workbench_aliases(legacy_aliases)

        default_page_mode = self._get_workbench_config_value(
            source,
            'default_page_mode',
            'defaultPageMode',
        )
        if default_page_mode:
            target['default_page_mode'] = str(default_page_mode)

        default_detail_surface_tab = self._get_workbench_config_value(
            source,
            'default_detail_surface_tab',
            'defaultDetailSurfaceTab',
        )
        if default_detail_surface_tab:
            target['default_detail_surface_tab'] = str(default_detail_surface_tab)

        default_document_surface_tab = self._get_workbench_config_value(
            source,
            'default_document_surface_tab',
            'defaultDocumentSurfaceTab',
        )
        if default_document_surface_tab:
            target['default_document_surface_tab'] = str(default_document_surface_tab)

        detail_panels = self._get_workbench_config_value(
            source,
            'detail_panels',
            'detailPanels',
        )
        if isinstance(detail_panels, list):
            target['detail_panels'] = list(detail_panels)

        async_indicators = self._get_workbench_config_value(
            source,
            'async_indicators',
            'asyncIndicators',
        )
        if isinstance(async_indicators, list):
            target['async_indicators'] = list(async_indicators)

        summary_cards = self._get_workbench_config_value(
            source,
            'summary_cards',
            'summaryCards',
        )
        if isinstance(summary_cards, list):
            target['summary_cards'] = list(summary_cards)

        queue_panels = self._get_workbench_config_value(
            source,
            'queue_panels',
            'queuePanels',
        )
        if isinstance(queue_panels, list):
            target['queue_panels'] = list(queue_panels)

        exception_panels = self._get_workbench_config_value(
            source,
            'exception_panels',
            'exceptionPanels',
        )
        if isinstance(exception_panels, list):
            target['exception_panels'] = list(exception_panels)

        closure_panel = self._get_workbench_config_value(
            source,
            'closure_panel',
            'closurePanel',
        )
        if isinstance(closure_panel, dict):
            target['closure_panel'] = dict(closure_panel)

        sla_indicators = self._get_workbench_config_value(
            source,
            'sla_indicators',
            'slaIndicators',
        )
        if isinstance(sla_indicators, list):
            target['sla_indicators'] = list(sla_indicators)

        recommended_actions = self._get_workbench_config_value(
            source,
            'recommended_actions',
            'recommendedActions',
        )
        if isinstance(recommended_actions, list):
            target['recommended_actions'] = list(recommended_actions)

        document_summary_sections = self._get_workbench_config_value(
            source,
            'document_summary_sections',
            'documentSummarySections',
        )
        if isinstance(document_summary_sections, list):
            target['document_summary_sections'] = list(document_summary_sections)

        toolbar = self._get_workbench_config_value(source, 'toolbar')
        if isinstance(toolbar, dict):
            primary_actions = self._get_workbench_config_value(
                toolbar,
                'primary_actions',
                'primaryActions',
            )
            if isinstance(primary_actions, list):
                target['toolbar']['primary_actions'] = list(primary_actions)

            secondary_actions = self._get_workbench_config_value(
                toolbar,
                'secondary_actions',
                'secondaryActions',
            )
            if isinstance(secondary_actions, list):
                target['toolbar']['secondary_actions'] = list(secondary_actions)

        return target

    def _build_runtime_workbench_payload(self, *, business_object, layout_bundle: dict) -> dict:
        object_code = str(getattr(self._object_meta, 'code', '') or getattr(business_object, 'code', '')).strip()
        menu_config = getattr(business_object, 'menu_config', {}) if business_object else {}
        if not isinstance(menu_config, dict):
            menu_config = {}

        menu_workbench = menu_config.get('workbench') if isinstance(menu_config.get('workbench'), dict) else {}
        layout_workbench = self._extract_layout_workbench(layout_bundle)

        payload = {
            'workspace_mode': 'standard',
            'primary_entry_route': f'/objects/{object_code}' if object_code else '',
            'legacy_aliases': [],
            'default_page_mode': 'record',
            'default_detail_surface_tab': 'process',
            'default_document_surface_tab': 'summary',
            'toolbar': {
                'primary_actions': [],
                'secondary_actions': [],
            },
            'detail_panels': [],
            'async_indicators': [],
            'summary_cards': [],
            'queue_panels': [],
            'exception_panels': [],
            'closure_panel': {},
            'sla_indicators': [],
            'recommended_actions': [],
            'document_summary_sections': [],
        }

        self._apply_workbench_overrides(payload, menu_config)
        self._apply_workbench_overrides(payload, menu_workbench)
        self._apply_workbench_overrides(payload, layout_workbench)

        return payload

    def _build_runtime_fields_payload(
        self,
        *,
        context: str,
        include_relations: bool,
        request_locale: str,
        runtime_i18n_enabled: bool,
        strict_identifier: bool,
        fallback_contexts: tuple[str, ...],
    ) -> dict:
        from apps.system.models import FieldDefinition

        editable_fields = []
        reverse_relations = []
        model_fields = []
        fields_query = FieldDefinition.objects.none()

        runtime_relations = (
            self._build_relation_runtime_fields(
                locale=request_locale,
                strict_identifier=strict_identifier,
            )
            if self._object_meta.is_hardcoded and include_relations
            else []
        )
        runtime_editable_relations = []
        if runtime_relations:
            runtime_editable_relations, runtime_relations = self._partition_runtime_relation_fields(
                runtime_relations,
                context=context,
            )

        if self._object_meta.is_hardcoded:
            model_fields = self._get_hardcoded_model_fields()

            for field_definition in model_fields:
                field_data = self._format_model_field(
                    field_definition,
                    context,
                    request_locale,
                    localize=runtime_i18n_enabled,
                    strict_identifier=strict_identifier,
                )
                if field_definition.field_type == 'sub_table':
                    if include_relations and not runtime_relations and not runtime_editable_relations:
                        reverse_relations.append(field_data)
                elif self._should_show_field(field_definition, context, is_model_field=True):
                    editable_fields.append(field_data)
        else:
            fields_query = FieldDefinition.objects.filter(
                business_object__code=self._object_meta.code
            ).order_by('sort_order')

            for field_definition in fields_query:
                field_data = self._format_field_definition(
                    field_definition,
                    context,
                    request_locale,
                    localize=runtime_i18n_enabled,
                    strict_identifier=strict_identifier,
                )
                if field_definition.is_reverse_relation:
                    if include_relations:
                        reverse_relations.append(field_data)
                elif self._should_show_field(field_definition, context, is_model_field=False):
                    editable_fields.append(field_data)

        if context in fallback_contexts and not editable_fields:
            if self._object_meta.is_hardcoded:
                for field_definition in model_fields:
                    if field_definition.field_type == 'sub_table':
                        continue
                    editable_fields.append(
                        self._format_model_field(
                            field_definition,
                            context,
                            request_locale,
                            localize=runtime_i18n_enabled,
                            strict_identifier=strict_identifier,
                        )
                    )
            else:
                for field_definition in fields_query:
                    if field_definition.is_reverse_relation:
                        continue
                    editable_fields.append(
                        self._format_field_definition(
                            field_definition,
                            context,
                            request_locale,
                            localize=runtime_i18n_enabled,
                            strict_identifier=strict_identifier,
                        )
                    )

        if runtime_editable_relations:
            editable_fields.extend(runtime_editable_relations)
        if runtime_relations:
            reverse_relations = runtime_relations

        return {
            'editable_fields': editable_fields,
            'reverse_relations': reverse_relations,
            'context': context,
            'locale': request_locale,
        }

    def _resolve_runtime_list_layout_bundle(
        self,
        *,
        request,
        business_object,
        mode: str,
        layout_merge_unified_enabled: bool,
    ) -> dict:
        from apps.system.services.column_config_service import ColumnConfigService
        from apps.system.services.layout_generator import LayoutGenerator

        generated = LayoutGenerator.generate_list_layout(business_object) or {}
        user_column_config = {}
        try:
            if request.user and request.user.is_authenticated:
                user_column_config = (
                    ColumnConfigService.get_column_config(request.user, self._object_meta.code) or {}
                )
        except Exception:
            user_column_config = {}

        columns = user_column_config.get('columns')
        if not isinstance(columns, list) or not columns:
            columns = generated.get('columns') if isinstance(generated.get('columns'), list) else []

        layout_payload = {
            'layout_type': 'list',
            'layout_config': {
                'columns': columns,
                'columnOrder': (
                    user_column_config.get('columnOrder')
                    if isinstance(user_column_config.get('columnOrder'), list)
                    else []
                ),
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

        return {
            'runtime_version': 1,
            'object_code': self._object_meta.code,
            'mode': mode,
            'context': 'list',
            'locale': self._get_request_locale(request),
            'layout_source': layout_source,
            'layout_layers': layout_layers,
            'layout_id': layout_payload.get('id'),
            'layout': layout_payload,
            'is_default': user_column_config.get('source', 'default') != 'user',
        }

    def _resolve_runtime_layout_bundle(
        self,
        *,
        request,
        business_object,
        mode: str,
        layout_merge_unified_enabled: bool,
    ) -> dict:
        from apps.system.models import PageLayout
        from apps.system.serializers import PageLayoutSerializer

        if mode == 'list':
            return self._resolve_runtime_list_layout_bundle(
                request=request,
                business_object=business_object,
                mode=mode,
                layout_merge_unified_enabled=layout_merge_unified_enabled,
            )

        layout_type = self._resolve_runtime_layout_type(mode)
        org_id = getattr(request, 'organization_id', None)
        base_filters = {
            'business_object': business_object,
            'layout_type': layout_type,
            'is_active': True,
        }

        base_qs = PageLayout.objects.filter(**base_filters, is_deleted=False)

        def _scope_custom(queryset):
            if org_id:
                return queryset.filter(organization_id=org_id)
            return queryset

        def _scope_default(queryset):
            if org_id:
                return queryset.filter(Q(organization_id=org_id) | Q(organization__isnull=True))
            return queryset

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
                    raw_layout_config,
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
                'is_template': True,
            }
            is_default = True
            layout_source = 'default'

        if layout_merge_unified_enabled:
            layout_layers = ['user', 'role', 'org', 'global', 'default']
        else:
            layout_layers = ['default']

        return {
            'layout_source': layout_source,
            'layout_layers': layout_layers,
            'layout_id': layout_payload.get('id') if isinstance(layout_payload, dict) else None,
            'layout': layout_payload,
            'is_default': is_default,
        }

    @action(detail=False, methods=['get'], url_path='fields')
    def fields(self, request, *args, **kwargs):
        """
        Get field definitions with context-aware filtering.

        GET /api/objects/{code}/fields/?context={context}&include_relations={true|false}
        """
        error_response = self._ensure_object_meta_loaded(kwargs)
        if error_response is not None:
            return error_response

        context = request.query_params.get('context', 'form')
        include_relations = request.query_params.get('include_relations', 'false').lower() == 'true'
        request_locale = self._get_request_locale(request)
        runtime_i18n_enabled = self._is_feature_enabled(
            'runtime_i18n_enabled',
            default=True,
            request=request,
        )

        if context not in self._VALID_FIELD_CONTEXTS:
            return BaseResponse.error(
                'VALIDATION_ERROR',
                f'Invalid context. Must be one of: {", ".join(self._VALID_FIELD_CONTEXTS)}',
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        payload = self._build_runtime_fields_payload(
            context=context,
            include_relations=include_relations,
            request_locale=request_locale,
            runtime_i18n_enabled=runtime_i18n_enabled,
            strict_identifier=False,
            fallback_contexts=('detail',),
        )
        return BaseResponse.success(payload)

    @action(detail=False, methods=['get'], url_path='runtime')
    def runtime(self, request, *args, **kwargs):
        """
        Get runtime metadata (fields + active layout) for frontend rendering.

        GET /api/system/objects/{code}/runtime/?mode={edit|readonly|list|search}&include_relations={true|false}
        """
        error_response = self._ensure_object_meta_loaded(kwargs)
        if error_response is not None:
            return error_response

        from apps.system.models import BusinessObject

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
        context = self._resolve_runtime_context(mode)

        fields_payload = self._build_runtime_fields_payload(
            context=context,
            include_relations=include_relations,
            request_locale=request_locale,
            runtime_i18n_enabled=runtime_i18n_enabled,
            strict_identifier=True,
            fallback_contexts=('form', 'detail'),
        )

        business_object = BusinessObject.objects.filter(code=self._object_meta.code).first()
        if not business_object:
            return BaseResponse.not_found(f"Business object '{self._object_meta.code}' not found")

        aggregate_relations = RelationQueryService().list_relations(
            parent_object_code=self._object_meta.code,
            locale=request_locale,
        )
        aggregate_payload = self._build_aggregate_runtime_payload(
            business_object=business_object,
            relations=aggregate_relations,
            editable_fields=fields_payload['editable_fields'],
            reverse_relations=fields_payload['reverse_relations'],
        )
        layout_bundle = self._resolve_runtime_layout_bundle(
            request=request,
            business_object=business_object,
            mode=mode,
            layout_merge_unified_enabled=layout_merge_unified_enabled,
        )

        return BaseResponse.success({
            'runtime_version': 1,
            'object_code': self._object_meta.code,
            'mode': mode,
            'context': fields_payload['context'],
            'locale': request_locale,
            'layout_source': layout_bundle['layout_source'],
            'layout_layers': layout_bundle['layout_layers'],
            'layout_id': layout_bundle['layout_id'],
            'permissions': self._get_user_permissions(request.user, self._object_meta.code),
            'fields': fields_payload,
            'aggregate': aggregate_payload,
            'workbench': self._build_runtime_workbench_payload(
                business_object=business_object,
                layout_bundle=layout_bundle,
            ),
            'layout': layout_bundle['layout'],
            'is_default': layout_bundle['is_default'],
        })
