"""
Services for asset tag groups, tags, and asset-tag relations.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Prefetch, Q, QuerySet
from django.utils import timezone

from apps.assets.models import Asset, AssetTag, AssetTagRelation, TagGroup
from apps.common.services.base_crud import BaseCRUDService


def _normalize_uuid_strings(values: Iterable[Any]) -> List[str]:
    """Normalize a sequence of identifiers into a deduplicated string list."""
    normalized: List[str] = []
    seen = set()

    for value in values or []:
        value_str = str(value or '').strip()
        if not value_str or value_str in seen:
            continue
        seen.add(value_str)
        normalized.append(value_str)

    return normalized


class TagGroupService(BaseCRUDService):
    """Service helpers for tag group lifecycle management."""

    def __init__(self):
        super().__init__(TagGroup)

    def delete_group(self, instance: TagGroup, user=None) -> None:
        """Soft delete a tag group together with its tags and active relations."""
        if instance.is_system:
            raise ValidationError({'non_field_errors': ['System tag groups cannot be deleted.']})

        with transaction.atomic():
            active_relations = AssetTagRelation.all_objects.filter(
                organization_id=instance.organization_id,
                tag__tag_group=instance,
                is_deleted=False,
            )
            for relation in active_relations.select_related('tag'):
                relation.soft_delete(user=user)

            active_tags = AssetTag.all_objects.filter(
                organization_id=instance.organization_id,
                tag_group=instance,
                is_deleted=False,
            )
            for tag in active_tags:
                tag.soft_delete(user=user)

            instance.soft_delete(user=user)


class AssetTagService(BaseCRUDService):
    """Service helpers for asset tag CRUD and statistics."""

    def __init__(self):
        super().__init__(AssetTag)

    def delete_tag(self, instance: AssetTag, user=None) -> None:
        """Soft delete a tag and all active asset relations."""
        with transaction.atomic():
            active_relations = AssetTagRelation.all_objects.filter(
                organization_id=instance.organization_id,
                tag=instance,
                is_deleted=False,
            )
            for relation in active_relations:
                relation.soft_delete(user=user)

            instance.soft_delete(user=user)

    def get_tag_statistics(
        self,
        *,
        tag_group_id=None,
        organization_id=None,
        user=None,
    ) -> Dict[str, Any]:
        """Return aggregated tag usage statistics for the scoped organization."""
        tags_queryset = self._scope_queryset(
            AssetTag.all_objects.filter(
                is_deleted=False,
                is_active=True,
                tag_group__is_deleted=False,
                tag_group__is_active=True,
            ).select_related('tag_group'),
            organization_id=organization_id,
            user=user,
        )
        if tag_group_id:
            tags_queryset = tags_queryset.filter(tag_group_id=tag_group_id)

        relations_queryset = self._scope_queryset(
            AssetTagRelation.all_objects.filter(
                is_deleted=False,
                asset__is_deleted=False,
                tag__is_deleted=False,
                tag__is_active=True,
            ),
            organization_id=organization_id,
            user=user,
        )
        if tag_group_id:
            relations_queryset = relations_queryset.filter(tag__tag_group_id=tag_group_id)

        total_tagged_assets = relations_queryset.values('asset_id').distinct().count()
        annotated_tags = list(
            tags_queryset.annotate(
                asset_count=Count(
                    'asset_relations__asset',
                    filter=Q(
                        asset_relations__is_deleted=False,
                        asset_relations__asset__is_deleted=False,
                    ),
                    distinct=True,
                ),
            ).order_by('tag_group__sort_order', 'sort_order', 'name')
        )

        return {
            'total_tags': len(annotated_tags),
            'total_tagged_assets': total_tagged_assets,
            'tag_statistics': [
                {
                    'id': tag.id,
                    'tag_group': tag.tag_group_id,
                    'group_name': tag.tag_group.name,
                    'name': tag.name,
                    'code': tag.code,
                    'color': tag.color or tag.tag_group.color,
                    'asset_count': int(tag.asset_count or 0),
                    'percentage': round(
                        (int(tag.asset_count or 0) / total_tagged_assets) * 100,
                        2,
                    ) if total_tagged_assets else 0,
                }
                for tag in annotated_tags
            ],
        }


class AssetTagRelationService(BaseCRUDService):
    """Service helpers for assigning and removing tags on assets."""

    def __init__(self):
        super().__init__(AssetTagRelation)

    def _get_assets(
        self,
        *,
        asset_ids: Sequence[str],
        organization_id=None,
        user=None,
    ) -> List[Asset]:
        """Load scoped assets and ensure all requested IDs exist."""
        normalized_ids = _normalize_uuid_strings(asset_ids)
        queryset = self._scope_queryset(
            Asset.all_objects.filter(id__in=normalized_ids, is_deleted=False),
            organization_id=organization_id,
            user=user,
        )
        assets = list(queryset)
        if len(assets) != len(normalized_ids):
            found_ids = {str(asset.id) for asset in assets}
            missing_ids = [asset_id for asset_id in normalized_ids if asset_id not in found_ids]
            raise ValidationError({'asset_ids': [f'Assets not found: {", ".join(missing_ids)}']})
        return assets

    def _get_tags(
        self,
        *,
        tag_ids: Sequence[str],
        organization_id=None,
        user=None,
    ) -> List[AssetTag]:
        """Load scoped active tags and ensure all requested IDs exist."""
        normalized_ids = _normalize_uuid_strings(tag_ids)
        queryset = self._scope_queryset(
            AssetTag.all_objects.filter(
                id__in=normalized_ids,
                is_deleted=False,
                is_active=True,
                tag_group__is_deleted=False,
                tag_group__is_active=True,
            ).select_related('tag_group'),
            organization_id=organization_id,
            user=user,
        )
        tags = list(queryset)
        if len(tags) != len(normalized_ids):
            found_ids = {str(tag.id) for tag in tags}
            missing_ids = [tag_id for tag_id in normalized_ids if tag_id not in found_ids]
            raise ValidationError({'tag_ids': [f'Tags not found: {", ".join(missing_ids)}']})
        return tags

    def get_asset_relations(
        self,
        *,
        asset: Asset,
        organization_id=None,
        user=None,
    ) -> QuerySet[AssetTagRelation]:
        """Return active tag relations for the requested asset."""
        return self._scope_queryset(
            AssetTagRelation.all_objects.filter(
                asset=asset,
                is_deleted=False,
                tag__is_deleted=False,
                tag__is_active=True,
            ).select_related('tag__tag_group', 'tagged_by'),
            organization_id=organization_id or asset.organization_id,
            user=user,
        ).order_by('tag__tag_group__sort_order', 'tag__sort_order', 'tag__name')

    def add_tags_to_asset(
        self,
        *,
        asset: Asset,
        tag_ids: Sequence[str],
        user=None,
        notes: str = '',
        organization_id=None,
    ) -> Dict[str, Any]:
        """Attach one or more tags to an asset while restoring soft-deleted relations."""
        resolved_org_id = organization_id or asset.organization_id
        tags = self._get_tags(
            tag_ids=tag_ids,
            organization_id=resolved_org_id,
            user=user,
        )
        existing_relations = {
            str(relation.tag_id): relation
            for relation in AssetTagRelation.all_objects.filter(
                organization_id=resolved_org_id,
                asset=asset,
                tag_id__in=[tag.id for tag in tags],
            ).select_related('tag', 'tag__tag_group')
        }

        relations: List[AssetTagRelation] = []
        created_count = 0
        restored_count = 0
        skipped_count = 0

        with transaction.atomic():
            for tag in tags:
                relation = existing_relations.get(str(tag.id))
                if relation and not relation.is_deleted:
                    skipped_count += 1
                    relations.append(relation)
                    continue

                if relation and relation.is_deleted:
                    relation.is_deleted = False
                    relation.deleted_at = None
                    relation.deleted_by = None
                    relation.tagged_by = user if getattr(user, 'is_authenticated', False) else None
                    relation.tagged_at = timezone.now()
                    relation.notes = notes
                    if getattr(user, 'is_authenticated', False):
                        relation.updated_by = user
                    relation.save(
                        update_fields=[
                            'is_deleted',
                            'deleted_at',
                            'deleted_by',
                            'tagged_by',
                            'tagged_at',
                            'notes',
                            'updated_by',
                            'updated_at',
                        ]
                    )
                    restored_count += 1
                    relations.append(relation)
                    continue

                relation = AssetTagRelation.objects.create(
                    organization_id=resolved_org_id,
                    asset=asset,
                    tag=tag,
                    tagged_by=user if getattr(user, 'is_authenticated', False) else None,
                    notes=notes,
                    created_by=user if getattr(user, 'is_authenticated', False) else None,
                )
                created_count += 1
                relations.append(relation)

        refreshed_relations = list(
            AssetTagRelation.all_objects.filter(
                id__in=[relation.id for relation in relations],
            ).select_related('tag', 'tag__tag_group', 'tagged_by')
        )

        return {
            'asset': asset,
            'relations': refreshed_relations,
            'created_count': created_count,
            'restored_count': restored_count,
            'skipped_count': skipped_count,
        }

    def remove_tags_from_asset(
        self,
        *,
        asset: Asset,
        tag_ids: Sequence[str],
        user=None,
        organization_id=None,
    ) -> Dict[str, Any]:
        """Soft delete one or more active tag relations from an asset."""
        resolved_org_id = organization_id or asset.organization_id
        normalized_ids = _normalize_uuid_strings(tag_ids)
        relations = list(
            self._scope_queryset(
                AssetTagRelation.all_objects.filter(
                    asset=asset,
                    tag_id__in=normalized_ids,
                    is_deleted=False,
                ).select_related('tag'),
                organization_id=resolved_org_id,
                user=user,
            )
        )

        removed_count = 0
        with transaction.atomic():
            for relation in relations:
                relation.soft_delete(user=user)
                removed_count += 1

        return {
            'asset': asset,
            'removed_count': removed_count,
            'removed_tag_ids': [str(relation.tag_id) for relation in relations],
        }

    def batch_add_tags(
        self,
        *,
        asset_ids: Sequence[str],
        tag_ids: Sequence[str],
        user=None,
        notes: str = '',
        organization_id=None,
    ) -> Dict[str, Any]:
        """Apply one or more tags to multiple assets."""
        assets = self._get_assets(
            asset_ids=asset_ids,
            organization_id=organization_id,
            user=user,
        )
        normalized_tag_ids = _normalize_uuid_strings(tag_ids)

        results = []
        created_total = 0
        restored_total = 0
        skipped_total = 0

        for asset in assets:
            result = self.add_tags_to_asset(
                asset=asset,
                tag_ids=normalized_tag_ids,
                user=user,
                notes=notes,
                organization_id=organization_id or asset.organization_id,
            )
            created_total += result['created_count']
            restored_total += result['restored_count']
            skipped_total += result['skipped_count']
            results.append(
                {
                    'asset_id': asset.id,
                    'asset_code': asset.asset_code,
                    'tags_added': result['created_count'] + result['restored_count'],
                    'skipped': result['skipped_count'],
                }
            )

        return {
            'summary': {
                'total_assets': len(assets),
                'total_tags': len(normalized_tag_ids),
                'relations_created': created_total,
                'relations_restored': restored_total,
                'skipped': skipped_total,
            },
            'results': results,
        }

    def batch_remove_tags(
        self,
        *,
        asset_ids: Sequence[str],
        tag_ids: Sequence[str],
        user=None,
        organization_id=None,
    ) -> Dict[str, Any]:
        """Remove one or more tags from multiple assets."""
        assets = self._get_assets(
            asset_ids=asset_ids,
            organization_id=organization_id,
            user=user,
        )
        normalized_tag_ids = _normalize_uuid_strings(tag_ids)

        removed_total = 0
        results = []

        for asset in assets:
            result = self.remove_tags_from_asset(
                asset=asset,
                tag_ids=normalized_tag_ids,
                user=user,
                organization_id=organization_id or asset.organization_id,
            )
            removed_total += result['removed_count']
            results.append(
                {
                    'asset_id': asset.id,
                    'asset_code': asset.asset_code,
                    'tags_removed': result['removed_count'],
                }
            )

        return {
            'summary': {
                'total_assets': len(assets),
                'relations_removed': removed_total,
            },
            'results': results,
        }

    def get_assets_by_tags(
        self,
        *,
        tag_ids: Sequence[str],
        match_type: str = 'or',
        organization_id=None,
        user=None,
    ) -> QuerySet[Asset]:
        """Return assets that match the requested asset-tag criteria."""
        normalized_tag_ids = _normalize_uuid_strings(tag_ids)
        if not normalized_tag_ids:
            return self._scope_queryset(
                Asset.all_objects.filter(is_deleted=False),
                organization_id=organization_id,
                user=user,
            ).none()

        relation_filter = Q(
            asset_tag_relations__tag_id__in=normalized_tag_ids,
            asset_tag_relations__is_deleted=False,
            asset_tag_relations__tag__is_deleted=False,
            asset_tag_relations__tag__is_active=True,
        )
        queryset = self._scope_queryset(
            Asset.all_objects.filter(is_deleted=False),
            organization_id=organization_id,
            user=user,
        ).prefetch_related(
            Prefetch(
                'asset_tag_relations',
                queryset=AssetTagRelation.all_objects.filter(
                    is_deleted=False,
                    tag__is_deleted=False,
                    tag__is_active=True,
                ).select_related('tag', 'tag__tag_group'),
            )
        )

        if str(match_type or '').lower() == 'and':
            return queryset.annotate(
                matched_tag_count=Count(
                    'asset_tag_relations__tag',
                    filter=relation_filter,
                    distinct=True,
                ),
            ).filter(matched_tag_count=len(normalized_tag_ids)).distinct()

        return queryset.filter(relation_filter).distinct()
