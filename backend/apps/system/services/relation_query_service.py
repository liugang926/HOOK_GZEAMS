from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.apps import apps as django_apps
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db.models import Model, QuerySet

from apps.common.services.i18n_service import TranslationService
from apps.system.models import BusinessObject, ObjectRelationDefinition
from apps.system.services.object_registry import ObjectRegistry


@dataclass(frozen=True)
class RelationResolution:
    relation: ObjectRelationDefinition
    target_queryset: QuerySet
    target_object_code: str


class RelationQueryService:
    """
    Unified relation resolver for direct / through / derived relation kinds.
    """

    def list_relations(self, parent_object_code: str, locale: Optional[str] = None) -> list[dict]:
        resolved_locale = locale or TranslationService.DEFAULT_LANGUAGE
        rows = (
            ObjectRelationDefinition.objects
            .filter(parent_object_code=parent_object_code, is_active=True)
            .order_by('sort_order', 'relation_code')
        )

        target_codes = {row.target_object_code for row in rows}
        bo_map = {
            bo.code: bo
            for bo in BusinessObject.objects.filter(code__in=target_codes)
        }

        payload = []
        for row in rows:
            target_bo = bo_map.get(row.target_object_code)
            fallback_label = self._resolve_target_object_label(target_bo, resolved_locale) if target_bo else row.target_object_code
            label = self._resolve_relation_label(row, resolved_locale, fallback_label)
            group_meta = self._resolve_relation_group_meta(
                relation=row,
                locale=resolved_locale,
                fallback_label=label,
            )
            payload.append(
                {
                    'relation_code': row.relation_code,
                    'relation_name': label,
                    'target_object_code': row.target_object_code,
                    'relation_kind': row.relation_kind,
                    'display_mode': row.display_mode,
                    'sort_order': row.sort_order,
                    'target_fk_field': row.target_fk_field,
                    'through_object_code': row.through_object_code,
                    'through_parent_fk_field': row.through_parent_fk_field,
                    'through_target_fk_field': row.through_target_fk_field,
                    'derived_parent_key_field': row.derived_parent_key_field,
                    'derived_target_key_field': row.derived_target_key_field,
                    'extra_config': row.extra_config or {},
                    'group_key': group_meta['group_key'],
                    'group_name': group_meta['group_name'],
                    'group_order': group_meta['group_order'],
                    'default_expanded': group_meta['default_expanded'],
                }
            )
        return payload

    def _resolve_relation_label(
        self,
        relation: ObjectRelationDefinition,
        locale: str,
        fallback_label: str,
    ) -> str:
        i18n_map = (relation.extra_config or {}).get('relation_name_i18n')
        if isinstance(i18n_map, dict):
            localized = self._pick_locale_text(i18n_map, locale)
            if localized:
                return str(localized)

        is_en = str(locale or '').lower().startswith('en')
        legacy_label = relation.relation_name_en if is_en else relation.relation_name
        if legacy_label:
            return legacy_label

        return fallback_label

    def _resolve_target_object_label(self, business_object: BusinessObject, locale: str) -> str:
        localized = TranslationService.get_localized_value(
            business_object,
            field_name='name',
            lang_code=locale,
            fallback_to_original=True,
        )
        return str(localized or business_object.code)

    def _pick_locale_text(self, values: dict, locale: str):
        if not isinstance(values, dict):
            return None
        normalized = str(locale or '').strip()
        if normalized and normalized in values:
            return values.get(normalized)

        lowered_map = {str(key).lower(): value for key, value in values.items()}
        lowered_locale = normalized.lower()
        if lowered_locale in lowered_map:
            return lowered_map[lowered_locale]

        base_locale = lowered_locale.split('-', 1)[0] if '-' in lowered_locale else lowered_locale
        if base_locale:
            for key, value in lowered_map.items():
                if key.split('-', 1)[0] == base_locale:
                    return value

        if 'default' in values:
            return values.get('default')
        if 'default' in lowered_map:
            return lowered_map.get('default')
        return None

    def _resolve_relation_group_meta(
        self,
        *,
        relation: ObjectRelationDefinition,
        locale: str,
        fallback_label: str,
    ) -> dict:
        extra = relation.extra_config or {}
        group_cfg = extra.get('relation_group')
        if not isinstance(group_cfg, dict):
            group_cfg = {}

        raw_key = (
            group_cfg.get('key')
            or extra.get('group_key')
            or extra.get('relation_group_key')
        )
        group_key = str(raw_key or '').strip() or self._infer_relation_group_key(relation)

        raw_order = (
            group_cfg.get('order')
            if isinstance(group_cfg.get('order'), int)
            else extra.get('group_order')
        )
        if isinstance(raw_order, bool):
            raw_order = None
        if isinstance(raw_order, str) and raw_order.isdigit():
            raw_order = int(raw_order)
        group_order = raw_order if isinstance(raw_order, int) else self._default_group_order(group_key)

        raw_expanded = (
            group_cfg.get('default_expanded')
            if 'default_expanded' in group_cfg
            else extra.get('default_expanded')
        )
        default_expanded = bool(raw_expanded) if raw_expanded is not None else self._default_group_expanded(group_key)

        group_name_i18n = group_cfg.get('name_i18n') if isinstance(group_cfg.get('name_i18n'), dict) else None
        group_name = self._pick_locale_text(group_name_i18n, locale) if group_name_i18n else None
        if not group_name:
            explicit_group_name = group_cfg.get('name') or extra.get('group_name')
            if explicit_group_name:
                group_name = str(explicit_group_name)
        if not group_name:
            group_name = self._default_group_name(group_key=group_key, locale=locale, fallback_label=fallback_label)

        return {
            'group_key': group_key,
            'group_name': str(group_name),
            'group_order': int(group_order),
            'default_expanded': bool(default_expanded),
        }

    def _infer_relation_group_key(self, relation: ObjectRelationDefinition) -> str:
        target = str(relation.target_object_code or '').lower()
        relation_code = str(relation.relation_code or '').lower()
        parent = str(relation.parent_object_code or '').lower()

        sample = f'{parent}:{relation_code}:{target}'

        if any(token in sample for token in ('workflow', 'approval', 'instance', 'task')):
            return 'workflow'
        if any(token in sample for token in ('voucher', 'depreciation', 'finance')):
            return 'finance'
        if any(token in sample for token in ('inventory', 'snapshot', 'difference')):
            return 'inventory'
        if any(token in sample for token in ('consumable', 'issue', 'purchaseitem', 'purchase')):
            return 'consumables'
        if any(token in sample for token in ('itasset', 'itsoftware', 'configuration', 'licenseallocation')):
            return 'it_assets'
        if any(token in sample for token in ('insurance', 'policy', 'claim', 'premium', 'insured')):
            return 'insurance'
        if any(token in sample for token in ('lease', 'leasing', 'rent')):
            return 'leasing'
        if any(token in sample for token in ('organization', 'department', 'user')):
            return 'organization'
        if any(token in sample for token in ('category', 'supplier', 'location')):
            return 'master_data'
        return 'business'

    def _default_group_order(self, group_key: str) -> int:
        return {
            'business': 10,
            'workflow': 20,
            'finance': 30,
            'inventory': 40,
            'consumables': 50,
            'it_assets': 60,
            'insurance': 70,
            'leasing': 80,
            'organization': 90,
            'master_data': 100,
            'other': 999,
        }.get(group_key, 999)

    def _default_group_expanded(self, group_key: str) -> bool:
        return group_key in {'business', 'workflow'}

    def _default_group_name(self, *, group_key: str, locale: str, fallback_label: str) -> str:
        is_en = str(locale or '').lower().startswith('en')
        labels = {
            'business': ('业务单据', 'Business'),
            'workflow': ('流程协同', 'Workflow'),
            'finance': ('财务', 'Finance'),
            'inventory': ('盘点库存', 'Inventory'),
            'consumables': ('耗材', 'Consumables'),
            'it_assets': ('IT资产', 'IT Assets'),
            'insurance': ('保险', 'Insurance'),
            'leasing': ('租赁', 'Leasing'),
            'organization': ('组织与人员', 'Organization'),
            'master_data': ('主数据', 'Master Data'),
            'other': ('其他', 'Other'),
        }
        zh_name, en_name = labels.get(group_key, ('其他', 'Other'))
        resolved = en_name if is_en else zh_name
        return resolved or fallback_label

    def resolve_related_queryset(
        self,
        *,
        parent_object_code: str,
        parent_id: str,
        relation_code: str,
        organization_id: Optional[str],
    ) -> RelationResolution:
        relation = ObjectRelationDefinition.objects.filter(
            parent_object_code=parent_object_code,
            relation_code=relation_code,
            is_active=True,
        ).first()
        if not relation:
            raise ValidationError(f'relation_not_found:{relation_code}')

        parent_meta = ObjectRegistry.get_or_create_from_db(parent_object_code)
        if not parent_meta or not parent_meta.model_class:
            raise ValidationError(f'parent_model_not_available:{parent_object_code}')

        target_meta = ObjectRegistry.get_or_create_from_db(relation.target_object_code)
        if not target_meta or not target_meta.model_class:
            raise ValidationError(f'target_model_not_available:{relation.target_object_code}')

        parent = self._resolve_parent_instance(parent_meta.model_class, parent_id, organization_id)
        target_queryset = self._build_scoped_queryset(target_meta.model_class, organization_id)

        if relation.relation_kind == 'direct_fk':
            target_queryset = self._apply_direct_relation(
                queryset=target_queryset,
                model_class=target_meta.model_class,
                target_fk_field=relation.target_fk_field,
                parent=parent,
            )
        elif relation.relation_kind == 'through_line_item':
            target_queryset = self._apply_through_relation(
                queryset=target_queryset,
                relation=relation,
                parent=parent,
                organization_id=organization_id,
            )
        elif relation.relation_kind == 'derived_query':
            target_queryset = self._apply_derived_relation(
                queryset=target_queryset,
                model_class=target_meta.model_class,
                relation=relation,
                parent=parent,
            )
        else:
            raise ValidationError(f'unsupported_relation_kind:{relation.relation_kind}')

        return RelationResolution(
            relation=relation,
            target_queryset=target_queryset.distinct(),
            target_object_code=relation.target_object_code,
        )

    def _resolve_parent_instance(
        self,
        model_class: type[Model],
        parent_id: str,
        organization_id: Optional[str],
    ) -> Model:
        queryset = self._build_scoped_queryset(model_class, organization_id)
        instance = queryset.filter(id=parent_id).first()
        if not instance:
            raise ValidationError(f'parent_record_not_found:{parent_id}')
        return instance

    def _build_scoped_queryset(
        self,
        model_class: type[Model],
        organization_id: Optional[str],
    ) -> QuerySet:
        manager = getattr(model_class, 'all_objects', None) or model_class._default_manager
        queryset = manager.all()

        field_names = {f.name for f in model_class._meta.fields}
        if 'is_deleted' in field_names:
            queryset = queryset.filter(is_deleted=False)
        if organization_id and 'organization' in field_names:
            queryset = queryset.filter(organization_id=organization_id)
        return queryset

    def _apply_direct_relation(
        self,
        *,
        queryset: QuerySet,
        model_class: type[Model],
        target_fk_field: str,
        parent: Model,
    ) -> QuerySet:
        if not target_fk_field:
            raise ValidationError('direct_fk_field_required')

        try:
            field = model_class._meta.get_field(target_fk_field)
        except FieldDoesNotExist as exc:
            raise ValidationError(f'invalid_direct_fk_field:{target_fk_field}') from exc

        if getattr(field, 'is_relation', False):
            return queryset.filter(**{f'{target_fk_field}_id': parent.pk})
        return queryset.filter(**{target_fk_field: parent.pk})

    def _apply_through_relation(
        self,
        *,
        queryset: QuerySet,
        relation: ObjectRelationDefinition,
        parent: Model,
        organization_id: Optional[str],
    ) -> QuerySet:
        if not relation.through_object_code:
            raise ValidationError('through_object_code_required')
        if not relation.through_parent_fk_field or not relation.through_target_fk_field:
            raise ValidationError('through_fields_required')

        through_meta = ObjectRegistry.get_or_create_from_db(relation.through_object_code)
        through_model_class = through_meta.model_class if through_meta and through_meta.model_class else None
        if not through_model_class:
            through_model_class = self._resolve_model_class_from_code(relation.through_object_code)
        if not through_model_class:
            raise ValidationError(f'through_model_not_available:{relation.through_object_code}')

        through_queryset = self._build_scoped_queryset(through_model_class, organization_id)

        parent_lookup = self._build_lookup(
            model_class=through_model_class,
            field_name=relation.through_parent_fk_field,
            value=parent.pk,
        )
        target_value_field = self._resolve_value_field(
            model_class=through_model_class,
            field_name=relation.through_target_fk_field,
        )

        target_ids = list(
            through_queryset
            .filter(**parent_lookup)
            .values_list(target_value_field, flat=True)
        )
        if not target_ids:
            return queryset.none()
        return queryset.filter(id__in=target_ids)

    def _apply_derived_relation(
        self,
        *,
        queryset: QuerySet,
        model_class: type[Model],
        relation: ObjectRelationDefinition,
        parent: Model,
    ) -> QuerySet:
        if not relation.derived_parent_key_field or not relation.derived_target_key_field:
            raise ValidationError('derived_fields_required')

        parent_value = self._read_parent_key_value(parent, relation.derived_parent_key_field)
        if parent_value is None:
            return queryset.none()

        target_lookup = self._build_lookup(
            model_class=model_class,
            field_name=relation.derived_target_key_field,
            value=parent_value,
        )
        return queryset.filter(**target_lookup)

    def _read_parent_key_value(self, parent: Model, field_name: str):
        if not hasattr(parent, field_name):
            raise ValidationError(f'invalid_parent_key_field:{field_name}')
        value = getattr(parent, field_name)
        if hasattr(value, 'pk'):
            return value.pk
        return value

    def _build_lookup(self, *, model_class: type[Model], field_name: str, value) -> dict:
        try:
            field = model_class._meta.get_field(field_name)
        except FieldDoesNotExist as exc:
            raise ValidationError(f'invalid_field:{field_name}') from exc

        if getattr(field, 'is_relation', False):
            return {f'{field_name}_id': value}
        return {field_name: value}

    def _resolve_value_field(self, *, model_class: type[Model], field_name: str) -> str:
        try:
            field = model_class._meta.get_field(field_name)
        except FieldDoesNotExist as exc:
            raise ValidationError(f'invalid_field:{field_name}') from exc

        if getattr(field, 'is_relation', False):
            return f'{field_name}_id'
        return field_name

    def _resolve_model_class_from_code(self, code: str) -> Optional[type[Model]]:
        normalized = str(code or '').strip()
        if not normalized:
            return None

        lowered = normalized.lower()
        for model in django_apps.get_models():
            name = getattr(model, '__name__', '')
            if not name:
                continue
            if name == normalized or name.lower() == lowered:
                return model
        return None
