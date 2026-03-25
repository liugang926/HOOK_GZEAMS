"""
Tests for Lifecycle Services.

Tests cover:
- PurchaseRequestService (workflow operations)
- AssetReceiptService (inspection operations)
- MaintenanceService (workflow operations)
- MaintenancePlanService (plan management)
- MaintenanceTaskService (task execution)
- DisposalRequestService (workflow operations)
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.lifecycle.models import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
    AssetReceipt,
    AssetReceiptItem,
    AssetReceiptStatus,
    Maintenance,
    MaintenanceStatus,
    MaintenancePriority,
    MaintenancePlan,
    MaintenancePlanStatus,
    MaintenancePlanCycle,
    MaintenanceTask,
    MaintenanceTaskStatus,
    DisposalRequest,
    DisposalItem,
    DisposalRequestStatus,
    DisposalType,
    DisposalReason,
)
from apps.lifecycle.services import (
    PurchaseRequestService,
    AssetReceiptService,
    MaintenanceService,
    MaintenancePlanService,
    MaintenanceTaskService,
    DisposalRequestService,
)
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.assets.models import AssetCategory, Asset


class TestPurchaseRequestService(TestCase):
    """Tests for PurchaseRequestService"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.dept = Organization.objects.create(
            name='IT Department',
            code='IT',
            org_type='department',
            parent=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Computers'
        )
        self.service = PurchaseRequestService()

    def test_create_with_items(self):
        """Test creating purchase request with items"""
        data = {
            'request_date': timezone.now().date(),
            'expected_date': timezone.now().date(),
            'reason': 'Need equipment',
            'department': self.dept,
            'items': [
                {
                    'asset_category': self.category,
                    'item_name': 'Laptop',
                    'quantity': 10,
                    'unit': '台',
                    'unit_price': 5000.00
                }
            ]
        }
        pr = self.service.create_with_items(data, self.user)
        self.assertEqual(pr.applicant, self.user)
        self.assertEqual(pr.items.count(), 1)
        self.assertEqual(pr.items.first().item_name, 'Laptop')

    def test_submit_for_approval(self):
        """Test submitting purchase request for approval"""
        pr = PurchaseRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date(),
            reason='Need equipment'
        )
        updated = self.service.submit_for_approval(str(pr.id))
        self.assertEqual(updated.status, PurchaseRequestStatus.SUBMITTED)

    def test_submit_invalid_status(self):
        """Test submitting non-draft request fails"""
        pr = PurchaseRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date(),
            reason='Need equipment',
            status=PurchaseRequestStatus.APPROVED
        )
        with self.assertRaises(ValidationError):
            self.service.submit_for_approval(str(pr.id))

    def test_approve_request(self):
        """Test approving purchase request"""
        pr = PurchaseRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date(),
            reason='Need equipment',
            status=PurchaseRequestStatus.SUBMITTED
        )
        approved = self.service.approve(
            str(pr.id),
            self.user,
            'approved',
            'Approved'
        )
        self.assertEqual(approved.status, PurchaseRequestStatus.APPROVED)
        self.assertEqual(approved.approved_by, self.user)

    def test_reject_request(self):
        """Test rejecting purchase request"""
        pr = PurchaseRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date(),
            reason='Need equipment',
            status=PurchaseRequestStatus.SUBMITTED
        )
        rejected = self.service.approve(
            str(pr.id),
            self.user,
            'rejected',
            'Not needed'
        )
        self.assertEqual(rejected.status, PurchaseRequestStatus.REJECTED)


class TestAssetReceiptService(TestCase):
    """Tests for AssetReceiptService"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Computers'
        )
        self.service = AssetReceiptService()

    def test_create_with_items(self):
        """Test creating asset receipt with items"""
        data = {
            'receipt_date': timezone.now().date(),
            'supplier': 'ABC Supplier',
            'items': [
                {
                    'asset_category': self.category,
                    'item_name': 'Laptop',
                    'ordered_quantity': 10,
                    'received_quantity': 10,
                    'qualified_quantity': 10,
                    'unit_price': 5000.00
                }
            ]
        }
        receipt = self.service.create_with_items(data, self.user)
        self.assertEqual(receipt.receiver, self.user)
        self.assertEqual(receipt.items.count(), 1)

    def test_submit_for_inspection(self):
        """Test submitting receipt for inspection"""
        receipt = AssetReceipt.objects.create(
            organization=self.org,
            receipt_date=timezone.now().date(),
            receiver=self.user
        )
        updated = self.service.submit_for_inspection(str(receipt.id))
        self.assertEqual(updated.status, AssetReceiptStatus.INSPECTING)

    def test_record_inspection_passed(self):
        """Test recording passed inspection"""
        receipt = AssetReceipt.objects.create(
            organization=self.org,
            receipt_date=timezone.now().date(),
            receiver=self.user,
            status=AssetReceiptStatus.INSPECTING
        )
        updated = self.service.record_inspection_result(
            str(receipt.id),
            self.user,
            'All good',
            passed=True
        )
        self.assertEqual(updated.status, AssetReceiptStatus.PASSED)
        self.assertIsNotNone(updated.passed_at)

    def test_record_inspection_rejected(self):
        """Test recording failed inspection"""
        receipt = AssetReceipt.objects.create(
            organization=self.org,
            receipt_date=timezone.now().date(),
            receiver=self.user,
            status=AssetReceiptStatus.INSPECTING
        )
        updated = self.service.record_inspection_result(
            str(receipt.id),
            self.user,
            'Quality issues',
            passed=False
        )
        self.assertEqual(updated.status, AssetReceiptStatus.REJECTED)


class TestMaintenanceService(TestCase):
    """Tests for MaintenanceService"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.technician = User.objects.create_user(
            username='tech',
            email='tech@example.com',
            password='testpass123',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Computers'
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='ASSET001',
            asset_name='Laptop',
            asset_category=self.category,
            purchase_price=5000.00,
            purchase_date=timezone.now().date()
        )
        self.service = MaintenanceService()

    def test_create_maintenance(self):
        """Test creating maintenance record"""
        data = {
            'asset': self.asset,
            'priority': MaintenancePriority.NORMAL,
            'fault_description': 'Screen not working'
        }
        maintenance = self.service.create(data, self.user)
        self.assertEqual(maintenance.reporter, self.user)
        self.assertEqual(maintenance.status, MaintenanceStatus.REPORTED)

    def test_assign_technician(self):
        """Test assigning technician"""
        maintenance = Maintenance.objects.create(
            organization=self.org,
            asset=self.asset,
            reporter=self.user,
            report_time=timezone.now(),
            fault_description='Issue'
        )
        updated = self.service.assign_technician(str(maintenance.id), self.technician)
        self.assertEqual(updated.technician, self.technician)
        self.assertEqual(updated.status, MaintenanceStatus.ASSIGNED)

    def test_start_work(self):
        """Test starting maintenance work"""
        maintenance = Maintenance.objects.create(
            organization=self.org,
            asset=self.asset,
            reporter=self.user,
            report_time=timezone.now(),
            fault_description='Issue',
            technician=self.technician,
            status=MaintenanceStatus.ASSIGNED
        )
        updated = self.service.start_work(str(maintenance.id))
        self.assertEqual(updated.status, MaintenanceStatus.PROCESSING)
        self.assertIsNotNone(updated.start_time)

    def test_complete_work(self):
        """Test completing maintenance work"""
        maintenance = Maintenance.objects.create(
            organization=self.org,
            asset=self.asset,
            reporter=self.user,
            report_time=timezone.now(),
            fault_description='Issue',
            technician=self.technician,
            status=MaintenanceStatus.PROCESSING,
            start_time=timezone.now()
        )
        completion_data = {
            'fault_cause': 'Broken screen',
            'repair_method': 'Replaced screen',
            'labor_cost': 100,
            'material_cost': 200,
            'other_cost': 0
        }
        updated = self.service.complete_work(str(maintenance.id), completion_data)
        self.assertEqual(updated.status, MaintenanceStatus.COMPLETED)
        self.assertEqual(updated.total_cost, 300)


class TestMaintenancePlanService(TestCase):
    """Tests for MaintenancePlanService"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.service = MaintenancePlanService()

    def test_create_plan(self):
        """Test creating maintenance plan"""
        data = {
            'plan_name': 'Monthly Maintenance',
            'plan_code': 'MP001',
            'cycle_type': MaintenancePlanCycle.MONTHLY,
            'cycle_value': 1,
            'start_date': timezone.now().date(),
            'maintenance_content': 'Check health',
            'estimated_hours': 2
        }
        plan = self.service.create(data, self.user)
        self.assertEqual(plan.organization, self.org)
        self.assertEqual(plan.status, MaintenancePlanStatus.ACTIVE)

    def test_pause_plan(self):
        """Test pausing maintenance plan"""
        plan = MaintenancePlan.objects.create(
            organization=self.org,
            plan_name='Monthly Maintenance',
            plan_code='MP001',
            cycle_type=MaintenancePlanCycle.MONTHLY,
            cycle_value=1,
            start_date=timezone.now().date(),
            maintenance_content='Check health',
            estimated_hours=2
        )
        paused = self.service.pause(str(plan.id))
        self.assertEqual(paused.status, MaintenancePlanStatus.PAUSED)

    def test_activate_plan(self):
        """Test activating paused plan"""
        plan = MaintenancePlan.objects.create(
            organization=self.org,
            plan_name='Monthly Maintenance',
            plan_code='MP001',
            cycle_type=MaintenancePlanCycle.MONTHLY,
            cycle_value=1,
            start_date=timezone.now().date(),
            maintenance_content='Check health',
            estimated_hours=2,
            status=MaintenancePlanStatus.PAUSED
        )
        activated = self.service.activate(str(plan.id))
        self.assertEqual(activated.status, MaintenancePlanStatus.ACTIVE)


class TestMaintenanceTaskService(TestCase):
    """Tests for MaintenanceTaskService"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Computers'
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='ASSET001',
            asset_name='Laptop',
            asset_category=self.category,
            purchase_price=5000.00,
            purchase_date=timezone.now().date()
        )
        self.plan = MaintenancePlan.objects.create(
            organization=self.org,
            plan_name='Monthly Maintenance',
            plan_code='MP001',
            cycle_type=MaintenancePlanCycle.MONTHLY,
            cycle_value=1,
            start_date=timezone.now().date(),
            maintenance_content='Check health',
            estimated_hours=2
        )
        self.service = MaintenanceTaskService()

    def test_assign_executor(self):
        """Test assigning executor to task"""
        task = MaintenanceTask.objects.create(
            organization=self.org,
            plan=self.plan,
            asset=self.asset,
            scheduled_date=timezone.now().date(),
            deadline_date=timezone.now().date()
        )
        assigned = self.service.assign_executor(str(task.id), self.user)
        self.assertEqual(assigned.executor, self.user)
        self.assertEqual(assigned.status, MaintenanceTaskStatus.IN_PROGRESS)

    def test_complete_execution(self):
        """Test completing task execution"""
        task = MaintenanceTask.objects.create(
            organization=self.org,
            plan=self.plan,
            asset=self.asset,
            scheduled_date=timezone.now().date(),
            deadline_date=timezone.now().date(),
            status=MaintenanceTaskStatus.IN_PROGRESS
        )
        execution_data = {
            'execution_content': 'Task completed',
            'finding': 'All good'
        }
        completed = self.service.complete_execution(str(task.id), execution_data, self.user)
        self.assertEqual(completed.status, MaintenanceTaskStatus.COMPLETED)

    def test_skip_task(self):
        """Test skipping task"""
        task = MaintenanceTask.objects.create(
            organization=self.org,
            plan=self.plan,
            asset=self.asset,
            scheduled_date=timezone.now().date(),
            deadline_date=timezone.now().date()
        )
        skipped = self.service.skip(str(task.id), 'Not needed')
        self.assertEqual(skipped.status, MaintenanceTaskStatus.SKIPPED)


class TestDisposalRequestService(TestCase):
    """Tests for DisposalRequestService"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.dept = Organization.objects.create(
            name='IT Department',
            code='IT',
            org_type='department',
            parent=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Computers'
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='ASSET001',
            asset_name='Laptop',
            asset_category=self.category,
            purchase_price=5000.00,
            purchase_date=timezone.now().date()
        )
        self.service = DisposalRequestService()

    def test_create_with_items(self):
        """Test creating disposal request with items"""
        data = {
            'department': self.dept,
            'request_date': timezone.now().date(),
            'disposal_reason': 'Obsolete',
            'reason_type': DisposalReason.OBSOLETE,
            'items': [
                {
                    'asset': self.asset,
                    'original_value': 5000,
                    'accumulated_depreciation': 3000,
                    'net_value': 2000
                }
            ]
        }
        dr = self.service.create_with_items(data, self.user)
        self.assertEqual(dr.applicant, self.user)
        self.assertEqual(dr.items.count(), 1)

    def test_submit_for_approval(self):
        """Test submitting disposal request"""
        dr = DisposalRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            disposal_reason='Obsolete',
            reason_type=DisposalReason.OBSOLETE
        )
        updated = self.service.submit_for_approval(str(dr.id))
        self.assertEqual(updated.status, DisposalRequestStatus.SUBMITTED)

    def test_start_appraisal(self):
        """Test starting appraisal process"""
        dr = DisposalRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            disposal_reason='Obsolete',
            reason_type=DisposalReason.OBSOLETE,
            status=DisposalRequestStatus.SUBMITTED
        )
        updated = self.service.start_appraisal(str(dr.id))
        self.assertEqual(updated.status, DisposalRequestStatus.APPRAISING)

    def test_record_appraisal(self):
        """Test recording appraisal for item"""
        dr = DisposalRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            disposal_reason='Obsolete',
            reason_type=DisposalReason.OBSOLETE,
            status=DisposalRequestStatus.APPRAISING
        )
        item = DisposalItem.objects.create(
            organization=self.org,
            disposal_request=dr,
            asset=self.asset,
            sequence=1,
            original_value=5000,
            accumulated_depreciation=3000,
            net_value=2000
        )
        appraised = self.service.record_appraisal(
            str(item.id),
            self.user,
            'Still usable',
            500
        )
        self.assertEqual(appraised.residual_value, 500)
        self.assertEqual(appraised.appraised_by, self.user)

    def test_execute_disposal(self):
        """Test executing disposal for item"""
        dr = DisposalRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            disposal_reason='Obsolete',
            reason_type=DisposalReason.OBSOLETE,
            status=DisposalRequestStatus.EXECUTING
        )
        item = DisposalItem.objects.create(
            organization=self.org,
            disposal_request=dr,
            asset=self.asset,
            sequence=1,
            original_value=5000,
            accumulated_depreciation=3000,
            net_value=2000,
            residual_value=500
        )
        executed = self.service.execute_disposal(
            str(item.id),
            600,
            'Sold to recycler'
        )
        self.assertTrue(executed.disposal_executed)
        self.assertEqual(executed.actual_residual_value, 600)
