"""
Insurance management viewsets.

This module contains viewsets for insurance-related models.
"""

import uuid
from decimal import Decimal
from datetime import date, timedelta
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from .models import (
    InsuranceCompany, InsurancePolicy, InsuredAsset,
    PremiumPayment, ClaimRecord, PolicyRenewal
)
from .serializers import (
    InsuranceCompanySerializer, InsurancePolicySerializer,
    InsuredAssetSerializer, PremiumPaymentSerializer,
    ClaimRecordSerializer, PolicyRenewalSerializer
)
from .filters import (
    InsuranceCompanyFilter, InsurancePolicyFilter,
    InsuredAssetFilter, PremiumPaymentFilter,
    ClaimRecordFilter, PolicyRenewalFilter
)


class InsuranceCompanyViewSet(BaseModelViewSetWithBatch):
    """Insurance Company ViewSet."""

    queryset = InsuranceCompany.objects.all()
    serializer_class = InsuranceCompanySerializer
    filterset_class = InsuranceCompanyFilter
    search_fields = ['code', 'name', 'short_name', 'contact_person']
    ordering_fields = ['code', 'name', 'created_at']


class InsurancePolicyViewSet(BaseModelViewSetWithBatch):
    """Insurance Policy ViewSet."""

    queryset = InsurancePolicy.objects.select_related(
        'company', 'organization', 'created_by'
    ).prefetch_related(
        'insured_assets', 'payments', 'claims'
    ).all()
    serializer_class = InsurancePolicySerializer
    filterset_class = InsurancePolicyFilter
    search_fields = ['policy_no', 'policy_name', 'company__name']
    ordering_fields = ['policy_no', 'start_date', 'end_date', 'total_premium', 'created_at']

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get insurance dashboard statistics."""
        from django.db.models import Sum

        policies = self.filter_queryset(self.get_queryset())

        stats = {
            'total_policies': policies.count(),
            'active_policies': policies.filter(status='active').count(),
            'draft_policies': policies.filter(status='draft').count(),
            'expired_policies': policies.filter(status='expired').count(),
            'cancelled_policies': policies.filter(status='cancelled').count(),
            'total_insured_amount': policies.aggregate(
                total=Sum('total_insured_amount')
            )['total'] or 0,
            'total_annual_premium': policies.aggregate(
                total=Sum('total_premium')
            )['total'] or 0,
            'unpaid_premium': policies.filter(
                status='active'
            ).aggregate(
                total=Sum('total_premium')
            )['total'] or 0,
        }

        return Response(stats)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a draft policy."""
        policy = self.get_object()
        if policy.status != 'draft':
            return Response(
                {'error': 'Only draft policies can be activated.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        policy.status = 'active'
        policy.save(update_fields=['status'])

        # Generate payment schedule
        self._generate_payment_schedule(policy)

        serializer = self.get_serializer(policy)
        return Response(serializer.data)

    def _generate_payment_schedule(self, policy):
        """Generate premium payment schedule for a policy.

        Creates payment records based on the policy's payment_frequency:
        - one_time: 1 payment due on start_date
        - annual: 1 payment per year
        - semi_annual: 2 payments per year
        - quarterly: 4 payments per year
        - monthly: 12 payments per year
        """
        if policy.payment_frequency == 'one_time':
            num_payments = 1
            months_interval = 0
        elif policy.payment_frequency == 'annual':
            num_payments = 1
            months_interval = 12
        elif policy.payment_frequency == 'semi_annual':
            num_payments = 2
            months_interval = 6
        elif policy.payment_frequency == 'quarterly':
            num_payments = 4
            months_interval = 3
        elif policy.payment_frequency == 'monthly':
            num_payments = 12
            months_interval = 1
        else:
            # Default to annual if unknown frequency
            num_payments = 1
            months_interval = 12

        # Calculate payment amount
        payment_amount = policy.total_premium / Decimal(num_payments)

        # Generate payment records
        from django.utils import timezone
        current_date = policy.start_date
        user = policy.created_by

        for i in range(num_payments):
            # Calculate due date
            if i == 0:
                due_date = policy.start_date
            else:
                # Add months to the start date
                year = current_date.year + (current_date.month + months_interval - 1) // 12
                month = (current_date.month + months_interval - 1) % 12 + 1
                # Keep the same day, but cap at last day of month
                day = min(current_date.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
                due_date = date(year, month, day)
                current_date = due_date

            # Skip if due date is beyond policy end date
            if due_date > policy.end_date:
                break

            # Generate payment number
            payment_no = f"PAY-{policy.policy_no}-{i + 1:03d}"

            PremiumPayment.objects.create(
                organization=policy.organization,
                policy=policy,
                payment_no=payment_no,
                due_date=due_date,
                amount=payment_amount,
                paid_amount=Decimal('0'),
                status='pending',
                created_by=user
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an active policy."""
        policy = self.get_object()
        if policy.status not in ['draft', 'active']:
            return Response(
                {'error': 'Only draft or active policies can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        policy.status = 'cancelled'
        policy.save(update_fields=['status'])
        serializer = self.get_serializer(policy)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get policy summary with statistics."""
        policy = self.get_object()
        return Response({
            'id': str(policy.id),
            'policy_no': policy.policy_no,
            'company': policy.company.name,
            'status': policy.status,
            'is_active': policy.is_active,
            'days_until_expiry': policy.days_until_expiry,
            'is_expiring_soon': policy.is_expiring_soon,
            'total_insured_assets': policy.total_insured_assets,
            'total_claims': policy.total_claims,
            'total_claim_amount': float(policy.total_claim_amount),
            'unpaid_premium': float(policy.unpaid_premium),
        })


class InsuredAssetViewSet(BaseModelViewSetWithBatch):
    """Insured Asset ViewSet."""

    queryset = InsuredAsset.objects.select_related(
        'policy', 'asset', 'organization'
    ).all()
    serializer_class = InsuredAssetSerializer
    filterset_class = InsuredAssetFilter
    search_fields = ['asset__asset_code', 'asset__asset_name']
    ordering_fields = ['insured_amount', 'premium_amount', 'created_at']


class PremiumPaymentViewSet(BaseModelViewSetWithBatch):
    """Premium Payment ViewSet."""

    queryset = PremiumPayment.objects.select_related(
        'policy', 'policy__company', 'organization'
    ).all()
    serializer_class = PremiumPaymentSerializer
    filterset_class = PremiumPaymentFilter
    search_fields = ['payment_no', 'policy__policy_no', 'invoice_no']
    ordering_fields = ['due_date', 'amount', 'created_at']

    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """Record a payment for this premium."""
        payment = self.get_object()
        if payment.status in ['paid', 'waived']:
            return Response(
                {'error': 'Payment is already final.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        amount = request.data.get('amount', 0)
        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid payment amount.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount <= 0:
            return Response(
                {'error': 'Payment amount must be positive.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.paid_amount += amount
        payment.payment_method = request.data.get('payment_method', payment.payment_method)
        payment.payment_reference = request.data.get('payment_reference', payment.payment_reference)

        # Update status
        if payment.paid_amount >= payment.amount:
            payment.status = 'paid'
            payment.paid_date = request.data.get('paid_date')
        elif payment.paid_amount > 0:
            payment.status = 'partial'

        payment.save()
        serializer = self.get_serializer(payment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_overdue(self, request, pk=None):
        """Mark a pending payment as overdue."""
        payment = self.get_object()
        if payment.status != 'pending':
            return Response(
                {'error': 'Only pending payments can be marked as overdue.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        payment.status = 'overdue'
        payment.save(update_fields=['status'])
        serializer = self.get_serializer(payment)
        return Response(serializer.data)


class ClaimRecordViewSet(BaseModelViewSetWithBatch):
    """Claim Record ViewSet."""

    queryset = ClaimRecord.objects.select_related(
        'policy', 'policy__company', 'asset', 'organization'
    ).all()
    serializer_class = ClaimRecordSerializer
    filterset_class = ClaimRecordFilter
    search_fields = ['claim_no', 'incident_description', 'adjuster_name']
    ordering_fields = ['incident_date', 'claimed_amount', 'created_at']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a claim."""
        claim = self.get_object()
        if claim.status not in ['reported', 'investigating']:
            return Response(
                {'error': 'Only reported or investigating claims can be approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        approved_amount = request.data.get('approved_amount')
        if approved_amount is not None:
            try:
                claim.approved_amount = Decimal(str(approved_amount))
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid approved amount.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        claim.status = 'approved'
        claim.save()
        serializer = self.get_serializer(claim)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a claim."""
        claim = self.get_object()
        if claim.status not in ['reported', 'investigating', 'approved']:
            return Response(
                {'error': 'This claim cannot be rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        claim.status = 'rejected'
        claim.save(update_fields=['status'])
        serializer = self.get_serializer(claim)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def record_settlement(self, request, pk=None):
        """Record claim settlement payment."""
        claim = self.get_object()
        if claim.status != 'approved':
            return Response(
                {'error': 'Only approved claims can be settled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        paid_amount = request.data.get('paid_amount')
        if paid_amount is None:
            return Response(
                {'error': 'Paid amount is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            claim.paid_amount = Decimal(str(paid_amount))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid paid amount.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        claim.status = 'paid'
        claim.paid_date = request.data.get('paid_date')
        claim.settlement_date = request.data.get('settlement_date')
        claim.settlement_notes = request.data.get('settlement_notes', '')
        claim.save()
        serializer = self.get_serializer(claim)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='record-payment')
    def record_payment(self, request, pk=None):
        """Alias for record_settlement - used by frontend.

        This endpoint provides compatibility with the frontend API
        which expects 'record-payment' URL format.
        """
        return self.record_settlement(request, pk=pk)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a claim."""
        claim = self.get_object()
        if claim.status not in ['paid', 'rejected']:
            return Response(
                {'error': 'Only paid or rejected claims can be closed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        claim.status = 'closed'
        claim.save(update_fields=['status'])
        serializer = self.get_serializer(claim)
        return Response(serializer.data)


class PolicyRenewalViewSet(BaseModelViewSetWithBatch):
    """Policy Renewal ViewSet."""

    queryset = PolicyRenewal.objects.select_related(
        'original_policy', 'renewed_policy', 'organization'
    ).all()
    serializer_class = PolicyRenewalSerializer
    filterset_class = PolicyRenewalFilter
    search_fields = ['renewal_no']
    ordering_fields = ['created_at', 'new_start_date', 'new_end_date']
