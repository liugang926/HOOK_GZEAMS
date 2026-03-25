from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import User
from apps.assets.models import Asset, AssetCategory, AssetReturn, Location, ReturnItem
from apps.organizations.models import Department, Organization
from apps.projects.models import AssetProject, ProjectAsset, ProjectMember
from apps.projects.serializers import ProjectAssetSerializer
from apps.projects.services import AssetProjectService, ProjectAssetService


@pytest.mark.django_db
class TestProjectServices:
    def setup_method(self):
        self.organization = Organization.objects.create(
            code="PROJECT_ORG",
            name="Project Org",
        )
        self.department = Department.objects.create(
            organization=self.organization,
            code="RD",
            name="R&D",
        )
        self.user = User.objects.create_user(
            username="project_service_user",
            password="pass123456",
            organization=self.organization,
        )
        self.asset_category = AssetCategory.objects.create(
            organization=self.organization,
            code="PROJECT_ASSET",
            name="Project Asset",
            created_by=self.user,
        )
        self.asset_project_service = AssetProjectService()
        self.project_asset_service = ProjectAssetService()

        self.source_project = AssetProject.objects.create(
            organization=self.organization,
            project_name="Source Project",
            project_type="development",
            project_manager=self.user,
            department=self.department,
            start_date=date.today(),
            status="active",
            created_by=self.user,
        )
        self.target_project = AssetProject.objects.create(
            organization=self.organization,
            project_name="Target Project",
            project_type="development",
            project_manager=self.user,
            department=self.department,
            start_date=date.today(),
            status="active",
            created_by=self.user,
        )

    def test_close_project_requires_no_active_allocations(self):
        asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-001",
            asset_name="GPU Server",
            asset_category=self.asset_category,
            purchase_price=Decimal("50000.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        ProjectAsset.objects.create(
            organization=self.organization,
            project=self.source_project,
            asset=asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="in_use",
            created_by=self.user,
        )

        with pytest.raises(ValidationError):
            self.asset_project_service.close_project(
                str(self.source_project.id),
                organization_id=str(self.organization.id),
                user=self.user,
            )

    def test_close_project_marks_project_completed(self):
        project = self.asset_project_service.close_project(
            str(self.source_project.id),
            organization_id=str(self.organization.id),
            user=self.user,
        )

        self.source_project.refresh_from_db()
        assert project.status == "completed"
        assert self.source_project.status == "completed"
        assert self.source_project.actual_end_date is not None

    def test_transfer_to_project_creates_new_allocation_and_closes_source_allocation(self):
        asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-002",
            asset_name="Edge Gateway",
            asset_category=self.asset_category,
            purchase_price=Decimal("12000.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        allocation = ProjectAsset.objects.create(
            organization=self.organization,
            project=self.source_project,
            asset=asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="in_use",
            created_by=self.user,
        )

        new_allocation = self.project_asset_service.transfer_to_project(
            str(allocation.id),
            target_project_id=str(self.target_project.id),
            reason="Scope changed",
            organization_id=str(self.organization.id),
            user=self.user,
        )

        allocation.refresh_from_db()
        self.source_project.refresh_from_db()
        self.target_project.refresh_from_db()

        assert new_allocation.project_id == self.target_project.id
        assert new_allocation.asset_id == asset.id
        assert allocation.return_status == "transferred"
        assert allocation.actual_return_date is not None
        assert self.source_project.active_assets == 0
        assert self.target_project.active_assets == 1

    def test_mark_returned_updates_allocation_status_and_rollups(self):
        asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-003",
            asset_name="QA Device",
            asset_category=self.asset_category,
            purchase_price=Decimal("8000.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        allocation = ProjectAsset.objects.create(
            organization=self.organization,
            project=self.source_project,
            asset=asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="in_use",
            created_by=self.user,
        )

        returned_allocation = self.project_asset_service.mark_returned(
            str(allocation.id),
            return_date=date.today(),
            note="Returned via RT2026030001",
            organization_id=str(self.organization.id),
            user=self.user,
        )

        allocation.refresh_from_db()
        self.source_project.refresh_from_db()

        assert returned_allocation.return_status == "returned"
        assert allocation.return_status == "returned"
        assert allocation.actual_return_date == date.today()
        assert "Returned via RT2026030001" in allocation.notes
        assert self.source_project.active_assets == 0

    def test_record_return_rejection_appends_note_without_changing_status(self):
        asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-004",
            asset_name="Docking Station",
            asset_category=self.asset_category,
            purchase_price=Decimal("1200.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        allocation = ProjectAsset.objects.create(
            organization=self.organization,
            project=self.source_project,
            asset=asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="in_use",
            created_by=self.user,
        )

        updated_allocation = self.project_asset_service.record_return_rejection(
            str(allocation.id),
            note="Return rejected via RT2026030002: Missing power adapter",
            organization_id=str(self.organization.id),
            user=self.user,
        )

        allocation.refresh_from_db()

        assert updated_allocation.return_status == "in_use"
        assert allocation.return_status == "in_use"
        assert "Return rejected via RT2026030002" in allocation.notes
        assert "Missing power adapter" in allocation.notes

    def test_project_asset_serializer_exposes_latest_return_summary(self):
        location = Location.objects.create(
            organization=self.organization,
            name="Main Storage",
            path="Main Storage",
            location_type="area",
            created_by=self.user,
        )
        asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-005",
            asset_name="Meeting Tablet",
            asset_category=self.asset_category,
            purchase_price=Decimal("3500.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        allocation = ProjectAsset.objects.create(
            organization=self.organization,
            project=self.source_project,
            asset=asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="in_use",
            created_by=self.user,
        )
        return_order = AssetReturn.objects.create(
            organization=self.organization,
            returner=self.user,
            return_date=date.today(),
            return_location=location,
            status="rejected",
            reject_reason="Missing stylus",
            created_by=self.user,
        )
        ReturnItem.objects.create(
            organization=self.organization,
            asset_return=return_order,
            asset=asset,
            project_allocation=allocation,
            asset_status="idle",
            created_by=self.user,
        )

        serializer = ProjectAssetSerializer(instance=allocation)
        latest_return_summary = serializer.data["latest_return_summary"]

        assert latest_return_summary["status"] == "rejected"
        assert latest_return_summary["reject_reason"] == "Missing stylus"
        assert latest_return_summary["return_id"] == str(return_order.id)

    def test_get_workspace_dashboard_aggregates_project_assets_members_and_returns(self):
        self.source_project.planned_budget = Decimal("100000.00")
        self.source_project.actual_cost = Decimal("26000.00")
        self.source_project.completed_milestones = 3
        self.source_project.total_milestones = 5
        self.source_project.save(
            update_fields=[
                "planned_budget",
                "actual_cost",
                "completed_milestones",
                "total_milestones",
                "updated_at",
            ]
        )

        active_asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-006A",
            asset_name="Portable Workstation",
            asset_category=self.asset_category,
            purchase_price=Decimal("12000.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        returned_asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-006B",
            asset_name="Lab Camera",
            asset_category=self.asset_category,
            purchase_price=Decimal("4500.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        transferred_asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-006C",
            asset_name="Debug Tablet",
            asset_category=self.asset_category,
            purchase_price=Decimal("2100.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        active_allocation = ProjectAsset.objects.create(
            organization=self.organization,
            project=self.source_project,
            asset=active_asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="in_use",
            allocation_cost=Decimal("12000.00"),
            created_by=self.user,
        )
        ProjectAsset.objects.create(
            organization=self.organization,
            project=self.source_project,
            asset=returned_asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="returned",
            allocation_cost=Decimal("4500.00"),
            created_by=self.user,
        )
        ProjectAsset.objects.create(
            organization=self.organization,
            project=self.source_project,
            asset=transferred_asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="transferred",
            allocation_cost=Decimal("2100.00"),
            created_by=self.user,
        )
        ProjectMember.objects.create(
            organization=self.organization,
            project=self.source_project,
            user=self.user,
            role="manager",
            is_primary=True,
            is_active=True,
            can_allocate_asset=True,
            can_view_cost=True,
            created_by=self.user,
        )
        secondary_user = User.objects.create_user(
            username="project_member_user",
            password="pass123456",
            organization=self.organization,
        )
        ProjectMember.objects.create(
            organization=self.organization,
            project=self.source_project,
            user=secondary_user,
            role="observer",
            is_primary=False,
            is_active=False,
            created_by=self.user,
        )
        location = Location.objects.create(
            organization=self.organization,
            name="Workspace Storage",
            path="Workspace Storage",
            location_type="area",
            created_by=self.user,
        )
        completed_return = AssetReturn.objects.create(
            organization=self.organization,
            returner=self.user,
            return_date=date.today() - timedelta(days=1),
            return_location=location,
            status="completed",
            completed_at=timezone.now() - timedelta(days=1),
            created_by=self.user,
        )
        rejected_return = AssetReturn.objects.create(
            organization=self.organization,
            returner=self.user,
            return_date=date.today(),
            return_location=location,
            status="rejected",
            reject_reason="Accessory missing",
            created_by=self.user,
        )
        pending_return = AssetReturn.objects.create(
            organization=self.organization,
            returner=self.user,
            return_date=date.today(),
            return_location=location,
            status="pending",
            created_by=self.user,
        )
        for return_order in (completed_return, rejected_return, pending_return):
            ReturnItem.objects.create(
                organization=self.organization,
                asset_return=return_order,
                asset=active_asset,
                project_allocation=active_allocation,
                asset_status="idle",
                created_by=self.user,
            )

        dashboard = self.asset_project_service.get_workspace_dashboard(
            str(self.source_project.id),
            organization_id=str(self.organization.id),
            user=self.user,
        )

        assert dashboard["project"]["project_code"] == self.source_project.project_code
        assert dashboard["project"]["status"] == "active"
        assert dashboard["project"]["status_label"] == "Active"
        assert dashboard["project"]["project_manager_name"] == "project_service_user"
        assert dashboard["project"]["planned_budget"] == "100000.00"
        assert dashboard["project"]["actual_cost"] == "26000.00"
        assert dashboard["project"]["asset_cost"] == "18600.00"
        assert dashboard["project"]["progress"] == 60.0
        assert dashboard["assets"]["total_count"] == 3
        assert dashboard["assets"]["in_use_count"] == 1
        assert dashboard["assets"]["returned_count"] == 1
        assert dashboard["assets"]["transferred_count"] == 1
        assert dashboard["members"]["total_count"] == 2
        assert dashboard["members"]["active_count"] == 1
        assert dashboard["members"]["primary_count"] == 1
        assert dashboard["members"]["allocators_count"] == 1
        assert dashboard["returns"]["pending_count"] == 1
        assert dashboard["returns"]["completed_count"] == 1
        assert dashboard["returns"]["rejected_count"] == 1
        assert dashboard["returns"]["processed_count"] == 2

    def test_get_return_dashboard_aggregates_summary_history_and_trend(self):
        location = Location.objects.create(
            organization=self.organization,
            name="Project Warehouse",
            path="Project Warehouse",
            location_type="area",
            created_by=self.user,
        )
        asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-006",
            asset_name="Conference Screen",
            asset_category=self.asset_category,
            purchase_price=Decimal("6400.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        allocation = ProjectAsset.objects.create(
            organization=self.organization,
            project=self.source_project,
            asset=asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="in_use",
            created_by=self.user,
        )
        completed_return = AssetReturn.objects.create(
            organization=self.organization,
            returner=self.user,
            return_date=date.today() - timedelta(days=1),
            return_location=location,
            status="completed",
            completed_at=timezone.now() - timedelta(days=1),
            created_by=self.user,
        )
        rejected_return = AssetReturn.objects.create(
            organization=self.organization,
            returner=self.user,
            return_date=date.today(),
            return_location=location,
            status="rejected",
            reject_reason="Missing HDMI cable",
            created_by=self.user,
        )
        pending_return = AssetReturn.objects.create(
            organization=self.organization,
            returner=self.user,
            return_date=date.today(),
            return_location=location,
            status="pending",
            created_by=self.user,
        )
        for return_order in (completed_return, rejected_return, pending_return):
            ReturnItem.objects.create(
                organization=self.organization,
                asset_return=return_order,
                asset=asset,
                project_allocation=allocation,
                asset_status="idle",
                created_by=self.user,
            )

        dashboard = self.asset_project_service.get_return_dashboard(
            str(self.source_project.id),
            range_key="7d",
            organization_id=str(self.organization.id),
            user=self.user,
        )

        assert dashboard["summary"]["pending_count"] == 1
        assert dashboard["summary"]["completed_count"] == 1
        assert dashboard["summary"]["rejected_count"] == 1
        assert dashboard["summary"]["processed_count"] == 2
        assert dashboard["history"]["total_count"] == 2
        assert dashboard["history"]["rows"][0]["status"] == "rejected"
        assert dashboard["history"]["rows"][0]["reject_reason"] == "Missing HDMI cable"
        assert dashboard["trend"]["bucket"] == "day"
        assert len(dashboard["trend"]["points"]) >= 2
        assert dashboard["window"]["range_key"] == "7d"
