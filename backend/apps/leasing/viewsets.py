"""
Leasing management viewsets.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Exists, OuterRef, Q
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.filters.base import BaseModelFilter
from .models import (
    LeaseContract, LeaseItem, RentPayment,
    LeaseReturn, LeaseExtension
)
from .serializers import (
    LeaseContractSerializer, LeaseItemSerializer, RentPaymentSerializer,
    LeaseReturnSerializer, LeaseExtensionSerializer
)
from .filters import (
    LeaseContractFilter, RentPaymentFilter, LeaseReturnFilter,
    LeaseItemFilter, LeaseExtensionFilter
)


class LeaseContractViewSet(BaseModelViewSetWithBatch):
    """Lease Contract ViewSet."""
    queryset = LeaseContract.objects.all()
    serializer_class = LeaseContractSerializer
    filterset_class = LeaseContractFilter

    def perform_create(self, serializer):
        """Set organization and created_by."""
        serializer.save(
            organization_id=self.request.user.organization_id,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a draft contract."""
        contract = self.get_object()

        if contract.status != 'draft':
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Only draft contracts can be activated'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        contract.status = 'active'
        contract.actual_start_date = timezone.now().date()
        contract.approved_by = request.user
        contract.approved_at = timezone.now()
        contract.save()

        # Generate payment schedule
        self._generate_payment_schedule(contract)

        serializer = self.get_serializer(contract)
        return Response({
            'success': True,
            'message': 'Contract activated successfully',
            'data': serializer.data
        })

    def _generate_payment_schedule(self, contract):
        """Generate rent payment schedule based on payment type."""
        from .models import RentPayment

        if contract.payment_type == 'one_time':
            RentPayment.objects.create(
                organization_id=contract.organization_id,
                contract=contract,
                due_date=contract.start_date,
                amount=contract.total_rent,
                created_by=contract.created_by
            )
            return

        # Calculate payment intervals
        intervals = {
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
        }

        interval = intervals.get(contract.payment_type, timedelta(days=30))
        total_days = contract.total_days() or 30
        payment_count = max(1, int(total_days / interval.days))
        payment_amount = contract.total_rent / payment_count

        current_date = contract.start_date
        for i in range(payment_count):
            RentPayment.objects.create(
                organization_id=contract.organization_id,
                contract=contract,
                due_date=current_date,
                amount=round(payment_amount, 2),
                created_by=contract.created_by
            )
            current_date += interval

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete/Close a contract."""
        contract = self.get_object()

        if contract.status not in ['active', 'suspended']:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Only active or suspended contracts can be completed'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        contract.status = 'completed'
        contract.actual_end_date = timezone.now().date()
        contract.save()

        serializer = self.get_serializer(contract)
        return Response({
            'success': True,
            'message': 'Contract completed',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate a contract."""
        contract = self.get_object()

        if contract.status != 'active':
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Only active contracts can be terminated'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get('reason', '')

        contract.status = 'terminated'
        contract.actual_end_date = timezone.now().date()
        contract.notes = f"{contract.notes}\nTerminated: {reason}".strip() if reason else contract.notes
        contract.save()

        serializer = self.get_serializer(contract)
        return Response({
            'success': True,
            'message': 'Contract terminated',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get contracts expiring within 30 days."""
        delta = timezone.now().date() + timedelta(days=30)

        contracts = self.queryset.filter(
            end_date__lte=delta,
            status='active'
        )

        page = self.paginate_queryset(contracts)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get contracts with overdue payments."""
        from .models import RentPayment

        overdue_payments = RentPayment.objects.filter(
            contract=OuterRef('pk'),
            due_date__lt=timezone.now().date(),
            status__in=['pending', 'partial']
        )

        contracts = self.queryset.filter(
            status='active'
        ).filter(Exists(overdue_payments))

        page = self.paginate_queryset(contracts)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend an active contract."""
        contract = self.get_object()

        if contract.status != 'active':
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Only active contracts can be suspended'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        contract.status = 'suspended'
        contract.save()

        serializer = self.get_serializer(contract)
        return Response({
            'success': True,
            'message': 'Contract suspended',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a suspended contract."""
        contract = self.get_object()

        if contract.status != 'suspended':
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Only suspended contracts can be reactivated'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        contract.status = 'active'
        contract.save()

        serializer = self.get_serializer(contract)
        return Response({
            'success': True,
            'message': 'Contract reactivated',
            'data': serializer.data
        })


class LeaseItemViewSet(BaseModelViewSetWithBatch):
    """Lease Item ViewSet."""
    queryset = LeaseItem.objects.all()
    serializer_class = LeaseItemSerializer
    filterset_class = LeaseItemFilter

    def perform_create(self, serializer):
        """Set organization and created_by."""
        serializer.save(
            organization_id=self.request.user.organization_id,
            created_by=self.request.user
        )


class RentPaymentViewSet(BaseModelViewSetWithBatch):
    """Rent Payment ViewSet."""
    queryset = RentPayment.objects.all()
    serializer_class = RentPaymentSerializer
    filterset_class = RentPaymentFilter

    def perform_create(self, serializer):
        """Set organization and created_by."""
        serializer.save(
            organization_id=self.request.user.organization_id,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """Record a payment."""
        payment = self.get_object()

        from decimal import Decimal
        amount = request.data.get('amount', 0)
        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            amount = Decimal('0')

        if amount <= 0:
            return Response(
                {
                    'success': False,
                    'error': {'code': 'INVALID_AMOUNT', 'message': 'Amount must be positive'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.paid_amount += amount
        payment.paid_date = timezone.now().date()
        payment.payment_method = request.data.get('payment_method', '')

        if payment.paid_amount >= payment.amount:
            payment.status = 'paid'
        else:
            payment.status = 'partial'

        payment.save()

        serializer = self.get_serializer(payment)
        return Response({
            'success': True,
            'message': 'Payment recorded',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def mark_overdue(self, request, pk=None):
        """Mark a payment as overdue."""
        payment = self.get_object()

        if payment.status != 'pending':
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Only pending payments can be marked overdue'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.status = 'overdue'
        payment.save()

        serializer = self.get_serializer(payment)
        return Response({
            'success': True,
            'message': 'Payment marked as overdue',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def waive(self, request, pk=None):
        """Waive a payment."""
        payment = self.get_object()

        if payment.status == 'paid':
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Paid payments cannot be waived'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.status = 'waived'
        payment.save()

        serializer = self.get_serializer(payment)
        return Response({
            'success': True,
            'message': 'Payment waived',
            'data': serializer.data
        })


class LeaseReturnViewSet(BaseModelViewSetWithBatch):
    """Lease Return ViewSet."""
    queryset = LeaseReturn.objects.all()
    serializer_class = LeaseReturnSerializer
    filterset_class = LeaseReturnFilter

    def perform_create(self, serializer):
        """Set received_by and update contract."""
        return_obj = serializer.save(
            received_by=self.request.user,
            created_by=self.request.user
        )

        # Update lease item return condition
        contract = return_obj.contract
        try:
            lease_item = LeaseItem.objects.get(
                contract=contract,
                asset=return_obj.asset
            )
            lease_item.return_condition = return_obj.condition
            lease_item.damage_description = return_obj.damage_description
            lease_item.actual_end_date = return_obj.return_date
            lease_item.save()
        except LeaseItem.DoesNotExist:
            pass

    @action(detail=False, methods=['get'])
    def pending_returns(self, request):
        """Get contracts with assets pending return."""
        # Active contracts where actual_end_date is past but no return recorded
        today = timezone.now().date()
        active_contracts = LeaseContract.objects.filter(
            status='active',
            actual_end_date__lt=today
        )

        contract_ids = active_contracts.values_list('id', flat=True)

        # Get assets from these contracts
        leased_assets = LeaseItem.objects.filter(
            contract_id__in=contract_ids
        ).exclude(
            return_condition__isnull=False
        )

        from .serializers import LeaseItemSerializer
        page = self.paginate_queryset(leased_assets)
        serializer = LeaseItemSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class LeaseExtensionViewSet(BaseModelViewSetWithBatch):
    """Lease Extension ViewSet."""
    queryset = LeaseExtension.objects.all()
    serializer_class = LeaseExtensionSerializer
    filterset_class = LeaseExtensionFilter

    def perform_create(self, serializer):
        """Process extension and update contract."""
        extension = serializer.save(
            created_by=self.request.user
        )

        # Update contract end date
        contract = extension.contract
        contract.end_date = extension.new_end_date
        contract.total_rent += extension.additional_rent
        contract.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a lease extension."""
        extension = self.get_object()

        extension.approved_by = request.user
        extension.approved_at = timezone.now()
        extension.save()

        serializer = self.get_serializer(extension)
        return Response({
            'success': True,
            'message': 'Extension approved',
            'data': serializer.data
        })
