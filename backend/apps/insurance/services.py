"""
Insurance management service layer.

Provides business logic encapsulation for insurance-related operations
following BaseCRUDService patterns.
"""
from decimal import Decimal
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

from apps.common.services.base_crud import BaseCRUDService
from apps.system.services.activity_log_service import ActivityLogService
from .models import (
    InsuranceCompany, InsurancePolicy, InsuredAsset,
    PremiumPayment, ClaimRecord, PolicyRenewal
)


def _normalize_free_text(value) -> str:
    return str(value or '').strip()


def _set_custom_field_text(instance, key: str, value) -> str:
    normalized_value = _normalize_free_text(value)
    custom_fields = dict(instance.custom_fields or {})

    if normalized_value:
        custom_fields[key] = normalized_value
    elif key in custom_fields:
        custom_fields.pop(key, None)

    instance.custom_fields = custom_fields
    return normalized_value


class InsuranceCompanyService(BaseCRUDService):
    """Service layer for insurance company management."""

    def __init__(self):
        super().__init__(InsuranceCompany)

    def get_active_companies(self, organization_id=None, user=None):
        """Get all active insurance companies."""
        return self.query(
            filters={'is_active': True},
            organization_id=organization_id,
            user=user,
        )

    def deactivate(self, company_id, organization_id=None, user=None):
        """Deactivate an insurance company."""
        company = self.get(company_id, organization_id=organization_id, user=user)
        company.is_active = False
        company.save(update_fields=['is_active', 'updated_at'])
        return company


class InsurancePolicyService(BaseCRUDService):
    """Service layer for insurance policy lifecycle management."""

    def __init__(self):
        super().__init__(InsurancePolicy)

    @transaction.atomic
    def activate(self, policy_id, organization_id=None, user=None):
        """Activate a draft policy and generate payment schedule."""
        policy = self.get(policy_id, organization_id=organization_id, user=user)
        if policy.status != 'draft':
            raise ValidationError({
                'status': ['Only draft policies can be activated.']
            })
        policy.status = 'active'
        policy.save(update_fields=['status', 'updated_at'])
        self._generate_payment_schedule(policy)
        return policy

    def cancel(self, policy_id, reason=None, organization_id=None, user=None):
        """Cancel a draft or active policy."""
        policy = self.get(policy_id, organization_id=organization_id, user=user)
        if policy.status not in ['draft', 'active']:
            raise ValidationError({
                'status': ['Only draft or active policies can be cancelled.']
            })
        before_snapshot = ActivityLogService.snapshot_instance(policy, fields={'status', 'custom_fields', 'notes'})
        policy.status = 'cancelled'
        normalized_reason = _set_custom_field_text(policy, 'cancel_reason', reason)
        if normalized_reason:
            existing_notes = str(policy.notes or '').strip()
            policy.notes = (
                f'{existing_notes}\n\nCancellation reason: {normalized_reason}'
                if existing_notes
                else f'Cancellation reason: {normalized_reason}'
            )
        policy.save(update_fields=['status', 'custom_fields', 'notes', 'updated_at'])
        if user is not None:
            ActivityLogService.log_update(
                actor=user,
                before_snapshot=before_snapshot,
                instance=policy,
                changed_fields={'status', 'custom_fields', 'notes'},
                organization=policy.organization,
            )
        return policy

    def get_expiring_soon(self, days=30, organization_id=None, user=None):
        """Get policies expiring within the specified number of days."""
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
        """Get aggregated insurance dashboard statistics."""
        policies = self.query(organization_id=organization_id, user=user)
        return {
            'total_policies': policies.count(),
            'active_policies': policies.filter(status='active').count(),
            'draft_policies': policies.filter(status='draft').count(),
            'expired_policies': policies.filter(status='expired').count(),
            'cancelled_policies': policies.filter(status='cancelled').count(),
            'total_insured_amount': policies.aggregate(
                total=Sum('total_insured_amount')
            )['total'] or Decimal('0'),
            'total_annual_premium': policies.aggregate(
                total=Sum('total_premium')
            )['total'] or Decimal('0'),
        }

    def _generate_payment_schedule(self, policy):
        """Generate premium payment records based on payment frequency."""
        frequency_map = {
            'one_time': (1, 0),
            'annual': (1, 12),
            'semi_annual': (2, 6),
            'quarterly': (4, 3),
            'monthly': (12, 1),
        }
        num_payments, months_interval = frequency_map.get(
            policy.payment_frequency, (1, 12)
        )

        payment_amount = policy.total_premium / Decimal(num_payments)
        current_date = policy.start_date

        for i in range(num_payments):
            if i == 0:
                due_date = policy.start_date
            else:
                year = current_date.year + (current_date.month + months_interval - 1) // 12
                month = (current_date.month + months_interval - 1) % 12 + 1
                max_day = [31, 29 if year % 4 == 0 else 28,
                           31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
                day = min(current_date.day, max_day)
                due_date = date(year, month, day)
                current_date = due_date

            if due_date > policy.end_date:
                break

            PremiumPayment.objects.create(
                organization=policy.organization,
                policy=policy,
                payment_no=f"PAY-{policy.policy_no}-{i + 1:03d}",
                due_date=due_date,
                amount=payment_amount,
                paid_amount=Decimal('0'),
                status='pending',
                created_by=policy.created_by,
            )


class PremiumPaymentService(BaseCRUDService):
    """Service layer for premium payment processing."""

    def __init__(self):
        super().__init__(PremiumPayment)

    @transaction.atomic
    def record_payment(self, payment_id, amount, payment_method='',
                       payment_reference='', paid_date=None,
                       organization_id=None, user=None):
        """Record a payment against a premium."""
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
        """Get all overdue pending/partial payments."""
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


class ClaimRecordService(BaseCRUDService):
    """Service layer for insurance claim lifecycle management."""

    def __init__(self):
        super().__init__(ClaimRecord)

    def approve(self, claim_id, approved_amount=None,
                organization_id=None, user=None):
        """Approve a reported or investigating claim."""
        claim = self.get(claim_id, organization_id=organization_id, user=user)
        if claim.status not in ['reported', 'investigating']:
            raise ValidationError({
                'status': ['Only reported or investigating claims can be approved.']
            })
        if approved_amount is not None:
            claim.approved_amount = Decimal(str(approved_amount))
        claim.status = 'approved'
        claim.save()
        return claim

    def reject(self, claim_id, organization_id=None, user=None):
        """Reject a claim."""
        claim = self.get(claim_id, organization_id=organization_id, user=user)
        if claim.status not in ['reported', 'investigating', 'approved']:
            raise ValidationError({
                'status': ['This claim cannot be rejected in its current state.']
            })
        claim.status = 'rejected'
        claim.save(update_fields=['status', 'updated_at'])
        return claim

    @transaction.atomic
    def record_settlement(self, claim_id, paid_amount, paid_date=None,
                          settlement_date=None, settlement_notes='',
                          organization_id=None, user=None):
        """Record a settlement payment for an approved claim."""
        claim = self.get(claim_id, organization_id=organization_id, user=user)
        if claim.status != 'approved':
            raise ValidationError({
                'status': ['Only approved claims can be settled.']
            })
        claim.paid_amount = Decimal(str(paid_amount))
        claim.status = 'paid'
        claim.paid_date = paid_date
        claim.settlement_date = settlement_date
        claim.settlement_notes = settlement_notes
        claim.save()
        return claim

    def close(self, claim_id, organization_id=None, user=None):
        """Close a paid or rejected claim."""
        claim = self.get(claim_id, organization_id=organization_id, user=user)
        if claim.status not in ['paid', 'rejected']:
            raise ValidationError({
                'status': ['Only paid or rejected claims can be closed.']
            })
        claim.status = 'closed'
        claim.save(update_fields=['status', 'updated_at'])
        return claim


class PolicyRenewalService(BaseCRUDService):
    """Service layer for policy renewal tracking."""

    def __init__(self):
        super().__init__(PolicyRenewal)
