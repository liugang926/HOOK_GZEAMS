"""
Tests for Asset Operation Models (Pickup, Transfer, Return, Loan).

Tests cover:
- Model functionality (code generation, status transitions, etc.)
- Service layer business logic
- API endpoint behavior
"""
from django.test import TestCase
from django.core.exceptions import ValidationError, PermissionDenied
from decimal import Decimal
from datetime import date, timedelta
from apps.assets.models import (
    Asset,
    AssetCategory,
    Location,
    AssetPickup,
    PickupItem,
    AssetTransfer,
    TransferItem,
    AssetReturn,
    ReturnItem,
    AssetLoan,
    LoanItem,
)
from apps.assets.services.operation_service import (
    AssetPickupService,
    AssetTransferService,
    AssetReturnService,
    AssetLoanService,
)
from apps.organizations.models import Organization, Department
from apps.accounts.models import User


# ========== Model Tests ==========

class AssetPickupModelTest(TestCase):
    """Test AssetPickup model functionality"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Organization',
            code='TEST_ORG'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            current_organization=self.org
        )
        # Create Department (not Organization with org_type='department')
        self.dept = Department.objects.create(
            name='IT Department',
            code='IT',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTER',
            name='Computer Equipment',
            created_by=self.user
        )

    def test_create_pickup_minimal(self):
        """Test creating pickup with minimal fields"""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today(),
            created_by=self.user
        )

        self.assertTrue(pickup.pickup_no.startswith('LY'))
        self.assertEqual(pickup.status, 'draft')
        self.assertEqual(pickup.applicant, self.user)

    def test_pickup_no_generation(self):
        """Test pickup number generation"""
        pickup1 = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today()
        )
        pickup2 = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today()
        )

        self.assertNotEqual(pickup1.pickup_no, pickup2.pickup_no)




class AssetTransferModelTest(TestCase):
    """Test AssetTransfer model functionality"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(name='Test Org', code='TEST')
        self.user = User.objects.create_user(username='test', organization=self.org)
        self.from_dept = Department.objects.create(
            name='IT', code='IT', organization=self.org
        )
        self.to_dept = Department.objects.create(
            name='HR', code='HR', organization=self.org
        )

    def test_transfer_no_generation(self):
        """Test transfer number generation"""
        transfer = AssetTransfer.objects.create(
            organization=self.org,
            from_department=self.from_dept,
            to_department=self.to_dept,
            transfer_date=date.today()
        )
        self.assertTrue(transfer.transfer_no.startswith('TF'))

    def test_status_transitions(self):
        """Test status transition flow"""
        transfer = AssetTransfer.objects.create(
            organization=self.org,
            from_department=self.from_dept,
            to_department=self.to_dept,
            transfer_date=date.today(),
            status='pending'
        )
        transfer.status = 'out_approved'
        transfer.save()
        transfer.status = 'approved'
        transfer.save()
        self.assertEqual(transfer.status, 'approved')


class AssetReturnModelTest(TestCase):
    """Test AssetReturn model functionality"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(name='Test Org', code='TEST')
        self.user = User.objects.create_user(username='test', organization=self.org)
        self.location = Location.objects.create(
            organization=self.org,
            name='Warehouse',
            location_type='warehouse'
        )

    def test_return_no_generation(self):
        """Test return number generation"""
        return_order = AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location
        )
        self.assertTrue(return_order.return_no.startswith('RT'))


class AssetLoanModelTest(TestCase):
    """Test AssetLoan model functionality"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(name='Test Org', code='TEST')
        self.user = User.objects.create_user(username='test', organization=self.org)

    def test_loan_no_generation(self):
        """Test loan number generation"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=30)
        )
        self.assertTrue(loan.loan_no.startswith('LN'))

    def test_is_overdue(self):
        """Test overdue detection"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today() - timedelta(days=60),
            expected_return_date=date.today() - timedelta(days=10),
            status='borrowed'
        )
        self.assertTrue(loan.is_overdue())
        self.assertEqual(loan.overdue_days(), 10)

    def test_not_overdue(self):
        """Test non-overdue loan"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=30),
            status='borrowed'
        )
        self.assertFalse(loan.is_overdue())
        self.assertEqual(loan.overdue_days(), 0)


# ========== Service Tests ==========

class AssetPickupServiceTest(TestCase):
    """Test AssetPickupService functionality"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(name='Test Org', code='TEST')
        self.user = User.objects.create_user(username='applicant', organization=self.org)
        self.approver = User.objects.create_user(username='approver', organization=self.org)
        self.dept = Department.objects.create(
            name='IT', code='IT', organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org, code='PC', name='Computer', created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user
        )
        self.service = AssetPickupService()

    def test_create_pickup_with_items(self):
        """Test creating pickup with items"""
        data = {
            'department': self.dept,
            'pickup_date': date.today(),
            'pickup_reason': 'New hire equipment'
        }
        items = [
            {'asset_id': str(self.asset.id), 'quantity': 1}
        ]

        pickup = self.service.create_with_items(
            data, items, self.user, str(self.org.id)
        )

        self.assertEqual(pickup.applicant, self.user)
        self.assertEqual(pickup.items.count(), 1)

    def test_submit_pickup(self):
        """Test submitting pickup for approval"""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today()
        )
        PickupItem.objects.create(
            organization=self.org,
            pickup=pickup,
            asset=self.asset
        )

        result = self.service.submit_for_approval(str(pickup.id), self.user)
        self.assertEqual(result.status, 'pending')

    def test_approve_pickup(self):
        """Test approving pickup"""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today(),
            status='pending'
        )
        PickupItem.objects.create(
            organization=self.org,
            pickup=pickup,
            asset=self.asset
        )

        result = self.service.approve(
            str(pickup.id), self.approver, 'approved', 'Approved'
        )

        self.assertEqual(result.status, 'approved')
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.asset_status, 'in_use')
        self.assertEqual(self.asset.custodian, self.user)

    def test_reject_pickup(self):
        """Test rejecting pickup"""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today(),
            status='pending'
        )
        PickupItem.objects.create(
            organization=self.org,
            pickup=pickup,
            asset=self.asset
        )

        result = self.service.approve(
            str(pickup.id), self.approver, 'rejected', 'Not needed'
        )

        self.assertEqual(result.status, 'rejected')
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.asset_status, 'idle')

    def test_complete_pickup(self):
        """Test completing pickup"""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today(),
            status='approved'
        )

        result = self.service.complete_pickup(str(pickup.id), self.user)
        self.assertEqual(result.status, 'completed')
        self.assertIsNotNone(result.completed_at)

    def test_cancel_pickup(self):
        """Test cancelling pickup"""
        pickup = AssetPickup.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.dept,
            pickup_date=date.today(),
            status='draft'
        )

        result = self.service.cancel_pickup(str(pickup.id), self.user)
        self.assertEqual(result.status, 'cancelled')


class AssetTransferServiceTest(TestCase):
    """Test AssetTransferService functionality"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(name='Test Org', code='TEST')
        self.user = User.objects.create_user(username='mgr', current_organization=self.org)
        self.from_dept = Department.objects.create(
            name='IT', code='IT', organization=self.org
        )
        self.to_dept = Department.objects.create(
            name='HR', code='HR', organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org, code='PC', name='Computer', created_by=self.user
        )
        self.location = Location.objects.create(
            organization=self.org, name='Office', location_type='area'
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date=date.today(),
            asset_status='in_use',
            department=self.from_dept,
            location=self.location,
            custodian=self.user,
            created_by=self.user
        )
        self.service = AssetTransferService()

    def test_create_transfer(self):
        """Test creating transfer"""
        data = {
            'from_department': self.from_dept,
            'to_department': self.to_dept,
            'transfer_date': date.today(),
            'transfer_reason': 'Department transfer'
        }
        items = [
            {'asset_id': str(self.asset.id)}
        ]

        transfer = self.service.create_with_items(
            data, items, self.user, str(self.org.id)
        )

        self.assertEqual(transfer.from_department, self.from_dept)
        self.assertEqual(transfer.to_department, self.to_dept)

    def test_complete_transfer(self):
        """Test completing transfer"""
        transfer = AssetTransfer.objects.create(
            organization=self.org,
            from_department=self.from_dept,
            to_department=self.to_dept,
            transfer_date=date.today(),
            status='approved'
        )
        TransferItem.objects.create(
            organization=self.org,
            transfer=transfer,
            asset=self.asset,
            from_location=self.location,
            from_custodian=self.user
        )

        result = self.service.complete_transfer(str(transfer.id), self.user)

        self.asset.refresh_from_db()
        self.assertEqual(self.asset.department, self.to_dept)
        self.assertEqual(result.status, 'completed')


class AssetReturnServiceTest(TestCase):
    """Test AssetReturnService functionality"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(name='Test Org', code='TEST')
        self.user = User.objects.create_user(username='user', organization=self.org)
        self.admin = User.objects.create_user(username='admin', organization=self.org)
        self.location = Location.objects.create(
            organization=self.org, name='Warehouse', location_type='warehouse'
        )
        self.category = AssetCategory.objects.create(
            organization=self.org, code='PC', name='Computer', created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date=date.today(),
            asset_status='in_use',
            custodian=self.user,
            created_by=self.user
        )
        self.service = AssetReturnService()

    def test_create_return(self):
        """Test creating return order"""
        data = {
            'return_date': date.today(),
            'return_reason': 'Project completed',
            'return_location': self.location
        }
        items = [
            {'asset_id': str(self.asset.id), 'asset_status': 'idle'}
        ]

        return_order = self.service.create_with_items(
            data, items, self.user, str(self.org.id)
        )

        self.assertEqual(return_order.returner, self.user)

    def test_confirm_return(self):
        """Test confirming return"""
        return_order = AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status='pending'
        )
        ReturnItem.objects.create(
            organization=self.org,
            asset_return=return_order,
            asset=self.asset,
            asset_status='idle'
        )

        result = self.service.confirm_return(str(return_order.id), self.admin)

        self.asset.refresh_from_db()
        self.assertEqual(self.asset.asset_status, 'idle')
        self.assertIsNone(self.asset.custodian)
        self.assertEqual(result.status, 'completed')


class AssetLoanServiceTest(TestCase):
    """Test AssetLoanService functionality"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(name='Test Org', code='TEST')
        self.user = User.objects.create_user(username='borrower', organization=self.org)
        self.admin = User.objects.create_user(username='admin', organization=self.org)
        self.category = AssetCategory.objects.create(
            organization=self.org, code='PC', name='Computer', created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user
        )
        self.service = AssetLoanService()

    def test_create_loan(self):
        """Test creating loan"""
        data = {
            'borrow_date': date.today(),
            'expected_return_date': date.today() + timedelta(days=30),
            'loan_reason': 'Temporary use'
        }
        items = [
            {'asset_id': str(self.asset.id)}
        ]

        loan = self.service.create_with_items(
            data, items, self.user, str(self.org.id)
        )

        self.assertEqual(loan.borrower, self.user)

    def test_approve_loan(self):
        """Test approving loan"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=30),
            status='pending'
        )
        LoanItem.objects.create(
            organization=self.org,
            loan=loan,
            asset=self.asset
        )

        result = self.service.approve_loan(
            str(loan.id), self.admin, 'approved'
        )

        self.assertEqual(result.status, 'approved')

    def test_confirm_borrow(self):
        """Test confirming borrow"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=30),
            status='approved'
        )
        LoanItem.objects.create(
            organization=self.org,
            loan=loan,
            asset=self.asset
        )

        result = self.service.confirm_borrow(str(loan.id), self.admin)

        self.asset.refresh_from_db()
        self.assertEqual(self.asset.asset_status, 'in_use')
        self.assertEqual(result.status, 'borrowed')

    def test_confirm_return(self):
        """Test confirming return"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=30),
            status='borrowed'
        )
        LoanItem.objects.create(
            organization=self.org,
            loan=loan,
            asset=self.asset
        )
        # First mark as borrowed
        self.asset.asset_status = 'in_use'
        self.asset.custodian = self.user
        self.asset.save()

        result = self.service.confirm_return(
            str(loan.id), self.admin, 'good'
        )

        self.asset.refresh_from_db()
        self.assertEqual(self.asset.asset_status, 'idle')
        self.assertEqual(result.status, 'returned')

    def test_check_overdue(self):
        """Test checking overdue loans"""
        # Create overdue loan
        loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today() - timedelta(days=60),
            expected_return_date=date.today() - timedelta(days=10),
            status='borrowed'
        )

        count = self.service.check_overdue_loans(str(self.org.id))
        self.assertGreater(count, 0)

        loan.refresh_from_db()
        self.assertEqual(loan.status, 'overdue')
