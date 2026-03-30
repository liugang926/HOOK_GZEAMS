import uuid
from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import User, UserOrganization
from apps.assets.models import (
    Asset,
    AssetCategory,
    AssetLoan,
    AssetReturn,
    AssetTransfer,
    LoanItem,
    Location,
    ReturnItem,
    TransferItem,
)
from apps.organizations.models import Department, Organization


class AssetOperationApiCompatTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        suffix = uuid.uuid4().hex[:8]

        self.org = Organization.objects.create(
            name=f'Compat Org {suffix}',
            code=f'COMPAT_ORG_{suffix}',
        )
        self.user = User.objects.create_user(
            username=f'compat_user_{suffix}',
            password='pass123456',
            organization=self.org,
        )
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org,
            role='admin',
            is_active=True,
            is_primary=True,
        )
        self.user.current_organization = self.org
        self.user.save(update_fields=['current_organization'])

        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

        self.department = Department.objects.create(
            organization=self.org,
            code=f'DEPT_{suffix}',
            name='Compatibility Department',
        )
        self.target_department = Department.objects.create(
            organization=self.org,
            code=f'TGT_{suffix}',
            name='Compatibility Target Department',
        )
        self.location = Location.objects.create(
            organization=self.org,
            name='Compatibility Warehouse',
            location_type='warehouse',
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'CAT_{suffix}',
            name='Compatibility Category',
            created_by=self.user,
        )

    def tearDown(self):
        from apps.common.middleware import clear_current_organization

        clear_current_organization()
        super().tearDown()

    def _create_asset(self, name: str, *, status: str = 'idle', custodian=None):
        return Asset.objects.create(
            organization=self.org,
            asset_name=name,
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date=date.today(),
            asset_status=status,
            department=self.department,
            location=self.location,
            custodian=custodian,
            created_by=self.user,
        )

    def test_transfer_approve_and_reject_aliases(self):
        asset = self._create_asset('Transfer Alias Asset', custodian=self.user)
        transfer = AssetTransfer.objects.create(
            organization=self.org,
            from_department=self.department,
            to_department=self.target_department,
            transfer_date=date.today(),
            status='pending',
            created_by=self.user,
        )
        TransferItem.objects.create(
            organization=self.org,
            transfer=transfer,
            asset=asset,
            from_location=self.location,
            from_custodian=self.user,
            to_location=self.location,
        )

        approve_response = self.client.post(
            f'/api/assets/transfers/{transfer.id}/approve/',
            {'comment': 'Source department approved'},
            format='json',
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        transfer.refresh_from_db()
        self.assertEqual(transfer.status, 'out_approved')

        second_approve_response = self.client.post(
            f'/api/assets/transfers/{transfer.id}/approve/',
            {'comment': 'Target department approved'},
            format='json',
        )
        self.assertEqual(second_approve_response.status_code, status.HTTP_200_OK)
        transfer.refresh_from_db()
        self.assertEqual(transfer.status, 'approved')

        reject_transfer = AssetTransfer.objects.create(
            organization=self.org,
            from_department=self.department,
            to_department=self.target_department,
            transfer_date=date.today(),
            status='pending',
            created_by=self.user,
        )
        TransferItem.objects.create(
            organization=self.org,
            transfer=reject_transfer,
            asset=self._create_asset('Transfer Reject Asset', custodian=self.user),
            from_location=self.location,
            from_custodian=self.user,
            to_location=self.location,
        )

        reject_response = self.client.post(
            f'/api/assets/transfers/{reject_transfer.id}/reject/',
            {'reason': 'Rejected by source approver'},
            format='json',
        )
        self.assertEqual(reject_response.status_code, status.HTTP_200_OK)
        reject_transfer.refresh_from_db()
        self.assertEqual(reject_transfer.status, 'rejected')

    def test_loan_submit_cancel_and_return_aliases(self):
        draft_loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today(),
            status='draft',
            created_by=self.user,
        )
        LoanItem.objects.create(
            organization=self.org,
            loan=draft_loan,
            asset=self._create_asset('Loan Submit Asset'),
        )

        submit_response = self.client.post(f'/api/assets/loans/{draft_loan.id}/submit/')
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        draft_loan.refresh_from_db()
        self.assertEqual(draft_loan.status, 'pending')

        cancel_loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today(),
            status='draft',
            created_by=self.user,
        )
        LoanItem.objects.create(
            organization=self.org,
            loan=cancel_loan,
            asset=self._create_asset('Loan Cancel Asset'),
        )

        cancel_response = self.client.post(f'/api/assets/loans/{cancel_loan.id}/cancel/')
        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        cancel_loan.refresh_from_db()
        self.assertEqual(cancel_loan.status, 'cancelled')

        borrowed_loan = AssetLoan.objects.create(
            organization=self.org,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today(),
            status='borrowed',
            created_by=self.user,
        )
        LoanItem.objects.create(
            organization=self.org,
            loan=borrowed_loan,
            asset=self._create_asset('Loan Return Asset', status='in_use', custodian=self.user),
        )

        return_response = self.client.post(
            f'/api/assets/loans/{borrowed_loan.id}/return/',
            {'returnDate': str(date.today()), 'remark': 'Returned from compatibility test'},
            format='json',
        )
        self.assertEqual(return_response.status_code, status.HTTP_200_OK)
        borrowed_loan.refresh_from_db()
        self.assertEqual(borrowed_loan.status, 'returned')
        self.assertEqual(str(borrowed_loan.actual_return_date), str(date.today()))

    def test_return_submit_cancel_and_approve_aliases(self):
        submit_return = AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status='draft',
            created_by=self.user,
        )
        ReturnItem.objects.create(
            organization=self.org,
            asset_return=submit_return,
            asset=self._create_asset('Return Submit Asset', custodian=self.user),
            asset_status='idle',
        )

        submit_response = self.client.post(f'/api/assets/returns/{submit_return.id}/submit/')
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        submit_return.refresh_from_db()
        self.assertEqual(submit_return.status, 'pending')

        cancel_return = AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status='draft',
            created_by=self.user,
        )
        ReturnItem.objects.create(
            organization=self.org,
            asset_return=cancel_return,
            asset=self._create_asset('Return Cancel Asset', custodian=self.user),
            asset_status='idle',
        )

        cancel_response = self.client.post(f'/api/assets/returns/{cancel_return.id}/cancel/')
        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        cancel_return.refresh_from_db()
        self.assertEqual(cancel_return.status, 'cancelled')

        approve_return = AssetReturn.objects.create(
            organization=self.org,
            returner=self.user,
            return_date=date.today(),
            return_location=self.location,
            status='pending',
            created_by=self.user,
        )
        ReturnItem.objects.create(
            organization=self.org,
            asset_return=approve_return,
            asset=self._create_asset('Return Approve Asset', custodian=self.user),
            asset_status='idle',
        )

        approve_response = self.client.post(f'/api/assets/returns/{approve_return.id}/approve/')
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        approve_return.refresh_from_db()
        self.assertEqual(approve_return.status, 'completed')
