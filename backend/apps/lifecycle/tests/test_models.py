"""
Tests for Lifecycle Models.

Tests cover:
- PurchaseRequest and PurchaseRequestItem models
- AssetReceipt and AssetReceiptItem models
- Maintenance model
- MaintenancePlan and MaintenanceTask models
- DisposalRequest and DisposalItem models
"""
from django.test import TestCase
from django.utils import timezone
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
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.assets.models import AssetCategory, Asset


class TestPurchaseRequest(TestCase):
    """Tests for PurchaseRequest model"""

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

    def test_purchase_request_creation(self):
        """Test creating a purchase request"""
        pr = PurchaseRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date(),
            reason='Need new equipment'
        )
        self.assertIsNotNone(pr.request_no)
        self.assertTrue(pr.request_no.startswith('PR'))
        self.assertEqual(pr.status, PurchaseRequestStatus.DRAFT)

    def test_purchase_request_number_generation(self):
        """Test purchase request number generation"""
        pr1 = PurchaseRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date(),
            reason='Need equipment 1'
        )
        pr2 = PurchaseRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date(),
            reason='Need equipment 2'
        )
        # Numbers should be different
        self.assertNotEqual(pr1.request_no, pr2.request_no)

    def test_purchase_request_str(self):
        """Test purchase request string representation"""
        pr = PurchaseRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date(),
            reason='Need equipment'
        )
        expected = f"{pr.request_no} - Draft"
        self.assertEqual(str(pr), expected)


class TestPurchaseRequestItem(TestCase):
    """Tests for PurchaseRequestItem model"""

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
        self.pr = PurchaseRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date(),
            reason='Need equipment'
        )

    def test_purchase_request_item_creation(self):
        """Test creating a purchase request item"""
        item = PurchaseRequestItem.objects.create(
            organization=self.org,
            purchase_request=self.pr,
            asset_category=self.category,
            sequence=1,
            item_name='Laptop',
            quantity=10,
            unit='台',
            unit_price=5000.00
        )
        self.assertEqual(item.item_name, 'Laptop')
        self.assertEqual(item.total_amount, 50000.00)

    def test_purchase_request_item_auto_calculate_total(self):
        """Test automatic total amount calculation"""
        item = PurchaseRequestItem.objects.create(
            organization=self.org,
            purchase_request=self.pr,
            asset_category=self.category,
            sequence=1,
            item_name='Laptop',
            quantity=10,
            unit='台',
            unit_price=5000.00,
            total_amount=0  # Will be auto-calculated
        )
        item.save()
        self.assertEqual(item.total_amount, 50000.00)


class TestAssetReceipt(TestCase):
    """Tests for AssetReceipt model"""

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

    def test_asset_receipt_creation(self):
        """Test creating an asset receipt"""
        receipt = AssetReceipt.objects.create(
            organization=self.org,
            receipt_date=timezone.now().date(),
            receiver=self.user,
            supplier='ABC Supplier'
        )
        self.assertIsNotNone(receipt.receipt_no)
        self.assertTrue(receipt.receipt_no.startswith('RC'))
        self.assertEqual(receipt.status, AssetReceiptStatus.DRAFT)

    def test_asset_receipt_number_generation(self):
        """Test receipt number generation"""
        receipt1 = AssetReceipt.objects.create(
            organization=self.org,
            receipt_date=timezone.now().date(),
            receiver=self.user
        )
        receipt2 = AssetReceipt.objects.create(
            organization=self.org,
            receipt_date=timezone.now().date(),
            receiver=self.user
        )
        # Numbers should be different
        self.assertNotEqual(receipt1.receipt_no, receipt2.receipt_no)


class TestAssetReceiptItem(TestCase):
    """Tests for AssetReceiptItem model"""

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
        self.receipt = AssetReceipt.objects.create(
            organization=self.org,
            receipt_date=timezone.now().date(),
            receiver=self.user
        )

    def test_asset_receipt_item_creation(self):
        """Test creating an asset receipt item"""
        item = AssetReceiptItem.objects.create(
            organization=self.org,
            asset_receipt=self.receipt,
            asset_category=self.category,
            sequence=1,
            item_name='Laptop',
            ordered_quantity=10,
            received_quantity=10,
            qualified_quantity=10,
            unit_price=5000.00
        )
        self.assertEqual(item.item_name, 'Laptop')
        self.assertEqual(item.qualified_quantity, 10)
        self.assertEqual(item.defective_quantity, 0)

    def test_asset_receipt_item_defective_calculation(self):
        """Test defective quantity calculation"""
        item = AssetReceiptItem.objects.create(
            organization=self.org,
            asset_receipt=self.receipt,
            asset_category=self.category,
            sequence=1,
            item_name='Laptop',
            ordered_quantity=10,
            received_quantity=10,
            qualified_quantity=8,
            unit_price=5000.00,
            defective_quantity=0  # Will be auto-calculated
        )
        item.save()
        self.assertEqual(item.defective_quantity, 2)


class TestMaintenance(TestCase):
    """Tests for Maintenance model"""

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

    def test_maintenance_creation(self):
        """Test creating a maintenance record"""
        maintenance = Maintenance.objects.create(
            organization=self.org,
            asset=self.asset,
            reporter=self.user,
            report_time=timezone.now(),
            fault_description='Screen not working'
        )
        self.assertIsNotNone(maintenance.maintenance_no)
        self.assertTrue(maintenance.maintenance_no.startswith('MT'))
        self.assertEqual(maintenance.status, MaintenanceStatus.REPORTED)
        self.assertEqual(maintenance.priority, MaintenancePriority.NORMAL)

    def test_maintenance_number_generation(self):
        """Test maintenance number generation"""
        m1 = Maintenance.objects.create(
            organization=self.org,
            asset=self.asset,
            reporter=self.user,
            report_time=timezone.now(),
            fault_description='Issue 1'
        )
        m2 = Maintenance.objects.create(
            organization=self.org,
            asset=self.asset,
            reporter=self.user,
            report_time=timezone.now(),
            fault_description='Issue 2'
        )
        # Numbers should be different
        self.assertNotEqual(m1.maintenance_no, m2.maintenance_no)

    def test_maintenance_calculate_total_cost(self):
        """Test total cost calculation"""
        maintenance = Maintenance.objects.create(
            organization=self.org,
            asset=self.asset,
            reporter=self.user,
            report_time=timezone.now(),
            fault_description='Issue'
        )
        maintenance.labor_cost = 100
        maintenance.material_cost = 200
        maintenance.other_cost = 50
        maintenance.calculate_total_cost()
        self.assertEqual(maintenance.total_cost, 350)


class TestMaintenancePlan(TestCase):
    """Tests for MaintenancePlan model"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Computers'
        )

    def test_maintenance_plan_creation(self):
        """Test creating a maintenance plan"""
        plan = MaintenancePlan.objects.create(
            organization=self.org,
            plan_name='Monthly Server Maintenance',
            plan_code='MP001',
            cycle_type=MaintenancePlanCycle.MONTHLY,
            cycle_value=1,
            start_date=timezone.now().date(),
            maintenance_content='Check server health',
            estimated_hours=2
        )
        self.assertEqual(plan.plan_code, 'MP001')
        self.assertEqual(plan.status, MaintenancePlanStatus.ACTIVE)

    def test_maintenance_plan_str(self):
        """Test maintenance plan string representation"""
        plan = MaintenancePlan.objects.create(
            organization=self.org,
            plan_name='Monthly Server Maintenance',
            plan_code='MP001',
            cycle_type=MaintenancePlanCycle.MONTHLY,
            cycle_value=1,
            start_date=timezone.now().date(),
            maintenance_content='Check server health',
            estimated_hours=2
        )
        expected = "MP001 - Monthly Server Maintenance"
        self.assertEqual(str(plan), expected)


class TestMaintenanceTask(TestCase):
    """Tests for MaintenanceTask model"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
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

    def test_maintenance_task_creation(self):
        """Test creating a maintenance task"""
        task = MaintenanceTask.objects.create(
            organization=self.org,
            plan=self.plan,
            asset=self.asset,
            scheduled_date=timezone.now().date(),
            deadline_date=timezone.now().date()
        )
        self.assertIsNotNone(task.task_no)
        self.assertEqual(task.status, MaintenanceTaskStatus.PENDING)


class TestDisposalRequest(TestCase):
    """Tests for DisposalRequest model"""

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

    def test_disposal_request_creation(self):
        """Test creating a disposal request"""
        dr = DisposalRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            disposal_reason='Equipment is obsolete',
            reason_type=DisposalReason.OBSOLETE
        )
        self.assertIsNotNone(dr.request_no)
        self.assertTrue(dr.request_no.startswith('DS'))
        self.assertEqual(dr.status, DisposalRequestStatus.DRAFT)
        self.assertEqual(dr.disposal_type, DisposalType.SCRAP)

    def test_disposal_request_number_generation(self):
        """Test disposal request number generation"""
        dr1 = DisposalRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            disposal_reason='Reason 1',
            reason_type=DisposalReason.OTHER
        )
        dr2 = DisposalRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            disposal_reason='Reason 2',
            reason_type=DisposalReason.OTHER
        )
        # Numbers should be different
        self.assertNotEqual(dr1.request_no, dr2.request_no)


class TestDisposalItem(TestCase):
    """Tests for DisposalItem model"""

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
        self.dr = DisposalRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            request_date=timezone.now().date(),
            disposal_reason='Obsolete',
            reason_type=DisposalReason.OBSOLETE
        )

    def test_disposal_item_creation(self):
        """Test creating a disposal item"""
        item = DisposalItem.objects.create(
            organization=self.org,
            disposal_request=self.dr,
            asset=self.asset,
            sequence=1,
            original_value=5000.00,
            accumulated_depreciation=3000.00,
            net_value=2000.00
        )
        self.assertEqual(item.asset, self.asset)
        self.assertEqual(item.original_value, 5000.00)
        self.assertEqual(item.net_value, 2000.00)
        self.assertFalse(item.disposal_executed)
