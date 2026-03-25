"""
Tests for Leasing API endpoints.

This module contains tests for all leasing-related API endpoints
following TDD approach with UUID-based unique suffixes for test isolation.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.leasing.models import (
    LeaseContract, LeaseItem, RentPayment,
    LeaseReturn, LeaseExtension
)
from apps.organizations.models import Organization
from apps.accounts.models import User


class LeaseContractAPITest(APITestCase):
    """LeaseContract API Tests."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Use both class name and UUID for uniqueness across test classes
        self.unique_suffix = f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"

        self.organization = Organization.objects.create(
            name=f"Test Org {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.client.force_authenticate(user=self.user)

    def test_list_contracts(self):
        """Test listing lease contracts."""
        # Create test contracts with unique numbers
        for i in range(3):
            LeaseContract.objects.create(
                organization=self.organization,
                contract_no=f"ZL{self.unique_suffix}{100+i:04d}",
                lessee_name=f"Customer {self.unique_suffix} {i}",
                start_date="2026-01-01",
                end_date="2026-12-31",
                total_rent=10000 + i * 1000,
                created_by=self.user
            )

        url = '/api/leasing/lease-contracts/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 3)

    def test_create_contract(self):
        """Test creating a lease contract."""
        url = '/api/leasing/lease-contracts/'
        data = {
            'contract_no': f"ZL{self.unique_suffix}0001",
            'lessee_name': f"Test Customer {self.unique_suffix}",
            'lessee_type': 'company',
            'lessee_contact': 'John Doe',
            'lessee_phone': '1234567890',
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'payment_type': 'monthly',
            'total_rent': '12000.00',
            'deposit_amount': '2000.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['lessee_name'], f"Test Customer {self.unique_suffix}")

    def test_activate_contract(self):
        """Test activating a draft contract."""
        contract = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0002",
            lessee_name=f"Customer {self.unique_suffix}",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_rent=12000,
            status='draft',
            created_by=self.user
        )

        url = f'/api/leasing/lease-contracts/{contract.id}/activate/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'active')

    def test_complete_contract(self):
        """Test completing an active contract."""
        contract = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0003",
            lessee_name=f"Customer {self.unique_suffix}",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=1),
            total_rent=12000,
            status='active',
            actual_start_date=date.today() - timedelta(days=30),
            created_by=self.user
        )

        url = f'/api/leasing/lease-contracts/{contract.id}/complete/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'completed')

    def test_terminate_contract(self):
        """Test terminating an active contract."""
        contract = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0004",
            lessee_name=f"Customer {self.unique_suffix}",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_rent=12000,
            status='active',
            created_by=self.user
        )

        url = f'/api/leasing/lease-contracts/{contract.id}/terminate/'
        data = {'reason': 'Early termination by customer'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'terminated')

    def test_suspend_contract(self):
        """Test suspending an active contract."""
        contract = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0005",
            lessee_name=f"Customer {self.unique_suffix}",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_rent=12000,
            status='active',
            created_by=self.user
        )

        url = f'/api/leasing/lease-contracts/{contract.id}/suspend/'
        data = {'reason': 'Payment dispute'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'suspended')

    def test_reactivate_contract(self):
        """Test reactivating a suspended contract."""
        contract = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0006",
            lessee_name=f"Customer {self.unique_suffix}",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_rent=12000,
            status='suspended',
            created_by=self.user
        )

        url = f'/api/leasing/lease-contracts/{contract.id}/reactivate/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'active')

    def test_filter_by_status(self):
        """Test filtering contracts by status."""
        LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0007",
            lessee_name=f"Customer {self.unique_suffix} 1",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=10000,
            status='draft',
            created_by=self.user
        )
        LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0008",
            lessee_name=f"Customer {self.unique_suffix} 2",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_rent=12000,
            status='active',
            created_by=self.user
        )

        url = '/api/leasing/lease-contracts/?status=active'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)


class LeaseItemAPITest(APITestCase):
    """LeaseItem API Tests."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Use both class name and UUID for uniqueness across test classes
        self.unique_suffix = f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"

        self.organization = Organization.objects.create(
            name=f"Test Org {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.client.force_authenticate(user=self.user)

        # Import Asset model
        from apps.assets.models import Asset, AssetCategory

        category = AssetCategory.objects.create(
            organization=self.organization,
            code=f"CAT{self.unique_suffix}",
            name=f"Test Category {self.unique_suffix}",
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.organization,
            asset_code=f"ASSET{self.unique_suffix}",
            asset_name=f"Test Asset {self.unique_suffix}",
            asset_category=category,
            purchase_price=Decimal('5000.00'),
            purchase_date=date.today() - timedelta(days=365),
            created_by=self.user
        )

        self.contract = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0001",
            lessee_name=f"Customer {self.unique_suffix}",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=12000,
            created_by=self.user
        )

    def test_list_items(self):
        """Test listing lease items."""
        for i in range(3):
            LeaseItem.objects.create(
                organization=self.organization,
                contract=self.contract,
                asset=self.asset,
                daily_rate=100 + i * 10,
                created_by=self.user
            )

        url = '/api/leasing/lease-items/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 3)

    def test_create_item(self):
        """Test creating a lease item."""
        url = '/api/leasing/lease-items/'
        data = {
            'contract': self.contract.id,
            'asset': self.asset.id,
            'daily_rate': '100.00',
            'insured_value': '5000.00',
            'start_condition': 'good'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['daily_rate']), 100.00)

    def test_filter_by_contract(self):
        """Test filtering items by contract."""
        # Create another contract
        contract2 = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0002",
            lessee_name=f"Customer {self.unique_suffix} 2",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=10000,
            created_by=self.user
        )

        LeaseItem.objects.create(
            organization=self.organization,
            contract=self.contract,
            asset=self.asset,
            daily_rate=100,
            created_by=self.user
        )
        LeaseItem.objects.create(
            organization=self.organization,
            contract=contract2,
            asset=self.asset,
            daily_rate=150,
            created_by=self.user
        )

        url = f'/api/leasing/lease-items/?contract={self.contract.id}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)


class RentPaymentAPITest(APITestCase):
    """RentPayment API Tests."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Use both class name and UUID for uniqueness across test classes
        self.unique_suffix = f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"

        self.organization = Organization.objects.create(
            name=f"Test Org {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.client.force_authenticate(user=self.user)

        self.contract = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0001",
            lessee_name=f"Customer {self.unique_suffix}",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=12000,
            created_by=self.user
        )

    def test_list_payments(self):
        """Test listing rent payments."""
        for i in range(3):
            RentPayment.objects.create(
                organization=self.organization,
                contract=self.contract,
                payment_no=f"PAY{self.unique_suffix}{i}",
                due_date=date.today() + timedelta(days=30 * i),
                amount=1000 + i * 100,
                created_by=self.user
            )

        url = '/api/leasing/rent-payments/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 3)

    def test_create_payment(self):
        """Test creating a rent payment."""
        url = '/api/leasing/rent-payments/'
        data = {
            'payment_no': f"PAY{self.unique_suffix}",
            'contract': self.contract.id,
            'due_date': str(date.today() + timedelta(days=30)),
            'amount': '1000.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['amount']), 1000.00)

    def test_record_payment(self):
        """Test recording a payment."""
        payment = RentPayment.objects.create(
            organization=self.organization,
            contract=self.contract,
            payment_no=f"PAY{self.unique_suffix}",
            due_date=date.today(),
            amount=1000,
            paid_amount=0,
            status='pending',
            created_by=self.user
        )

        url = f'/api/leasing/rent-payments/{payment.id}/record_payment/'
        data = {'amount': 500, 'payment_method': 'bank_transfer'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(float(response.data['data']['paid_amount']), 500)
        self.assertEqual(response.data['data']['status'], 'partial')

    def test_record_full_payment(self):
        """Test recording full payment."""
        payment = RentPayment.objects.create(
            organization=self.organization,
            contract=self.contract,
            payment_no=f"PAY{self.unique_suffix}",
            due_date=date.today(),
            amount=1000,
            paid_amount=0,
            status='pending',
            created_by=self.user
        )

        url = f'/api/leasing/rent-payments/{payment.id}/record_payment/'
        data = {'amount': 1000, 'payment_method': 'cash'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'paid')

    def test_mark_overdue(self):
        """Test marking a payment as overdue."""
        payment = RentPayment.objects.create(
            organization=self.organization,
            contract=self.contract,
            payment_no=f"PAY{self.unique_suffix}",
            due_date=date.today() - timedelta(days=10),
            amount=1000,
            status='pending',
            created_by=self.user
        )

        url = f'/api/leasing/rent-payments/{payment.id}/mark_overdue/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'overdue')

    def test_waive_payment(self):
        """Test waiving a payment."""
        payment = RentPayment.objects.create(
            organization=self.organization,
            contract=self.contract,
            payment_no=f"PAY{self.unique_suffix}",
            due_date=date.today() - timedelta(days=10),
            amount=1000,
            status='pending',
            created_by=self.user
        )

        url = f'/api/leasing/rent-payments/{payment.id}/waive/'
        data = {'reason': 'Customer dispute resolution'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['status'], 'waived')

    def test_filter_overdue_payments(self):
        """Test filtering overdue payments."""
        # Create overdue payment (pending status with past due date)
        RentPayment.objects.create(
            organization=self.organization,
            contract=self.contract,
            payment_no=f"PAY{self.unique_suffix}1",
            due_date=date.today() - timedelta(days=10),
            amount=1000,
            status='pending',
            created_by=self.user
        )

        # Create pending payment not overdue
        RentPayment.objects.create(
            organization=self.organization,
            contract=self.contract,
            payment_no=f"PAY{self.unique_suffix}2",
            due_date=date.today() + timedelta(days=10),
            amount=1000,
            status='pending',
            created_by=self.user
        )

        url = '/api/leasing/rent-payments/?overdue_only=true'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)


class LeaseReturnAPITest(APITestCase):
    """LeaseReturn API Tests."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Use both class name and UUID for uniqueness across test classes
        self.unique_suffix = f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"

        self.organization = Organization.objects.create(
            name=f"Test Org {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.client.force_authenticate(user=self.user)

        from apps.assets.models import Asset, AssetCategory

        category = AssetCategory.objects.create(
            organization=self.organization,
            code=f"CAT{self.unique_suffix}",
            name=f"Test Category {self.unique_suffix}",
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.organization,
            asset_code=f"ASSET{self.unique_suffix}",
            asset_name=f"Test Asset {self.unique_suffix}",
            asset_category=category,
            purchase_price=Decimal('5000.00'),
            purchase_date=date.today() - timedelta(days=365),
            created_by=self.user
        )

        self.contract = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0001",
            lessee_name=f"Customer {self.unique_suffix}",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=12000,
            status='active',
            created_by=self.user
        )

    def test_list_returns(self):
        """Test listing lease returns."""
        for i in range(3):
            LeaseReturn.objects.create(
                organization=self.organization,
                contract=self.contract,
                asset=self.asset,
                return_no=f"LR{self.unique_suffix}{100+i:04d}",
                return_date=date.today() - timedelta(days=i),
                condition='good',
                created_by=self.user
            )

        url = '/api/leasing/lease-returns/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 3)

    def test_create_return(self):
        """Test creating a lease return."""
        url = '/api/leasing/lease-returns/'
        data = {
            'return_no': f"RET{self.unique_suffix}",
            'contract': self.contract.id,
            'asset': self.asset.id,
            'return_date': str(date.today()),
            'condition': 'good',
            'damage_fee': '0.00',
            'refund_amount': '500.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['condition'], 'good')

    def test_filter_by_contract(self):
        """Test filtering returns by contract."""
        # Create another contract
        contract2 = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0002",
            lessee_name=f"Customer {self.unique_suffix} 2",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=10000,
            created_by=self.user
        )

        LeaseReturn.objects.create(
            organization=self.organization,
            contract=self.contract,
            asset=self.asset,
            return_no=f"LR{self.unique_suffix}0001",
            return_date=date.today(),
            condition='good',
            created_by=self.user
        )
        LeaseReturn.objects.create(
            organization=self.organization,
            contract=contract2,
            asset=self.asset,
            return_no=f"LR{self.unique_suffix}0002",
            return_date=date.today(),
            condition='excellent',
            created_by=self.user
        )

        url = f'/api/leasing/lease-returns/?contract={self.contract.id}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)


class LeaseExtensionAPITest(APITestCase):
    """LeaseExtension API Tests."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Use both class name and UUID for uniqueness across test classes
        self.unique_suffix = f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"

        self.organization = Organization.objects.create(
            name=f"Test Org {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.client.force_authenticate(user=self.user)

        self.contract = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0001",
            lessee_name=f"Customer {self.unique_suffix}",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_rent=12000,
            status='active',
            created_by=self.user
        )

    def test_list_extensions(self):
        """Test listing lease extensions."""
        for i in range(3):
            LeaseExtension.objects.create(
                organization=self.organization,
                contract=self.contract,
                extension_no=f"EXT{self.unique_suffix}{i}",
                original_end_date=date.today() + timedelta(days=365),
                new_end_date=date.today() + timedelta(days=365 + 30 * (i + 1)),
                additional_rent=1000 * (i + 1),
                created_by=self.user
            )

        url = '/api/leasing/lease-extensions/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 3)

    def test_create_extension(self):
        """Test creating a lease extension."""
        url = '/api/leasing/lease-extensions/'
        original_end = date.today() + timedelta(days=365)
        new_end = date.today() + timedelta(days=395)

        data = {
            'extension_no': f"EXT{self.unique_suffix}",
            'contract': self.contract.id,
            'original_end_date': str(original_end),
            'new_end_date': str(new_end),
            'additional_rent': '1000.00',
            'reason': 'Customer needs equipment for longer'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['additional_rent']), 1000.00)

    def test_approve_extension(self):
        """Test approving a lease extension."""
        extension = LeaseExtension.objects.create(
            organization=self.organization,
            contract=self.contract,
            extension_no=f"EXT{self.unique_suffix}",
            original_end_date=date.today() + timedelta(days=365),
            new_end_date=date.today() + timedelta(days=395),
            additional_rent=1000,
            created_by=self.user
        )

        url = f'/api/leasing/lease-extensions/{extension.id}/approve/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIsNotNone(response.data['data']['approved_by'])
        self.assertIsNotNone(response.data['data']['approved_at'])

    def test_filter_by_contract(self):
        """Test filtering extensions by contract."""
        # Create another contract
        contract2 = LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL{self.unique_suffix}0002",
            lessee_name=f"Customer {self.unique_suffix} 2",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_rent=10000,
            created_by=self.user
        )

        LeaseExtension.objects.create(
            organization=self.organization,
            contract=self.contract,
            extension_no=f"EXT{self.unique_suffix}1",
            original_end_date=date.today() + timedelta(days=365),
            new_end_date=date.today() + timedelta(days=395),
            additional_rent=1000,
            created_by=self.user
        )
        LeaseExtension.objects.create(
            organization=self.organization,
            contract=contract2,
            extension_no=f"EXT{self.unique_suffix}2",
            original_end_date=date.today() + timedelta(days=365),
            new_end_date=date.today() + timedelta(days=395),
            additional_rent=500,
            created_by=self.user
        )

        url = f'/api/leasing/lease-extensions/?contract={self.contract.id}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)
