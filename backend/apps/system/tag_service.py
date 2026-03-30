"""
Tag service for CRUD extensions and object-tag association workflows.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum
from django.utils.module_loading import import_string

from apps.common.models import BaseModel
from apps.common.services.base_crud import BaseCRUDService
from apps.system.models import BusinessObject, DynamicData, Tag, TagAssignment


class TagService(BaseCRUDService):
    """Service layer for tag CRUD, statistics, and assignment actions."""

    def __init__(self):
        super().__init__(Tag)

    def get_business_object_options(self) -> List[Dict[str, Any]]:
        """Return selectable business object options for tag grouping."""
        queryset = (
            BusinessObject.objects
            .filter(is_deleted=False, allow_standalone_query=True)
            .order_by('name', 'code')
        )
        return [
            {
                'value': row.code,
                'label': row.name,
                'name_en': row.name_en,
                'is_hardcoded': row.is_hardcoded,
            }
            for row in queryset
        ]

    def get_statistics(self, organization_id=None, user=None) -> Dict[str, Any]:
        """Return aggregate statistics for the current organization."""
        queryset = self._scope_queryset(
            Tag.all_objects.filter(is_deleted=False),
            organization_id=organization_id,
            user=user,
        )

        option_map = {
            row['value']: row
            for row in self.get_business_object_options()
        }
        by_biz_type_rows = (
            queryset.values('biz_type')
            .annotate(count=Count('id'), usage_count=Sum('usage_count'))
            .order_by('biz_type')
        )

        by_biz_type = []
        for row in by_biz_type_rows:
            biz_type = str(row.get('biz_type') or '').strip()
            option = option_map.get(biz_type, {})
            by_biz_type.append({
                'biz_type': biz_type,
                'label': option.get('label') or ('All Objects' if not biz_type else biz_type),
                'name_en': option.get('name_en') or '',
                'count': int(row.get('count') or 0),
                'usage_count': int(row.get('usage_count') or 0),
            })

        top_tags = list(
            queryset.order_by('-usage_count', 'name').values(
                'id',
                'name',
                'color',
                'biz_type',
                'usage_count',
            )[:10]
        )

        return {
            'total': queryset.count(),
            'used': queryset.filter(usage_count__gt=0).count(),
            'unused': queryset.filter(usage_count=0).count(),
            'by_biz_type': by_biz_type,
            'top_tags': top_tags,
        }

    def apply_tags(
        self,
        *,
        tag_ids: Sequence[str],
        object_ids: Sequence[str],
        biz_type: str,
        user=None,
        organization_id=None,
    ) -> Dict[str, Any]:
        """Assign one or more tags to one or more business object records."""
        resolved_org_id = self._resolve_organization_id(
            organization_id=organization_id,
            user=user,
        )
        tags = self._get_active_tags(
            tag_ids=tag_ids,
            biz_type=biz_type,
            organization_id=resolved_org_id,
            user=user,
        )
        model_class, target_queryset = self._resolve_target_queryset(
            biz_type=biz_type,
            organization_id=resolved_org_id,
            user=user,
        )
        targets = self._get_target_records(
            queryset=target_queryset,
            object_ids=object_ids,
        )
        content_type = ContentType.objects.get_for_model(model_class, for_concrete_model=False)

        existing_assignments = {
            (str(assignment.tag_id), str(assignment.object_id)): assignment
            for assignment in TagAssignment.all_objects.filter(
                organization_id=resolved_org_id,
                tag_id__in=[tag.id for tag in tags],
                content_type=content_type,
                object_id__in=[target.id for target in targets],
            )
        }

        created_count = 0
        restored_count = 0
        skipped_count = 0

        with transaction.atomic():
            for tag in tags:
                for target in targets:
                    assignment_key = (str(tag.id), str(target.id))
                    assignment = existing_assignments.get(assignment_key)
                    if assignment:
                        if assignment.is_deleted:
                            assignment.is_deleted = False
                            assignment.deleted_at = None
                            assignment.deleted_by = None
                            assignment.biz_type = biz_type
                            if user and getattr(user, 'is_authenticated', False):
                                assignment.updated_by = user
                            assignment.save()
                            restored_count += 1
                        else:
                            skipped_count += 1
                        continue

                    TagAssignment.objects.create(
                        organization_id=resolved_org_id,
                        tag=tag,
                        content_type=content_type,
                        object_id=target.id,
                        biz_type=biz_type,
                        created_by=user if getattr(user, 'is_authenticated', False) else None,
                    )
                    created_count += 1

            self._sync_usage_counts(
                tag_ids=[tag.id for tag in tags],
                organization_id=resolved_org_id,
            )

        return {
            'biz_type': biz_type,
            'tag_ids': [str(tag.id) for tag in tags],
            'object_ids': [str(target.id) for target in targets],
            'created_count': created_count,
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'assignment_count': created_count + restored_count,
        }

    def remove_tags(
        self,
        *,
        tag_ids: Sequence[str],
        object_ids: Sequence[str],
        biz_type: str,
        user=None,
        organization_id=None,
    ) -> Dict[str, Any]:
        """Remove one or more tags from one or more business object records."""
        resolved_org_id = self._resolve_organization_id(
            organization_id=organization_id,
            user=user,
        )
        tags = self._get_active_tags(
            tag_ids=tag_ids,
            biz_type=biz_type,
            organization_id=resolved_org_id,
            user=user,
        )
        model_class, target_queryset = self._resolve_target_queryset(
            biz_type=biz_type,
            organization_id=resolved_org_id,
            user=user,
        )
        targets = self._get_target_records(
            queryset=target_queryset,
            object_ids=object_ids,
        )
        content_type = ContentType.objects.get_for_model(model_class, for_concrete_model=False)

        assignments = list(
            TagAssignment.all_objects.filter(
                organization_id=resolved_org_id,
                tag_id__in=[tag.id for tag in tags],
                content_type=content_type,
                object_id__in=[target.id for target in targets],
                is_deleted=False,
            )
        )

        removed_count = 0
        with transaction.atomic():
            for assignment in assignments:
                assignment.soft_delete(user=user)
                removed_count += 1

            self._sync_usage_counts(
                tag_ids=[tag.id for tag in tags],
                organization_id=resolved_org_id,
            )

        return {
            'biz_type': biz_type,
            'tag_ids': [str(tag.id) for tag in tags],
            'object_ids': [str(target.id) for target in targets],
            'removed_count': removed_count,
        }

    def _get_active_tags(
        self,
        *,
        tag_ids: Sequence[str],
        biz_type: str,
        organization_id=None,
        user=None,
    ) -> List[Tag]:
        """Load active tags and validate business object compatibility."""
        queryset = self._scope_queryset(
            Tag.all_objects.filter(id__in=tag_ids, is_deleted=False),
            organization_id=organization_id,
            user=user,
        )
        tags = list(queryset)
        if len(tags) != len(set(str(tag_id) for tag_id in tag_ids)):
            found_ids = {str(tag.id) for tag in tags}
            missing_ids = [str(tag_id) for tag_id in tag_ids if str(tag_id) not in found_ids]
            raise ValidationError({'tag_ids': [f'Tags not found: {", ".join(missing_ids)}']})

        incompatible = [
            tag.name
            for tag in tags
            if str(tag.biz_type or '').strip() and str(tag.biz_type).strip() != biz_type
        ]
        if incompatible:
            raise ValidationError({
                'tag_ids': [
                    f'Tags are not compatible with business object "{biz_type}": {", ".join(incompatible)}'
                ]
            })

        return tags

    def _resolve_target_queryset(
        self,
        *,
        biz_type: str,
        organization_id=None,
        user=None,
    ) -> Tuple[type, Any]:
        """Resolve the target queryset for hardcoded or dynamic business objects."""
        business_object = BusinessObject.objects.filter(code=biz_type, is_deleted=False).first()
        if business_object and not business_object.is_hardcoded:
            queryset = self._scope_queryset(
                DynamicData.all_objects.filter(
                    is_deleted=False,
                    business_object__code=biz_type,
                ),
                organization_id=organization_id,
                user=user,
            )
            return DynamicData, queryset

        model_class = None
        if business_object and business_object.django_model_path:
            try:
                model_class = import_string(business_object.django_model_path)
            except ImportError:
                model_class = None

        if model_class is None:
            from apps.system.services.business_object_service import BusinessObjectService

            model_class = BusinessObjectService().get_django_model(biz_type)

        if model_class is None or not issubclass(model_class, BaseModel):
            raise ValidationError({'biz_type': [f'Unknown business object "{biz_type}".']})

        queryset = self._scope_queryset(
            model_class.all_objects.filter(is_deleted=False),
            organization_id=organization_id,
            user=user,
        )
        return model_class, queryset

    def _get_target_records(self, *, queryset, object_ids: Sequence[str]) -> List[Any]:
        """Validate target records and preserve the requested ID order."""
        objects = list(queryset.filter(id__in=object_ids))
        object_map = {str(obj.id): obj for obj in objects}
        missing_ids = [str(object_id) for object_id in object_ids if str(object_id) not in object_map]
        if missing_ids:
            raise ValidationError({'object_ids': [f'Records not found: {", ".join(missing_ids)}']})
        return [object_map[str(object_id)] for object_id in object_ids]

    def _sync_usage_counts(self, *, tag_ids: Iterable[str], organization_id=None) -> None:
        """Refresh usage_count after assignment changes."""
        normalized_tag_ids = [str(tag_id) for tag_id in tag_ids]
        if not normalized_tag_ids:
            return

        counts = {
            str(row['tag_id']): int(row['total'])
            for row in (
                TagAssignment.all_objects
                .filter(
                    organization_id=organization_id,
                    tag_id__in=normalized_tag_ids,
                    is_deleted=False,
                )
                .values('tag_id')
                .annotate(total=Count('id'))
            )
        }

        for tag in Tag.all_objects.filter(id__in=normalized_tag_ids):
            next_count = counts.get(str(tag.id), 0)
            if tag.usage_count == next_count:
                continue
            tag.usage_count = next_count
            tag.save(update_fields=['usage_count', 'updated_at'])
