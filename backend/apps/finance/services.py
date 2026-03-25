"""
Finance management service layer.

Provides business logic for financial voucher lifecycle management,
voucher entry operations, and template-based voucher generation.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.common.services.base_crud import BaseCRUDService
from .models import FinanceVoucher, VoucherEntry, VoucherTemplate


class FinanceVoucherService(BaseCRUDService):
    """Service layer for financial voucher lifecycle management."""

    def __init__(self):
        super().__init__(FinanceVoucher)

    def submit(self, voucher_id, organization_id=None, user=None):
        """Submit a draft voucher for approval."""
        voucher = self.get(voucher_id, organization_id=organization_id, user=user)
        if not voucher.can_submit():
            if voucher.status != 'draft':
                raise ValidationError({
                    'status': ['Only draft vouchers can be submitted.']
                })
            if not voucher.is_balanced():
                raise ValidationError({
                    'entries': ['Voucher debits must equal credits before submitting.']
                })
        voucher.status = 'submitted'
        voucher.save(update_fields=['status', 'updated_at'])
        return voucher

    def approve(self, voucher_id, organization_id=None, user=None):
        """Approve a submitted voucher."""
        voucher = self.get(voucher_id, organization_id=organization_id, user=user)
        if not voucher.can_approve():
            raise ValidationError({
                'status': ['Only submitted vouchers can be approved.']
            })
        voucher.status = 'approved'
        voucher.save(update_fields=['status', 'updated_at'])
        return voucher

    def reject(self, voucher_id, organization_id=None, user=None):
        """Reject a submitted voucher back to draft."""
        voucher = self.get(voucher_id, organization_id=organization_id, user=user)
        if voucher.status != 'submitted':
            raise ValidationError({
                'status': ['Only submitted vouchers can be rejected.']
            })
        voucher.status = 'rejected'
        voucher.save(update_fields=['status', 'updated_at'])
        return voucher

    @transaction.atomic
    def post_voucher(self, voucher_id, erp_voucher_no='',
                     organization_id=None, user=None):
        """Post an approved voucher to ERP system."""
        voucher = self.get(voucher_id, organization_id=organization_id, user=user)
        if not voucher.can_post():
            raise ValidationError({
                'status': ['Only approved vouchers without ERP numbers can be posted.']
            })
        voucher.status = 'posted'
        voucher.erp_voucher_no = erp_voucher_no
        voucher.posted_at = timezone.now()
        voucher.posted_by = user
        voucher.save(update_fields=[
            'status', 'erp_voucher_no', 'posted_at', 'posted_by', 'updated_at'
        ])
        return voucher

    @transaction.atomic
    def reverse_voucher(self, voucher_id, organization_id=None, user=None):
        """Create a reversal voucher for a posted voucher.

        Generates a new voucher with swapped debit/credit entries.
        """
        original = self.get(voucher_id, organization_id=organization_id, user=user)
        if original.status != 'posted':
            raise ValidationError({
                'status': ['Only posted vouchers can be reversed.']
            })

        # Create reversal voucher
        reversal = FinanceVoucher.objects.create(
            organization=original.organization,
            voucher_no=f"REV-{original.voucher_no}",
            voucher_date=timezone.now().date(),
            business_type=original.business_type,
            summary=f"Reversal of {original.voucher_no}: {original.summary}",
            total_amount=original.total_amount,
            status='draft',
            notes=f"Auto-generated reversal for {original.voucher_no}",
            created_by=user,
        )

        # Create reversed entries (swap debit/credit)
        for entry in original.entries.all():
            VoucherEntry.objects.create(
                organization=original.organization,
                voucher=reversal,
                account_code=entry.account_code,
                account_name=entry.account_name,
                debit_amount=entry.credit_amount,
                credit_amount=entry.debit_amount,
                description=f"Reversal: {entry.description}",
                line_no=entry.line_no,
                created_by=user,
            )

        return reversal


class VoucherEntryService(BaseCRUDService):
    """Service layer for voucher entry operations."""

    def __init__(self):
        super().__init__(VoucherEntry)


class VoucherTemplateService(BaseCRUDService):
    """Service layer for voucher template management."""

    def __init__(self):
        super().__init__(VoucherTemplate)

    def get_active_templates(self, business_type=None,
                             organization_id=None, user=None):
        """Get active voucher templates, optionally filtered by business type."""
        filters = {'is_active': True}
        if business_type:
            filters['business_type'] = business_type
        return self.query(
            filters=filters,
            order_by='code',
            organization_id=organization_id,
            user=user,
        )

    @transaction.atomic
    def generate_voucher_from_template(self, template_id, voucher_date,
                                       amount, summary='',
                                       organization_id=None, user=None):
        """Generate a voucher from a template configuration.

        The template_config JSON defines account mappings and amount formulas.
        Expected format:
        {
            "entries": [
                {"account_code": "1001", "account_name": "Fixed Assets", "type": "debit"},
                {"account_code": "2001", "account_name": "Accounts Payable", "type": "credit"}
            ]
        }
        """
        template = self.get(template_id, organization_id=organization_id, user=user)
        if not template.is_active:
            raise ValidationError({
                'is_active': ['Template is not active.']
            })

        amount = Decimal(str(amount))
        config = template.template_config or {}
        entry_defs = config.get('entries', [])

        # Generate unique voucher number
        import uuid
        voucher_no = f"V{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"

        voucher = FinanceVoucher.objects.create(
            organization_id=organization_id,
            voucher_no=voucher_no,
            voucher_date=voucher_date,
            business_type=template.business_type,
            summary=summary or f"Generated from template: {template.name}",
            total_amount=amount,
            status='draft',
            created_by=user,
        )

        # Create entries from template definition
        for idx, entry_def in enumerate(entry_defs, start=1):
            entry_type = entry_def.get('type', 'debit')
            VoucherEntry.objects.create(
                organization_id=organization_id,
                voucher=voucher,
                account_code=entry_def.get('account_code', ''),
                account_name=entry_def.get('account_name', ''),
                debit_amount=amount if entry_type == 'debit' else Decimal('0'),
                credit_amount=amount if entry_type == 'credit' else Decimal('0'),
                description=entry_def.get('description', template.name),
                line_no=idx,
                created_by=user,
            )

        return voucher
