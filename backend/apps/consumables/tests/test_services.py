"""
Tests for Consumable Services.

Tests cover:
- ConsumableCategoryService (tree operations, children queries)
- ConsumableService (low stock check, stock adjustment)
- ConsumablePurchaseService (workflow operations)
- ConsumableIssueService (workflow operations)
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.consumables.models import (
    ConsumableCategory,
    Consumable,
    ConsumableStock,
    ConsumablePurchase,
    PurchaseItem,
    ConsumableIssue,
    IssueItem,
    TransactionType,
)
from apps.consumables.services.consumable_service import (
    ConsumableCategoryService,
    ConsumableService,
    ConsumablePurchaseService,
    ConsumableIssueService,
)
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.assets.models import Supplier


class TestConsumableCategoryService(TestCase):
    """Tests for ConsumableCategoryService"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )
        self.service = ConsumableCategoryService()

    def test_get_tree(self):
        """Test getting category tree"""
        parent = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Office Supplies',
            unit='件'
        )
        child = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001-01',
            name='Paper',
            parent=parent,
            unit='包'
        )
        tree = self.service.get_tree(organization_id=str(self.org.id))
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['name'], 'Office Supplies')
        self.assertEqual(len(tree[0]['children']), 1)
        self.assertEqual(tree[0]['children'][0]['name'], 'Paper')

    def test_get_children(self):
        """Test getting category children"""
        parent = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Office Supplies',
            unit='件'
        )
        child = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001-01',
            name='Paper',
            parent=parent,
            unit='包'
        )
        children = self.service.get_children(str(parent.id))
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].name, 'Paper')

    def test_get_consumables_in_category(self):
        """Test getting consumables in category"""
        category = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Office Supplies',
            unit='件'
        )
        consumable = Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=category
        )
        consumables = self.service.get_consumables(str(category.id))
        self.assertEqual(consumables.count(), 1)
        self.assertEqual(consumables.first().name, 'A4 Paper')

    def test_get_consumables_in_descendants(self):
        """Test getting consumables in category and descendants"""
        parent = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Office Supplies',
            unit='件'
        )
        child = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001-01',
            name='Paper',
            parent=parent,
            unit='包'
        )
        Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=child
        )
        # Get from parent with descendants
        consumables = self.service.get_consumables(
            str(parent.id),
            include_descendants=True
        )
        self.assertEqual(consumables.count(), 1)
        # Get from parent without descendants
        consumables = self.service.get_consumables(
            str(parent.id),
            include_descendants=False
        )
        self.assertEqual(consumables.count(), 0)


class TestConsumableService(TestCase):
    """Tests for ConsumableService"""

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
        self.category = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Office Supplies',
            unit='件'
        )
        self.service = ConsumableService()

    def test_check_low_stock(self):
        """Test checking low stock items"""
        # Normal stock
        Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='Pen',
            category=self.category,
            current_stock=100,
            available_stock=100,
            reorder_point=20
        )
        # Low stock
        low_stock = Consumable.objects.create(
            organization=self.org,
            code='CON002',
            name='Paper',
            category=self.category,
            current_stock=15,
            available_stock=15,
            reorder_point=20
        )
        low_stock_items = self.service.check_low_stock(
            organization_id=str(self.org.id)
        )
        self.assertEqual(low_stock_items.count(), 1)
        self.assertEqual(low_stock_items.first().name, 'Paper')

    def test_check_out_of_stock(self):
        """Test checking out of stock items"""
        Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='Pen',
            category=self.category,
            current_stock=100,
            available_stock=100
        )
        out_of_stock = Consumable.objects.create(
            organization=self.org,
            code='CON002',
            name='Paper',
            category=self.category,
            current_stock=0,
            available_stock=0
        )
        items = self.service.check_out_of_stock(
            organization_id=str(self.org.id)
        )
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().name, 'Paper')

    def test_get_stock_transactions(self):
        """Test getting stock transactions for consumable"""
        consumable = Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=self.category
        )
        ConsumableStock.objects.create(
            organization=self.org,
            consumable=consumable,
            transaction_type=TransactionType.PURCHASE,
            quantity=50,
            before_stock=0,
            after_stock=50
        )
        transactions = self.service.get_stock_transactions(str(consumable.id))
        self.assertEqual(transactions.count(), 1)

    def test_adjust_stock(self):
        """Test manual stock adjustment"""
        consumable = Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=self.category,
            current_stock=100,
            available_stock=100
        )
        transaction = self.service.adjust_stock(
            consumable_id=str(consumable.id),
            quantity=50,
            transaction_type=TransactionType.INVENTORY_ADD,
            user=self.user
        )
        self.assertEqual(transaction.quantity, 50)
        consumable.refresh_from_db()
        self.assertEqual(consumable.current_stock, 150)
        self.assertEqual(consumable.available_stock, 150)

    def test_get_stock_summary(self):
        """Test getting stock summary"""
        Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=self.category,
            current_stock=100,
            available_stock=100,
            average_price=25.00
        )
        summary = self.service.get_stock_summary(
            organization_id=str(self.org.id)
        )
        self.assertEqual(summary['total_consumables'], 1)
        self.assertEqual(summary['total_value'], 2500.0)


class TestConsumablePurchaseService(TestCase):
    """Tests for ConsumablePurchaseService"""

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
        self.supplier = Supplier.objects.create(
            organization=self.org,
            name='Test Supplier',
            code='SUP001'
        )
        self.category = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Office Supplies',
            unit='件'
        )
        self.consumable = Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=self.category
        )
        self.service = ConsumablePurchaseService()

    def test_create_with_items(self):
        """Test creating purchase with items"""
        data = {
            'purchase_date': timezone.now().date(),
            'supplier_id': str(self.supplier.id),
            'items': [
                {
                    'consumable_id': str(self.consumable.id),
                    'quantity': 10,
                    'unit_price': 25.00
                }
            ],
            'remark': 'Test purchase'
        }
        purchase = self.service.create_with_items(data, self.user)
        self.assertEqual(purchase.total_amount, 250)
        self.assertEqual(purchase.items.count(), 1)

    def test_submit_for_approval(self):
        """Test submitting purchase for approval"""
        purchase = ConsumablePurchase.objects.create(
            organization=self.org,
            purchase_date=timezone.now().date(),
            supplier=self.supplier,
            status='draft'
        )
        updated = self.service.submit_for_approval(str(purchase.id))
        self.assertEqual(updated.status, 'pending')

    def test_approve_purchase(self):
        """Test approving purchase"""
        purchase = ConsumablePurchase.objects.create(
            organization=self.org,
            purchase_date=timezone.now().date(),
            supplier=self.supplier,
            status='pending'
        )
        approved = self.service.approve(
            str(purchase.id),
            self.user,
            'approved',
            'Looks good'
        )
        self.assertEqual(approved.status, 'approved')
        self.assertEqual(approved.approved_by, self.user)

    def test_reject_purchase(self):
        """Test rejecting purchase"""
        purchase = ConsumablePurchase.objects.create(
            organization=self.org,
            purchase_date=timezone.now().date(),
            supplier=self.supplier,
            status='pending'
        )
        rejected = self.service.approve(
            str(purchase.id),
            self.user,
            'rejected',
            'Not needed'
        )
        self.assertEqual(rejected.status, 'cancelled')

    def test_receive_purchase(self):
        """Test receiving purchase"""
        purchase = ConsumablePurchase.objects.create(
            organization=self.org,
            purchase_date=timezone.now().date(),
            supplier=self.supplier,
            status='approved'
        )
        PurchaseItem.objects.create(
            organization=self.org,
            purchase=purchase,
            consumable=self.consumable,
            quantity=10,
            unit_price=25.00
        )
        received = self.service.receive(str(purchase.id), self.user)
        self.assertEqual(received.status, 'received')
        self.consumable.refresh_from_db()
        self.assertEqual(self.consumable.current_stock, 10)
        self.assertEqual(self.consumable.available_stock, 10)


class TestConsumableIssueService(TestCase):
    """Tests for ConsumableIssueService"""

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
        self.category = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Office Supplies',
            unit='件'
        )
        self.consumable = Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=self.category,
            current_stock=100,
            available_stock=100
        )
        self.service = ConsumableIssueService()

    def test_create_with_items(self):
        """Test creating issue with items"""
        data = {
            'issue_date': timezone.now().date(),
            'applicant_id': str(self.user.id),
            'department_id': str(self.dept.id),
            'issue_reason': 'Need paper',
            'items': [
                {
                    'consumable_id': str(self.consumable.id),
                    'quantity': 10
                }
            ]
        }
        issue = self.service.create_with_items(data, self.user)
        self.assertEqual(issue.items.count(), 1)
        # Stock should be locked
        self.consumable.refresh_from_db()
        self.assertEqual(self.consumable.locked_stock, 10)
        self.assertEqual(self.consumable.available_stock, 90)

    def test_submit_for_approval(self):
        """Test submitting issue for approval"""
        issue = ConsumableIssue.objects.create(
            organization=self.org,
            issue_date=timezone.now().date(),
            applicant=self.user,
            department=self.dept,
            status='draft'
        )
        updated = self.service.submit_for_approval(str(issue.id))
        self.assertEqual(updated.status, 'pending')

    def test_approve_issue(self):
        """Test approving issue"""
        issue = ConsumableIssue.objects.create(
            organization=self.org,
            issue_date=timezone.now().date(),
            applicant=self.user,
            department=self.dept,
            status='pending'
        )
        approved = self.service.approve(
            str(issue.id),
            self.user,
            'approved',
            'Approved'
        )
        self.assertEqual(approved.status, 'approved')
        self.assertEqual(approved.approved_by, self.user)

    def test_issue_items(self):
        """Test issuing items"""
        issue = ConsumableIssue.objects.create(
            organization=self.org,
            issue_date=timezone.now().date(),
            applicant=self.user,
            department=self.dept,
            status='approved'
        )
        IssueItem.objects.create(
            organization=self.org,
            issue=issue,
            consumable=self.consumable,
            quantity=10,
            snapshot_before_stock=100
        )
        # Lock stock first
        self.consumable.locked_stock = 10
        self.consumable.available_stock = 90
        self.consumable.save()

        issued = self.service.issue(str(issue.id), self.user)
        self.assertEqual(issued.status, 'issued')
        self.consumable.refresh_from_db()
        self.assertEqual(self.consumable.locked_stock, 0)
        self.assertEqual(self.consumable.current_stock, 90)
