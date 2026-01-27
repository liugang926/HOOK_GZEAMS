"""
Celery Tasks for WeWork Sync

Async tasks for WeWork contacts synchronization.
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_wework_contacts(self, org_id: int, sync_type: str = 'full'):
    """
    Sync WeWork contacts (departments and users).

    Args:
        org_id: Organization ID
        sync_type: Sync type (full/department/user)

    Returns:
        Sync result dictionary
    """
    from apps.sso.models import WeWorkConfig
    from apps.sso.services.wework_sync_service import WeWorkSyncService

    # Prevent duplicate tasks
    lock_key = f"sync_wework_lock_{org_id}"
    if cache.get(lock_key):
        logger.warning(f"Sync task already running: org_id={org_id}")
        return {'status': 'duplicate', 'org_id': org_id}

    try:
        cache.set(lock_key, True, timeout=3600)  # 1 hour lock

        config = WeWorkConfig.objects.get(
            organization_id=org_id,
            is_enabled=True
        )

        service = WeWorkSyncService(config)

        if sync_type == 'department':
            log = service.sync_departments_only()
        elif sync_type == 'user':
            log = service.sync_users_only()
        else:
            log = service.full_sync()

        logger.info(f"Sync task completed: org_id={org_id}, log_id={log.id}")

        return {
            'org_id': org_id,
            'sync_log_id': str(log.id),
            'status': log.status,
            'stats': {
                'total': log.total_count,
                'created': log.created_count,
                'updated': log.updated_count,
                'failed': log.failed_count,
            }
        }

    except WeWorkConfig.DoesNotExist:
        logger.error(f"WeWork config not found: org_id={org_id}")
        return {'status': 'not_found', 'org_id': org_id}

    except Exception as exc:
        logger.error(f"Sync task failed: org_id={org_id}, error={str(exc)}", exc_info=True)
        raise

    finally:
        cache.delete(lock_key)


@shared_task
def sync_all_orgs_wework():
    """Sync all organizations with WeWork enabled."""
    from apps.sso.models import WeWorkConfig

    configs = WeWorkConfig.objects.filter(is_enabled=True)

    results = []
    for config in configs:
        result = sync_wework_contacts.delay(config.organization_id)
        results.append({
            'org_id': config.organization_id,
            'task_id': result.id
        })

    logger.info(f"Started {len(results)} sync tasks")
    return results


@shared_task
def cleanup_old_sync_logs(days: int = 30):
    """
    Clean up old sync logs.

    Args:
        days: Number of days to keep logs (default: 30)

    Returns:
        Number of deleted logs
    """
    from datetime import timedelta
    from apps.sso.models import SyncLog
    from django.utils import timezone

    cutoff_date = timezone.now() - timedelta(days=days)

    deleted_count = SyncLog.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['success', 'failed']
    ).delete()

    logger.info(f"Cleaned up {deleted_count} old sync logs")
    return deleted_count[0] if isinstance(deleted_count, list) else deleted_count
