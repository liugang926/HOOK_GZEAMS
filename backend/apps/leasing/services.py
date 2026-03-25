"""
Leasing management service layer.

Provides business logic encapsulation for lease contract lifecycle,
rent payment processing, asset return handling, and lease extensions.
"""
from decimal import Decimal
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.common.services.base_crud import BaseCRUDService
from .models import (
    LeaseContract, LeaseItem, RentPayment,
    LeaseReturn, LeaseExtension
)


class LeaseContractService(BaseCRUDService):
    """Service layer for lease contract lifecycle management."""

    def __init__(self):
        super().__init__(LeaseContract)

    @transaction.atomic
    def activate(self, contract_id, actual_start_date=None,
                 organization_id=None, user=None):
        """Activate a draft contract (assets delivered to lessee)."""
        contract = self.get(contract_id, organization_id=organization_id, user=user)
        if contract.status != 'draft':
            raise ValidationError({
                'status': ['Only draft contracts can be activated.']
            })
        contract.status = 'active'
        contract.actual_start_date = actual_start_date or timezone.now().date()
        contract.save(update_fields=['status', 'actual_start_date', 'updated_at'])
        return contract

    def suspend(self, contract_id, organization_id=None, user=None):
        """Suspend an active contract."""
        contract = self.get(contract_id, organization_id=organization_id, user=user)
        if contract.status != 'active':
            raise ValidationError({
                'status': ['Only active contracts can be suspended.']
            })
        contract.status = 'suspended'
        contract.save(update_fields=['status', 'updated_at'])
        return contract

    @transaction.atomic
    def terminate(self, contract_id, actual_end_date=None,
                  organization_id=None, user=None):
        """Terminate an active or suspended contract."""
        contract = self.get(contract_id, organization_id=organization_id, user=user)
        if contract.status not in ['active', 'suspended']:
            raise ValidationError({
                'status': ['Only active or suspended contracts can be terminated.']
            })
        contract.status = 'terminated'
        contract.actual_end_date = actual_end_date or timezone.now().date()
        contract.save(update_fields=['status', 'actual_end_date', 'updated_at'])
        return contract

    @transaction.atomic
    def complete(self, contract_id, actual_end_date=None,
                 organization_id=None, user=None):
        """Complete an active contract (all assets returned)."""
        contract = self.get(contract_id, organization_id=organization_id, user=user)
        if contract.status != 'active':
            raise ValidationError({
                'status': ['Only active contracts can be marked as completed.']
            })
        contract.status = 'completed'
        contract.actual_end_date = actual_end_date or timezone.now().date()
        contract.save(update_fields=['status', 'actual_end_date', 'updated_at'])
        return contract

    def get_expiring_contracts(self, days=30, organization_id=None, user=None):
        """Get contracts expiring within the specified number of days."""
        today = timezone.now().date()
        cutoff = today + timedelta(days=days)
        return self.query(
            filters={
                'status': 'active',
                'end_date__lte': cutoff,
                'end_date__gte': today,
            },
            order_by='end_date',
            organization_id=organization_id,
            user=user,
        )

    def get_dashboard_stats(self, organization_id=None, user=None):
        """Get aggregated leasing dashboard statistics."""
        contracts = self.query(organization_id=organization_id, user=user)
        return {
            'total_contracts': contracts.count(),
            'active_contracts': contracts.filter(status='active').count(),
            'draft_contracts': contracts.filter(status='draft').count(),
            'completed_contracts': contracts.filter(status='completed').count(),
            'terminated_contracts': contracts.filter(status='terminated').count(),
            'total_rent': contracts.aggregate(
                total=Sum('total_rent')
            )['total'] or Decimal('0'),
            'total_deposit': contracts.aggregate(
                total=Sum('deposit_amount')
            )['total'] or Decimal('0'),
        }


class LeaseItemService(BaseCRUDService):
    """Service layer for lease item management."""

    def __init__(self):
        super().__init__(LeaseItem)


class RentPaymentService(BaseCRUDService):
    """Service layer for rent payment processing."""

    def __init__(self):
        super().__init__(RentPayment)

    @transaction.atomic
    def record_payment(self, payment_id, amount, payment_method='',
                       payment_reference='', paid_date=None,
                       organization_id=None, user=None):
        """Record a rent payment."""
        payment = self.get(payment_id, organization_id=organization_id, user=user)
        if payment.status in ['paid', 'waived']:
            raise ValidationError({
                'status': ['Payment is already finalized.']
            })

        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValidationError({
                'amount': ['Payment amount must be positive.']
            })

        payment.paid_amount += amount
        payment.payment_method = payment_method or payment.payment_method
        payment.payment_reference = payment_reference or payment.payment_reference

        if payment.paid_amount >= payment.amount:
            payment.status = 'paid'
            payment.paid_date = paid_date or timezone.now().date()
        elif payment.paid_amount > 0:
            payment.status = 'partial'

        payment.save()
        return payment

    def get_overdue_payments(self, organization_id=None, user=None):
        """Get all overdue rent payments."""
        today = timezone.now().date()
        return self.query(
            filters={
                'status__in': ['pending', 'partial'],
                'due_date__lt': today,
            },
            order_by='due_date',
            organization_id=organization_id,
            user=user,
        )


class LeaseReturnService(BaseCRUDService):
    """Service layer for lease return processing."""

    def __init__(self):
        super().__init__(LeaseReturn)

    def calculate_charges(self, return_id, organization_id=None, user=None):
        """Calculate damage fees and deposit deductions for a return."""
        lease_return = self.get(return_id, organization_id=organization_id, user=user)
        contract = lease_return.contract

        # Calculate deposit refund: deposit_paid - damage_fee
        refund_amount = max(
            Decimal('0'),
            Decimal(str(contract.deposit_paid)) - lease_return.damage_fee
        )
        lease_return.deposit_deduction = min(
            lease_return.damage_fee,
            Decimal(str(contract.deposit_paid))
        )
        lease_return.refund_amount = refund_amount
        lease_return.save(update_fields=[
            'deposit_deduction', 'refund_amount', 'updated_at'
        ])
        return lease_return


class LeaseExtensionService(BaseCRUDService):
    """Service layer for lease extension management."""

    def __init__(self):
        super().__init__(LeaseExtension)

    @transaction.atomic
    def approve_extension(self, extension_id, approved_by=None,
                          organization_id=None, user=None):
        """Approve an extension and update the parent contract's end date."""
        extension = self.get(extension_id, organization_id=organization_id, user=user)
        contract = extension.contract

        extension.approved_by = approved_by or user
        extension.approved_at = timezone.now()
        extension.save(update_fields=['approved_by', 'approved_at', 'updated_at'])

        # Update contract end date
        contract.end_date = extension.new_end_date
        contract.total_rent += extension.additional_rent
        contract.save(update_fields=['end_date', 'total_rent', 'updated_at'])

        return extension
