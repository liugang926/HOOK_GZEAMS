"""Closed-loop operational metrics aggregation service."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import Coalesce

from apps.accounts.models import User
from apps.finance.models import FinanceVoucher
from apps.insurance.models import ClaimRecord, InsurancePolicy
from apps.inventory.models import InventoryDifference
from apps.leasing.models import LeaseContract
from apps.organizations.models import UserDepartment
from apps.projects.models import AssetProject
from apps.system.services.metrics_adapters import DEFAULT_CLOSED_LOOP_METRICS_ADAPTERS
from apps.workflows.models import WorkflowTask
from apps.workflows.services.sla_service import SLAService


class ClosedLoopMetricsService:
    """Aggregate standardized closed-loop metrics across business domains."""

    RANKING_SOURCE_KEYS = (
        "workflow_tasks",
        "inventory_differences",
        "projects",
        "finance_vouchers",
        "insurance_policies",
        "claim_records",
        "leasing_contracts",
    )

    WINDOW_DAY_MAP = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
    }

    METRIC_CONTRACT = {
        "opened_count": "Records created in the selected time window.",
        "closed_count": "Records reaching a terminal closure state in the selected time window.",
        "backlog_count": "Records still in an open or processing state.",
        "overdue_count": "Open records exceeding a domain-specific due or SLA threshold.",
        "auto_closed_count": "Closed records completed without manual exception handling when the domain supports it.",
        "exception_backlog_count": "Open exception items still requiring review, execution, or follow-up.",
        "avg_cycle_hours": "Average elapsed hours from opening to closure for records closed in the selected window.",
        "closure_rate": "Closed records divided by opened records in the selected window.",
        "overdue_rate": "Overdue records divided by open backlog.",
        "automatic_closure_rate": "Automatically closed records divided by all closed records.",
    }

    def __init__(self, adapter_classes=None):
        self.adapter_classes = adapter_classes or DEFAULT_CLOSED_LOOP_METRICS_ADAPTERS
        self.adapters = [adapter_class() for adapter_class in self.adapter_classes]
        self.sla_service = SLAService()

    def build_overview(self, *, window_key="30d", organization_id, user=None, object_codes=None) -> dict[str, Any]:
        window = self.build_window(window_key)
        object_results = self._collect_object_results(
            window=window,
            organization_id=organization_id,
            user=user,
            object_codes=object_codes,
        )
        overview_summary = self._build_aggregated_summary(object_results)
        workflow_summary = self._build_workflow_sla_summary(window=window, organization_id=organization_id)

        return {
            "window": window["payload"],
            "metric_contract": self.METRIC_CONTRACT,
            "summary": overview_summary,
            "trend": {
                "bucket": "day",
                "points": self._aggregate_trend_points(window=window, object_results=object_results),
            },
            "workflow_sla": workflow_summary,
            "owner_rankings": self._build_owner_rankings(window=window, organization_id=organization_id),
            "department_rankings": self._build_department_rankings(window=window, organization_id=organization_id),
            "objects_covered": [
                {
                    "object_code": entry["object_code"],
                    "object_name": entry["object_name"],
                    "primary_route": entry["primary_route"],
                }
                for entry in object_results
            ],
        }

    def build_by_object(self, *, window_key="30d", organization_id, user=None, object_codes=None) -> dict[str, Any]:
        window = self.build_window(window_key)
        results = self._collect_object_results(
            window=window,
            organization_id=organization_id,
            user=user,
            object_codes=object_codes,
        )
        return {
            "window": window["payload"],
            "results": results,
        }

    def build_queues(self, *, window_key="30d", organization_id, user=None, object_codes=None) -> dict[str, Any]:
        window = self.build_window(window_key)
        object_results = self._collect_object_results(
            window=window,
            organization_id=organization_id,
            user=user,
            object_codes=object_codes,
        )
        queues: list[dict[str, Any]] = []
        for entry in object_results:
            for queue in entry["queues"]:
                queues.append({
                    "source_type": "object",
                    "object_code": entry["object_code"],
                    "object_name": entry["object_name"],
                    **queue,
                })

        queues.sort(key=lambda item: (-int(item.get("count") or 0), item.get("object_code") or "", item.get("code") or ""))
        return {
            "window": window["payload"],
            "results": queues,
        }

    def build_bottlenecks(self, *, window_key="30d", organization_id, user=None, object_codes=None) -> dict[str, Any]:
        window = self.build_window(window_key)
        object_results = self._collect_object_results(
            window=window,
            organization_id=organization_id,
            user=user,
            object_codes=object_codes,
        )
        bottlenecks: list[dict[str, Any]] = []
        for entry in object_results:
            for bottleneck in entry["bottlenecks"]:
                bottlenecks.append({
                    "source_type": "object",
                    "object_code": entry["object_code"],
                    "object_name": entry["object_name"],
                    **bottleneck,
                })

        workflow_bottlenecks = self.sla_service.get_bottleneck_report(
            days=window["days"],
            organization_id=organization_id,
        )
        for bottleneck in workflow_bottlenecks:
            bottlenecks.append({
                "source_type": "workflow",
                "object_code": "WorkflowTask",
                "object_name": "Workflow Tasks",
                "code": f"workflow::{bottleneck['workflow_definition_id']}::{bottleneck['node_id']}",
                "label": bottleneck["node_name"],
                "count": int(bottleneck.get("task_count") or 0),
                "route": "/workflow/dashboard",
                "severity": bottleneck.get("severity") or "none",
                "metric_type": "workflow_sla",
                "workflow_definition_id": bottleneck["workflow_definition_id"],
                "workflow_name": bottleneck["workflow_name"],
                "node_id": bottleneck["node_id"],
                "avg_duration_hours": float(bottleneck.get("avg_duration_hours") or 0),
                "sla_hours": float(bottleneck.get("sla_hours") or 0),
                "sla_compliance_rate": float(bottleneck.get("sla_compliance_rate") or 0),
            })

        bottlenecks.sort(
            key=lambda item: (
                -int(item.get("count") or 0),
                -float(item.get("avg_duration_hours") or 0),
                item.get("object_code") or "",
            )
        )
        return {
            "window": window["payload"],
            "results": bottlenecks,
        }

    def build_window(self, window_key: str | None) -> dict[str, Any]:
        normalized_key = self.normalize_window_key(window_key)
        days = self.WINDOW_DAY_MAP[normalized_key]
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)
        start_datetime = timezone.make_aware(
            datetime.combine(start_date, time.min),
            timezone.get_current_timezone(),
        )
        end_datetime = timezone.make_aware(
            datetime.combine(today, time.max),
            timezone.get_current_timezone(),
        )
        now = timezone.now()
        return {
            "key": normalized_key,
            "days": days,
            "today": today,
            "start_date": start_date,
            "end_date": today,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "now": now,
            "payload": {
                "key": normalized_key,
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": today.isoformat(),
            },
        }

    def normalize_window_key(self, window_key: str | None) -> str:
        normalized = str(window_key or "").strip().lower()
        if normalized in self.WINDOW_DAY_MAP:
            return normalized
        return "30d"

    def _collect_object_results(self, *, window: dict[str, Any], organization_id, user=None, object_codes=None) -> list[dict[str, Any]]:
        selected_codes = None
        if object_codes:
            selected_codes = {str(code).strip() for code in object_codes if str(code).strip()}

        results = []
        for adapter in self.adapters:
            if selected_codes and adapter.object_code not in selected_codes:
                continue
            results.append(
                adapter.build(
                    window=window,
                    organization_id=organization_id,
                    user=user,
                )
            )
        return results

    def _aggregate_trend_points(self, *, window: dict[str, Any], object_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

        for result in object_results:
            for point in result["trend"]["points"]:
                bucket = points.get(point["date"])
                if not bucket:
                    continue
                bucket["opened"] += int(point.get("opened") or 0)
                bucket["closed"] += int(point.get("closed") or 0)

        return [points[key] for key in sorted(points.keys())]

    def _build_aggregated_summary(self, object_results: list[dict[str, Any]]) -> dict[str, Any]:
        opened_count = 0
        closed_count = 0
        backlog_count = 0
        overdue_count = 0
        auto_closed_count = 0
        exception_backlog_count = 0
        weighted_cycle_seconds = 0.0

        for result in object_results:
            summary = result["summary"]
            opened_count += int(summary.get("opened_count") or 0)
            closed_count += int(summary.get("closed_count") or 0)
            backlog_count += int(summary.get("backlog_count") or 0)
            overdue_count += int(summary.get("overdue_count") or 0)
            auto_closed_count += int(summary.get("auto_closed_count") or 0)
            exception_backlog_count += int(summary.get("exception_backlog_count") or 0)
            weighted_cycle_seconds += float(summary.get("avg_cycle_hours") or 0) * int(summary.get("closed_count") or 0) * 3600

        avg_cycle_hours = 0.0
        if closed_count > 0:
            avg_cycle_hours = round(weighted_cycle_seconds / closed_count / 3600, 2)

        return {
            "opened_count": opened_count,
            "closed_count": closed_count,
            "backlog_count": backlog_count,
            "overdue_count": overdue_count,
            "auto_closed_count": auto_closed_count,
            "exception_backlog_count": exception_backlog_count,
            "avg_cycle_hours": avg_cycle_hours,
            "closure_rate": self._rate(closed_count, opened_count),
            "overdue_rate": self._rate(overdue_count, backlog_count),
            "automatic_closure_rate": self._rate(auto_closed_count, closed_count),
        }

    def _build_workflow_sla_summary(self, *, window: dict[str, Any], organization_id) -> dict[str, Any]:
        active_tasks = WorkflowTask.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status="pending",
        )
        overdue_tasks = active_tasks.filter(due_date__lt=window["now"])
        escalated_tasks = active_tasks.filter(
            created_at__lt=window["now"] - timedelta(hours=self.sla_service.DEFAULT_ESCALATION_HOURS),
        )
        bottlenecks = self.sla_service.get_bottleneck_report(
            days=window["days"],
            organization_id=organization_id,
        )
        return {
            "active_task_count": active_tasks.count(),
            "overdue_task_count": overdue_tasks.count(),
            "escalated_task_count": escalated_tasks.count(),
            "bottleneck_count": len(bottlenecks),
        }

    def _build_owner_rankings(self, *, window: dict[str, Any], organization_id) -> list[dict[str, Any]]:
        rankings: dict[str, dict[str, Any]] = {}

        def ensure_entry(user_id: str) -> dict[str, Any]:
            key = str(user_id)
            entry = rankings.get(key)
            if entry is None:
                entry = {
                    "user_id": key,
                    "open_count": 0,
                    "overdue_count": 0,
                    "source_counts": self._empty_source_counts(),
                }
                rankings[key] = entry
            return entry

        def accumulate(rows, *, user_key: str, source_key: str, count_key: str = "total", overdue: bool = False):
            for row in rows:
                user_id = row.get(user_key)
                if not user_id:
                    continue
                count = int(row.get(count_key) or 0)
                if count <= 0:
                    continue
                entry = ensure_entry(str(user_id))
                if overdue:
                    entry["overdue_count"] += count
                else:
                    entry["open_count"] += count
                    entry["source_counts"][source_key] += count

        workflow_open_rows = WorkflowTask.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status="pending",
            assignee_id__isnull=False,
        ).values("assignee_id").annotate(total=Count("id"))
        accumulate(workflow_open_rows, user_key="assignee_id", source_key="workflow_tasks")

        workflow_overdue_rows = WorkflowTask.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status="pending",
            assignee_id__isnull=False,
            due_date__lt=window["now"],
        ).values("assignee_id").annotate(total=Count("id"))
        accumulate(workflow_overdue_rows, user_key="assignee_id", source_key="workflow_tasks", overdue=True)

        unresolved_difference_rows = InventoryDifference.all_objects.filter(
            is_deleted=False,
            task__organization_id=organization_id,
            status__in=[
                InventoryDifference.STATUS_PENDING,
                InventoryDifference.STATUS_CONFIRMED,
                InventoryDifference.STATUS_IN_REVIEW,
                InventoryDifference.STATUS_APPROVED,
                InventoryDifference.STATUS_EXECUTING,
            ],
        ).annotate(
            responsible_user_id=Coalesce("owner_id", "created_by_id"),
        ).values("responsible_user_id").annotate(total=Count("id"))
        accumulate(
            unresolved_difference_rows,
            user_key="responsible_user_id",
            source_key="inventory_differences",
        )

        stale_difference_rows = InventoryDifference.all_objects.filter(
            is_deleted=False,
            task__organization_id=organization_id,
            status__in=[
                InventoryDifference.STATUS_PENDING,
                InventoryDifference.STATUS_CONFIRMED,
                InventoryDifference.STATUS_IN_REVIEW,
                InventoryDifference.STATUS_APPROVED,
                InventoryDifference.STATUS_EXECUTING,
            ],
            created_at__lt=window["now"] - timedelta(days=7),
        ).annotate(
            responsible_user_id=Coalesce("owner_id", "created_by_id"),
        ).values("responsible_user_id").annotate(total=Count("id"))
        accumulate(
            stale_difference_rows,
            user_key="responsible_user_id",
            source_key="inventory_differences",
            overdue=True,
        )

        project_open_rows = AssetProject.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["planning", "active", "suspended"],
            project_manager_id__isnull=False,
        ).values("project_manager_id").annotate(total=Count("id"))
        accumulate(project_open_rows, user_key="project_manager_id", source_key="projects")

        project_overdue_rows = AssetProject.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["active", "suspended"],
            project_manager_id__isnull=False,
            end_date__isnull=False,
            end_date__lt=window["today"],
        ).values("project_manager_id").annotate(total=Count("id"))
        accumulate(
            project_overdue_rows,
            user_key="project_manager_id",
            source_key="projects",
            overdue=True,
        )

        finance_open_rows = FinanceVoucher.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["draft", "submitted", "approved"],
            created_by_id__isnull=False,
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate(finance_open_rows, user_key="created_by_id", source_key="finance_vouchers")

        finance_overdue_rows = FinanceVoucher.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["draft", "submitted", "approved"],
            created_by_id__isnull=False,
            created_at__lt=window["now"] - timedelta(days=7),
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate(
            finance_overdue_rows,
            user_key="created_by_id",
            source_key="finance_vouchers",
            overdue=True,
        )

        policy_open_rows = InsurancePolicy.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["draft", "active"],
            created_by_id__isnull=False,
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate(policy_open_rows, user_key="created_by_id", source_key="insurance_policies")

        policy_overdue_rows = InsurancePolicy.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status="active",
            created_by_id__isnull=False,
            end_date__lt=window["today"],
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate(
            policy_overdue_rows,
            user_key="created_by_id",
            source_key="insurance_policies",
            overdue=True,
        )

        claim_open_rows = ClaimRecord.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["reported", "investigating", "approved"],
            created_by_id__isnull=False,
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate(claim_open_rows, user_key="created_by_id", source_key="claim_records")

        claim_overdue_rows = ClaimRecord.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["reported", "investigating", "approved"],
            created_by_id__isnull=False,
            created_at__lt=window["now"] - timedelta(days=7),
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate(
            claim_overdue_rows,
            user_key="created_by_id",
            source_key="claim_records",
            overdue=True,
        )

        lease_open_rows = LeaseContract.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["draft", "active", "suspended"],
            created_by_id__isnull=False,
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate(lease_open_rows, user_key="created_by_id", source_key="leasing_contracts")

        lease_overdue_rows = LeaseContract.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["active", "suspended", "overdue"],
            created_by_id__isnull=False,
            end_date__lt=window["today"],
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate(
            lease_overdue_rows,
            user_key="created_by_id",
            source_key="leasing_contracts",
            overdue=True,
        )

        if not rankings:
            return []

        users = {
            str(user.id): user
            for user in User.all_objects.filter(id__in=list(rankings.keys()))
        }

        ranking_rows = []
        for user_id, entry in rankings.items():
            user = users.get(user_id)
            display_name = self._resolve_user_display_name(user)
            source_counts = {
                key: int(value)
                for key, value in entry["source_counts"].items()
                if int(value) > 0
            }
            top_source = ""
            if source_counts:
                top_source = max(source_counts.items(), key=lambda item: item[1])[0]

            ranking_rows.append({
                "user_id": user_id,
                "username": str(getattr(user, "username", "") or "").strip(),
                "display_name": display_name,
                "open_count": int(entry["open_count"]),
                "overdue_count": int(entry["overdue_count"]),
                "top_source": top_source,
                "source_counts": source_counts,
            })

        ranking_rows.sort(
            key=lambda item: (
                -int(item["overdue_count"]),
                -int(item["open_count"]),
                item["display_name"],
                item["username"],
            )
        )
        return ranking_rows[:10]

    def _build_department_rankings(self, *, window: dict[str, Any], organization_id) -> list[dict[str, Any]]:
        rankings: dict[str, dict[str, Any]] = {}

        def ensure_entry(department_id: str, department_name: str) -> dict[str, Any]:
            key = str(department_id)
            entry = rankings.get(key)
            if entry is None:
                entry = {
                    "department_id": key,
                    "department_name": str(department_name or "").strip(),
                    "open_count": 0,
                    "overdue_count": 0,
                    "source_counts": self._empty_source_counts(),
                }
                rankings[key] = entry
            elif department_name and not entry["department_name"]:
                entry["department_name"] = str(department_name).strip()
            return entry

        def accumulate_direct(rows, *, department_key: str, department_name_key: str, source_key: str, count_key: str = "total", overdue: bool = False):
            for row in rows:
                department_id = row.get(department_key)
                if not department_id:
                    continue
                count = int(row.get(count_key) or 0)
                if count <= 0:
                    continue
                entry = ensure_entry(str(department_id), str(row.get(department_name_key) or "").strip())
                if overdue:
                    entry["overdue_count"] += count
                else:
                    entry["open_count"] += count
                    entry["source_counts"][source_key] += count

        user_primary_department_map = self._build_primary_department_map(organization_id=organization_id)

        def accumulate_user(rows, *, user_key: str, source_key: str, count_key: str = "total", overdue: bool = False):
            for row in rows:
                user_id = row.get(user_key)
                if not user_id:
                    continue
                department_info = user_primary_department_map.get(str(user_id))
                if not department_info:
                    continue
                count = int(row.get(count_key) or 0)
                if count <= 0:
                    continue
                entry = ensure_entry(department_info["department_id"], department_info["department_name"])
                if overdue:
                    entry["overdue_count"] += count
                else:
                    entry["open_count"] += count
                    entry["source_counts"][source_key] += count

        workflow_open_rows = WorkflowTask.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status="pending",
            assignee_id__isnull=False,
        ).values("assignee_id").annotate(total=Count("id"))
        accumulate_user(workflow_open_rows, user_key="assignee_id", source_key="workflow_tasks")

        workflow_overdue_rows = WorkflowTask.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status="pending",
            assignee_id__isnull=False,
            due_date__lt=window["now"],
        ).values("assignee_id").annotate(total=Count("id"))
        accumulate_user(workflow_overdue_rows, user_key="assignee_id", source_key="workflow_tasks", overdue=True)

        direct_difference_rows = InventoryDifference.all_objects.filter(
            is_deleted=False,
            task__organization_id=organization_id,
            task__department_id__isnull=False,
            status__in=[
                InventoryDifference.STATUS_PENDING,
                InventoryDifference.STATUS_CONFIRMED,
                InventoryDifference.STATUS_IN_REVIEW,
                InventoryDifference.STATUS_APPROVED,
                InventoryDifference.STATUS_EXECUTING,
            ],
        ).values("task__department_id", "task__department__name").annotate(total=Count("id"))
        accumulate_direct(
            direct_difference_rows,
            department_key="task__department_id",
            department_name_key="task__department__name",
            source_key="inventory_differences",
        )

        fallback_difference_rows = InventoryDifference.all_objects.filter(
            is_deleted=False,
            task__organization_id=organization_id,
            task__department_id__isnull=True,
            status__in=[
                InventoryDifference.STATUS_PENDING,
                InventoryDifference.STATUS_CONFIRMED,
                InventoryDifference.STATUS_IN_REVIEW,
                InventoryDifference.STATUS_APPROVED,
                InventoryDifference.STATUS_EXECUTING,
            ],
        ).annotate(
            responsible_user_id=Coalesce("owner_id", "created_by_id"),
        ).values("responsible_user_id").annotate(total=Count("id"))
        accumulate_user(
            fallback_difference_rows,
            user_key="responsible_user_id",
            source_key="inventory_differences",
        )

        direct_stale_difference_rows = InventoryDifference.all_objects.filter(
            is_deleted=False,
            task__organization_id=organization_id,
            task__department_id__isnull=False,
            status__in=[
                InventoryDifference.STATUS_PENDING,
                InventoryDifference.STATUS_CONFIRMED,
                InventoryDifference.STATUS_IN_REVIEW,
                InventoryDifference.STATUS_APPROVED,
                InventoryDifference.STATUS_EXECUTING,
            ],
            created_at__lt=window["now"] - timedelta(days=7),
        ).values("task__department_id", "task__department__name").annotate(total=Count("id"))
        accumulate_direct(
            direct_stale_difference_rows,
            department_key="task__department_id",
            department_name_key="task__department__name",
            source_key="inventory_differences",
            overdue=True,
        )

        fallback_stale_difference_rows = InventoryDifference.all_objects.filter(
            is_deleted=False,
            task__organization_id=organization_id,
            task__department_id__isnull=True,
            status__in=[
                InventoryDifference.STATUS_PENDING,
                InventoryDifference.STATUS_CONFIRMED,
                InventoryDifference.STATUS_IN_REVIEW,
                InventoryDifference.STATUS_APPROVED,
                InventoryDifference.STATUS_EXECUTING,
            ],
            created_at__lt=window["now"] - timedelta(days=7),
        ).annotate(
            responsible_user_id=Coalesce("owner_id", "created_by_id"),
        ).values("responsible_user_id").annotate(total=Count("id"))
        accumulate_user(
            fallback_stale_difference_rows,
            user_key="responsible_user_id",
            source_key="inventory_differences",
            overdue=True,
        )

        project_open_rows = AssetProject.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["planning", "active", "suspended"],
            department_id__isnull=False,
        ).values("department_id", "department__name").annotate(total=Count("id"))
        accumulate_direct(
            project_open_rows,
            department_key="department_id",
            department_name_key="department__name",
            source_key="projects",
        )

        project_overdue_rows = AssetProject.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["active", "suspended"],
            department_id__isnull=False,
            end_date__isnull=False,
            end_date__lt=window["today"],
        ).values("department_id", "department__name").annotate(total=Count("id"))
        accumulate_direct(
            project_overdue_rows,
            department_key="department_id",
            department_name_key="department__name",
            source_key="projects",
            overdue=True,
        )

        finance_open_rows = FinanceVoucher.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["draft", "submitted", "approved"],
            created_by_id__isnull=False,
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate_user(finance_open_rows, user_key="created_by_id", source_key="finance_vouchers")

        finance_overdue_rows = FinanceVoucher.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["draft", "submitted", "approved"],
            created_by_id__isnull=False,
            created_at__lt=window["now"] - timedelta(days=7),
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate_user(
            finance_overdue_rows,
            user_key="created_by_id",
            source_key="finance_vouchers",
            overdue=True,
        )

        policy_open_rows = InsurancePolicy.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["draft", "active"],
            created_by_id__isnull=False,
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate_user(policy_open_rows, user_key="created_by_id", source_key="insurance_policies")

        policy_overdue_rows = InsurancePolicy.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status="active",
            created_by_id__isnull=False,
            end_date__lt=window["today"],
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate_user(
            policy_overdue_rows,
            user_key="created_by_id",
            source_key="insurance_policies",
            overdue=True,
        )

        claim_open_rows = ClaimRecord.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["reported", "investigating", "approved"],
            created_by_id__isnull=False,
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate_user(claim_open_rows, user_key="created_by_id", source_key="claim_records")

        claim_overdue_rows = ClaimRecord.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["reported", "investigating", "approved"],
            created_by_id__isnull=False,
            created_at__lt=window["now"] - timedelta(days=7),
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate_user(
            claim_overdue_rows,
            user_key="created_by_id",
            source_key="claim_records",
            overdue=True,
        )

        lease_open_rows = LeaseContract.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["draft", "active", "suspended"],
            created_by_id__isnull=False,
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate_user(lease_open_rows, user_key="created_by_id", source_key="leasing_contracts")

        lease_overdue_rows = LeaseContract.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            status__in=["active", "suspended", "overdue"],
            created_by_id__isnull=False,
            end_date__lt=window["today"],
        ).values("created_by_id").annotate(total=Count("id"))
        accumulate_user(
            lease_overdue_rows,
            user_key="created_by_id",
            source_key="leasing_contracts",
            overdue=True,
        )

        ranking_rows = []
        for department_id, entry in rankings.items():
            source_counts = {
                key: int(value)
                for key, value in entry["source_counts"].items()
                if int(value) > 0
            }
            top_source = ""
            if source_counts:
                top_source = max(source_counts.items(), key=lambda item: item[1])[0]

            ranking_rows.append({
                "department_id": department_id,
                "department_name": entry["department_name"],
                "open_count": int(entry["open_count"]),
                "overdue_count": int(entry["overdue_count"]),
                "top_source": top_source,
                "source_counts": source_counts,
            })

        ranking_rows.sort(
            key=lambda item: (
                -int(item["overdue_count"]),
                -int(item["open_count"]),
                item["department_name"],
            )
        )
        return ranking_rows[:10]

    @staticmethod
    def _build_primary_department_map(*, organization_id) -> dict[str, dict[str, str]]:
        mappings = {}
        user_departments = UserDepartment.all_objects.filter(
            is_deleted=False,
            organization_id=organization_id,
            is_primary=True,
            department_id__isnull=False,
        ).select_related("department")

        for membership in user_departments:
            department = getattr(membership, "department", None)
            if department is None:
                continue
            mappings[str(membership.user_id)] = {
                "department_id": str(department.id),
                "department_name": str(department.name or "").strip(),
            }
        return mappings

    @classmethod
    def _empty_source_counts(cls) -> dict[str, int]:
        return {key: 0 for key in cls.RANKING_SOURCE_KEYS}

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
    def _rate(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100, 1)
