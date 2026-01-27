"""
Tests for Insurance API endpoints.

This module contains tests for all insurance-related API endpoints
following TDD approach with UUID-based unique suffixes for test isolation.
"""

import uuid
from datetime import date, timedelta
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.insurance.models import (
    InsuranceCompany, InsurancePolicy, InsuredAsset,
    PremiumPayment, ClaimRecord, PolicyRenewal
)
from apps.organizations.models import Organization
from apps.accounts.models import User


class InsuranceCompanyAPITest(APITestCase):
    """InsuranceCompany API Tests."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]

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

    def test_list_companies(self):
        """Test listing insurance companies."""
        # Create test companies
        for i in range(3):
            InsuranceCompany.objects.create(
                organization=self.organization,
                code=f"PICC_{self.unique_suffix}_{i}",
                name=f"Insurance Co {self.unique_suffix} {i}",
                created_by=self.user
            )

        url = '/api/insurance/companies/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 3)

    def test_create_company(self):
        """Test creating an insurance company."""
        url = '/api/insurance/companies/'
        data = {
            'code': f"PICC_{self.unique_suffix}",
            'name': f"People Insurance {self.unique_suffix}",
            'short_name': 'PICC',
            'contact_person': 'John Doe',
            'contact_phone': '1234567890',
            'is_active': True
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], f"PICC_{self.unique_suffix}")

    def test_filter_company_by_type(self):
        """Test filtering companies by type."""
        InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_{self.unique_suffix}",
            name=f"Insurance Co {self.unique_suffix}",
            company_type='property',
            created_by=self.user
        )

        url = f'/api/insurance/companies/?company_type=property'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)


class InsurancePolicyAPITest(APITestCase):
    """InsurancePolicy API Tests."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]

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
        self.company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_{self.unique_suffix}",
            name=f"Insurance Co {self.unique_suffix}",
            created_by=self.user
        )

    def test_list_policies(self):
        """Test listing insurance policies."""
        for i in range(3):
            InsurancePolicy.objects.create(
                organization=self.organization,
                policy_no=f"POL-{self.unique_suffix}-{i}",
                company=self.company,
                insurance_type="property",
                start_date="2026-01-01",
                end_date="2026-12-31",
                total_insured_amount=100000,
                total_premium=5000 + i * 1000,
                created_by=self.user
            )

        url = '/api/insurance/policies/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 3)

    def test_create_policy(self):
        """Test creating an insurance policy."""
        url = '/api/insurance/policies/'
        data = {
            'policy_no': f"POL-{self.unique_suffix}",
            'company': self.company.id,
            'insurance_type': 'property',
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'total_insured_amount': 1000000,
            'total_premium': 5000,
            'payment_frequency': 'annual'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['policy_no'], f"POL-{self.unique_suffix}")

    def test_activate_policy(self):
        """Test activating a draft policy."""
        policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_insured_amount=100000,
            total_premium=5000,
            status='draft',
            created_by=self.user
        )

        url = f'/api/insurance/policies/{policy.id}/activate/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'active')

    def test_activate_policy_generates_payment_schedule(self):
        """Test that activating a draft policy generates payment schedule.

        When a policy is activated, the system should automatically generate
        premium payment records based on the payment_frequency.
        """
        from apps.insurance.models import PremiumPayment

        # Test with annual payment frequency
        policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}-ANNUAL",
            company=self.company,
            insurance_type="property",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_insured_amount=100000,
            total_premium=12000,
            payment_frequency='annual',
            status='draft',
            created_by=self.user
        )

        # Verify no payments exist before activation
        self.assertEqual(PremiumPayment.objects.filter(policy=policy).count(), 0)

        # Activate the policy
        url = f'/api/insurance/policies/{policy.id}/activate/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'active')

        # Verify payment schedule was generated (1 payment for annual)
        payments = PremiumPayment.objects.filter(policy=policy).order_by('due_date')
        self.assertEqual(payments.count(), 1)
        self.assertEqual(float(payments.first().amount), 12000)
        self.assertEqual(payments.first().status, 'pending')

    def test_activate_policy_generates_monthly_payments(self):
        """Test that activating a policy with monthly frequency generates 12 payments."""
        from apps.insurance.models import PremiumPayment

        policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}-MONTHLY",
            company=self.company,
            insurance_type="property",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_insured_amount=100000,
            total_premium=12000,
            payment_frequency='monthly',
            status='draft',
            created_by=self.user
        )

        # Activate the policy
        url = f'/api/insurance/policies/{policy.id}/activate/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify 12 monthly payments were generated
        payments = PremiumPayment.objects.filter(policy=policy).order_by('due_date')
        self.assertEqual(payments.count(), 12)

        # Verify each payment amount (12000 / 12 = 1000)
        for payment in payments:
            self.assertEqual(float(payment.amount), 1000)
            self.assertEqual(payment.status, 'pending')

    def test_activate_policy_generates_quarterly_payments(self):
        """Test that activating a policy with quarterly frequency generates 4 payments."""
        from apps.insurance.models import PremiumPayment

        policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}-QUARTERLY",
            company=self.company,
            insurance_type="property",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_insured_amount=100000,
            total_premium=12000,
            payment_frequency='quarterly',
            status='draft',
            created_by=self.user
        )

        # Activate the policy
        url = f'/api/insurance/policies/{policy.id}/activate/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify 4 quarterly payments were generated
        payments = PremiumPayment.objects.filter(policy=policy).order_by('due_date')
        self.assertEqual(payments.count(), 4)

        # Verify each payment amount (12000 / 4 = 3000)
        for payment in payments:
            self.assertEqual(float(payment.amount), 3000)
            self.assertEqual(payment.status, 'pending')

    def test_cancel_policy(self):
        """Test cancelling an active policy."""
        policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_insured_amount=100000,
            total_premium=5000,
            status='active',
            created_by=self.user
        )

        url = f'/api/insurance/policies/{policy.id}/cancel/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cancelled')

    def test_policy_summary(self):
        """Test getting policy summary."""
        policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_insured_amount=100000,
            total_premium=5000,
            status='active',
            created_by=self.user
        )

        url = f'/api/insurance/policies/{policy.id}/summary/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_insured_assets', response.data)
        self.assertIn('total_claims', response.data)

    def test_filter_expiring_soon(self):
        """Test filtering policies expiring soon."""
        # Create policy expiring in 15 days
        InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date=date.today() - timedelta(days=350),
            end_date=date.today() + timedelta(days=15),
            total_insured_amount=100000,
            total_premium=5000,
            status='active',
            created_by=self.user
        )

        url = '/api/insurance/policies/?expires_soon=true'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)

    def test_filter_expiring_soon_with_days(self):
        """Test filtering policies expiring soon with custom days parameter."""
        unique_suffix = uuid.uuid4().hex[:8]

        # Create policy expiring in 15 days
        InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date=date.today() - timedelta(days=350),
            end_date=date.today() + timedelta(days=15),
            total_insured_amount=100000,
            total_premium=5000,
            status='active',
            created_by=self.user
        )

        # Create policy expiring in 60 days
        InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{unique_suffix}-2",
            company=self.company,
            insurance_type="property",
            start_date=date.today() - timedelta(days=305),
            end_date=date.today() + timedelta(days=60),
            total_insured_amount=100000,
            total_premium=5000,
            status='active',
            created_by=self.user
        )

        url = '/api/insurance/policies/?expires_soon=true&days=30'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)

    def test_get_dashboard_stats(self):
        """Test getting insurance dashboard statistics."""
        unique_suffix = uuid.uuid4().hex[:8]

        # Create active policies
        for i in range(3):
            InsurancePolicy.objects.create(
                organization=self.organization,
                policy_no=f"POL-{unique_suffix}-{i}",
                company=self.company,
                insurance_type="property",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=365),
                total_insured_amount=100000 + i * 50000,
                total_premium=5000 + i * 1000,
                status='active',
                created_by=self.user
            )

        # Create a draft policy
        InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{unique_suffix}-draft",
            company=self.company,
            insurance_type="property",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_insured_amount=50000,
            total_premium=2000,
            status='draft',
            created_by=self.user
        )

        # DRF routers convert underscores to dashes by default
        url = '/api/insurance/policies/dashboard-stats/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_policies', response.data)
        self.assertIn('total_insured_amount', response.data)
        self.assertIn('total_annual_premium', response.data)
        self.assertEqual(response.data['total_policies'], 4)
        self.assertEqual(response.data['active_policies'], 3)
        self.assertEqual(response.data['draft_policies'], 1)


class PremiumPaymentAPITest(APITestCase):
    """PremiumPayment API Tests."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]

        self.organization = Organization.objects.create(
            name=f"Test Org Premium {self.unique_suffix}",
            code=f"TESTORG_PREMIUM_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_premium_{self.unique_suffix}",
            email=f"testpremium{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.client.force_authenticate(user=self.user)
        self.company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_PREMIUM_{self.unique_suffix}",
            name=f"Insurance Co Premium {self.unique_suffix}",
            created_by=self.user
        )
        self.policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-PREMIUM-{self.unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_insured_amount=100000,
            total_premium=5000,
            created_by=self.user
        )

    def test_list_payments(self):
        """Test listing premium payments."""
        unique_suffix = uuid.uuid4().hex[:8]
        for i in range(3):
            PremiumPayment.objects.create(
                organization=self.organization,
                policy=self.policy,
                payment_no=f"PAY-{unique_suffix}-{i}",
                due_date=date.today() + timedelta(days=30 * i),
                amount=1000 + i * 100,
                created_by=self.user
            )

        url = '/api/insurance/payments/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 3)

    def test_create_payment(self):
        """Test creating a premium payment."""
        unique_suffix = uuid.uuid4().hex[:8]
        url = '/api/insurance/payments/'
        data = {
            'policy': self.policy.id,
            'payment_no': f"PAY-{unique_suffix}",
            'due_date': str(date.today() + timedelta(days=30)),
            'amount': '1000.00',
            'status': 'pending'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['payment_no'], f"PAY-{unique_suffix}")

    def test_record_payment(self):
        """Test recording a payment."""
        unique_suffix = uuid.uuid4().hex[:8]
        payment = PremiumPayment.objects.create(
            organization=self.organization,
            policy=self.policy,
            payment_no=f"PAY-{unique_suffix}",
            due_date=date.today(),
            amount=1000,
            paid_amount=0,
            status='pending',
            created_by=self.user
        )

        url = f'/api/insurance/payments/{payment.id}/record_payment/'
        data = {'amount': 500, 'payment_method': 'bank_transfer'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['paid_amount']), 500)
        self.assertEqual(response.data['status'], 'partial')

    def test_filter_overdue_payments(self):
        """Test filtering overdue payments."""
        unique_suffix = uuid.uuid4().hex[:8]
        # Create overdue payment
        PremiumPayment.objects.create(
            organization=self.organization,
            policy=self.policy,
            payment_no=f"PAY-{unique_suffix}_1",
            due_date=date.today() - timedelta(days=10),
            amount=1000,
            status='pending',
            created_by=self.user
        )

        # Create pending payment not overdue
        PremiumPayment.objects.create(
            organization=self.organization,
            policy=self.policy,
            payment_no=f"PAY-{unique_suffix}_2",
            due_date=date.today() + timedelta(days=10),
            amount=1000,
            status='pending',
            created_by=self.user
        )

        url = '/api/insurance/payments/?overdue_only=true'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 1)


class ClaimRecordAPITest(APITestCase):
    """ClaimRecord API Tests."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]

        self.organization = Organization.objects.create(
            name=f"Test Org Claim {self.unique_suffix}",
            code=f"TESTORG_CLAIM_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_claim_{self.unique_suffix}",
            email=f"testclaim{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.client.force_authenticate(user=self.user)
        self.company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_CLAIM_{self.unique_suffix}",
            name=f"Insurance Co Claim {self.unique_suffix}",
            created_by=self.user
        )
        self.policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-CLAIM-{self.unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_insured_amount=100000,
            total_premium=5000,
            created_by=self.user
        )

    def test_list_claims(self):
        """Test listing claim records."""
        unique_suffix = uuid.uuid4().hex[:8]
        for i in range(3):
            ClaimRecord.objects.create(
                organization=self.organization,
                policy=self.policy,
                incident_date=date.today() - timedelta(days=i),
                incident_type='damage',
                incident_description=f"Test damage {unique_suffix} {i}",
                claimed_amount=10000 + i * 1000,
                created_by=self.user
            )

        url = '/api/insurance/claims/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['results']), 3)

    def test_create_claim(self):
        """Test creating a claim record."""
        url = '/api/insurance/claims/'
        data = {
            'policy': self.policy.id,
            'incident_date': str(date.today()),
            'incident_type': 'damage',
            'incident_description': 'Water damage from pipe burst',
            'claimed_amount': '10000.00'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['incident_type'], 'damage')

    def test_approve_claim(self):
        """Test approving a claim."""
        unique_suffix = uuid.uuid4().hex[:8]
        claim = ClaimRecord.objects.create(
            organization=self.organization,
            policy=self.policy,
            incident_date=date.today(),
            incident_type='damage',
            incident_description=f'Test damage {unique_suffix}',
            claimed_amount=10000,
            status='reported',
            created_by=self.user
        )

        url = f'/api/insurance/claims/{claim.id}/approve/'
        data = {'approved_amount': 8000}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
        self.assertEqual(float(response.data['approved_amount']), 8000)

    def test_reject_claim(self):
        """Test rejecting a claim."""
        unique_suffix = uuid.uuid4().hex[:8]
        claim = ClaimRecord.objects.create(
            organization=self.organization,
            policy=self.policy,
            incident_date=date.today(),
            incident_type='damage',
            incident_description=f'Test damage {unique_suffix}',
            claimed_amount=10000,
            status='reported',
            created_by=self.user
        )

        url = f'/api/insurance/claims/{claim.id}/reject/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rejected')

    def test_record_settlement(self):
        """Test recording claim settlement."""
        unique_suffix = uuid.uuid4().hex[:8]
        claim = ClaimRecord.objects.create(
            organization=self.organization,
            policy=self.policy,
            incident_date=date.today(),
            incident_type='damage',
            incident_description=f'Test damage {unique_suffix}',
            claimed_amount=10000,
            approved_amount=8000,
            status='approved',
            created_by=self.user
        )

        url = f'/api/insurance/claims/{claim.id}/record_settlement/'
        data = {'paid_amount': 8000, 'settlement_date': str(date.today())}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'paid')
        self.assertEqual(float(response.data['paid_amount']), 8000)

    def test_close_claim(self):
        """Test closing a claim."""
        unique_suffix = uuid.uuid4().hex[:8]
        claim = ClaimRecord.objects.create(
            organization=self.organization,
            policy=self.policy,
            incident_date=date.today(),
            incident_type='damage',
            incident_description=f'Test damage {unique_suffix}',
            claimed_amount=10000,
            approved_amount=8000,
            paid_amount=8000,
            status='paid',
            created_by=self.user
        )

        url = f'/api/insurance/claims/{claim.id}/close/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'closed')

    def test_record_payment_alias(self):
        """Test record-payment alias endpoint for claim settlement.

        This test verifies that the record-payment endpoint (used by frontend)
        works as an alias for the record_settlement endpoint.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        claim = ClaimRecord.objects.create(
            organization=self.organization,
            policy=self.policy,
            incident_date=date.today(),
            incident_type='damage',
            incident_description=f'Test damage {unique_suffix}',
            claimed_amount=10000,
            approved_amount=8000,
            status='approved',
            created_by=self.user
        )

        # Use record-payment URL (as called by frontend)
        url = f'/api/insurance/claims/{claim.id}/record-payment/'
        data = {'paid_amount': 7500, 'settlement_date': str(date.today())}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'paid')
        self.assertEqual(float(response.data['paid_amount']), 7500)
