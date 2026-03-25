"""
System Module App Configuration

This module contains the app configuration for the system module,
which handles the low-code metadata engine.
"""
import logging
import os
import sys
from django.apps import AppConfig


logger = logging.getLogger(__name__)


class SystemConfig(AppConfig):
    """
    Configuration class for the system module.

    Handles automatic metadata synchronization on startup.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.system'
    verbose_name = 'System'

    def ready(self) -> None:
        """
        Called when Django starts.

        Automatically syncs hardcoded models to metadata tables.
        This ensures BusinessObject records and ModelFieldDefinition
        entries are created for all hardcoded Django models.

        Also auto-registers standard business objects for dynamic routing.

        Also registers signal handlers for translation cleanup.
        """
        # Import here to avoid circular imports
        from apps.system.services.metadata_sync_service import sync_metadata_on_startup
        from apps.system.services.object_registry import ObjectRegistry
        from apps.system import signals  # Register signal handlers
        from django.conf import settings

        # Engineering note:
        # - AppConfig.ready() runs for *every* process (runserver, celery, management commands).
        # - Performing DB writes here can create surprising side-effects (e.g. a "dry-run" command mutates DB).
        # Policy:
        # - Default: enable in DEBUG for `runserver` only.
        # - Override via env `SYNC_METADATA_ON_STARTUP=True|False`.
        enabled_env = os.getenv('SYNC_METADATA_ON_STARTUP')
        enabled = settings.DEBUG if enabled_env is None else enabled_env.strip().lower() == 'true'

        proc = os.path.basename(sys.argv[0] or '').lower()
        cmd = (sys.argv[1] if len(sys.argv) > 1 else '').lower()
        is_celery = 'celery' in proc or cmd == 'celery'
        is_runserver = cmd == 'runserver'
        is_manage_command = bool(cmd) and cmd != 'runserver'

        if not enabled:
            logger.info("SYNC_METADATA_ON_STARTUP disabled; skipping metadata sync and auto-registration")
            return
        if is_celery:
            logger.info("Skipping metadata sync on celery process startup")
            return
        if is_manage_command and not is_runserver:
            logger.info(f"Skipping metadata sync on management command startup: {cmd}")
            return
        # Avoid double-running on Django's auto-reloader parent process.
        # Only perform startup sync in the reloader child (RUN_MAIN=true).
        if is_runserver and os.environ.get('RUN_MAIN') != 'true':
            logger.info("Skipping metadata sync on runserver reloader parent (RUN_MAIN!=true)")
            return

        # Check if database is ready before attempting sync
        # This prevents "unable to open database file" errors during startup
        if not self._is_database_ready():
            logger.warning("Database not ready, skipping metadata sync on startup")
            logger.info("Run 'python manage.py sync_metadata' manually to sync metadata")
        else:
            # Perform metadata sync
            # Note: This runs in every process (web server, celery worker, etc.)
            # In production with multiple workers, the first worker to start
            # will create the records, subsequent workers will see they exist.
            try:
                sync_metadata_on_startup(force=False)
            except Exception as e:
                logger.warning(f"Metadata sync on startup failed: {e}")
                # Don't fail startup if sync has issues
                # The sync can be retried manually via management command

        # Auto-register standard business objects for dynamic routing
        try:
            count = ObjectRegistry.auto_register_standard_objects()
            logger.info(f"Auto-registered {count} standard business objects")
        except Exception as e:
            logger.warning(f"Object registry auto-registration failed: {e}")
            # Don't fail startup if registry has issues

    def _is_database_ready(self) -> bool:
        """
        Check if database connection is ready.

        Returns True if we can successfully query the database,
        False otherwise. This prevents database errors during
        AppConfig.ready() when the database hasn't fully initialized.
        """
        try:
            from django.db import connection
            from django.core.exceptions import ImproperlyConfigured

            # Try to get a database connection and execute a simple query
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception as e:
            logger.debug(f"Database not ready: {e}")
            return False
