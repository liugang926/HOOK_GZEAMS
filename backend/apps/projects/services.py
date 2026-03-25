"""
Services for asset project management models.
"""
from decimal import Decimal
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, Count, DateTimeField, Q, Sum, When
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.common.services.base_crud import BaseCRUDService

from .models import AssetProject, ProjectAsset, ProjectMember


class AssetProjectService(BaseCRUDService):
    """Service layer for asset project business logic."""

    RETURN_DASHBOARD_RANGE_DAYS = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
    }

    def __init__(self):
        super().__init__(AssetProject)

    def refresh_rollups(self, project_id, organization_id=None, user=None):
        """Refresh project allocation rollups and return the updated project."""
        project = self.get(project_id, organization_id=organization_id, user=user)
        project.refresh_rollups()
        return project

    def close_project(self, project_id, organization_id=None, user=None):
        """Close a project after all active allocations have been handled."""
        project = self.get(project_id, organization_id=organization_id, user=user)

        if project.status == "completed":
            raise ValidationError({
                "status": ["Project is already completed."]
            })

        active_allocations = project.project_assets.filter(
            is_deleted=False,
            return_status="in_use",
        ).count()
        if active_allocations > 0:
            raise ValidationError({
                "project_assets": [
                    f"{active_allocations} active project assets must be returned or transferred before closing the project."
                ]
            })

        project.status = "completed"
        project.actual_end_date = timezone.now().date()
        project.save(update_fields=["status", "actual_end_date", "updated_at"])
        return project

    def get_workspace_dashboard(self, project_id, organization_id=None, user=None):
        """Build a unified workspace overview payload for an asset project."""
        project = self.get(project_id, organization_id=organization_id, user=user)

        asset_aggregate = project.project_assets.filter(is_deleted=False).aggregate(
            total_count=Count("id"),
            in_use_count=Count("id", filter=Q(return_status="in_use")),
            returned_count=Count("id", filter=Q(return_status="returned")),
            transferred_count=Count("id", filter=Q(return_status="transferred")),
            allocation_cost_total=Sum("allocation_cost"),
        )
        member_aggregate = project.members.filter(is_deleted=False).aggregate(
            total_count=Count("id"),
            active_count=Count("id", filter=Q(is_active=True)),
            primary_count=Count("id", filter=Q(is_primary=True)),
            allocators_count=Count("id", filter=Q(is_active=True, can_allocate_asset=True)),
            cost_viewers_count=Count("id", filter=Q(is_active=True, can_view_cost=True)),
        )
        return_status_counts = self._build_group_count_map(
            self._get_project_return_queryset(project),
            "status",
        )

        asset_cost_total = asset_aggregate.get("allocation_cost_total") or Decimal("0")

        return {
            "project": {
                "project_code": project.project_code,
                "project_name": project.project_name,
                "project_alias": project.project_alias,
                "status": project.status,
                "status_label": project.get_status_display(),
                "project_type": project.project_type,
                "project_type_label": project.get_project_type_display(),
                "project_manager_name": self._resolve_user_display_name(project.project_manager),
                "department_name": str(getattr(project.department, "name", "") or "").strip(),
                "start_date": project.start_date.isoformat() if project.start_date else "",
                "end_date": project.end_date.isoformat() if project.end_date else "",
                "actual_start_date": project.actual_start_date.isoformat() if project.actual_start_date else "",
                "actual_end_date": project.actual_end_date.isoformat() if project.actual_end_date else "",
                "planned_budget": self._serialize_decimal(project.planned_budget),
                "actual_cost": self._serialize_decimal(project.actual_cost),
                "asset_cost": self._serialize_decimal(asset_cost_total),
                "completed_milestones": int(project.completed_milestones or 0),
                "total_milestones": int(project.total_milestones or 0),
                "progress": self._calculate_progress(project.completed_milestones, project.total_milestones),
                "is_overdue": self._is_project_overdue(project),
            },
            "assets": {
                "total_count": int(asset_aggregate.get("total_count") or 0),
                "in_use_count": int(asset_aggregate.get("in_use_count") or 0),
                "returned_count": int(asset_aggregate.get("returned_count") or 0),
                "transferred_count": int(asset_aggregate.get("transferred_count") or 0),
                "allocation_cost_total": self._serialize_decimal(asset_cost_total),
            },
            "members": {
                "total_count": int(member_aggregate.get("total_count") or 0),
                "active_count": int(member_aggregate.get("active_count") or 0),
                "primary_count": int(member_aggregate.get("primary_count") or 0),
                "allocators_count": int(member_aggregate.get("allocators_count") or 0),
                "cost_viewers_count": int(member_aggregate.get("cost_viewers_count") or 0),
            },
            "returns": {
                "pending_count": int(return_status_counts.get("pending", 0)),
                "completed_count": int(return_status_counts.get("completed", 0)),
                "rejected_count": int(return_status_counts.get("rejected", 0)),
                "processed_count": int(
                    return_status_counts.get("completed", 0)
                    + return_status_counts.get("rejected", 0)
                ),
            },
        }

    def get_return_dashboard(
        self,
        project_id,
        *,
        range_key="30d",
        organization_id=None,
        user=None,
    ):
        """Build aggregated return dashboard data for an asset project."""
        project = self.get(project_id, organization_id=organization_id, user=user)

        normalized_range_key = self._normalize_return_dashboard_range_key(range_key)
        range_days = self.RETURN_DASHBOARD_RANGE_DAYS[normalized_range_key]
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=range_days - 1)

        base_queryset = self._get_project_return_queryset(project)
        status_counts = self._build_group_count_map(base_queryset, "status")

        processed_at_expression = Case(
            When(
                status="completed",
                then=Coalesce("completed_at", "confirmed_at", "updated_at", "created_at"),
            ),
            When(
                status="rejected",
                then=Coalesce("updated_at", "created_at"),
            ),
            default=Coalesce("updated_at", "created_at"),
            output_field=DateTimeField(),
        )

        processed_queryset = base_queryset.filter(
            status__in=["completed", "rejected"],
        ).annotate(
            processed_at=processed_at_expression,
            processed_date=TruncDate(processed_at_expression),
        ).filter(
            processed_date__gte=start_date,
            processed_date__lte=end_date,
        )

        history_queryset = processed_queryset.annotate(
            items_count=Count("items", distinct=True),
        ).order_by("-processed_at", "-created_at")
        history_rows = list(history_queryset[:8])
        history_total_count = history_queryset.count()

        trend_rows = list(
            processed_queryset.values("processed_date").annotate(
                completed_count=Count("id", filter=Q(status="completed")),
                rejected_count=Count("id", filter=Q(status="rejected")),
                total_count=Count("id"),
            ).order_by("processed_date")
        )

        trend_points = []
        max_total_count = 0
        for row in trend_rows:
            processed_date = row.get("processed_date")
            total_count = int(row.get("total_count") or 0)
            max_total_count = max(max_total_count, total_count)
            trend_points.append({
                "date": processed_date.isoformat() if processed_date else "",
                "label": processed_date.strftime("%m-%d") if processed_date else "",
                "completed_count": int(row.get("completed_count") or 0),
                "rejected_count": int(row.get("rejected_count") or 0),
                "total_count": total_count,
            })

        return {
            "summary": {
                "pending_count": int(status_counts.get("pending", 0)),
                "completed_count": int(status_counts.get("completed", 0)),
                "rejected_count": int(status_counts.get("rejected", 0)),
                "processed_count": int(status_counts.get("completed", 0) + status_counts.get("rejected", 0)),
            },
            "history": {
                "total_count": history_total_count,
                "rows": [self._serialize_return_dashboard_row(row) for row in history_rows],
            },
            "trend": {
                "bucket": "day",
                "max_total_count": max_total_count,
                "points": trend_points,
            },
            "window": {
                "range_key": normalized_range_key,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        }

    def _normalize_return_dashboard_range_key(self, range_key) -> str:
        normalized = str(range_key or "").strip().lower()
        if normalized in self.RETURN_DASHBOARD_RANGE_DAYS:
            return normalized
        return "30d"

    @staticmethod
    def _build_group_count_map(queryset, field_name: str) -> dict[str, int]:
        rows = queryset.values(field_name).annotate(total=Count("id"))
        return {
            str(row.get(field_name) or ""): int(row.get("total") or 0)
            for row in rows
        }

    @staticmethod
    def _resolve_user_display_name(user) -> str:
        if user is None:
            return ""

        full_name_getter = getattr(user, "get_full_name", None)
        full_name = ""
        if callable(full_name_getter):
            full_name = str(full_name_getter() or "").strip()
        if full_name:
            return full_name
        return str(getattr(user, "username", "") or "").strip()

    @staticmethod
    def _serialize_decimal(value) -> str:
        amount = value if isinstance(value, Decimal) else Decimal(str(value or 0))
        return f"{amount.quantize(Decimal('0.01'))}"

    @staticmethod
    def _calculate_progress(completed_milestones, total_milestones) -> float:
        completed = int(completed_milestones or 0)
        total = int(total_milestones or 0)
        if total <= 0:
            return 0.0
        return round((completed / total) * 100, 2)

    @staticmethod
    def _is_project_overdue(project) -> bool:
        if not project.end_date:
            return False
        if project.status in {"completed", "cancelled"}:
            return False
        return project.end_date < timezone.now().date()

    @staticmethod
    def _get_project_return_queryset(project):
        from apps.assets.models import AssetReturn, ReturnItem

        linked_return_ids = ReturnItem.objects.filter(
            organization_id=project.organization_id,
            project_allocation__project_id=project.id,
            is_deleted=False,
            asset_return__is_deleted=False,
        ).values_list("asset_return_id", flat=True).distinct()

        return AssetReturn.objects.filter(
            organization_id=project.organization_id,
            is_deleted=False,
            id__in=linked_return_ids,
        ).select_related("returner", "return_location", "confirmed_by")

    @staticmethod
    def _serialize_return_dashboard_row(return_order):
        return {
            "id": str(return_order.id),
            "return_no": return_order.return_no,
            "status": return_order.status,
            "status_label": return_order.get_status_label(),
            "return_date": return_order.return_date.isoformat() if return_order.return_date else "",
            "items_count": int(getattr(return_order, "items_count", 0) or 0),
            "return_reason": return_order.return_reason,
            "reject_reason": return_order.reject_reason,
            "processed_at": (
                getattr(return_order, "processed_at", None).isoformat()
                if getattr(return_order, "processed_at", None)
                else ""
            ),
        }


class ProjectAssetService(BaseCRUDService):
    """Service layer for project asset allocation logic."""

    def __init__(self):
        super().__init__(ProjectAsset)

    @transaction.atomic
    def mark_returned(
        self,
        allocation_id,
        *,
        return_date=None,
        note="",
        organization_id=None,
        user=None,
    ):
        """Mark an active project allocation as returned."""
        allocation = self.get(allocation_id, organization_id=organization_id, user=user)

        if allocation.return_status != "in_use":
            raise ValidationError({
                "return_status": ["Only assets that are currently in use can be marked as returned."]
            })

        allocation.return_status = "returned"
        allocation.actual_return_date = return_date or timezone.now().date()

        normalized_note = str(note or "").strip()
        if normalized_note:
            allocation.notes = (
                f"{allocation.notes}\n{normalized_note}".strip()
                if allocation.notes
                else normalized_note
            )

        update_fields = ["return_status", "actual_return_date", "updated_at"]
        if normalized_note:
            update_fields.append("notes")
        allocation.save(update_fields=update_fields)
        return allocation

    @transaction.atomic
    def record_return_rejection(
        self,
        allocation_id,
        *,
        note="",
        organization_id=None,
        user=None,
    ):
        """Append return rejection audit information without changing allocation status."""
        allocation = self.get(allocation_id, organization_id=organization_id, user=user)

        normalized_note = str(note or "").strip()
        if not normalized_note:
            return allocation

        allocation.notes = (
            f"{allocation.notes}\n{normalized_note}".strip()
            if allocation.notes
            else normalized_note
        )
        allocation.save(update_fields=["notes", "updated_at"])
        return allocation

    @transaction.atomic
    def transfer_to_project(
        self,
        allocation_id,
        *,
        target_project_id,
        reason="",
        organization_id=None,
        user=None,
    ):
        """Transfer an active project allocation into another active project."""
        allocation = self.get(allocation_id, organization_id=organization_id, user=user)

        if allocation.return_status != "in_use":
            raise ValidationError({
                "return_status": ["Only assets that are currently in use can be transferred."]
            })

        target_queryset = AssetProject.objects.filter(is_deleted=False, id=target_project_id)
        if organization_id:
            target_queryset = target_queryset.filter(organization_id=organization_id)
        target_project = target_queryset.first()

        if target_project is None:
            raise ValidationError({
                "target_project_id": ["Target project does not exist in the current organization."]
            })

        if str(target_project.id) == str(allocation.project_id):
            raise ValidationError({
                "target_project_id": ["Target project must be different from the source project."]
            })

        if target_project.status != "active":
            raise ValidationError({
                "target_project_id": ["Target project must be active."]
            })

        operator = user or getattr(allocation, "allocated_by", None) or getattr(allocation, "created_by", None)
        transfer_reason = str(reason or "").strip()
        target_purpose = allocation.purpose or ""
        if transfer_reason:
            source_code = getattr(allocation.project, "project_code", str(allocation.project_id))
            target_purpose = f"Transferred from {source_code}: {transfer_reason}"

        target_notes = allocation.notes or ""
        if transfer_reason:
            target_notes = (
                f"{target_notes}\nTransfer reason: {transfer_reason}".strip()
                if target_notes
                else f"Transfer reason: {transfer_reason}"
            )

        new_allocation = ProjectAsset.objects.create(
            organization=target_project.organization,
            project=target_project,
            asset=allocation.asset,
            allocation_date=timezone.now().date(),
            allocation_type=allocation.allocation_type,
            allocated_by=operator,
            custodian=allocation.custodian,
            return_date=allocation.return_date,
            allocation_cost=allocation.allocation_cost,
            depreciation_rate=allocation.depreciation_rate,
            monthly_depreciation=allocation.monthly_depreciation,
            purpose=target_purpose,
            usage_location=allocation.usage_location,
            asset_snapshot=allocation.asset_snapshot,
            notes=target_notes,
            created_by=operator,
        )

        allocation.return_status = "transferred"
        allocation.actual_return_date = timezone.now().date()
        if transfer_reason:
            allocation.notes = (
                f"{allocation.notes}\nTransferred to {target_project.project_code}: {transfer_reason}".strip()
                if allocation.notes
                else f"Transferred to {target_project.project_code}: {transfer_reason}"
            )
        allocation.save(update_fields=["return_status", "actual_return_date", "notes", "updated_at"])

        return new_allocation


class ProjectMemberService(BaseCRUDService):
    """Service layer for project membership management."""

    def __init__(self):
        super().__init__(ProjectMember)
