from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserOrganization
from apps.finance.models import FinanceVoucher
from apps.insurance.models import ClaimRecord, InsuranceCompany, InsurancePolicy
from apps.inventory.models import InventoryDifference, InventoryTask
from apps.leasing.models import LeaseContract, RentPayment
from apps.organizations.models import Department, Organization, UserDepartment
from apps.projects.models import AssetProject
from apps.system.models import ClosedLoopDashboardSnapshot
from apps.workflows.models import WorkflowDefinition, WorkflowInstance, WorkflowTask


def _read_key(payload, snake_key, camel_key=None, default=None):
    candidate = camel_key or "".join(
        [snake_key.split("_")[0]] + [part.title() for part in snake_key.split("_")[1:]]
    )
    if isinstance(payload, dict):
        if snake_key in payload:
            return payload.get(snake_key, default)
        if candidate in payload:
            return payload.get(candidate, default)
    return default


def _create_workflow_definition(*, organization, user, business_object_code: str) -> WorkflowDefinition:
    return WorkflowDefinition.objects.create(
        organization=organization,
        code=f"clm_{business_object_code.lower()}_{organization.code.lower()}",
        name="Closed Loop Workflow",
        business_object_code=business_object_code,
        status="published",
        graph_data={
            "nodes": [
                {"id": "start_1", "type": "start", "text": "Start"},
                {"id": "approval_1", "type": "approval", "text": "Approval"},
                {"id": "end_1", "type": "end", "text": "End"},
            ],
            "edges": [
                {"id": "edge_1", "sourceNodeId": "start_1", "targetNodeId": "approval_1"},
                {"id": "edge_2", "sourceNodeId": "approval_1", "targetNodeId": "end_1"},
            ],
        },
        created_by=user,
    )


def _build_dataset():
    organization = Organization.objects.create(name="Metrics Org", code="metrics-org")
    user = User.objects.create_user(
        username="metrics_user",
        password="testpass123",
        organization=organization,
    )
    UserOrganization.objects.create(
        user=user,
        organization=organization,
        role="member",
        is_active=True,
    )
    department = Department.objects.create(
        organization=organization,
        code="OPS",
        name="Operations",
        created_by=user,
    )
    UserDepartment.objects.create(
        organization=organization,
        user=user,
        department=department,
        is_primary=True,
        created_by=user,
    )

    AssetProject.objects.create(
        organization=organization,
        project_name="Overdue Project",
        project_manager=user,
        department=department,
        status="active",
        start_date=timezone.localdate() - timedelta(days=20),
        end_date=timezone.localdate() - timedelta(days=2),
        created_by=user,
    )
    AssetProject.objects.create(
        organization=organization,
        project_name="Completed Project",
        project_manager=user,
        department=department,
        status="completed",
        start_date=timezone.localdate() - timedelta(days=15),
        end_date=timezone.localdate() - timedelta(days=1),
        actual_end_date=timezone.localdate() - timedelta(days=1),
        created_by=user,
    )

    overdue_task = InventoryTask.objects.create(
        organization=organization,
        task_name="Overdue Inventory",
        inventory_type=InventoryTask.TYPE_FULL,
        status=InventoryTask.STATUS_IN_PROGRESS,
        planned_date=timezone.localdate() - timedelta(days=3),
        total_count=10,
        scanned_count=7,
        started_at=timezone.now() - timedelta(days=4),
        created_by=user,
    )
    InventoryDifference.objects.create(
        organization=organization,
        task=overdue_task,
        difference_type=InventoryDifference.TYPE_MISSING,
        description="Missing monitor",
        status=InventoryDifference.STATUS_APPROVED,
        closure_type=InventoryDifference.CLOSURE_TYPE_CREATE_CARD,
        linked_action_code="create_asset_card",
        custom_fields={
            "linked_action_execution": {
                "status": "manual_follow_up",
                "can_send_follow_up": True,
                "follow_up_assignee_id": str(user.id),
            }
        },
        created_by=user,
    )
    InventoryTask.objects.create(
        organization=organization,
        task_name="Clean Inventory",
        inventory_type=InventoryTask.TYPE_FULL,
        status=InventoryTask.STATUS_COMPLETED,
        planned_date=timezone.localdate() - timedelta(days=1),
        started_at=timezone.now() - timedelta(days=2),
        completed_at=timezone.now() - timedelta(hours=6),
        total_count=5,
        scanned_count=5,
        created_by=user,
    )

    stalled_voucher = FinanceVoucher.objects.create(
        organization=organization,
        voucher_no="FV-STALLED-001",
        voucher_date=timezone.localdate() - timedelta(days=10),
        business_type="purchase",
        summary="Stalled voucher",
        total_amount=Decimal("1200.00"),
        status="approved",
        created_by=user,
    )
    FinanceVoucher.all_objects.filter(id=stalled_voucher.id).update(
        created_at=timezone.now() - timedelta(days=10),
    )
    FinanceVoucher.objects.create(
        organization=organization,
        voucher_no="FV-POSTED-001",
        voucher_date=timezone.localdate() - timedelta(days=1),
        business_type="purchase",
        summary="Posted voucher",
        total_amount=Decimal("980.00"),
        status="posted",
        erp_voucher_no="ERP-001",
        posted_at=timezone.now() - timedelta(hours=8),
        created_by=user,
    )

    company = InsuranceCompany.objects.create(
        organization=organization,
        code="INS-METRICS",
        name="Metrics Insurance",
        created_by=user,
    )
    InsurancePolicy.objects.create(
        organization=organization,
        policy_no="POL-EXP-001",
        policy_name="Expiring Policy",
        company=company,
        insurance_type="equipment",
        start_date=timezone.localdate() - timedelta(days=200),
        end_date=timezone.localdate() + timedelta(days=10),
        total_insured_amount=Decimal("50000.00"),
        total_premium=Decimal("1500.00"),
        status="active",
        created_by=user,
    )
    InsurancePolicy.objects.create(
        organization=organization,
        policy_no="POL-OD-001",
        policy_name="Overdue Renewal Policy",
        company=company,
        insurance_type="equipment",
        start_date=timezone.localdate() - timedelta(days=300),
        end_date=timezone.localdate() - timedelta(days=5),
        total_insured_amount=Decimal("35000.00"),
        total_premium=Decimal("1000.00"),
        status="active",
        created_by=user,
    )
    InsurancePolicy.objects.create(
        organization=organization,
        policy_no="POL-RNW-001",
        policy_name="Renewed Policy",
        company=company,
        insurance_type="equipment",
        start_date=timezone.localdate() - timedelta(days=400),
        end_date=timezone.localdate() - timedelta(days=2),
        total_insured_amount=Decimal("45000.00"),
        total_premium=Decimal("1200.00"),
        status="renewed",
        created_by=user,
    )

    stale_claim = ClaimRecord.objects.create(
        organization=organization,
        policy=InsurancePolicy.objects.get(policy_no="POL-EXP-001"),
        incident_date=timezone.localdate() - timedelta(days=12),
        incident_type="damage",
        incident_description="Damaged keyboard",
        claimed_amount=Decimal("300.00"),
        status="investigating",
        created_by=user,
    )
    ClaimRecord.all_objects.filter(id=stale_claim.id).update(
        created_at=timezone.now() - timedelta(days=10),
    )
    ClaimRecord.objects.create(
        organization=organization,
        policy=InsurancePolicy.objects.get(policy_no="POL-EXP-001"),
        incident_date=timezone.localdate() - timedelta(days=5),
        incident_type="loss",
        incident_description="Lost tablet",
        claimed_amount=Decimal("800.00"),
        status="paid",
        approved_amount=Decimal("750.00"),
        paid_amount=Decimal("750.00"),
        paid_date=timezone.localdate() - timedelta(days=1),
        settlement_date=timezone.localdate() - timedelta(days=1),
        created_by=user,
    )

    active_contract = LeaseContract.objects.create(
        organization=organization,
        contract_name="Active Lease",
        lessee_name="ACME Tenant",
        start_date=timezone.localdate() - timedelta(days=30),
        end_date=timezone.localdate() + timedelta(days=8),
        actual_start_date=timezone.localdate() - timedelta(days=29),
        total_rent=Decimal("6000.00"),
        deposit_amount=Decimal("500.00"),
        deposit_paid=Decimal("500.00"),
        status="active",
        created_by=user,
    )
    RentPayment.objects.create(
        organization=organization,
        contract=active_contract,
        due_date=timezone.localdate() - timedelta(days=6),
        amount=Decimal("1200.00"),
        paid_amount=Decimal("400.00"),
        status="partial",
        created_by=user,
    )
    LeaseContract.objects.create(
        organization=organization,
        contract_name="Completed Lease",
        lessee_name="Finished Tenant",
        start_date=timezone.localdate() - timedelta(days=60),
        end_date=timezone.localdate() - timedelta(days=2),
        actual_start_date=timezone.localdate() - timedelta(days=59),
        actual_end_date=timezone.localdate() - timedelta(days=1),
        total_rent=Decimal("8800.00"),
        deposit_amount=Decimal("800.00"),
        deposit_paid=Decimal("800.00"),
        status="completed",
        created_by=user,
    )

    definition = _create_workflow_definition(
        organization=organization,
        user=user,
        business_object_code="InventoryTask",
    )
    workflow_instance = WorkflowInstance.objects.create(
        organization=organization,
        definition=definition,
        instance_no="WF-CLM-001",
        business_object_code="InventoryTask",
        business_id=str(overdue_task.id),
        initiator=user,
        status=WorkflowInstance.STATUS_PENDING_APPROVAL,
        current_node_id="approval_1",
        current_node_name="Manager Approval",
        created_by=user,
    )
    workflow_task = WorkflowTask.objects.create(
        organization=organization,
        instance=workflow_instance,
        node_id="approval_1",
        node_name="Manager Approval",
        node_type="approval",
        assignee=user,
        status=WorkflowTask.STATUS_PENDING,
        due_date=timezone.now() - timedelta(hours=4),
        created_by=user,
    )
    WorkflowTask.all_objects.filter(id=workflow_task.id).update(
        created_at=timezone.now() - timedelta(hours=72),
    )
    completed_instance = WorkflowInstance.objects.create(
        organization=organization,
        definition=definition,
        instance_no="WF-CLM-002",
        business_object_code="InventoryTask",
        business_id=str(overdue_task.id),
        initiator=user,
        status=WorkflowInstance.STATUS_APPROVED,
        current_node_id="end_1",
        current_node_name="Completed",
        completed_at=timezone.now() - timedelta(hours=1),
        created_by=user,
    )
    completed_task = WorkflowTask.objects.create(
        organization=organization,
        instance=completed_instance,
        node_id="approval_1",
        node_name="Manager Approval",
        node_type="approval",
        assignee=user,
        status="approved",
        due_date=timezone.now() - timedelta(hours=30),
        completed_at=timezone.now() - timedelta(hours=2),
        created_by=user,
    )
    WorkflowTask.all_objects.filter(id=completed_task.id).update(
        created_at=timezone.now() - timedelta(hours=40),
    )

    return {
        "organization": organization,
        "user": user,
    }


@pytest.mark.django_db
def test_closed_loop_metrics_overview_returns_aggregated_summary_and_workflow_sla():
    data = _build_dataset()
    client = APIClient()
    client.force_authenticate(user=data["user"])

    response = client.get("/api/system/metrics/closed-loop/overview/?window=30d")
    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    result = payload["data"]

    assert _read_key(result["window"], "key") == "30d"
    summary = result["summary"]
    assert _read_key(summary, "opened_count") >= 10
    assert _read_key(summary, "closed_count") >= 5
    assert _read_key(summary, "overdue_count") >= 5
    assert _read_key(summary, "auto_closed_count") >= 2

    workflow_sla = _read_key(result, "workflow_sla")
    assert _read_key(workflow_sla, "overdue_task_count") == 1
    assert _read_key(workflow_sla, "escalated_task_count") == 1

    owner_rankings = _read_key(result, "owner_rankings")
    assert len(owner_rankings) == 1
    assert _read_key(owner_rankings[0], "username") == "metrics_user"
    assert _read_key(owner_rankings[0], "open_count") >= 6
    assert _read_key(owner_rankings[0], "overdue_count") >= 4
    source_counts = _read_key(owner_rankings[0], "source_counts")
    assert _read_key(source_counts, "workflow_tasks") == 1

    department_rankings = _read_key(result, "department_rankings")
    assert len(department_rankings) == 1
    assert _read_key(department_rankings[0], "department_name") == "Operations"
    assert _read_key(department_rankings[0], "open_count") >= 7
    assert _read_key(department_rankings[0], "overdue_count") >= 5
    assert _read_key(department_rankings[0], "top_source") == "insurance_policies"

    covered_codes = {_read_key(entry, "object_code") for entry in _read_key(result, "objects_covered")}
    assert covered_codes == {
        "AssetProject",
        "InventoryTask",
        "FinanceVoucher",
        "InsurancePolicy",
        "ClaimRecord",
        "LeasingContract",
    }


@pytest.mark.django_db
def test_closed_loop_metrics_by_object_returns_normalized_domain_payloads():
    data = _build_dataset()
    client = APIClient()
    client.force_authenticate(user=data["user"])

    response = client.get("/api/system/metrics/closed-loop/by-object/?window=30d")
    assert response.status_code == 200

    payload = response.json()
    results = {
        _read_key(entry, "object_code"): entry
        for entry in _read_key(payload["data"], "results")
    }

    inventory_summary = _read_key(results["InventoryTask"], "summary")
    assert _read_key(inventory_summary, "backlog_count") == 1
    assert _read_key(inventory_summary, "overdue_count") == 1
    assert _read_key(inventory_summary, "auto_closed_count") == 1
    assert _read_key(inventory_summary, "exception_backlog_count") == 1

    finance_summary = _read_key(results["FinanceVoucher"], "summary")
    assert _read_key(finance_summary, "backlog_count") == 1
    assert _read_key(finance_summary, "overdue_count") == 1
    assert _read_key(finance_summary, "auto_closed_count") == 1

    insurance_queues = {
        _read_key(entry, "code"): _read_key(entry, "count")
        for entry in _read_key(results["InsurancePolicy"], "queues")
    }
    assert insurance_queues["insurance_expiring_soon"] == 1
    assert insurance_queues["insurance_overdue_renewal"] == 1

    claim_summary = _read_key(results["ClaimRecord"], "summary")
    assert _read_key(claim_summary, "backlog_count") == 1
    assert _read_key(claim_summary, "overdue_count") == 1

    leasing_summary = _read_key(results["LeasingContract"], "summary")
    assert _read_key(leasing_summary, "overdue_count") == 1


@pytest.mark.django_db
def test_closed_loop_metrics_queues_and_bottlenecks_include_cross_domain_entries():
    data = _build_dataset()
    client = APIClient()
    client.force_authenticate(user=data["user"])

    queues_response = client.get("/api/system/metrics/closed-loop/queues/?window=30d")
    assert queues_response.status_code == 200
    queue_results = _read_key(queues_response.json()["data"], "results")
    queue_codes = {_read_key(entry, "code") for entry in queue_results}

    assert "inventory_manual_follow_up" in queue_codes
    assert "finance_stalled" in queue_codes
    assert "insurance_expiring_soon" in queue_codes
    assert "leasing_overdue" in queue_codes

    bottlenecks_response = client.get("/api/system/metrics/closed-loop/bottlenecks/?window=30d")
    assert bottlenecks_response.status_code == 200
    bottleneck_results = _read_key(bottlenecks_response.json()["data"], "results")

    assert any(
        _read_key(entry, "source_type") == "workflow" and _read_key(entry, "label") == "Manager Approval"
        for entry in bottleneck_results
    )
    assert any(
        _read_key(entry, "source_type") == "object" and _read_key(entry, "code") == "inventory_manual_follow_up"
        for entry in bottleneck_results
    )


@pytest.mark.django_db
def test_closed_loop_metrics_support_object_filters():
    data = _build_dataset()
    client = APIClient()
    client.force_authenticate(user=data["user"])

    response = client.get(
        "/api/system/metrics/closed-loop/by-object/?window=30d&object_codes=InventoryTask,FinanceVoucher"
    )
    assert response.status_code == 200

    result_codes = {
        _read_key(entry, "object_code")
        for entry in _read_key(response.json()["data"], "results")
    }
    assert result_codes == {"InventoryTask", "FinanceVoucher"}


@pytest.mark.django_db
def test_closed_loop_metrics_support_explicit_organization_scope():
    data = _build_dataset()
    user = data["user"]

    branch_org = Organization.objects.create(name="Branch Org", code="branch-org")
    UserOrganization.objects.create(
        user=user,
        organization=branch_org,
        role="member",
        is_active=True,
    )
    branch_department = Department.objects.create(
        organization=branch_org,
        code="BRANCH",
        name="Branch Operations",
        created_by=user,
    )
    AssetProject.objects.create(
        organization=branch_org,
        project_name="Branch Rollout",
        project_manager=user,
        department=branch_department,
        status="active",
        start_date=timezone.localdate() - timedelta(days=5),
        end_date=timezone.localdate() + timedelta(days=10),
        created_by=user,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        f"/api/system/metrics/closed-loop/overview/?window=30d&organization_id={branch_org.id}"
    )
    assert response.status_code == 200

    payload = response.json()["data"]
    summary = _read_key(payload, "summary")
    assert _read_key(summary, "opened_count") == 1
    assert _read_key(summary, "closed_count") == 0
    assert _read_key(summary, "backlog_count") == 1
    assert _read_key(summary, "overdue_count") == 0

    department_rankings = _read_key(payload, "department_rankings")
    assert len(department_rankings) == 1
    assert _read_key(department_rankings[0], "department_name") == "Branch Operations"
    assert _read_key(department_rankings[0], "open_count") == 1

    covered_codes = {_read_key(entry, "object_code") for entry in _read_key(payload, "objects_covered")}
    assert covered_codes == {
        "AssetProject",
        "InventoryTask",
        "FinanceVoucher",
        "InsurancePolicy",
        "ClaimRecord",
        "LeasingContract",
    }


@pytest.mark.django_db
def test_closed_loop_snapshot_crud_uses_shared_server_side_payloads():
    data = _build_dataset()
    client = APIClient()
    client.force_authenticate(user=data["user"])

    create_response = client.post(
        "/api/system/metrics/closed-loop/snapshots/",
        {
            "label": "Month End Review",
            "window": "30d",
            "objectCodes": ["InventoryTask", "FinanceVoucher"],
        },
        format="json",
    )
    assert create_response.status_code == 201

    payload = create_response.json()["data"]
    snapshot_id = _read_key(payload, "id")
    assert _read_key(payload, "label") == "Month End Review"
    assert _read_key(payload, "window_key") == "30d"
    assert _read_key(payload, "object_codes") == ["InventoryTask", "FinanceVoucher"]
    assert _read_key(_read_key(payload, "payload"), "overview")
    assert _read_key(_read_key(payload, "payload"), "by_object_items")

    snapshot = ClosedLoopDashboardSnapshot.objects.get(id=snapshot_id)
    assert snapshot.organization_id == data["organization"].id
    assert snapshot.created_by_id == data["user"].id
    assert snapshot.object_codes == ["InventoryTask", "FinanceVoucher"]

    list_response = client.get("/api/system/metrics/closed-loop/snapshots/")
    assert list_response.status_code == 200
    list_results = _read_key(list_response.json()["data"], "results")
    assert len(list_results) == 1
    assert _read_key(list_results[0], "label") == "Month End Review"
    assert "payload" not in list_results[0]

    detail_response = client.get(f"/api/system/metrics/closed-loop/snapshots/{snapshot_id}/")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()["data"]
    assert _read_key(_read_key(detail_payload, "payload"), "queues") is not None
    assert _read_key(_read_key(detail_payload, "payload"), "bottlenecks") is not None

    delete_response = client.delete(f"/api/system/metrics/closed-loop/snapshots/{snapshot_id}/")
    assert delete_response.status_code == 200
    snapshot.refresh_from_db()
    assert snapshot.is_deleted is True


@pytest.mark.django_db
def test_closed_loop_snapshot_respects_explicit_organization_scope():
    data = _build_dataset()
    user = data["user"]

    branch_org = Organization.objects.create(name="Branch Org", code="branch-org-snapshot")
    UserOrganization.objects.create(
        user=user,
        organization=branch_org,
        role="member",
        is_active=True,
    )
    branch_department = Department.objects.create(
        organization=branch_org,
        code="BRS",
        name="Branch Snapshot Dept",
        created_by=user,
    )
    AssetProject.objects.create(
        organization=branch_org,
        project_name="Branch Snapshot Project",
        project_manager=user,
        department=branch_department,
        status="active",
        start_date=timezone.localdate() - timedelta(days=3),
        end_date=timezone.localdate() + timedelta(days=7),
        created_by=user,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    create_response = client.post(
        "/api/system/metrics/closed-loop/snapshots/",
        {
            "label": "Branch Snapshot",
            "window": "30d",
            "organizationId": str(branch_org.id),
        },
        format="json",
    )
    assert create_response.status_code == 201
    snapshot_id = _read_key(create_response.json()["data"], "id")

    snapshot = ClosedLoopDashboardSnapshot.objects.get(id=snapshot_id)
    assert snapshot.organization_id == branch_org.id

    list_response = client.get(
        f"/api/system/metrics/closed-loop/snapshots/?organization_id={branch_org.id}"
    )
    assert list_response.status_code == 200
    list_results = _read_key(list_response.json()["data"], "results")
    assert len(list_results) == 1
    assert _read_key(list_results[0], "organization")["id"] == str(branch_org.id)

    wrong_scope_response = client.get(
        f"/api/system/metrics/closed-loop/snapshots/{snapshot_id}/?organization_id={data['organization'].id}"
    )
    assert wrong_scope_response.status_code == 404
