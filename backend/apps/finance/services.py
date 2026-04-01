"""
Finance management service layer.

Provides business logic for financial voucher lifecycle management,
voucher entry operations, and template-based voucher generation.
"""
import re
import uuid
from decimal import Decimal
from typing import Iterable

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.common.services.base_crud import BaseCRUDService
from .models import FinanceVoucher, VoucherEntry, VoucherTemplate


class FinanceVoucherService(BaseCRUDService):
    """Service layer for financial voucher lifecycle management."""

    def __init__(self):
        super().__init__(FinanceVoucher)

    @staticmethod
    def _generate_voucher_no(prefix='VCH'):
        """Generate a short unique voucher number."""
        return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"

    @staticmethod
    def _build_default_entries(total_amount, debit_desc='Debit', credit_desc='Credit'):
        """Build balanced placeholder entries for generated vouchers."""
        return [
            {
                'account_code': '1001',
                'account_name': 'Asset/Expense',
                'debit_amount': total_amount,
                'credit_amount': Decimal('0.00'),
                'description': debit_desc,
                'line_no': 1,
            },
            {
                'account_code': '2001',
                'account_name': 'Payable/Accumulated',
                'debit_amount': Decimal('0.00'),
                'credit_amount': total_amount,
                'description': credit_desc,
                'line_no': 2,
            },
        ]

    @staticmethod
    def _normalize_uuid_value(value):
        """Return a normalized UUID string or an empty string."""
        raw_value = str(value or '').strip()
        if not raw_value:
            return ''
        try:
            return str(uuid.UUID(raw_value))
        except (ValueError, TypeError, AttributeError):
            return ''

    @staticmethod
    def _humanize_object_code(value: str) -> str:
        """Convert an object code into a readable label."""
        normalized = str(value or '').strip()
        if not normalized:
            return ''
        return re.sub(r'(?<!^)(?=[A-Z])', ' ', normalized).replace('_', ' ').strip()

    def _build_source_trace_payload(
        self,
        *,
        primary_object_code='',
        primary_id='',
        primary_record_no='',
        requested_business_id='',
        asset_ids=None,
        asset_codes=None,
        purchase_request=None,
        receipt=None,
        extra=None,
    ):
        """Build a normalized source trace payload stored in custom fields."""
        normalized_asset_ids = [str(item).strip() for item in (asset_ids or []) if str(item).strip()]
        normalized_asset_codes = [str(item).strip() for item in (asset_codes or []) if str(item).strip()]
        asset_id_index = ''.join(f'|{asset_id}|' for asset_id in normalized_asset_ids)
        payload = {
            'source_object_code': str(primary_object_code or '').strip(),
            'source_object_label': self._humanize_object_code(str(primary_object_code or '').strip()),
            'source_id': str(primary_id or '').strip(),
            'source_record_no': str(primary_record_no or '').strip(),
            'requested_business_id': str(requested_business_id or '').strip(),
            'asset_ids': normalized_asset_ids,
            'asset_codes': normalized_asset_codes,
            'asset_id_index': asset_id_index,
            'source_purchase_request_id': '',
            'source_purchase_request_no': '',
            'source_receipt_id': '',
            'source_receipt_no': '',
        }

        if purchase_request is not None:
            payload['source_purchase_request_id'] = str(purchase_request.id)
            payload['source_purchase_request_no'] = str(getattr(purchase_request, 'request_no', '') or '').strip()
        if receipt is not None:
            payload['source_receipt_id'] = str(receipt.id)
            payload['source_receipt_no'] = str(getattr(receipt, 'receipt_no', '') or '').strip()
        if extra:
            payload.update(extra)

        return {
            'source_trace': payload,
            'source_object_code': payload['source_object_code'],
            'source_object_label': payload['source_object_label'],
            'source_id': payload['source_id'],
            'source_record_no': payload['source_record_no'],
            'requested_business_id': payload['requested_business_id'],
            'asset_ids': payload['asset_ids'],
            'asset_codes': payload['asset_codes'],
            'asset_id_index': payload['asset_id_index'],
            'source_purchase_request_id': payload['source_purchase_request_id'],
            'source_purchase_request_no': payload['source_purchase_request_no'],
            'source_receipt_id': payload['source_receipt_id'],
            'source_receipt_no': payload['source_receipt_no'],
        }

    def _build_asset_purchase_source_trace(self, *, assets, business_id, organization_id):
        """Build source trace for asset purchase voucher generation."""
        from apps.lifecycle.models import AssetReceipt, PurchaseRequest

        asset_list = list(assets)
        asset_ids = [str(asset.id) for asset in asset_list]
        asset_codes = [str(getattr(asset, 'asset_code', '') or '').strip() for asset in asset_list]

        normalized_business_id = self._normalize_uuid_value(business_id)
        purchase_request = None
        receipt = None
        primary_object_code = ''
        primary_id = ''
        primary_record_no = ''

        if normalized_business_id:
            purchase_request = PurchaseRequest.all_objects.filter(
                id=normalized_business_id,
                organization_id=organization_id,
                is_deleted=False,
            ).first()
            if purchase_request is not None:
                primary_object_code = 'PurchaseRequest'
                primary_id = str(purchase_request.id)
                primary_record_no = str(getattr(purchase_request, 'request_no', '') or '').strip()
            else:
                receipt = AssetReceipt.all_objects.filter(
                    id=normalized_business_id,
                    organization_id=organization_id,
                    is_deleted=False,
                ).first()
                if receipt is not None:
                    primary_object_code = 'AssetReceipt'
                    primary_id = str(receipt.id)
                    primary_record_no = str(getattr(receipt, 'receipt_no', '') or '').strip()

        if purchase_request is None:
            request_ids = {
                str(asset.source_purchase_request_id)
                for asset in asset_list
                if getattr(asset, 'source_purchase_request_id', None)
            }
            if len(request_ids) == 1:
                purchase_request = getattr(asset_list[0], 'source_purchase_request', None)
                if purchase_request is not None and not primary_object_code:
                    primary_object_code = 'PurchaseRequest'
                    primary_id = str(purchase_request.id)
                    primary_record_no = str(getattr(purchase_request, 'request_no', '') or '').strip()

        if receipt is None:
            receipt_ids = {
                str(asset.source_receipt_id)
                for asset in asset_list
                if getattr(asset, 'source_receipt_id', None)
            }
            if len(receipt_ids) == 1:
                receipt = getattr(asset_list[0], 'source_receipt', None)
                if receipt is not None and not primary_object_code:
                    primary_object_code = 'AssetReceipt'
                    primary_id = str(receipt.id)
                    primary_record_no = str(getattr(receipt, 'receipt_no', '') or '').strip()

        if not primary_object_code and len(asset_list) == 1:
            primary_object_code = 'Asset'
            primary_id = str(asset_list[0].id)
            primary_record_no = str(getattr(asset_list[0], 'asset_code', '') or '').strip()
        elif not primary_object_code:
            primary_object_code = 'Asset'
            primary_record_no = f'{len(asset_list)} assets'

        return self._build_source_trace_payload(
            primary_object_code=primary_object_code,
            primary_id=primary_id,
            primary_record_no=primary_record_no,
            requested_business_id=business_id,
            asset_ids=asset_ids,
            asset_codes=asset_codes,
            purchase_request=purchase_request,
            receipt=receipt,
        )

    def find_existing_voucher_by_source(
        self,
        *,
        organization_id,
        source_object_code='',
        source_id='',
        purchase_request_id='',
        receipt_id='',
    ):
        """Find an existing active voucher linked to the provided source scope."""
        source_filters = Q()
        normalized_source_object_code = str(source_object_code or '').strip()
        normalized_source_id = str(source_id or '').strip()
        normalized_purchase_request_id = str(purchase_request_id or '').strip()
        normalized_receipt_id = str(receipt_id or '').strip()

        if normalized_source_object_code and normalized_source_id:
            source_filters |= Q(
                custom_fields__source_object_code=normalized_source_object_code,
                custom_fields__source_id=normalized_source_id,
            )
        if normalized_purchase_request_id:
            source_filters |= Q(custom_fields__source_purchase_request_id=normalized_purchase_request_id)
        if normalized_receipt_id:
            source_filters |= Q(custom_fields__source_receipt_id=normalized_receipt_id)
        if not source_filters:
            return None

        return FinanceVoucher.objects.filter(
            organization_id=organization_id,
            is_deleted=False,
        ).filter(source_filters).order_by('-created_at').first()

    @transaction.atomic
    def generate_purchase_voucher_for_assets(
        self,
        *,
        assets: Iterable,
        organization_id,
        user,
        business_id='',
        voucher_date=None,
        notes='',
        summary='',
    ):
        """Generate a purchase voucher for the provided assets and source business object."""
        asset_list = list(assets)
        if not organization_id:
            raise ValidationError({'organization': ['Organization context is required.']})
        if not asset_list:
            raise ValidationError({'asset_ids': ['At least one asset is required to generate a finance voucher.']})

        total_amount = sum(
            (Decimal(str(getattr(asset, 'purchase_price', None) or '0.00')) for asset in asset_list),
            Decimal('0.00'),
        )
        total_amount = Decimal(str(total_amount or '0.00'))
        if total_amount <= 0:
            raise ValidationError({'asset_ids': ['No valid amount found from selected assets.']})

        source_trace = self._build_asset_purchase_source_trace(
            assets=asset_list,
            business_id=business_id,
            organization_id=organization_id,
        )
        existing_voucher = self.find_existing_voucher_by_source(
            organization_id=organization_id,
            source_object_code=source_trace.get('source_object_code', ''),
            source_id=source_trace.get('source_id', ''),
            purchase_request_id=source_trace.get('source_purchase_request_id', ''),
            receipt_id=source_trace.get('source_receipt_id', ''),
        )
        if existing_voucher is not None:
            raise ValidationError({
                'business_id': [f'Finance voucher {existing_voucher.voucher_no} already exists for this source.']
            })

        resolved_voucher_date = voucher_date or timezone.now().date()
        source_record_no = str(source_trace.get('source_record_no', '') or '').strip()
        resolved_summary = summary or f"Asset purchase voucher ({source_record_no or 'N/A'})"
        entries = self._build_default_entries(total_amount, 'Asset purchase debit', 'Asset purchase credit')

        voucher = FinanceVoucher.objects.create(
            organization_id=organization_id,
            voucher_no=self._generate_voucher_no(),
            voucher_date=resolved_voucher_date,
            business_type='purchase',
            summary=resolved_summary,
            total_amount=total_amount,
            status='draft',
            notes=str(notes or '').strip(),
            custom_fields=source_trace,
            created_by=user,
        )

        for entry in entries:
            VoucherEntry.objects.create(
                organization_id=organization_id,
                voucher=voucher,
                account_code=entry['account_code'],
                account_name=entry['account_name'],
                debit_amount=entry['debit_amount'],
                credit_amount=entry['credit_amount'],
                description=entry.get('description', ''),
                line_no=entry.get('line_no', 1),
                created_by=user,
            )

        return voucher

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
