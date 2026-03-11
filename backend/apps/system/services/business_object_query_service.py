"""
Query and response-assembly service for business object metadata.

This service owns read-side shaping for hardcoded and metadata-driven business
objects. Mutation workflows remain in BusinessObjectService and dedicated sync
services.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.db.models import QuerySet
from django.utils.module_loading import import_string

from apps.system.layout_sections import get_field_section_metadata
from apps.system.object_catalog import (
    get_hardcoded_object_definition,
    iter_hardcoded_object_definitions,
)
from apps.system.models import BusinessObject, FieldDefinition, ModelFieldDefinition


class BusinessObjectQueryService:
    def get_all_objects(
        self,
        organization_id: Optional[str] = None,
        include_hardcoded: bool = True,
        include_custom: bool = True,
    ) -> Dict[str, List[Dict[str, Any]]]:
        result = {
            "hardcoded": [],
            "custom": [],
        }

        if include_hardcoded:
            result["hardcoded"] = self._get_hardcoded_objects()

        if include_custom:
            queryset = BusinessObject.objects.filter(is_deleted=False, is_hardcoded=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            result["custom"] = self._format_custom_objects(queryset)

        return result

    def get_reference_options(
        self,
        organization_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        result = []

        for obj in self._get_hardcoded_objects():
            result.append(
                {
                    "value": obj["code"],
                    "label": obj["name"],
                    "label_en": obj.get("name_en", ""),
                    "type": "hardcoded",
                    "app_label": obj.get("app_label", ""),
                    "icon": self._get_object_icon(obj["code"]),
                }
            )

        queryset = BusinessObject.objects.filter(
            is_deleted=False,
            is_hardcoded=False,
        )
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        for obj in queryset:
            result.append(
                {
                    "value": obj.code,
                    "label": obj.name,
                    "label_en": obj.name_en or "",
                    "type": "custom",
                    "icon": "document",
                }
            )

        return result

    def get_object_fields(
        self,
        object_code: str,
        *,
        context: str = "form",
        include_relations: bool = False,
        locale: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self.is_hardcoded_model(object_code):
            return self._get_hardcoded_object_fields(
                object_code,
                context=context,
                include_relations=include_relations,
                locale=locale,
            )

        try:
            obj = BusinessObject.objects.get(code=object_code, is_deleted=False)
        except BusinessObject.DoesNotExist:
            return {
                "error": f'Business object "{object_code}" not found',
            }

        return self._get_custom_object_fields(
            obj,
            context=context,
            include_relations=include_relations,
            locale=locale,
        )

    def is_hardcoded_model(self, object_code: str) -> bool:
        obj = BusinessObject.objects.filter(
            code=object_code,
            is_deleted=False,
            is_hardcoded=True,
        ).only("id").first()
        if obj is not None:
            return True
        return get_hardcoded_object_definition(object_code) is not None

    def get_django_model(self, object_code: str):
        model_path = self._get_hardcoded_model_path(object_code)
        if not model_path:
            return None

        try:
            return import_string(model_path)
        except ImportError:
            return None

    def _get_hardcoded_model_path(self, object_code: str) -> Optional[str]:
        obj = (
            BusinessObject.objects.filter(
                code=object_code,
                is_deleted=False,
                is_hardcoded=True,
            )
            .only("django_model_path")
            .first()
        )
        if obj and obj.django_model_path:
            return obj.django_model_path

        definition = get_hardcoded_object_definition(object_code)
        if definition:
            return definition.django_model_path
        return None

    def _get_hardcoded_objects(self) -> List[Dict[str, Any]]:
        existing_objects = {
            obj.code: obj
            for obj in BusinessObject.objects.filter(
                is_deleted=False,
                is_hardcoded=True,
            ).only("code", "name", "name_en")
        }

        result = []
        for definition in iter_hardcoded_object_definitions():
            obj = existing_objects.get(definition.code)
            result.append(
                {
                    "code": definition.code,
                    "name": obj.name if obj else definition.name,
                    "name_en": (obj.name_en or "") if obj else definition.name_en,
                    "app_label": definition.app_label,
                    "model_path": definition.django_model_path,
                    "type": "hardcoded",
                }
            )

        return sorted(result, key=lambda item: item["code"])

    def _format_custom_objects(self, queryset: QuerySet) -> List[Dict[str, Any]]:
        return [
            {
                "code": obj.code,
                "name": obj.name,
                "name_en": obj.name_en or "",
                "table_name": obj.table_name,
                "field_count": obj.field_definitions.count(),
                "layout_count": obj.page_layouts.count(),
                "type": "custom",
                "enable_workflow": obj.enable_workflow,
            }
            for obj in queryset
        ]

    def _should_show_model_field_in_context(self, field_def: ModelFieldDefinition, context: str) -> bool:
        if context == "list":
            return bool(getattr(field_def, "show_in_list", True))
        if context == "detail":
            return bool(getattr(field_def, "show_in_detail", True))
        return bool(getattr(field_def, "show_in_form", True))

    def _should_show_custom_field_in_context(self, field_def: FieldDefinition, context: str) -> bool:
        if context == "list":
            return bool(getattr(field_def, "show_in_list", False))
        if context == "detail":
            return bool(getattr(field_def, "show_in_detail", True))
        return bool(getattr(field_def, "show_in_form", True))

    def _get_hardcoded_object_fields(
        self,
        object_code: str,
        *,
        context: str = "form",
        include_relations: bool = False,
        locale: Optional[str] = None,
    ) -> Dict[str, Any]:
        obj = BusinessObject.objects.filter(code=object_code).first()
        if not obj:
            definition = get_hardcoded_object_definition(object_code)
            if not definition:
                return {
                    "error": f'Business object "{object_code}" not registered',
                }
            obj = BusinessObject(
                code=definition.code,
                name=definition.name,
                name_en=definition.name_en,
                is_hardcoded=True,
                django_model_path=definition.django_model_path,
            )

        model_class = self.get_django_model(object_code)
        if not model_class:
            return {
                "error": f"Django model not found for: {object_code}",
            }

        normalized_context = context if context in {"form", "detail", "list"} else "form"
        fields: list[dict[str, Any]] = []

        for field in model_class._meta.get_fields():
            is_reverse_relation = bool(field.auto_created and getattr(field, "one_to_many", False))
            if field.auto_created and not is_reverse_relation:
                continue
            if is_reverse_relation:
                if not include_relations:
                    continue
                relation_code = getattr(field, "get_accessor_name", lambda: field.name)() or field.name
                fields.append(
                    {
                        "fieldName": relation_code,
                        "displayName": relation_code,
                        "displayNameEn": relation_code,
                        "fieldType": "sub_table",
                        "djangoFieldType": field.__class__.__name__,
                        "isRequired": False,
                        "isReadonly": True,
                        "isEditable": False,
                        "isUnique": False,
                        "showInList": False,
                        "showInDetail": True,
                        "showInForm": False,
                        "sortOrder": 0,
                        "referenceModelPath": "",
                        "maxLength": None,
                        "decimalPlaces": None,
                        "isReverseRelation": True,
                        "reverseRelationModel": "",
                        "reverseRelationField": "",
                        "relationDisplayMode": "tab_readonly",
                    }
                )
                continue

            if field.is_relation and not field.many_to_one and not field.one_to_many:
                continue

            field_def = ModelFieldDefinition.from_django_field(obj, field)
            section_meta = get_field_section_metadata(object_code, field_def.field_name, locale=locale)

            if not self._should_show_model_field_in_context(field_def, normalized_context):
                continue

            fields.append(
                {
                    "fieldName": field_def.field_name,
                    "displayName": field_def.display_name,
                    "displayNameEn": field_def.display_name_en or "",
                    "fieldType": field_def.field_type,
                    "djangoFieldType": field_def.django_field_type,
                    "isRequired": field_def.is_required,
                    "isReadonly": field_def.is_readonly,
                    "isEditable": field_def.is_editable,
                    "isUnique": field_def.is_unique,
                    "showInList": field_def.show_in_list,
                    "showInDetail": field_def.show_in_detail,
                    "showInForm": field_def.show_in_form,
                    "sortOrder": field_def.sort_order,
                    "referenceModelPath": field_def.reference_model_path,
                    "maxLength": field_def.max_length,
                    "decimalPlaces": field_def.decimal_places,
                    "isReverseRelation": False,
                    "sectionName": section_meta["section_name"],
                    "sectionTitle": section_meta["section_title"],
                    "sectionTitleI18n": section_meta["section_title_i18n"],
                    "sectionTranslationKey": section_meta["section_translation_key"],
                    "sectionIcon": section_meta["section_icon"],
                }
            )

        return {
            "objectCode": obj.code,
            "objectName": obj.name,
            "objectNameEn": obj.name_en or "",
            "isHardcoded": True,
            "modelPath": obj.django_model_path,
            "fields": fields,
        }

    def _get_custom_object_fields(
        self,
        obj: BusinessObject,
        *,
        context: str = "form",
        include_relations: bool = False,
        locale: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_context = context if context in {"form", "detail", "list"} else "form"
        rows = []
        queryset = obj.field_definitions.filter(is_deleted=False).order_by("sort_order")

        def _snake_to_camel(name: str) -> str:
            parts = name.split('_')
            return parts[0] + ''.join(p.capitalize() for p in parts[1:])

        def _with_camel_keys(d: dict) -> dict:
            extra = {}
            for k, v in d.items():
                ck = _snake_to_camel(k)
                if ck != k and ck not in d:
                    extra[ck] = v
            d.update(extra)
            return d

        for field in queryset:
            if getattr(field, "is_reverse_relation", False) and not include_relations:
                continue
            if not self._should_show_custom_field_in_context(field, normalized_context):
                continue
            section_meta = get_field_section_metadata(obj.code, field.code, locale=locale)
            rows.append(
                _with_camel_keys({
                    "field_name": field.code,
                    "display_name": field.name,
                    "field_type": field.field_type,
                    "is_required": field.is_required,
                    "is_readonly": field.is_readonly,
                    "is_unique": field.is_unique,
                    "show_in_list": field.show_in_list,
                    "show_in_detail": field.show_in_detail,
                    "show_in_form": field.show_in_form,
                    "sort_order": field.sort_order,
                    "options": field.options,
                    "reference_object": field.reference_object,
                    "formula": field.formula,
                    "is_reverse_relation": getattr(field, "is_reverse_relation", False),
                    "reverse_relation_model": getattr(field, "reverse_relation_model", ""),
                    "reverse_relation_field": getattr(field, "reverse_relation_field", ""),
                    "relation_display_mode": getattr(field, "relation_display_mode", "tab_readonly"),
                    "section_name": section_meta["section_name"],
                    "section_title": section_meta["section_title"],
                    "section_title_i18n": section_meta["section_title_i18n"],
                    "section_translation_key": section_meta["section_translation_key"],
                    "section_icon": section_meta["section_icon"],
                })
            )

        return {
            "object_code": obj.code,
            "object_name": obj.name,
            "object_name_en": obj.name_en or "",
            "is_hardcoded": False,
            "table_name": obj.table_name,
            "fields": rows,
        }

    def _get_object_icon(self, code: str) -> str:
        definition = get_hardcoded_object_definition(code)
        if definition:
            return definition.icon
        return "document"
