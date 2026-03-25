"""
Celery tasks for finance voucher integration.
"""
import logging
import uuid
from typing import Optional

from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.finance.models import FinanceVoucher
from apps.integration.constants import SyncDirection, SyncStatus
from apps.integration.models import IntegrationLog, IntegrationSyncTask
from apps.notifications.models import Notification
from apps.notifications.services import notification_service

logger = logging.getLogger(__name__)


def _update_sync_task(
    sync_task_id: Optional[str],
    *,
    status_value: Optional[str] = None,
    total_count: Optional[int] = None,
    success_count: Optional[int] = None,
    failed_count: Optional[int] = None,
    error_summary: Optional[list] = None,
    started_at=None,
    completed_at=None,
    duration_ms: Optional[int] = None,
):
    """Best-effort sync task status update (no exception bubbling)."""
    if not sync_task_id:
        return

    task = IntegrationSyncTask.all_objects.filter(id=sync_task_id, is_deleted=False).first()
    if not task:
        return

    fields = []
    if status_value is not None:
        task.status = status_value
        fields.append('status')
    if total_count is not None:
        task.total_count = total_count
        fields.append('total_count')
    if success_count is not None:
        task.success_count = success_count
        fields.append('success_count')
    if failed_count is not None:
        task.failed_count = failed_count
        fields.append('failed_count')
    if error_summary is not None:
        task.error_summary = error_summary
        fields.append('error_summary')
    if started_at is not None:
        task.started_at = started_at
        fields.append('started_at')
    if completed_at is not None:
        task.completed_at = completed_at
        fields.append('completed_at')
    if duration_ms is not None:
        task.duration_ms = duration_ms
        fields.append('duration_ms')

    if fields:
        fields.append('updated_at')
        task.save(update_fields=fields)


def _create_failure_alert(voucher: FinanceVoucher, user_id: Optional[str], message: str):
    """
    Emit failure alert.
    Currently implemented as:
    1) structured error log
    2) inbox notification for trigger user (if available)
    """
    logger.error(
        'FINANCE_VOUCHER_PUSH_ALERT voucher_id=%s voucher_no=%s org_id=%s error=%s',
        voucher.id,
        voucher.voucher_no,
        voucher.organization_id,
        message,
    )

    if not user_id:
        return

    recipient = User.all_objects.filter(id=user_id, is_deleted=False).first()
    if not recipient:
        return

    alert_title = f'Voucher push failed: {voucher.voucher_no}'
    alert_content = f'Voucher push failed. Check integration config and logs. Error: {message}'
    variables = {
        'voucher_id': str(voucher.id),
        'voucher_no': voucher.voucher_no,
        'organization_id': str(voucher.organization_id) if voucher.organization_id else '',
        'error': message,
        'title': alert_title,
        'content': alert_content,
    }

    try:
        result = notification_service.send(
            recipient=recipient,
            notification_type='finance_voucher_push_failed',
            variables=variables,
            channels=['inbox'],
            priority='high',
            sender=recipient,
        )

        result_items = result.get('results', []) if isinstance(result, dict) else []
        notification_id = None
        if result_items and isinstance(result_items[0], dict):
            notification_id = result_items[0].get('notification_id')

        if result.get('success') and notification_id:
            # Keep tenant isolation for finance alerts even when sent via notification_service.
            notification = Notification.all_objects.filter(id=notification_id, is_deleted=False).first()
            if notification:
                update_fields = []
                if voucher.organization_id and notification.organization_id != voucher.organization_id:
                    notification.organization_id = voucher.organization_id
                    update_fields.append('organization')
                if not notification.created_by_id:
                    notification.created_by_id = recipient.id
                    update_fields.append('created_by')
                # If template is missing, service falls back to a generic title/content.
                if not notification.title or notification.title == 'finance_voucher_push_failed':
                    notification.title = alert_title
                    update_fields.append('title')
                if not notification.content or notification.content == str(variables):
                    notification.content = alert_content
                    update_fields.append('content')
                if update_fields:
                    update_fields.append('updated_at')
                    notification.save(update_fields=update_fields)
            return

        logger.warning(
            'Notification service returned non-success for finance alert, fallback to direct inbox. '
            'voucher_id=%s user_id=%s result=%s',
            voucher.id,
            user_id,
            result,
        )
    except Exception:
        logger.exception(
            'Failed to send finance alert via notification_service, fallback to direct inbox. '
            'voucher_id=%s user_id=%s',
            voucher.id,
            user_id,
        )

    Notification.objects.create(
        organization_id=voucher.organization_id,
        recipient=recipient,
        notification_type='finance_voucher_push_failed',
        priority='high',
        channel='inbox',
        title=alert_title,
        content=alert_content,
        data={
            'voucherId': str(voucher.id),
            'voucherNo': voucher.voucher_no,
            'organizationId': str(voucher.organization_id) if voucher.organization_id else '',
        },
        status='pending',
        created_by=recipient,
        sender=recipient,
    )


def _create_integration_log(
    *,
    voucher: FinanceVoucher,
    system_type: str,
    sync_task_id: Optional[str],
    user_id: Optional[str],
    success: bool,
    status_code: int,
    request_body: Optional[dict] = None,
    response_body: Optional[dict] = None,
    error_message: str = '',
):
    sync_task = None
    if sync_task_id:
        sync_task = IntegrationSyncTask.all_objects.filter(id=sync_task_id, is_deleted=False).first()

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
        created_by_id=user_id,
    )


@shared_task(
    bind=True,
    autoretry_for=(TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
    retry_backoff_max=300,
    max_retries=3
)
def push_voucher_to_erp_task(
    self,
    *,
    voucher_id: str,
    organization_id: Optional[str],
    user_id: Optional[str],
    system_type: str,
    trigger: str = 'push',
    sync_task_id: Optional[str] = None,
    queue_key: Optional[str] = None,
):
    """
    Async voucher push task.

    Notes:
    - In current phase ERP call is simulated.
    - Retry with exponential backoff is enabled for timeout/connection errors.
    """
    started_at = timezone.now()
    _update_sync_task(
        sync_task_id,
        status_value=SyncStatus.RUNNING,
        started_at=started_at,
    )

    try:
        with transaction.atomic():
            voucher = FinanceVoucher.all_objects.select_for_update().filter(
                id=voucher_id,
                is_deleted=False
            ).first()
            if not voucher:
                _update_sync_task(
                    sync_task_id,
                    status_value=SyncStatus.FAILED,
                    total_count=1,
                    success_count=0,
                    failed_count=1,
                    error_summary=[{'error': 'Voucher not found'}],
                )
                return {'success': False, 'error': 'Voucher not found'}

            if organization_id and str(voucher.organization_id) != str(organization_id):
                _update_sync_task(
                    sync_task_id,
                    status_value=SyncStatus.FAILED,
                    total_count=1,
                    success_count=0,
                    failed_count=1,
                    error_summary=[{'error': 'Organization mismatch'}],
                )
                return {'success': False, 'error': 'Organization mismatch'}

            # Idempotent success branch.
            if voucher.status == 'posted' and voucher.erp_voucher_no:
                _create_integration_log(
                    voucher=voucher,
                    system_type=system_type,
                    sync_task_id=sync_task_id,
                    user_id=user_id,
                    success=True,
                    status_code=200,
                    request_body={'voucher_id': str(voucher.id), 'trigger': trigger, 'idempotent': True},
                    response_body={'external_voucher_no': voucher.erp_voucher_no, 'idempotent': True},
                )
                completed_at = timezone.now()
                duration_ms = int((completed_at - started_at).total_seconds() * 1000)
                _update_sync_task(
                    sync_task_id,
                    status_value=SyncStatus.SUCCESS,
                    total_count=1,
                    success_count=1,
                    failed_count=0,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                )
                return {
                    'success': True,
                    'external_voucher_no': voucher.erp_voucher_no,
                    'idempotent': True,
                }

            if not voucher.can_post():
                message = 'Voucher is not ready for posting'
                _create_integration_log(
                    voucher=voucher,
                    system_type=system_type,
                    sync_task_id=sync_task_id,
                    user_id=user_id,
                    success=False,
                    status_code=400,
                    request_body={'voucher_id': str(voucher.id), 'trigger': trigger},
                    response_body={},
                    error_message=message,
                )
                _create_failure_alert(voucher, user_id, message)
                completed_at = timezone.now()
                duration_ms = int((completed_at - started_at).total_seconds() * 1000)
                _update_sync_task(
                    sync_task_id,
                    status_value=SyncStatus.FAILED,
                    total_count=1,
                    success_count=0,
                    failed_count=1,
                    error_summary=[{'error': message}],
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                )
                return {'success': False, 'error': message}

            # Simulate successful ERP posting.
            voucher.erp_voucher_no = f"ERP-{voucher.voucher_no}-{uuid.uuid4().hex[:8].upper()}"
            voucher.posted_at = timezone.now()
            voucher.status = 'posted'
            if user_id:
                user = User.all_objects.filter(id=user_id, is_deleted=False).first()
                if user:
                    voucher.posted_by = user
            update_fields = ['erp_voucher_no', 'posted_at', 'status', 'updated_at']
            if voucher.posted_by_id:
                update_fields.append('posted_by')
            voucher.save(update_fields=update_fields)

            _create_integration_log(
                voucher=voucher,
                system_type=system_type,
                sync_task_id=sync_task_id,
                user_id=user_id,
                success=True,
                status_code=200,
                request_body={'voucher_id': str(voucher.id), 'trigger': trigger},
                response_body={'external_voucher_no': voucher.erp_voucher_no},
            )

        completed_at = timezone.now()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        _update_sync_task(
            sync_task_id,
            status_value=SyncStatus.SUCCESS,
            total_count=1,
            success_count=1,
            failed_count=0,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )
        return {'success': True, 'external_voucher_no': voucher.erp_voucher_no}

    except Exception as exc:
        # For autoretry-for exceptions Celery handles retry/backoff automatically.
        voucher = FinanceVoucher.all_objects.filter(id=voucher_id, is_deleted=False).first()
        if voucher:
            _create_integration_log(
                voucher=voucher,
                system_type=system_type,
                sync_task_id=sync_task_id,
                user_id=user_id,
                success=False,
                status_code=500,
                request_body={'voucher_id': str(voucher.id), 'trigger': trigger},
                response_body={},
                error_message=str(exc),
            )
            _create_failure_alert(voucher, user_id, str(exc))

        completed_at = timezone.now()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        _update_sync_task(
            sync_task_id,
            status_value=SyncStatus.FAILED,
            total_count=1,
            success_count=0,
            failed_count=1,
            error_summary=[{'error': str(exc)}],
            completed_at=completed_at,
            duration_ms=duration_ms,
        )
        logger.exception('Voucher push task failed. voucher_id=%s trigger=%s', voucher_id, trigger)
        raise

    finally:
        if queue_key:
            cache.delete(queue_key)
