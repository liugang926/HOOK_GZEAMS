"""
WeWork Sync Service

Service for syncing WeWork (企业微信) contacts (departments and users)
to the local system. Uses BaseCRUDService for unified data operations.
"""
import logging
import secrets
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from apps.sso.models import WeWorkConfig, SyncLog, UserMapping
from apps.sso.adapters.wework_adapter import WeWorkAdapter
from apps.organizations.models import Organization
from apps.common.services.base_crud import BaseCRUDService

User = get_user_model()
logger = logging.getLogger(__name__)


class WeWorkSyncService:
    """WeWork (企业微信) Sync Service - Uses BaseCRUDService for operations."""

    def __init__(self, config: WeWorkConfig):
        """Initialize sync service with WeWork configuration.

        Args:
            config: WeWorkConfig instance
        """
        self.config = config
        self.adapter = WeWorkAdapter(config)
        self.organization = config.organization
        self.log: Optional[SyncLog] = None
        self.errors = []

        # Use BaseCRUDService for managing SyncLog
        self.sync_log_service = BaseCRUDService(SyncLog)

    # ==================== Full Sync ====================

    def full_sync(self) -> SyncLog:
        """Full sync (departments + users).

        Returns:
            SyncLog: Sync log record
        """
        # Create sync log using BaseCRUDService
        self.log = self.sync_log_service.create(
            data={
                'organization': self.organization.id,
                'sync_type': SyncLog.SyncTypeChoices.FULL,
                'sync_source': 'wework',
                'status': SyncLog.StatusChoices.RUNNING
            }
        )

        logger.info(f"Starting full sync: organization={self.organization.id}")

        try:
            # 1. Sync departments
            dept_stats = self.sync_departments()

            # 2. Update department hierarchy
            self._update_department_hierarchy()

            # 3. Sync users
            user_stats = self.sync_users()

            # Update sync log with success status
            self.log.mark_success(
                total=dept_stats['total'] + user_stats['total'],
                created=dept_stats['created'] + user_stats['created'],
                updated=dept_stats['updated'] + user_stats['updated'],
                deleted=dept_stats.get('deleted', 0)
            )

            logger.info(f"Full sync completed: total={self.log.total_count}, "
                       f"created={self.log.created_count}, updated={self.log.updated_count}")

        except Exception as e:
            logger.error(f"Full sync failed: {str(e)}", exc_info=True)
            self.log.mark_failed(
                error_message=str(e),
                error_details={'errors': self.errors[:10]}
            )
            raise

        return self.log

    # ==================== Department Sync ====================

    def sync_departments(self) -> Dict:
        """Sync department structure.

        Returns:
            Statistics dictionary
        """
        logger.info("Starting department sync")

        # Use BaseCRUDService for managing Organization (departments)
        org_service = BaseCRUDService(Organization)

        # Get WeWork department list
        wework_depts = self.adapter.get_department_list()
        stats = {
            'total': len(wework_depts),
            'created': 0,
            'updated': 0,
            'deleted': 0
        }

        # Query existing departments with WeWork mapping
        existing_depts = org_service.query(
            filters={
                'wework_dept_id__isnull': False
            }
        )

        # Build mapping {wework_id: local_dept}
        dept_map = {
            d.wework_dept_id: d
            for d in existing_depts
            if d.wework_dept_id
        }

        # Track processed department IDs
        processed_ids = set()

        for wework_dept in wework_depts:
            wework_id = str(wework_dept['id'])
            processed_ids.add(wework_id)

            try:
                if wework_id in dept_map:
                    # Update existing department
                    dept = dept_map[wework_id]
                    update_data = {
                        'name': wework_dept['name'],
                        'wework_parent_id': wework_dept.get('parentid')
                    }

                    # Update if there are changes
                    if (dept.name != wework_dept['name'] or
                            dept.wework_parent_id != wework_dept.get('parentid')):
                        org_service.update(dept.id, data=update_data)
                        stats['updated'] += 1
                        logger.debug(f"Updated department: {dept.name} -> {wework_dept['name']}")
                else:
                    # Create new department
                    parent_id = None
                    wework_parent_id = wework_dept.get('parentid')
                    if wework_parent_id:
                        # Find parent by WeWork parent ID
                        parent = org_service.query(
                            filters={'wework_dept_id': str(wework_parent_id)}
                        ).first()
                        if parent:
                            parent_id = parent.id

                    org_service.create(
                        data={
                            'name': wework_dept['name'],
                            'code': f"WW_{wework_id}",
                            'org_type': 'department',
                            'parent_id': parent_id,
                            'wework_dept_id': wework_id,
                            'wework_parent_id': wework_parent_id,
                            'is_active': True
                        }
                    )
                    stats['created'] += 1
                    logger.debug(f"Created department: {wework_dept['name']}")

            except Exception as e:
                error_msg = f"Failed to sync department {wework_dept.get('name', wework_id)}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)

        logger.info(f"Department sync completed: {stats}")
        return stats

    def _update_department_hierarchy(self):
        """Update department hierarchy (establish parent-child relationships)."""
        org_service = BaseCRUDService(Organization)

        depts = org_service.query(
            filters={
                'wework_dept_id__isnull': False
            }
        )

        for dept in depts:
            if dept.wework_parent_id is not None:
                # Find parent by WeWork parent ID
                parent_depts = org_service.query(
                    filters={
                        'wework_dept_id': str(dept.wework_parent_id)
                    }
                )
                parent = parent_depts.first()

                if parent and dept.parent_id != parent.id:
                    org_service.update(
                        instance_id=dept.id,
                        data={
                            'parent': parent.id
                        }
                    )
                    logger.debug(f"Updated hierarchy: {dept.name} -> parent {parent.name}")

        logger.debug("Department hierarchy updated")

    # ==================== User Sync ====================

    def sync_users(self) -> Dict:
        """Sync user information.

        Returns:
            Statistics dictionary
        """
        logger.info("Starting user sync")

        # Use BaseCRUDService for managing users
        user_service = BaseCRUDService(User)

        # Get all departments from WeWork
        wework_depts = self.adapter.get_department_list()
        stats = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'deleted': 0
        }

        # Query existing user mappings
        user_mappings = UserMapping.objects.filter(
            platform='wework',
            organization=self.organization
        ).select_related('system_user')

        user_map = {
            m.platform_userid: (m.system_user, m)
            for m in user_mappings
        }

        # Track processed user IDs
        processed_user_ids = set()

        for dept in wework_depts:
            try:
                # Get department members
                wework_users = self.adapter.get_department_users(dept['id'])
                stats['total'] += len(wework_users)

                for wework_user in wework_users:
                    user_id = wework_user['userid']
                    processed_user_ids.add(user_id)

                    try:
                        if user_id in user_map:
                            # Update existing user
                            user, mapping = user_map[user_id]
                            self._update_user_from_wework(user, wework_user, user_service)
                            stats['updated'] += 1
                        else:
                            # Create new user
                            user = self._create_user_from_wework(wework_user, user_service)
                            stats['created'] += 1

                    except Exception as e:
                        error_msg = f"Failed to sync user {wework_user.get('name', user_id)}: {str(e)}"
                        logger.error(error_msg)
                        self.errors.append(error_msg)

            except Exception as e:
                error_msg = f"Failed to get department members {dept.get('name', dept['id'])}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)

        logger.info(f"User sync completed: {stats}")
        return stats

    def _create_user_from_wework(self, wework_user: Dict, user_service: BaseCRUDService):
        """Create system user from WeWork user.

        Args:
            wework_user: WeWork user info
            user_service: BaseCRUDService instance

        Returns:
            Created User instance
        """
        username = f"ww_{wework_user['userid']}"

        # Check if username exists, add random suffix if needed
        if User.objects.filter(username=username).exists():
            username = f"ww_{wework_user['userid']}_{secrets.token_hex(4)}"

        # Get main department
        main_dept_id = None
        dept_ids = wework_user.get('department', [])
        if dept_ids:
            # Use first department as main department
            main_dept_wework_id = str(dept_ids[0])
            org_service = BaseCRUDService(Organization)
            main_dept = org_service.query(
                filters={'wework_dept_id': main_dept_wework_id}
            ).first()
            if main_dept:
                main_dept_id = main_dept.id

        # Create user
        user_data = {
            'username': username,
            'email': wework_user.get('email', ''),
            'mobile': wework_user.get('mobile', ''),
            'organization': self.organization.id,
            'department_id': main_dept_id,
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
        }

        # Check if user model has real_name field
        user = user_service.create(data=user_data)

        if hasattr(user, 'real_name'):
            user.real_name = wework_user['name']
            user.save(update_fields=['real_name'])

        # Create user mapping
        UserMapping.objects.create(
            organization=self.organization,
            system_user=user,
            platform='wework',
            platform_userid=wework_user['userid'],
            platform_name=wework_user['name'],
            platform_unionid=wework_user.get('unionid', ''),
            extra_data={
                'avatar': wework_user.get('avatar', ''),
                'position': wework_user.get('position', ''),
                'english_name': wework_user.get('english_name', ''),
                'department': wework_user.get('department', []),
            }
        )

        logger.debug(f"Created user: {user.real_name or username}")
        return user

    def _update_user_from_wework(self, user: User, wework_user: Dict, user_service: BaseCRUDService):
        """Update system user from WeWork user.

        Args:
            user: System User instance
            wework_user: WeWork user info
            user_service: BaseCRUDService instance
        """
        update_data = {}

        if hasattr(user, 'real_name') and user.real_name != wework_user['name']:
            user.real_name = wework_user['name']
            user.save(update_fields=['real_name'])

        email = wework_user.get('email', '')
        if user.email != email and email:
            update_data['email'] = email

        mobile = wework_user.get('mobile', '')
        if hasattr(user, 'mobile') and user.mobile != mobile and mobile:
            update_data['mobile'] = mobile

        avatar = wework_user.get('avatar', '')
        if hasattr(user, 'avatar') and user.avatar != avatar and avatar:
            user.avatar = avatar
            user.save(update_fields=['avatar'])

        if update_data:
            user_service.update(user.id, data=update_data)
            logger.debug(f"Updated user: {user.real_name or user.username}")

        # Update mapping
        UserMapping.objects.filter(
            organization=self.organization,
            platform='wework',
            platform_userid=wework_user['userid'],
            system_user=user
        ).update(
            platform_name=wework_user['name'],
            platform_unionid=wework_user.get('unionid', ''),
            extra_data={
                'avatar': wework_user.get('avatar', ''),
                'position': wework_user.get('position', ''),
                'english_name': wework_user.get('english_name', ''),
                'department': wework_user.get('department', []),
            }
        )

    # ==================== Individual Sync Methods ====================

    def sync_departments_only(self) -> SyncLog:
        """Sync departments only.

        Returns:
            SyncLog instance
        """
        self.log = self.sync_log_service.create(
            data={
                'organization': self.organization.id,
                'sync_type': SyncLog.SyncTypeChoices.DEPARTMENT,
                'sync_source': 'wework',
                'status': SyncLog.StatusChoices.RUNNING
            }
        )

        try:
            stats = self.sync_departments()
            self._update_department_hierarchy()

            self.log.mark_success(
                total=stats['total'],
                created=stats['created'],
                updated=stats['updated']
            )

        except Exception as e:
            logger.error(f"Department sync failed: {str(e)}", exc_info=True)
            self.log.mark_failed(error_message=str(e))
            raise

        return self.log

    def sync_users_only(self) -> SyncLog:
        """Sync users only.

        Returns:
            SyncLog instance
        """
        self.log = self.sync_log_service.create(
            data={
                'organization': self.organization.id,
                'sync_type': SyncLog.SyncTypeChoices.USER,
                'sync_source': 'wework',
                'status': SyncLog.StatusChoices.RUNNING
            }
        )

        try:
            stats = self.sync_users()

            self.log.mark_success(
                total=stats['total'],
                created=stats['created'],
                updated=stats['updated']
            )

        except Exception as e:
            logger.error(f"User sync failed: {str(e)}", exc_info=True)
            self.log.mark_failed(error_message=str(e))
            raise

        return self.log

    # ==================== Incremental Sync ====================

    def incremental_sync(self) -> SyncLog:
        """
        Incremental sync (only sync changed data).

        Note: WeWork API doesn't support true incremental queries,
        so this performs a full sync but with optimized logic.

        Returns:
            SyncLog instance
        """
        # For WeWork, incremental is same as full since API doesn't support it
        return self.full_sync()
