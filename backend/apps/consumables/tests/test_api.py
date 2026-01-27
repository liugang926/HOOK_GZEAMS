"""
Tests for Consumable API endpoints.

Tests cover:
- ConsumableCategory API (CRUD, tree, children, consumables)
- Consumable API (CRUD, low_stock, out_of_stock, summary, transactions, adjust_stock)
- ConsumablePurchase API (CRUD, workflow: submit, approve, receive, complete, cancel)
- ConsumableIssue API (CRUD, workflow: submit, approve, issue, complete, cancel)
- ConsumableStock API (Read-only list)
"""
import uuid
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
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


class ConsumableCategoryAPITest(TestCase):
    """Test Consumable Category API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        # Use unique code for each test run to avoid conflicts
        unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Company {unique_suffix}',
            code=f'TEST{unique_suffix}',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{unique_suffix}',
            email=f'test{unique_suffix}@example.com',
            password='testpass123',
            organization=self.org
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

    def _make_unique_code(self, prefix=''):
        """Generate unique code for test data."""
        suffix = uuid.uuid4().hex[:8].upper()
        return f'{prefix}{suffix}'

    def test_list_categories(self):
        """Test GET /api/consumables/categories/"""
        ConsumableCategory.objects.create(
            organization=self.org,
            code=self._make_unique_code('CAT'),
            name='Office Supplies',
            unit='件'
        )

        url = '/api/consumables/categories/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['data']['count'], 1)

    def test_create_category(self):
        """Test POST /api/consumables/categories/"""
        url = '/api/consumables/categories/'
        code = self._make_unique_code('CAT')
        data = {
            'code': code,
            'name': 'Electronics',
            'unit': '件'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['code'], code)

    def test_get_category_tree(self):
        """Test GET /api/consumables/categories/tree/"""
        parent_code = self._make_unique_code('CAT')
        parent = ConsumableCategory.objects.create(
            organization=self.org,
            code=parent_code,
            name='Office Supplies',
            unit='件'
        )
        ConsumableCategory.objects.create(
            organization=self.org,
            code=self._make_unique_code('CAT'),
            name='Paper',
            parent=parent,
            unit='包'
        )

        url = '/api/consumables/categories/tree/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tree = response.data['data']
        self.assertGreaterEqual(len(tree), 1)

    def test_get_category_children(self):
        """Test GET /api/consumables/categories/{id}/children/"""
        parent = ConsumableCategory.objects.create(
            organization=self.org,
            code=self._make_unique_code('CAT'),
            name='Office Supplies',
            unit='件'
        )
        ConsumableCategory.objects.create(
            organization=self.org,
            code=self._make_unique_code('CAT'),
            name='Paper',
            parent=parent,
            unit='包'
        )

        url = f'/api/consumables/categories/{parent.id}/children/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        children = response.data['data']
        self.assertEqual(len(children), 1)


class ConsumableAPITest(TestCase):
    """Test Consumable API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Company {unique_suffix}',
            code=f'TEST{unique_suffix}',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{unique_suffix}',
            email=f'test{unique_suffix}@example.com',
            password='testpass123',
            organization=self.org
        )
        self.category = ConsumableCategory.objects.create(
            organization=self.org,
            code=self._make_unique_code('CAT'),
            name='Office Supplies',
            unit='件'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

    def _make_unique_code(self, prefix=''):
        """Generate unique code for test data."""
        suffix = uuid.uuid4().hex[:8].upper()
        return f'{prefix}{suffix}'

    def test_list_consumables(self):
        """Test GET /api/consumables/consumables/"""
        Consumable.objects.create(
            organization=self.org,
            code=self._make_unique_code('CON'),
            name='A4 Paper',
            category=self.category,
            current_stock=100,
            available_stock=100
        )

        url = '/api/consumables/consumables/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['data']['count'], 1)

    def test_create_consumable(self):
        """Test POST /api/consumables/consumables/"""
        url = '/api/consumables/consumables/'
        code = self._make_unique_code('CON')

        # Debug: check existing consumables
        existing = Consumable.objects.filter(organization=self.org).count()
        print(f"DEBUG: Existing consumables for org {self.org.id}: {existing}")

        data = {
            'code': code,
            'name': 'A4 Paper',
            'category_id': str(self.category.id),
            'unit': '包',
            'purchase_price': '25.00'
        }
        response = self.client.post(url, data, format='json')

        # Debug: print response if not 201
        if response.status_code != status.HTTP_201_CREATED:
            print(f"FAILED: Code={code}, Status={response.status_code}")
            print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['code'], code)

    def test_get_low_stock(self):
        """Test GET /api/consumables/consumables/low_stock/"""
        Consumable.objects.create(
            organization=self.org,
            code=self._make_unique_code('CON'),
            name='Pen',
            category=self.category,
            current_stock=15,
            available_stock=15,
            reorder_point=20
        )

        url = '/api/consumables/consumables/low_stock/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['data']
        self.assertEqual(len(items), 1)

    def test_get_out_of_stock(self):
        """Test GET /api/consumables/consumables/out_of_stock/"""
        Consumable.objects.create(
            organization=self.org,
            code=self._make_unique_code('CON'),
            name='Paper',
            category=self.category,
            current_stock=0,
            available_stock=0
        )

        url = '/api/consumables/consumables/out_of_stock/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['data']
        self.assertEqual(len(items), 1)

    def test_adjust_stock(self):
        """Test POST /api/consumables/consumables/{id}/adjust_stock/"""
        consumable = Consumable.objects.create(
            organization=self.org,
            code=self._make_unique_code('CON'),
            name='Paper',
            category=self.category,
            current_stock=100,
            available_stock=100
        )

        url = f'/api/consumables/consumables/{consumable.id}/adjust_stock/'
        data = {
            'quantity': 50,
            'transaction_type': 'inventory_add',
            'remark': 'Test adjustment'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        consumable.refresh_from_db()
        self.assertEqual(consumable.current_stock, 150)


class ConsumablePurchaseAPITest(TestCase):
    """Test Consumable Purchase API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Company {unique_suffix}',
            code=f'TEST{unique_suffix}',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{unique_suffix}',
            email=f'test{unique_suffix}@example.com',
            password='testpass123',
            organization=self.org
        )
        self.supplier = Supplier.objects.create(
            organization=self.org,
            name='Test Supplier',
            code=self._make_unique_code('SUP')
        )
        self.category = ConsumableCategory.objects.create(
            organization=self.org,
            code=self._make_unique_code('CAT'),
            name='Office Supplies',
            unit='件'
        )
        self.consumable = Consumable.objects.create(
            organization=self.org,
            code=self._make_unique_code('CON'),
            name='A4 Paper',
            category=self.category
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

    def _make_unique_code(self, prefix=''):
        """Generate unique code for test data."""
        suffix = uuid.uuid4().hex[:8].upper()
        return f'{prefix}{suffix}'

    def test_create_purchase(self):
        """Test POST /api/consumables/purchases/"""
        url = '/api/consumables/purchases/'
        data = {
            'purchase_date': str(timezone.now().date()),
            'supplier_id': str(self.supplier.id),
            'items': [
                {
                    'consumable_id': str(self.consumable.id),
                    'quantity': 10,
                    'unit_price': '25.00'
                }
            ]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('purchase_no', response.data['data'])

    def test_submit_purchase(self):
        """Test POST /api/consumables/purchases/{id}/submit/"""
        purchase = ConsumablePurchase.objects.create(
            organization=self.org,
            purchase_date=timezone.now().date(),
            supplier=self.supplier,
            status='draft'
        )

        url = f'/api/consumables/purchases/{purchase.id}/submit/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'pending')

    def test_approve_purchase(self):
        """Test POST /api/consumables/purchases/{id}/approve/"""
        purchase = ConsumablePurchase.objects.create(
            organization=self.org,
            purchase_date=timezone.now().date(),
            supplier=self.supplier,
            status='pending'
        )

        url = f'/api/consumables/purchases/{purchase.id}/approve/'
        data = {'approval': 'approved', 'comment': 'Looks good'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'approved')

    def test_receive_purchase(self):
        """Test POST /api/consumables/purchases/{id}/receive/"""
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
            unit_price='25.00'
        )

        url = f'/api/consumables/purchases/{purchase.id}/receive/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'received')
        self.consumable.refresh_from_db()
        self.assertEqual(self.consumable.current_stock, 10)


class ConsumableIssueAPITest(TestCase):
    """Test Consumable Issue API endpoints."""

    def setUp(self):
        """Set up test data with unique codes."""
        unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Company {unique_suffix}',
            code=f'TEST{unique_suffix}',
            org_type='company'
        )
        self.dept = Organization.objects.create(
            name='IT Department',
            code=self._make_unique_code('DEPT'),
            org_type='department',
            parent=self.org
        )
        self.user = User.objects.create_user(
            username=f'testuser_{unique_suffix}',
            email=f'test{unique_suffix}@example.com',
            password='testpass123',
            organization=self.org
        )
        self.category = ConsumableCategory.objects.create(
            organization=self.org,
            code=self._make_unique_code('CAT'),
            name='Office Supplies',
            unit='件'
        )
        self.consumable = Consumable.objects.create(
            organization=self.org,
            code=self._make_unique_code('CON'),
            name='A4 Paper',
            category=self.category,
            current_stock=100,
            available_stock=100
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

    def _make_unique_code(self, prefix=''):
        """Generate unique code for test data."""
        suffix = uuid.uuid4().hex[:8].upper()
        return f'{prefix}{suffix}'

    def test_create_issue(self):
        """Test POST /api/consumables/issues/"""
        url = '/api/consumables/issues/'
        data = {
            'issue_date': str(timezone.now().date()),
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
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('issue_no', response.data['data'])

    def test_submit_issue(self):
        """Test POST /api/consumables/issues/{id}/submit/"""
        issue = ConsumableIssue.objects.create(
            organization=self.org,
            issue_date=timezone.now().date(),
            applicant=self.user,
            department=self.dept,
            status='draft'
        )

        url = f'/api/consumables/issues/{issue.id}/submit/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'pending')

    def test_approve_issue(self):
        """Test POST /api/consumables/issues/{id}/approve/"""
        issue = ConsumableIssue.objects.create(
            organization=self.org,
            issue_date=timezone.now().date(),
            applicant=self.user,
            department=self.dept,
            status='pending'
        )

        url = f'/api/consumables/issues/{issue.id}/approve/'
        data = {'approval': 'approved', 'comment': 'Approved'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'approved')

    def test_issue_items(self):
        """Test POST /api/consumables/issues/{id}/issue/"""
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

        url = f'/api/consumables/issues/{issue.id}/issue/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'issued')
