"""
Tests for Consumable Models.

Tests cover:
- ConsumableCategory model (hierarchy, path generation)
- Consumable model (stock status, low stock detection)
- ConsumableStock model (transaction creation)
- ConsumablePurchase model (number generation, total calculation)
- ConsumableIssue model (number generation)
"""
from django.test import TestCase
from django.utils import timezone
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
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.assets.models import Supplier


class TestConsumableCategory(TestCase):
    """Tests for ConsumableCategory model"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )

    def test_category_creation(self):
        """Test creating a root category"""
        category = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Office Supplies',
            unit='件'
        )
        self.assertEqual(category.code, 'CAT001')
        self.assertEqual(category.name, 'Office Supplies')
        self.assertEqual(category.level, 1)
        self.assertEqual(category.path, 'Office Supplies')
        self.assertTrue(category.is_active)

    def test_category_hierarchy(self):
        """Test category parent-child relationship"""
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
        self.assertEqual(child.level, 2)
        self.assertEqual(child.path, 'Office Supplies/Paper')
        self.assertEqual(child.parent, parent)
        self.assertEqual(parent.children.count(), 1)

    def test_category_str(self):
        """Test category string representation"""
        category = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Office Supplies',
            unit='件'
        )
        self.assertEqual(str(category), 'CAT001 - Office Supplies')


class TestConsumable(TestCase):
    """Tests for Consumable model"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )
        self.category = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Office Supplies',
            unit='件'
        )

    def test_consumable_creation(self):
        """Test creating a consumable"""
        consumable = Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=self.category,
            specification='80gsm 500 sheets',
            brand='Double A',
            unit='包',
            current_stock=100,
            available_stock=100
        )
        self.assertEqual(consumable.code, 'CON001')
        self.assertEqual(consumable.name, 'A4 Paper')
        self.assertEqual(consumable.status, 'normal')
        self.assertEqual(consumable.current_stock, 100)
        self.assertEqual(consumable.available_stock, 100)

    def test_consumable_stock_status(self):
        """Test stock status updates"""
        consumable = Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=self.category,
            current_stock=100,
            available_stock=100,
            min_stock=10,
            reorder_point=20
        )
        # Normal stock
        self.assertEqual(consumable.status, 'normal')

        # Low stock - need to use save() to update status
        # Use available_stock <= min_stock to trigger LOW_STOCK
        consumable.available_stock = 10  # equal to min_stock
        consumable.save()
        self.assertEqual(consumable.status, 'low_stock')

        # Out of stock
        consumable.available_stock = 0
        consumable.save()
        self.assertEqual(consumable.status, 'out_of_stock')

    def test_is_low_stock(self):
        """Test low stock detection"""
        consumable = Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=self.category,
            current_stock=100,
            available_stock=15,
            reorder_point=20
        )
        self.assertTrue(consumable.is_low_stock())

        consumable.available_stock = 25
        self.assertFalse(consumable.is_low_stock())

    def test_consumable_str(self):
        """Test consumable string representation"""
        consumable = Consumable.objects.create(
            organization=self.org,
            code='CON001',
            name='A4 Paper',
            category=self.category
        )
        self.assertEqual(str(consumable), 'CON001 - A4 Paper')


class TestConsumableStock(TestCase):
    """Tests for ConsumableStock model"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
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

    def test_stock_transaction_creation(self):
        """Test creating a stock transaction"""
        transaction = ConsumableStock.objects.create(
            organization=self.org,
            consumable=self.consumable,
            transaction_type=TransactionType.PURCHASE,
            quantity=50,
            before_stock=100,
            after_stock=150,
            source_type='purchase',
            source_no='CP202401001'
        )
        self.assertEqual(transaction.consumable, self.consumable)
        self.assertEqual(transaction.quantity, 50)
        self.assertEqual(transaction.before_stock, 100)
        self.assertEqual(transaction.after_stock, 150)

    def test_create_transaction_method(self):
        """Test create_transaction class method"""
        transaction = ConsumableStock.create_transaction(
            consumable=self.consumable,
            transaction_type=TransactionType.PURCHASE,
            quantity=50,
            source_type='test',
            source_no='TEST001'
        )
        self.assertEqual(transaction.quantity, 50)
        self.assertEqual(transaction.before_stock, 100)
        self.assertEqual(transaction.after_stock, 150)
        self.consumable.refresh_from_db()
        self.assertEqual(self.consumable.current_stock, 150)
        self.assertEqual(self.consumable.available_stock, 150)


class TestConsumablePurchase(TestCase):
    """Tests for ConsumablePurchase model"""

    def setUp(self):
        """Set up test data"""
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
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

    def test_purchase_creation(self):
        """Test creating a purchase order"""
        purchase = ConsumablePurchase.objects.create(
            organization=self.org,
            purchase_date=timezone.now().date(),
            supplier=self.supplier,
            status='draft'
        )
        self.assertIsNotNone(purchase.purchase_no)
        self.assertTrue(purchase.purchase_no.startswith('CP'))
        self.assertEqual(purchase.status, 'draft')

    def test_purchase_number_generation(self):
        """Test purchase number generation"""
        purchase1 = ConsumablePurchase.objects.create(
            organization=self.org,
            purchase_date=timezone.now().date(),
            supplier=self.supplier,
            status='draft'
        )
        purchase2 = ConsumablePurchase.objects.create(
            organization=self.org,
            purchase_date=timezone.now().date(),
            supplier=self.supplier,
            status='draft'
        )
        # Numbers should be different
        self.assertNotEqual(purchase1.purchase_no, purchase2.purchase_no)

    def test_purchase_total_calculation(self):
        """Test purchase total calculation"""
        # Create a second consumable for testing
        consumable2 = Consumable.objects.create(
            organization=self.org,
            code='CON002',
            name='Pen',
            category=self.category
        )
        purchase = ConsumablePurchase.objects.create(
            organization=self.org,
            purchase_date=timezone.now().date(),
            supplier=self.supplier,
            status='draft'
        )
        PurchaseItem.objects.create(
            organization=self.org,
            purchase=purchase,
            consumable=self.consumable,
            quantity=10,
            unit_price=25.00,
            amount=250.00
        )
        PurchaseItem.objects.create(
            organization=self.org,
            purchase=purchase,
            consumable=consumable2,
            quantity=5,
            unit_price=30.00,
            amount=150.00
        )
        total = purchase.calculate_total()
        self.assertEqual(total, 400)
        purchase.refresh_from_db()
        self.assertEqual(purchase.total_amount, 400)


class TestConsumableIssue(TestCase):
    """Tests for ConsumableIssue model"""

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

    def test_issue_creation(self):
        """Test creating an issue order"""
        issue = ConsumableIssue.objects.create(
            organization=self.org,
            issue_date=timezone.now().date(),
            applicant=self.user,
            department=self.dept,
            status='draft'
        )
        self.assertIsNotNone(issue.issue_no)
        self.assertTrue(issue.issue_no.startswith('CI'))
        self.assertEqual(issue.status, 'draft')

    def test_issue_number_generation(self):
        """Test issue number generation"""
        issue1 = ConsumableIssue.objects.create(
            organization=self.org,
            issue_date=timezone.now().date(),
            applicant=self.user,
            department=self.dept
        )
        issue2 = ConsumableIssue.objects.create(
            organization=self.org,
            issue_date=timezone.now().date(),
            applicant=self.user,
            department=self.dept
        )
        # Numbers should be different
        self.assertNotEqual(issue1.issue_no, issue2.issue_no)

    def test_issue_item_creation(self):
        """Test creating issue items"""
        issue = ConsumableIssue.objects.create(
            organization=self.org,
            issue_date=timezone.now().date(),
            applicant=self.user,
            department=self.dept
        )
        item = IssueItem.objects.create(
            organization=self.org,
            issue=issue,
            consumable=self.consumable,
            quantity=10,
            snapshot_before_stock=100
        )
        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.snapshot_before_stock, 100)
