"""
Finance Module ViewSets

ViewSets for financial vouchers, voucher entries, and voucher templates.
"""
import uuid
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
from django.db.models import Sum, Max
from django.db import transaction
from decimal import Decimal
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.permissions.base import IsOrganizationMember
from apps.finance.models import FinanceVoucher, VoucherEntry, VoucherTemplate
from apps.finance.serializers import (
    FinanceVoucherSerializer, FinanceVoucherListSerializer, FinanceVoucherDetailSerializer,
    VoucherEntrySerializer, VoucherEntryListSerializer, VoucherEntryDetailSerializer,
    VoucherTemplateSerializer, VoucherTemplateListSerializer, VoucherTemplateDetailSerializer
)
from apps.finance.filters import FinanceVoucherFilter, VoucherEntryFilter, VoucherTemplateFilter
from apps.integration.models import IntegrationLog, IntegrationConfig, IntegrationSyncTask
from apps.integration.constants import IntegrationSystemType, IntegrationModuleType, SyncDirection, SyncStatus
from apps.integration.serializers import IntegrationLogListSerializer
from apps.finance.tasks import push_voucher_to_erp_task


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

    def _resolve_integration_system(self, request):
        """Resolve target system for finance integration logging."""
        request_system = request.data.get('system') or request.query_params.get('system')
        if request_system:
            return str(request_system)

        config = IntegrationConfig.objects.filter(
            organization_id=getattr(request, 'organization_id', None),
            is_enabled=True
        ).order_by('-updated_at').first()
        if config and config.system_type:
            return config.system_type

        return IntegrationSystemType.M18

    def _create_integration_log(
        self,
        voucher,
        system_type,
        success,
        sync_task=None,
        request_body=None,
        response_body=None,
        status_code=200,
        error_message='',
    ):
        """Persist a lightweight integration log entry for voucher push/retry flow."""
        IntegrationLog.objects.create(
            organization_id=voucher.organization_id,
            sync_task=sync_task,
            system_type=system_type,
            integration_type=f'{system_type}_finance_voucher',
            action=SyncDirection.PUSH,
            request_method='POST',
            request_url=f'/external/{system_type}/finance/vouchers',
            request_body=request_body or {},
            response_body=response_body or {},
            status_code=status_code,
            success=success,
            error_message=error_message,
            business_type='voucher',
            business_id=str(voucher.id),
            external_id=voucher.erp_voucher_no or '',
        )

    def _resolve_integration_config(self, organization_id, system_type):
        """Resolve active integration config for task tracking."""
        if not organization_id:
            return None
        return IntegrationConfig.all_objects.filter(
            organization_id=organization_id,
            system_type=system_type,
            is_enabled=True,
            is_deleted=False
        ).order_by('-updated_at').first()

    def _build_task_queue_key(self, voucher, system_type, trigger, idempotency_key):
        return (
            f'finance:voucher:push:{voucher.organization_id}:{voucher.id}:'
            f'{system_type}:{trigger}:{idempotency_key}'
        )

    def _enqueue_voucher_push(self, request, voucher, system_type, trigger):
        """
        Enqueue voucher push to async worker.

        Keeps API compatibility:
        - returns `success: true`
        - provides task metadata for async tracking
        - in eager/test mode additionally returns immediate `external_voucher_no`
        """
        raw_idempotency = (
            request.headers.get('Idempotency-Key')
            or request.headers.get('X-Idempotency-Key')
            or f'{trigger}:{voucher.id}'
        )
        idempotency_key = str(raw_idempotency).strip()[:120]
        queue_key = self._build_task_queue_key(voucher, system_type, trigger, idempotency_key)
        eager_mode = bool(getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False))

        if not eager_mode:
            duplicate_payload = cache.get(queue_key)
            if isinstance(duplicate_payload, dict) and duplicate_payload.get('task_id'):
                return Response({
                    'success': True,
                    'message': 'Push task already queued',
                    'data': {
                        'success': True,
                        'queued': True,
                        'duplicate': True,
                        'task_id': duplicate_payload.get('task_id'),
                        'sync_task_id': duplicate_payload.get('sync_task_id'),
                    }
                })
            # Lock before enqueue to reduce duplicate submits from repeated clicks.
            cache.set(queue_key, {'task_id': None, 'sync_task_id': None}, timeout=600)

        sync_task = None
        config = self._resolve_integration_config(voucher.organization_id, system_type)
        if config:
            sync_task = IntegrationSyncTask.objects.create(
                organization_id=voucher.organization_id,
                config=config,
                task_id=f"sync_{system_type}_voucher_{uuid.uuid4().hex[:8]}",
                module_type=IntegrationModuleType.FINANCE,
                direction=SyncDirection.PUSH,
                business_type='voucher',
                sync_params={
                    'voucher_id': str(voucher.id),
                    'trigger': trigger,
                    'idempotency_key': idempotency_key,
                },
                status=SyncStatus.PENDING,
                created_by=request.user
            )

        try:
            async_result = push_voucher_to_erp_task.delay(
                voucher_id=str(voucher.id),
                organization_id=str(voucher.organization_id) if voucher.organization_id else None,
                user_id=str(request.user.id) if request.user else None,
                system_type=system_type,
                trigger=trigger,
                sync_task_id=str(sync_task.id) if sync_task else None,
                queue_key=queue_key if not eager_mode else None,
            )
        except Exception as exc:
            if not eager_mode:
                cache.delete(queue_key)
            self._create_integration_log(
                voucher=voucher,
                system_type=system_type,
                sync_task=sync_task,
                success=False,
                request_body={
                    'voucher_id': str(voucher.id),
                    'trigger': trigger,
                    'idempotency_key': idempotency_key
                },
                response_body={},
                status_code=500,
                error_message=f'Failed to enqueue push task: {exc}',
            )
            return Response({
                'success': False,
                'error': {
                    'code': 'QUEUE_ERROR',
                    'message': 'Failed to enqueue push task'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if sync_task:
            IntegrationSyncTask.all_objects.filter(id=sync_task.id, is_deleted=False).update(
                celery_task_id=async_result.id
            )

        if not eager_mode:
            cache.set(
                queue_key,
                {
                    'task_id': async_result.id,
                    'sync_task_id': str(sync_task.id) if sync_task else None,
                },
                timeout=600
            )

        self._create_integration_log(
            voucher=voucher,
            system_type=system_type,
            sync_task=sync_task,
            success=True,
            request_body={
                'voucher_id': str(voucher.id),
                'trigger': trigger,
                'idempotency_key': idempotency_key
            },
            response_body={
                'queued': True,
                'task_id': async_result.id,
                'sync_task_id': str(sync_task.id) if sync_task else None,
            },
            status_code=202,
        )

        data = {
            'success': True,
            'queued': True,
            'task_id': async_result.id,
            'sync_task_id': str(sync_task.id) if sync_task else None,
        }

        # Tests run with eager mode; keep backward compatible payload in this mode.
        if eager_mode:
            voucher.refresh_from_db()
            if voucher.erp_voucher_no:
                data['external_voucher_no'] = voucher.erp_voucher_no

        return Response({
            'success': True,
            'message': 'Voucher push task queued',
            'data': data
        })

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

    @action(detail=True, methods=['post'], url_path='push')
    def push(self, request, pk=None):
        """
        Push voucher to external ERP.

        Alias endpoint for frontend compatibility:
        POST /api/finance/vouchers/{id}/push/
        """
        voucher = self.get_object()
        system_type = self._resolve_integration_system(request)

        # Idempotent behavior: already posted voucher can be pushed repeatedly.
        if voucher.status == 'posted' and voucher.erp_voucher_no:
            self._create_integration_log(
                voucher=voucher,
                system_type=system_type,
                success=True,
                request_body={'voucher_id': str(voucher.id), 'idempotent': True},
                response_body={'external_voucher_no': voucher.erp_voucher_no, 'idempotent': True},
                status_code=200,
            )
            return Response({
                'success': True,
                'message': 'Voucher already pushed to ERP',
                'data': {
                    'success': True,
                    'external_voucher_no': voucher.erp_voucher_no
                }
            })

        if not voucher.can_post():
            self._create_integration_log(
                voucher=voucher,
                system_type=system_type,
                success=False,
                request_body={'voucher_id': str(voucher.id)},
                response_body={},
                status_code=400,
                error_message='Voucher cannot be pushed. Must be approved and not already posted.',
            )
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Voucher cannot be pushed. Must be approved and not already posted.'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return self._enqueue_voucher_push(
            request=request,
            voucher=voucher,
            system_type=system_type,
            trigger='push',
        )

    @action(detail=True, methods=['get'], url_path='integration-logs')
    def integration_logs(self, request, pk=None):
        """
        Get integration logs for the specified voucher.

        Compatibility endpoint:
        GET /api/finance/vouchers/{id}/integration-logs/
        """
        voucher = self.get_object()
        logs = IntegrationLog.objects.filter(
            organization_id=voucher.organization_id,
            business_id=str(voucher.id),
            is_deleted=False
        ).order_by('-created_at')[:100]

        serializer = IntegrationLogListSerializer(logs, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='retry')
    def retry(self, request, pk=None):
        """
        Retry finance integration for a voucher.

        Compatibility endpoint:
        POST /api/finance/vouchers/{id}/retry/
        """
        voucher = self.get_object()
        system_type = self._resolve_integration_system(request)

        # If already posted, consider retry complete (idempotent behavior).
        if voucher.status == 'posted' and voucher.erp_voucher_no:
            self._create_integration_log(
                voucher=voucher,
                system_type=system_type,
                success=True,
                request_body={'voucher_id': str(voucher.id), 'retry': True, 'idempotent': True},
                response_body={'external_voucher_no': voucher.erp_voucher_no, 'retry': True},
                status_code=200,
            )
            return Response({
                'success': True,
                'message': 'Integration already completed',
                'data': {
                    'success': True,
                    'external_voucher_no': voucher.erp_voucher_no
                }
            })

        if not voucher.can_post():
            self._create_integration_log(
                voucher=voucher,
                system_type=system_type,
                success=False,
                request_body={'voucher_id': str(voucher.id), 'retry': True},
                response_body={},
                status_code=400,
                error_message='Voucher is not ready for retry push',
            )
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Voucher is not ready for retry push'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return self._enqueue_voucher_push(
            request=request,
            voucher=voucher,
            system_type=system_type,
            trigger='retry',
        )

    @action(detail=True, methods=['get', 'put'], url_path='entries')
    def entries(self, request, pk=None):
        """
        Get or replace voucher entries.

        GET /api/finance/vouchers/{id}/entries/
        PUT /api/finance/vouchers/{id}/entries/
        """
        voucher = self.get_object()

        if request.method.lower() == 'get':
            serializer = FinanceVoucherDetailSerializer(voucher)
            return Response({
                'success': True,
                'data': serializer.data
            })

        entries = request.data.get('entries', [])
        if not isinstance(entries, list):
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'entries must be a list'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            voucher.entries.all().delete()
            total_debit = Decimal('0.00')
            total_credit = Decimal('0.00')

            for idx, entry in enumerate(entries, start=1):
                account_code = entry.get('account_code') or entry.get('accountCode') or ''
                account_name = entry.get('account_name') or entry.get('accountName') or account_code or f'Line {idx}'
                debit_value = entry.get('debit_amount', entry.get('debit', 0)) or 0
                credit_value = entry.get('credit_amount', entry.get('credit', 0)) or 0
                description = entry.get('description') or ''

                debit_amount = Decimal(str(debit_value))
                credit_amount = Decimal(str(credit_value))

                VoucherEntry.objects.create(
                    voucher=voucher,
                    account_code=account_code,
                    account_name=account_name,
                    debit_amount=debit_amount,
                    credit_amount=credit_amount,
                    description=description,
                    line_no=idx,
                    organization_id=voucher.organization_id,
                    created_by=request.user
                )

                total_debit += debit_amount
                total_credit += credit_amount

            voucher.total_amount = total_debit
            voucher.updated_by = request.user
            voucher.save(update_fields=['total_amount', 'updated_by', 'updated_at'])

        serializer = FinanceVoucherDetailSerializer(voucher)
        return Response({
            'success': True,
            'message': f'Voucher entries updated ({len(entries)} lines)',
            'data': {
                **serializer.data,
                'is_balanced': total_debit == total_credit
            }
        })

    def _generate_voucher_no(self, prefix='VCH'):
        """Generate a short unique voucher number."""
        import uuid
        return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"

    def _build_default_entries(self, total_amount, debit_desc='Debit', credit_desc='Credit'):
        """Build balanced placeholder entries for generated vouchers."""
        return [
            {
                'account_code': '1001',
                'account_name': 'Asset/Expense',
                'debit_amount': total_amount,
                'credit_amount': Decimal('0.00'),
                'description': debit_desc,
                'line_no': 1
            },
            {
                'account_code': '2001',
                'account_name': 'Payable/Accumulated',
                'debit_amount': Decimal('0.00'),
                'credit_amount': total_amount,
                'description': credit_desc,
                'line_no': 2
            }
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
        import re

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

    def _build_disposal_source_trace(self, *, asset, business_id, organization_id):
        """Build source trace for disposal voucher generation."""
        from apps.lifecycle.models import DisposalRequest

        disposal_request = None
        normalized_business_id = self._normalize_uuid_value(business_id)
        if normalized_business_id:
            disposal_request = DisposalRequest.all_objects.filter(
                id=normalized_business_id,
                organization_id=organization_id,
                is_deleted=False,
            ).first()

        primary_object_code = 'Asset'
        primary_id = str(asset.id)
        primary_record_no = str(getattr(asset, 'asset_code', '') or '').strip()
        if disposal_request is not None:
            primary_object_code = 'DisposalRequest'
            primary_id = str(disposal_request.id)
            primary_record_no = str(getattr(disposal_request, 'request_no', '') or '').strip()

        return self._build_source_trace_payload(
            primary_object_code=primary_object_code,
            primary_id=primary_id,
            primary_record_no=primary_record_no,
            requested_business_id=business_id,
            asset_ids=[str(asset.id)],
            asset_codes=[str(getattr(asset, 'asset_code', '') or '').strip()],
            purchase_request=getattr(asset, 'source_purchase_request', None),
            receipt=getattr(asset, 'source_receipt', None),
        )

    def _build_depreciation_source_trace(self, *, period, category_ids):
        """Build source trace for depreciation voucher generation."""
        return self._build_source_trace_payload(
            primary_object_code='DepreciationRecord',
            primary_record_no=str(period or '').strip(),
            requested_business_id=str(period or '').strip(),
            extra={
                'category_ids': [str(item).strip() for item in (category_ids or []) if str(item).strip()],
            },
        )

    def _create_generated_voucher(self, request, business_type, summary, total_amount, entries, source_trace=None):
        from django.utils import timezone
        voucher_date = request.data.get('voucher_date') or request.query_params.get('voucher_date')
        if not voucher_date:
            voucher_date = timezone.now().date()

        voucher = FinanceVoucher.objects.create(
            voucher_no=self._generate_voucher_no(),
            voucher_date=voucher_date,
            business_type=business_type,
            summary=summary,
            total_amount=total_amount,
            status='draft',
            notes=request.data.get('notes', ''),
            custom_fields=source_trace or {},
            organization_id=request.organization_id,
            created_by=request.user
        )

        for entry in entries:
            VoucherEntry.objects.create(
                voucher=voucher,
                account_code=entry['account_code'],
                account_name=entry['account_name'],
                debit_amount=entry['debit_amount'],
                credit_amount=entry['credit_amount'],
                description=entry.get('description', ''),
                line_no=entry.get('line_no', 1),
                organization_id=request.organization_id,
                created_by=request.user
            )

        serializer = FinanceVoucherDetailSerializer(voucher)
        return Response({
            'success': True,
            'message': 'Voucher generated successfully',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='generate/asset-purchase')
    def generate_asset_purchase(self, request):
        """
        Generate voucher from asset purchase context.

        POST /api/finance/vouchers/generate/asset-purchase/
        """
        asset_ids = request.data.get('asset_ids') or request.data.get('assetIds') or []
        business_id = request.data.get('business_id') or request.data.get('businessId') or ''

        if not asset_ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'assetIds is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        from apps.assets.models import Asset
        assets = Asset.objects.filter(
            id__in=asset_ids,
            organization_id=request.organization_id,
            is_deleted=False
        ).select_related(
            'source_receipt',
            'source_purchase_request',
        )
        total_amount = sum((asset.purchase_price or Decimal('0.00')) for asset in assets)
        total_amount = Decimal(str(total_amount or '0.00'))

        if total_amount <= 0:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'No valid amount found from selected assets'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        summary = f"Asset purchase voucher ({business_id or 'N/A'})"
        entries = self._build_default_entries(total_amount, 'Asset purchase debit', 'Asset purchase credit')
        source_trace = self._build_asset_purchase_source_trace(
            assets=assets,
            business_id=business_id,
            organization_id=request.organization_id,
        )
        return self._create_generated_voucher(request, 'purchase', summary, total_amount, entries, source_trace=source_trace)

    @action(detail=False, methods=['post'], url_path='generate/depreciation')
    def generate_depreciation(self, request):
        """
        Generate voucher from depreciation records.

        POST /api/finance/vouchers/generate/depreciation/
        """
        period = request.data.get('period')
        category_ids = request.data.get('category_ids') or request.data.get('categoryIds') or []

        if not period:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'period is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        from apps.depreciation.models import DepreciationRecord
        queryset = DepreciationRecord.objects.filter(
            organization_id=request.organization_id,
            period=period,
            is_deleted=False
        )
        if category_ids:
            queryset = queryset.filter(asset__asset_category_id__in=category_ids)

        total_amount = queryset.aggregate(total=Sum('depreciation_amount'))['total'] or Decimal('0.00')
        total_amount = Decimal(str(total_amount))

        if total_amount <= 0:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': f'No depreciation amount found for period {period}'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        summary = f"Depreciation voucher ({period})"
        entries = self._build_default_entries(total_amount, 'Depreciation expense', 'Accumulated depreciation')
        source_trace = self._build_depreciation_source_trace(
            period=period,
            category_ids=category_ids,
        )
        return self._create_generated_voucher(request, 'depreciation', summary, total_amount, entries, source_trace=source_trace)

    @action(detail=False, methods=['post'], url_path='generate/disposal')
    def generate_disposal(self, request):
        """
        Generate voucher from disposal context.

        POST /api/finance/vouchers/generate/disposal/
        """
        asset_id = request.data.get('asset_id') or request.data.get('assetId')
        business_id = request.data.get('business_id') or request.data.get('businessId') or ''

        if not asset_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'assetId is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        from apps.assets.models import Asset
        try:
            asset = Asset.objects.get(
                id=asset_id,
                organization_id=request.organization_id,
                is_deleted=False
            )
        except Asset.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Asset not found'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        total_amount = Decimal(str(asset.current_value or asset.purchase_price or 0))
        if total_amount <= 0:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Asset value is invalid for voucher generation'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        summary = f"Asset disposal voucher ({business_id or asset.asset_code})"
        entries = self._build_default_entries(total_amount, 'Disposal loss/expense', 'Asset disposal credit')
        source_trace = self._build_disposal_source_trace(
            asset=asset,
            business_id=business_id,
            organization_id=request.organization_id,
        )
        return self._create_generated_voucher(request, 'disposal', summary, total_amount, entries, source_trace=source_trace)

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

        system_type = self._resolve_integration_system(request)
        results = []
        succeeded = 0
        failed = 0

        for voucher_id in ids:
            voucher = FinanceVoucher.all_objects.filter(
                id=voucher_id,
                organization_id=request.organization_id,
                is_deleted=False
            ).first()

            if not voucher:
                results.append({'id': str(voucher_id), 'success': False, 'error': 'Not found'})
                failed += 1
                continue

            # Keep behavior explicit for invalid state.
            if not voucher.can_post():
                self._create_integration_log(
                    voucher=voucher,
                    system_type=system_type,
                    success=False,
                    request_body={'voucher_id': str(voucher.id), 'trigger': 'batch_push'},
                    response_body={},
                    status_code=400,
                    error_message='Voucher not ready for posting',
                )
                results.append({
                    'id': str(voucher_id),
                    'success': False,
                    'error': 'Voucher not ready for posting'
                })
                failed += 1
                continue

            enqueue_response = self._enqueue_voucher_push(
                request=request,
                voucher=voucher,
                system_type=system_type,
                trigger='batch_push',
            )
            if enqueue_response.status_code >= 400:
                error_message = (
                    (enqueue_response.data or {}).get('error', {}).get('message')
                    if isinstance(enqueue_response.data, dict) else 'Queue error'
                )
                results.append({
                    'id': str(voucher_id),
                    'success': False,
                    'error': error_message or 'Queue error'
                })
                failed += 1
                continue

            payload = (enqueue_response.data or {}).get('data', {}) if isinstance(enqueue_response.data, dict) else {}
            results.append({
                'id': str(voucher_id),
                'success': True,
                'queued': payload.get('queued', True),
                'task_id': payload.get('task_id'),
                'sync_task_id': payload.get('sync_task_id'),
                'duplicate': bool(payload.get('duplicate', False)),
            })
            succeeded += 1

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
            max=Max('line_no')
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
