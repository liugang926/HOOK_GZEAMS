"""Cross-domain closed-loop metrics adapters."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Iterable

from django.db.models import Count, Q
from django.utils import timezone

from apps.finance.models import FinanceVoucher
from apps.insurance.models import ClaimRecord, InsurancePolicy
from apps.inventory.models import InventoryDifference, InventoryFollowUp, InventoryTask
from apps.leasing.models import LeaseContract, RentPayment
from apps.projects.models import AssetProject


class ClosedLoopMetricsAdapter:
    """Base adapter for domain-specific closed-loop metrics aggregation."""

    object_code = ""
    object_name = ""
    primary_route = ""

    def build(self, *, window: dict[str, Any], organization_id, user=None) -> dict[str, Any]:
        """Build a normalized payload for a business object."""
        raise NotImplementedError

    def _build_result(
        self,
        *,
        summary: dict[str, Any],
        trend_points: list[dict[str, Any]],
        queues: list[dict[str, Any]],
        bottlenecks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "object_code": self.object_code,
            "object_name": self.object_name,
            "primary_route": self.primary_route,
            "summary": summary,
            "trend": {
                "bucket": "day",
                "points": trend_points,
            },
            "queues": queues,
            "bottlenecks": bottlenecks,
        }

    @staticmethod
    def _blank_trend_points(window: dict[str, Any]) -> dict[str, dict[str, Any]]:
        points: dict[str, dict[str, Any]] = {}
        current_day = window["start_date"]
        while current_day <= window["end_date"]:
            iso_day = current_day.isoformat()
            points[iso_day] = {
                "date": iso_day,
                "opened": 0,
                "closed": 0,
            }
            current_day += timedelta(days=1)
        return points

    @staticmethod
    def _serialize_trend_points(points: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        return [points[key] for key in sorted(points.keys())]

    @staticmethod
    def _increment_trend(points: dict[str, dict[str, Any]], value: Any, bucket: str) -> None:
        day_value = ClosedLoopMetricsAdapter._coerce_date(value)
        if not day_value:
            return
        entry = points.get(day_value.isoformat())
        if entry is not None:
            entry[bucket] += 1

    @staticmethod
    def _coerce_date(value: Any) -> date | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
        if isinstance(value, date):
            return value
        return None

    @staticmethod
    def _coerce_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if timezone.is_naive(value):
                return timezone.make_aware(value, timezone.get_current_timezone())
            return value
        if isinstance(value, date):
            naive_datetime = datetime.combine(value, time.min)
            return timezone.make_aware(naive_datetime, timezone.get_current_timezone())
        return None

    def _calculate_average_cycle_hours(
        self,
        records: Iterable[Any],
        *,
        start_resolver,
        end_resolver,
    ) -> float:
        total_seconds = 0.0
        counted = 0
        for record in records:
            started_at = self._coerce_datetime(start_resolver(record))
            ended_at = self._coerce_datetime(end_resolver(record))
            if not started_at or not ended_at or ended_at < started_at:
                continue
            total_seconds += (ended_at - started_at).total_seconds()
            counted += 1
        if counted == 0:
            return 0.0
        return round(total_seconds / counted / 3600, 2)

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100, 1)

    @staticmethod
    def _build_summary(
        *,
        opened_count: int,
        closed_count: int,
        backlog_count: int,
        overdue_count: int,
        auto_closed_count: int,
        exception_backlog_count: int,
        avg_cycle_hours: float,
    ) -> dict[str, Any]:
        return {
            "opened_count": opened_count,
            "closed_count": closed_count,
            "backlog_count": backlog_count,
            "overdue_count": overdue_count,
            "auto_closed_count": auto_closed_count,
            "exception_backlog_count": exception_backlog_count,
            "avg_cycle_hours": avg_cycle_hours,
            "closure_rate": ClosedLoopMetricsAdapter._rate(closed_count, opened_count),
            "overdue_rate": ClosedLoopMetricsAdapter._rate(overdue_count, backlog_count),
            "automatic_closure_rate": ClosedLoopMetricsAdapter._rate(auto_closed_count, closed_count),
        }

    @staticmethod
    def _build_queue(*, code: str, label: str, count: int, route: str, tone: str = "info") -> dict[str, Any] | None:
        if count <= 0:
            return None
        return {
            "code": code,
            "label": label,
            "count": count,
            "route": route,
            "tone": tone,
        }

    @staticmethod
    def _build_bottleneck(
        *,
        code: str,
        label: str,
        count: int,
        route: str,
        severity: str = "medium",
        metric_type: str = "backlog",
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if count <= 0:
            return None
        payload = {
            "code": code,
            "label": label,
            "count": count,
            "route": route,
            "severity": severity,
            "metric_type": metric_type,
        }
        if extra:
            payload.update(extra)
        return payload


class AssetProjectMetricsAdapter(ClosedLoopMetricsAdapter):
    """Operational metrics adapter for asset projects."""

    object_code = "AssetProject"
    object_name = "Asset Projects"
    primary_route = "/objects/AssetProject"

    def build(self, *, window: dict[str, Any], organization_id, user=None) -> dict[str, Any]:
        projects = AssetProject.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
        )
        opened_qs = projects.filter(
            created_at__date__gte=window["start_date"],
            created_at__date__lte=window["end_date"],
        )
        closed_qs = projects.filter(
            status__in=["completed", "cancelled"],
            actual_end_date__gte=window["start_date"],
            actual_end_date__lte=window["end_date"],
        )
        backlog_qs = projects.filter(status__in=["planning", "active", "suspended"])
        overdue_qs = backlog_qs.filter(end_date__isnull=False, end_date__lt=window["today"])
        active_count = projects.filter(status="active").count()
        suspended_count = projects.filter(status="suspended").count()

        trend_points = self._blank_trend_points(window)
        for created_at in opened_qs.values_list("created_at", flat=True):
            self._increment_trend(trend_points, created_at, "opened")
        for actual_end_date in closed_qs.values_list("actual_end_date", flat=True):
            self._increment_trend(trend_points, actual_end_date, "closed")

        summary = self._build_summary(
            opened_count=opened_qs.count(),
            closed_count=closed_qs.count(),
            backlog_count=backlog_qs.count(),
            overdue_count=overdue_qs.count(),
            auto_closed_count=0,
            exception_backlog_count=overdue_qs.count(),
            avg_cycle_hours=self._calculate_average_cycle_hours(
                closed_qs.only("created_at", "actual_end_date"),
                start_resolver=lambda record: record.created_at,
                end_resolver=lambda record: record.actual_end_date,
            ),
        )
        queues = [
            self._build_queue(
                code="project_active",
                label="Active projects",
                count=active_count,
                route="/objects/AssetProject?status=active",
                tone="primary",
            ),
            self._build_queue(
                code="project_suspended",
                label="Suspended projects",
                count=suspended_count,
                route="/objects/AssetProject?status=suspended",
                tone="warning",
            ),
            self._build_queue(
                code="project_overdue",
                label="Projects overdue for closure",
                count=overdue_qs.count(),
                route="/objects/AssetProject?status=active",
                tone="danger",
            ),
        ]
        bottlenecks = [
            self._build_bottleneck(
                code="project_overdue",
                label="Projects overdue for closure",
                count=overdue_qs.count(),
                route="/objects/AssetProject?status=active",
                severity="high",
                metric_type="overdue",
            ),
        ]
        return self._build_result(
            summary=summary,
            trend_points=self._serialize_trend_points(trend_points),
            queues=[item for item in queues if item],
            bottlenecks=[item for item in bottlenecks if item],
        )


class InventoryTaskMetricsAdapter(ClosedLoopMetricsAdapter):
    """Operational metrics adapter for inventory tasks."""

    object_code = "InventoryTask"
    object_name = "Inventory Tasks"
    primary_route = "/objects/InventoryTask"

    def build(self, *, window: dict[str, Any], organization_id, user=None) -> dict[str, Any]:
        tasks = InventoryTask.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
        )
        differences = InventoryDifference.all_objects.filter(
            is_deleted=False,
            task__organization_id=organization_id,
        )
        opened_qs = tasks.filter(
            created_at__date__gte=window["start_date"],
            created_at__date__lte=window["end_date"],
        )
        closed_qs = tasks.filter(
            status=InventoryTask.STATUS_COMPLETED,
            completed_at__date__gte=window["start_date"],
            completed_at__date__lte=window["end_date"],
        )
        backlog_qs = tasks.filter(status__in=[InventoryTask.STATUS_PENDING, InventoryTask.STATUS_IN_PROGRESS])
        overdue_qs = backlog_qs.filter(planned_date__lt=window["today"])

        unresolved_difference_task_ids = differences.filter(
            status__in=[
                InventoryDifference.STATUS_PENDING,
                InventoryDifference.STATUS_CONFIRMED,
                InventoryDifference.STATUS_IN_REVIEW,
                InventoryDifference.STATUS_APPROVED,
                InventoryDifference.STATUS_EXECUTING,
            ]
        ).values_list("task_id", flat=True).distinct()
        manual_follow_up_task_ids = InventoryFollowUp.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status=InventoryFollowUp.STATUS_PENDING,
        ).values_list("task_id", flat=True).distinct()
        auto_closed_qs = closed_qs.annotate(
            difference_count=Count("differences", filter=Q(differences__is_deleted=False), distinct=True),
        ).filter(difference_count=0)

        trend_points = self._blank_trend_points(window)
        for created_at in opened_qs.values_list("created_at", flat=True):
            self._increment_trend(trend_points, created_at, "opened")
        for completed_at in closed_qs.values_list("completed_at", flat=True):
            self._increment_trend(trend_points, completed_at, "closed")

        unresolved_task_count = tasks.filter(id__in=unresolved_difference_task_ids).count()
        manual_follow_up_count = tasks.filter(id__in=manual_follow_up_task_ids).count()

        summary = self._build_summary(
            opened_count=opened_qs.count(),
            closed_count=closed_qs.count(),
            backlog_count=backlog_qs.count(),
            overdue_count=overdue_qs.count(),
            auto_closed_count=auto_closed_qs.count(),
            exception_backlog_count=unresolved_task_count,
            avg_cycle_hours=self._calculate_average_cycle_hours(
                closed_qs.only("created_at", "started_at", "completed_at"),
                start_resolver=lambda record: record.started_at or record.created_at,
                end_resolver=lambda record: record.completed_at,
            ),
        )
        queues = [
            self._build_queue(
                code="inventory_in_progress",
                label="Tasks in progress",
                count=tasks.filter(status=InventoryTask.STATUS_IN_PROGRESS).count(),
                route="/objects/InventoryTask?status=in_progress",
                tone="primary",
            ),
            self._build_queue(
                code="inventory_overdue",
                label="Tasks overdue",
                count=overdue_qs.count(),
                route="/objects/InventoryTask?status=in_progress",
                tone="danger",
            ),
            self._build_queue(
                code="inventory_unresolved_differences",
                label="Tasks with unresolved differences",
                count=unresolved_task_count,
                route="/objects/InventoryItem?unresolved_only=true",
                tone="warning",
            ),
            self._build_queue(
                code="inventory_manual_follow_up",
                label="Tasks awaiting manual follow-up",
                count=manual_follow_up_count,
                route="/objects/InventoryItem?manual_follow_up_only=true&unresolved_only=true",
                tone="warning",
            ),
        ]
        bottlenecks = [
            self._build_bottleneck(
                code="inventory_manual_follow_up",
                label="Inventory tasks awaiting manual follow-up",
                count=manual_follow_up_count,
                route="/objects/InventoryItem?manual_follow_up_only=true&unresolved_only=true",
                severity="high",
                metric_type="follow_up",
            ),
            self._build_bottleneck(
                code="inventory_overdue",
                label="Inventory tasks overdue",
                count=overdue_qs.count(),
                route="/objects/InventoryTask?status=in_progress",
                severity="high",
                metric_type="overdue",
            ),
        ]
        return self._build_result(
            summary=summary,
            trend_points=self._serialize_trend_points(trend_points),
            queues=[item for item in queues if item],
            bottlenecks=[item for item in bottlenecks if item],
        )


class FinanceVoucherMetricsAdapter(ClosedLoopMetricsAdapter):
    """Operational metrics adapter for finance vouchers."""

    object_code = "FinanceVoucher"
    object_name = "Finance Vouchers"
    primary_route = "/objects/FinanceVoucher"
    STALLED_AGE_DAYS = 7

    def build(self, *, window: dict[str, Any], organization_id, user=None) -> dict[str, Any]:
        vouchers = FinanceVoucher.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
        )
        opened_qs = vouchers.filter(
            created_at__date__gte=window["start_date"],
            created_at__date__lte=window["end_date"],
        )
        posted_closed_qs = vouchers.filter(
            status="posted",
            posted_at__date__gte=window["start_date"],
            posted_at__date__lte=window["end_date"],
        )
        rejected_closed_qs = vouchers.filter(
            status="rejected",
            updated_at__date__gte=window["start_date"],
            updated_at__date__lte=window["end_date"],
        )
        closed_count = posted_closed_qs.count() + rejected_closed_qs.count()
        backlog_qs = vouchers.filter(status__in=["draft", "submitted", "approved"])
        stalled_qs = backlog_qs.filter(created_at__lt=window["now"] - timedelta(days=self.STALLED_AGE_DAYS))

        trend_points = self._blank_trend_points(window)
        for created_at in opened_qs.values_list("created_at", flat=True):
            self._increment_trend(trend_points, created_at, "opened")
        for posted_at in posted_closed_qs.values_list("posted_at", flat=True):
            self._increment_trend(trend_points, posted_at, "closed")
        for updated_at in rejected_closed_qs.values_list("updated_at", flat=True):
            self._increment_trend(trend_points, updated_at, "closed")

        avg_cycle_hours = self._calculate_average_cycle_hours(
            list(posted_closed_qs.only("created_at", "posted_at")) + list(rejected_closed_qs.only("created_at", "updated_at")),
            start_resolver=lambda record: record.created_at,
            end_resolver=lambda record: getattr(record, "posted_at", None) or record.updated_at,
        )
        summary = self._build_summary(
            opened_count=opened_qs.count(),
            closed_count=closed_count,
            backlog_count=backlog_qs.count(),
            overdue_count=stalled_qs.count(),
            auto_closed_count=posted_closed_qs.exclude(erp_voucher_no="").count(),
            exception_backlog_count=stalled_qs.count(),
            avg_cycle_hours=avg_cycle_hours,
        )
        queues = [
            self._build_queue(
                code="finance_submitted",
                label="Submitted vouchers",
                count=vouchers.filter(status="submitted").count(),
                route="/objects/FinanceVoucher?status=submitted",
                tone="warning",
            ),
            self._build_queue(
                code="finance_approved",
                label="Approved vouchers pending posting",
                count=vouchers.filter(status="approved").count(),
                route="/objects/FinanceVoucher?status=approved",
                tone="primary",
            ),
            self._build_queue(
                code="finance_stalled",
                label="Stalled open vouchers",
                count=stalled_qs.count(),
                route="/objects/FinanceVoucher?status=approved",
                tone="danger",
            ),
        ]
        bottlenecks = [
            self._build_bottleneck(
                code="finance_stalled",
                label="Finance vouchers stalled before closure",
                count=stalled_qs.count(),
                route="/objects/FinanceVoucher?status=approved",
                severity="high",
                metric_type="overdue",
            ),
        ]
        return self._build_result(
            summary=summary,
            trend_points=self._serialize_trend_points(trend_points),
            queues=[item for item in queues if item],
            bottlenecks=[item for item in bottlenecks if item],
        )


class InsurancePolicyMetricsAdapter(ClosedLoopMetricsAdapter):
    """Operational metrics adapter for insurance policies."""

    object_code = "InsurancePolicy"
    object_name = "Insurance Policies"
    primary_route = "/objects/InsurancePolicy"
    EXPIRING_WINDOW_DAYS = 30

    def build(self, *, window: dict[str, Any], organization_id, user=None) -> dict[str, Any]:
        policies = InsurancePolicy.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
        )
        opened_qs = policies.filter(
            created_at__date__gte=window["start_date"],
            created_at__date__lte=window["end_date"],
        )
        backlog_qs = policies.filter(status__in=["draft", "active"])
        overdue_qs = policies.filter(status="active", end_date__lt=window["today"])
        expiring_qs = policies.filter(
            status="active",
            end_date__gte=window["today"],
            end_date__lte=window["today"] + timedelta(days=self.EXPIRING_WINDOW_DAYS),
        )
        terminal_qs = policies.filter(status__in=["expired", "cancelled", "terminated", "renewed"])

        trend_points = self._blank_trend_points(window)
        for created_at in opened_qs.values_list("created_at", flat=True):
            self._increment_trend(trend_points, created_at, "opened")

        closed_records = []
        for policy in terminal_qs.only("created_at", "updated_at", "end_date", "status"):
            closed_value = policy.updated_at if policy.status in {"cancelled", "terminated", "renewed"} else policy.end_date
            closed_day = self._coerce_date(closed_value)
            if closed_day and window["start_date"] <= closed_day <= window["end_date"]:
                closed_records.append(policy)
                self._increment_trend(trend_points, closed_value, "closed")

        summary = self._build_summary(
            opened_count=opened_qs.count(),
            closed_count=len(closed_records),
            backlog_count=backlog_qs.count(),
            overdue_count=overdue_qs.count(),
            auto_closed_count=0,
            exception_backlog_count=overdue_qs.count(),
            avg_cycle_hours=self._calculate_average_cycle_hours(
                closed_records,
                start_resolver=lambda record: record.created_at,
                end_resolver=lambda record: record.updated_at if record.status in {"cancelled", "terminated", "renewed"} else record.end_date,
            ),
        )
        queues = [
            self._build_queue(
                code="insurance_expiring_soon",
                label="Policies expiring within 30 days",
                count=expiring_qs.count(),
                route="/objects/InsurancePolicy?status=active",
                tone="warning",
            ),
            self._build_queue(
                code="insurance_overdue_renewal",
                label="Policies overdue for renewal",
                count=overdue_qs.count(),
                route="/objects/InsurancePolicy?status=active",
                tone="danger",
            ),
        ]
        bottlenecks = [
            self._build_bottleneck(
                code="insurance_overdue_renewal",
                label="Policies overdue for renewal",
                count=overdue_qs.count(),
                route="/objects/InsurancePolicy?status=active",
                severity="high",
                metric_type="overdue",
            ),
        ]
        return self._build_result(
            summary=summary,
            trend_points=self._serialize_trend_points(trend_points),
            queues=[item for item in queues if item],
            bottlenecks=[item for item in bottlenecks if item],
        )


class ClaimRecordMetricsAdapter(ClosedLoopMetricsAdapter):
    """Operational metrics adapter for insurance claims."""

    object_code = "ClaimRecord"
    object_name = "Claim Records"
    primary_route = "/objects/ClaimRecord"
    STALE_AGE_DAYS = 7

    def build(self, *, window: dict[str, Any], organization_id, user=None) -> dict[str, Any]:
        claims = ClaimRecord.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
        )
        opened_qs = claims.filter(
            created_at__date__gte=window["start_date"],
            created_at__date__lte=window["end_date"],
        )
        backlog_qs = claims.filter(status__in=["reported", "investigating", "approved"])
        stale_qs = backlog_qs.filter(created_at__lt=window["now"] - timedelta(days=self.STALE_AGE_DAYS))
        terminal_qs = claims.filter(status__in=["paid", "closed", "rejected"])

        trend_points = self._blank_trend_points(window)
        for created_at in opened_qs.values_list("created_at", flat=True):
            self._increment_trend(trend_points, created_at, "opened")

        closed_records = []
        for claim in terminal_qs.only("created_at", "updated_at", "settlement_date", "paid_date", "status"):
            closed_value = claim.settlement_date or claim.paid_date or claim.updated_at
            closed_day = self._coerce_date(closed_value)
            if closed_day and window["start_date"] <= closed_day <= window["end_date"]:
                closed_records.append(claim)
                self._increment_trend(trend_points, closed_value, "closed")

        summary = self._build_summary(
            opened_count=opened_qs.count(),
            closed_count=len(closed_records),
            backlog_count=backlog_qs.count(),
            overdue_count=stale_qs.count(),
            auto_closed_count=0,
            exception_backlog_count=backlog_qs.count(),
            avg_cycle_hours=self._calculate_average_cycle_hours(
                closed_records,
                start_resolver=lambda record: record.created_at,
                end_resolver=lambda record: record.settlement_date or record.paid_date or record.updated_at,
            ),
        )
        queues = [
            self._build_queue(
                code="claim_investigating",
                label="Claims under investigation",
                count=claims.filter(status="investigating").count(),
                route="/objects/ClaimRecord?status=investigating",
                tone="warning",
            ),
            self._build_queue(
                code="claim_approved_unpaid",
                label="Approved claims pending settlement",
                count=claims.filter(status="approved").count(),
                route="/objects/ClaimRecord?status=approved",
                tone="primary",
            ),
            self._build_queue(
                code="claim_stale",
                label="Claims exceeding handling SLA",
                count=stale_qs.count(),
                route="/objects/ClaimRecord?status=investigating",
                tone="danger",
            ),
        ]
        bottlenecks = [
            self._build_bottleneck(
                code="claim_stale",
                label="Claims exceeding handling SLA",
                count=stale_qs.count(),
                route="/objects/ClaimRecord?status=investigating",
                severity="high",
                metric_type="overdue",
            ),
        ]
        return self._build_result(
            summary=summary,
            trend_points=self._serialize_trend_points(trend_points),
            queues=[item for item in queues if item],
            bottlenecks=[item for item in bottlenecks if item],
        )


class LeasingContractMetricsAdapter(ClosedLoopMetricsAdapter):
    """Operational metrics adapter for lease contracts."""

    object_code = "LeasingContract"
    object_name = "Leasing Contracts"
    primary_route = "/objects/LeasingContract"
    EXPIRING_WINDOW_DAYS = 30

    def build(self, *, window: dict[str, Any], organization_id, user=None) -> dict[str, Any]:
        contracts = LeaseContract.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
        )
        overdue_payment_contract_ids = RentPayment.all_objects.filter(
            is_deleted=False,
            contract__organization_id=organization_id,
            status__in=["pending", "partial", "overdue"],
            due_date__lt=window["today"],
        ).values_list("contract_id", flat=True).distinct()

        opened_qs = contracts.filter(
            created_at__date__gte=window["start_date"],
            created_at__date__lte=window["end_date"],
        )
        closed_qs = contracts.filter(
            status__in=["completed", "terminated"],
            actual_end_date__gte=window["start_date"],
            actual_end_date__lte=window["end_date"],
        )
        backlog_qs = contracts.filter(status__in=["draft", "active", "suspended"])
        overdue_qs = contracts.filter(
            Q(status="overdue")
            | Q(id__in=overdue_payment_contract_ids)
            | Q(status__in=["active", "suspended"], end_date__lt=window["today"])
        ).distinct()
        expiring_qs = contracts.filter(
            status="active",
            end_date__gte=window["today"],
            end_date__lte=window["today"] + timedelta(days=self.EXPIRING_WINDOW_DAYS),
        )

        trend_points = self._blank_trend_points(window)
        for created_at in opened_qs.values_list("created_at", flat=True):
            self._increment_trend(trend_points, created_at, "opened")
        for actual_end_date in closed_qs.values_list("actual_end_date", flat=True):
            self._increment_trend(trend_points, actual_end_date, "closed")

        summary = self._build_summary(
            opened_count=opened_qs.count(),
            closed_count=closed_qs.count(),
            backlog_count=backlog_qs.count(),
            overdue_count=overdue_qs.count(),
            auto_closed_count=0,
            exception_backlog_count=overdue_qs.count(),
            avg_cycle_hours=self._calculate_average_cycle_hours(
                closed_qs.only("created_at", "actual_end_date"),
                start_resolver=lambda record: record.created_at,
                end_resolver=lambda record: record.actual_end_date,
            ),
        )
        queues = [
            self._build_queue(
                code="leasing_active",
                label="Active contracts",
                count=contracts.filter(status="active").count(),
                route="/objects/LeasingContract?status=active",
                tone="primary",
            ),
            self._build_queue(
                code="leasing_expiring_soon",
                label="Contracts expiring within 30 days",
                count=expiring_qs.count(),
                route="/objects/LeasingContract?status=active",
                tone="warning",
            ),
            self._build_queue(
                code="leasing_overdue",
                label="Contracts with overdue payments",
                count=overdue_qs.count(),
                route="/objects/LeasingContract?status=active",
                tone="danger",
            ),
        ]
        bottlenecks = [
            self._build_bottleneck(
                code="leasing_overdue",
                label="Leasing contracts with overdue payments",
                count=overdue_qs.count(),
                route="/objects/LeasingContract?status=active",
                severity="high",
                metric_type="overdue",
            ),
        ]
        return self._build_result(
            summary=summary,
            trend_points=self._serialize_trend_points(trend_points),
            queues=[item for item in queues if item],
            bottlenecks=[item for item in bottlenecks if item],
        )
