"""
Finance Module ViewSets

ViewSets for financial vouchers, voucher entries, and voucher templates.
"""
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.permissions.base import IsOrganizationMember
from apps.finance.models import FinanceVoucher, VoucherEntry, VoucherTemplate
from apps.finance.serializers import (
    FinanceVoucherSerializer, FinanceVoucherListSerializer, FinanceVoucherDetailSerializer,
    VoucherEntrySerializer, VoucherEntryListSerializer, VoucherEntryDetailSerializer,
    VoucherTemplateSerializer, VoucherTemplateListSerializer, VoucherTemplateDetailSerializer
)
from apps.finance.filters import FinanceVoucherFilter, VoucherEntryFilter, VoucherTemplateFilter


# Base permission classes
BASE_PERMISSION_CLASSES = [permissions.IsAuthenticated, IsOrganizationMember]


class FinanceVoucherViewSet(BaseModelViewSetWithBatch):
    """
    Finance Voucher ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - Custom actions: submit, approve, post, batch_push
    """

    queryset = FinanceVoucher.objects.select_related(
        'organization', 'created_by', 'updated_by', 'posted_by'
    ).prefetch_related('entries').all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = FinanceVoucherFilter
    search_fields = ['voucher_no', 'summary', 'notes']
    ordering_fields = ['created_at', 'updated_at', 'voucher_date', 'total_amount']
    ordering = ['-voucher_date', '-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return FinanceVoucherListSerializer
        if self.action == 'retrieve':
            return FinanceVoucherDetailSerializer
        return FinanceVoucherSerializer

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit voucher for approval.

        POST /api/finance/vouchers/{id}/submit/

        Validates:
        - Voucher must be in draft status
        - Voucher must be balanced (debits = credits)

        Response:
        {
            "success": true,
            "message": "Voucher submitted successfully",
            "data": {...}
        }
        """
        voucher = self.get_object()

        # Check if voucher can be submitted
        if not voucher.can_submit():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Voucher cannot be submitted. Must be in draft status and balanced.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update status
        voucher.status = 'submitted'
        voucher.updated_by = request.user
        voucher.save(update_fields=['status', 'updated_by', 'updated_at'])

        serializer = self.get_serializer(voucher)
        return Response({
            'success': True,
            'message': 'Voucher submitted successfully',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a submitted voucher.

        POST /api/finance/vouchers/{id}/approve/

        Request body:
        {
            "approved": true,
            "notes": "Optional approval notes"
        }

        Validates:
        - Voucher must be in submitted status
        """
        voucher = self.get_object()

        # Check if voucher can be approved
        if not voucher.can_approve():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Voucher cannot be approved. Must be in submitted status.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        approved = request.data.get('approved', True)

        if approved:
            voucher.status = 'approved'
            message = 'Voucher approved successfully'
        else:
            voucher.status = 'rejected'
            message = 'Voucher rejected'

        # Update notes if provided
        if 'notes' in request.data:
            voucher.notes = request.data['notes']

        voucher.updated_by = request.user
        voucher.save()

        serializer = self.get_serializer(voucher)
        return Response({
            'success': True,
            'message': message,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        """
        Post voucher to ERP system.

        POST /api/finance/vouchers/{id}/post/

        This is a placeholder for ERP integration.
        In production, this would:
        1. Call ERP API to create voucher
        2. Store ERP voucher number
        3. Mark as posted

        Validates:
        - Voucher must be approved
        - Voucher must not already be posted
        """
        voucher = self.get_object()

        # Check if voucher can be posted
        if not voucher.can_post():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Voucher cannot be posted. Must be approved and not already posted.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # TODO: Implement actual ERP integration
        # For now, simulate posting
        from django.utils import timezone
        import uuid

        # Simulate ERP voucher number
        voucher.erp_voucher_no = f"ERP-{voucher.voucher_no}-{uuid.uuid4().hex[:8].upper()}"
        voucher.posted_at = timezone.now()
        voucher.posted_by = request.user
        voucher.status = 'posted'
        voucher.save()

        serializer = self.get_serializer(voucher)
        return Response({
            'success': True,
            'message': 'Voucher posted to ERP successfully',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def batch_push(self, request):
        """
        Batch push multiple approved vouchers to ERP.

        POST /api/finance/vouchers/batch_push/

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }

        Response:
        {
            "success": true,
            "message": "Batch push completed",
            "summary": {"total": 3, "succeeded": 2, "failed": 1},
            "results": [...]
        }
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids parameter cannot be empty'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        succeeded = 0
        failed = 0

        for voucher_id in ids:
            try:
                voucher = FinanceVoucher.objects.get(id=voucher_id)

                # Check if can be posted
                if not voucher.can_post():
                    results.append({
                        'id': str(voucher_id),
                        'success': False,
                        'error': 'Voucher not ready for posting'
                    })
                    failed += 1
                    continue

                # Simulate ERP posting
                from django.utils import timezone
                import uuid

                voucher.erp_voucher_no = f"ERP-{voucher.voucher_no}-{uuid.uuid4().hex[:8].upper()}"
                voucher.posted_at = timezone.now()
                voucher.posted_by = request.user
                voucher.status = 'posted'
                voucher.save()

                results.append({'id': str(voucher_id), 'success': True})
                succeeded += 1

            except FinanceVoucher.DoesNotExist:
                results.append({'id': str(voucher_id), 'success': False, 'error': 'Not found'})
                failed += 1
            except Exception as e:
                results.append({'id': str(voucher_id), 'success': False, 'error': str(e)})
                failed += 1

        http_status = status.HTTP_200_OK if failed == 0 else status.HTTP_207_MULTI_STATUS
        return Response({
            'success': True,
            'message': 'Batch push completed',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        }, status=http_status)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get financial summary statistics.

        GET /api/finance/vouchers/summary/

        Returns:
        {
            "success": true,
            "data": {
                "total_vouchers": 100,
                "draft": 10,
                "submitted": 5,
                "approved": 15,
                "posted": 60,
                "rejected": 10,
                "total_amount": 1500000.00
            }
        }
        """
        from django.db.models import Count, Sum

        queryset = self.get_queryset()
        total_vouchers = queryset.count()

        # Count by status
        status_counts = {}
        for status_code, _ in FinanceVoucher.STATUS_CHOICES:
            count = queryset.filter(status=status_code).count()
            status_counts[status_code] = count

        # Total amount
        total_amount = queryset.aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        return Response({
            'success': True,
            'data': {
                'total_vouchers': total_vouchers,
                **status_counts,
                'total_amount': total_amount
            }
        })


class VoucherEntryViewSet(BaseModelViewSetWithBatch):
    """
    Voucher Entry ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    """

    queryset = VoucherEntry.objects.select_related(
        'voucher', 'organization', 'created_by', 'updated_by'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = VoucherEntryFilter
    search_fields = ['account_code', 'account_name', 'description']
    ordering_fields = ['created_at', 'line_no', 'debit_amount', 'credit_amount']
    ordering = ['voucher', 'line_no']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return VoucherEntryListSerializer
        if self.action == 'retrieve':
            return VoucherEntryDetailSerializer
        return VoucherEntrySerializer

    def perform_create(self, serializer):
        """Set line_no if not provided."""
        # Get existing entries count for this voucher
        voucher_id = serializer.validated_data.get('voucher').id
        max_line_no = VoucherEntry.objects.filter(
            voucher_id=voucher_id
        ).aggregate(
            max=models.Max('line_no')
        )['max'] or 0

        # Set line_no if not in validated_data
        if 'line_no' not in serializer.validated_data:
            serializer.validated_data['line_no'] = max_line_no + 1

        super().perform_create(serializer)


class VoucherTemplateViewSet(BaseModelViewSetWithBatch):
    """
    Voucher Template ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    """

    queryset = VoucherTemplate.objects.select_related(
        'organization', 'created_by', 'updated_by'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = VoucherTemplateFilter
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'code', 'name']
    ordering = ['code', 'name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return VoucherTemplateListSerializer
        if self.action == 'retrieve':
            return VoucherTemplateDetailSerializer
        return VoucherTemplateSerializer

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """
        Apply template to create a new voucher.

        POST /api/finance/templates/{id}/apply/

        Request body:
        {
            "voucher_date": "2025-01-25",
            "summary": "Custom summary",
            "total_amount": 10000.00,
            "notes": "Optional notes"
        }

        Creates a new voucher based on template configuration.
        """
        template = self.get_object()

        if not template.is_active:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Template is not active'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract request data
        voucher_date = request.data.get('voucher_date')
        summary = request.data.get('summary', f"Generated from template: {template.name}")
        total_amount = request.data.get('total_amount', 0)
        notes = request.data.get('notes', '')

        if not voucher_date:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'voucher_date is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate voucher number
        import uuid
        voucher_no = f"VCH-{uuid.uuid4().hex[:10].upper()}"

        # Create voucher
        voucher = FinanceVoucher.objects.create(
            voucher_no=voucher_no,
            voucher_date=voucher_date,
            business_type=template.business_type,
            summary=summary,
            total_amount=total_amount,
            status='draft',
            notes=notes,
            organization=request.organization,
            created_by=request.user
        )

        # Create entries from template config
        template_config = template.template_config or {}
        entries = template_config.get('entries', [])

        for idx, entry in enumerate(entries, start=1):
            VoucherEntry.objects.create(
                voucher=voucher,
                account_code=entry.get('account_code', ''),
                account_name=entry.get('account_name', ''),
                debit_amount=entry.get('debit_amount', 0),
                credit_amount=entry.get('credit_amount', 0),
                description=entry.get('description', ''),
                line_no=idx,
                organization=request.organization,
                created_by=request.user
            )

        serializer = FinanceVoucherSerializer(voucher)
        return Response({
            'success': True,
            'message': 'Voucher created from template successfully',
            'data': serializer.data
        })


__all__ = [
    'FinanceVoucherViewSet',
    'VoucherEntryViewSet',
    'VoucherTemplateViewSet',
]
