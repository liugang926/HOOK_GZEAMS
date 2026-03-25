from datetime import date, timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient, APITransactionTestCase

from apps.accounts.models import User
from apps.assets.models import Asset, AssetReturn, AssetCategory, Location, ReturnItem
from apps.common.middleware import clear_current_organization, set_current_organization
from apps.organizations.models import Department, Organization
from apps.projects.models import AssetProject, ProjectAsset, ProjectMember
from apps.system.services.object_registry import ObjectRegistry


class AssetProjectDashboardAPITest(APITransactionTestCase):
    """API tests for project workspace dashboard custom actions."""

    def setUp(self):
        clear_current_organization()
        ObjectRegistry.auto_register_standard_objects()

        self.client = APIClient()
        self.organization = Organization.objects.create(
            code="PROJECT_API_ORG",
            name="Project API Org",
        )
        self.department = Department.objects.create(
            organization=self.organization,
            code="RD",
            name="R&D",
        )
        self.user = User.objects.create_user(
            username="project_api_user",
            password="pass123456",
            organization=self.organization,
        )
        self.category = AssetCategory.objects.create(
            organization=self.organization,
            code="DISPLAY",
            name="Display",
            created_by=self.user,
        )
        self.location = Location.objects.create(
            organization=self.organization,
            name="Project Storage",
            path="Project Storage",
            location_type="area",
            created_by=self.user,
        )
        self.project = AssetProject.objects.create(
            organization=self.organization,
            project_name="Dashboard Project",
            project_type="development",
            project_manager=self.user,
            department=self.department,
            start_date=date.today(),
            status="active",
            planned_budget=Decimal("88000.00"),
            actual_cost=Decimal("21000.00"),
            created_by=self.user,
        )
        self.asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-DASH-001",
            asset_name="Dashboard Screen",
            asset_category=self.category,
            purchase_price=Decimal("5200.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        self.allocation = ProjectAsset.objects.create(
            organization=self.organization,
            project=self.project,
            asset=self.asset,
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
            return_location=self.location,
            status="completed",
            completed_at=self._now_minus_days(1),
            created_by=self.user,
        )
        rejected_return = AssetReturn.objects.create(
            organization=self.organization,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status="rejected",
            reject_reason="Missing power cable",
            created_by=self.user,
        )
        pending_return = AssetReturn.objects.create(
            organization=self.organization,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status="pending",
            created_by=self.user,
        )
        for return_order in (completed_return, rejected_return, pending_return):
            ReturnItem.objects.create(
                organization=self.organization,
                asset_return=return_order,
                asset=self.asset,
                project_allocation=self.allocation,
                asset_status="idle",
                created_by=self.user,
            )

        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.organization.id))
        set_current_organization(str(self.organization.id))

    @staticmethod
    def _now_minus_days(days: int):
        from django.utils import timezone

        return timezone.now() - timedelta(days=days)

    def test_return_dashboard_returns_summary_history_and_trend_payload(self):
        response = self.client.get(
            f"/api/system/objects/AssetProject/{self.project.id}/return_dashboard/?range_key=7d",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["summary"]["pending_count"], 1)
        self.assertEqual(data["summary"]["completed_count"], 1)
        self.assertEqual(data["summary"]["rejected_count"], 1)
        self.assertEqual(data["summary"]["processed_count"], 2)
        self.assertEqual(data["window"]["range_key"], "7d")
        self.assertEqual(data["history"]["total_count"], 2)
        self.assertEqual(data["history"]["rows"][0]["status"], "rejected")
        self.assertEqual(data["history"]["rows"][0]["reject_reason"], "Missing power cable")
        self.assertGreaterEqual(len(data["trend"]["points"]), 2)

    def test_workspace_dashboard_returns_project_assets_members_and_returns_payload(self):
        second_asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-DASH-002",
            asset_name="Meeting Camera",
            asset_category=self.category,
            purchase_price=Decimal("3200.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        third_asset = Asset.objects.create(
            organization=self.organization,
            asset_code="ASSET-DASH-003",
            asset_name="Loan Laptop",
            asset_category=self.category,
            purchase_price=Decimal("6800.00"),
            purchase_date=date.today(),
            created_by=self.user,
        )
        ProjectAsset.objects.create(
            organization=self.organization,
            project=self.project,
            asset=second_asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="returned",
            allocation_cost=Decimal("3200.00"),
            created_by=self.user,
        )
        ProjectAsset.objects.create(
            organization=self.organization,
            project=self.project,
            asset=third_asset,
            allocation_date=date.today(),
            allocation_type="temporary",
            allocated_by=self.user,
            return_status="transferred",
            allocation_cost=Decimal("6800.00"),
            created_by=self.user,
        )
        ProjectMember.objects.create(
            organization=self.organization,
            project=self.project,
            user=self.user,
            role="manager",
            is_primary=True,
            is_active=True,
            can_allocate_asset=True,
            can_view_cost=True,
            created_by=self.user,
        )
        teammate = User.objects.create_user(
            username="project_api_member",
            password="pass123456",
            organization=self.organization,
        )
        ProjectMember.objects.create(
            organization=self.organization,
            project=self.project,
            user=teammate,
            role="observer",
            is_primary=False,
            is_active=False,
            created_by=self.user,
        )

        response = self.client.get(
            f"/api/system/objects/AssetProject/{self.project.id}/workspace_dashboard/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["project"]["project_code"], self.project.project_code)
        self.assertEqual(data["project"]["status"], "active")
        self.assertEqual(data["project"]["status_label"], "Active")
        self.assertEqual(data["project"]["planned_budget"], "88000.00")
        self.assertEqual(data["project"]["actual_cost"], "21000.00")
        self.assertEqual(data["project"]["asset_cost"], "15200.00")
        self.assertEqual(data["assets"]["total_count"], 3)
        self.assertEqual(data["assets"]["in_use_count"], 1)
        self.assertEqual(data["assets"]["returned_count"], 1)
        self.assertEqual(data["assets"]["transferred_count"], 1)
        self.assertEqual(data["members"]["total_count"], 2)
        self.assertEqual(data["members"]["active_count"], 1)
        self.assertEqual(data["members"]["primary_count"], 1)
        self.assertEqual(data["members"]["allocators_count"], 1)
        self.assertEqual(data["returns"]["pending_count"], 1)
        self.assertEqual(data["returns"]["completed_count"], 1)
        self.assertEqual(data["returns"]["rejected_count"], 1)
        self.assertEqual(data["returns"]["processed_count"], 2)

    def tearDown(self):
        clear_current_organization()
        super().tearDown()
