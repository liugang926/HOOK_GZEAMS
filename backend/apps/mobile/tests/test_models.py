"""
Model Tests for Mobile Enhancement Module.

Tests all mobile models for:
- Field definitions and constraints
- BaseModel inheritance functionality
- Custom methods and properties
- Relationships between models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.mobile.models import (
    MobileDevice,
    DeviceSecurityLog,
    OfflineData,
    SyncConflict,
    SyncLog,
    ApprovalDelegate,
)
from apps.organizations.models import Organization

User = get_user_model()


class MobileDeviceModelTest(TestCase):
    """Test cases for MobileDevice model."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(name='Test Org', code='TEST001')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )

    def test_create_mobile_device(self):
        """Test creating a mobile device."""
        device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_001',
            device_name='iPhone 13',
            device_type='ios',
            os_version='16.0',
            app_version='1.0.0',
            device_info={'brand': 'Apple', 'model': 'iPhone13'}
        )
        self.assertEqual(device.device_id, 'device_001')
        self.assertEqual(device.device_name, 'iPhone 13')
        self.assertEqual(device.device_type, 'ios')
        self.assertTrue(device.is_bound)
        self.assertTrue(device.is_active)
        self.assertFalse(device.enable_biometric)
        self.assertTrue(device.allow_offline)

    def test_device_type_choices(self):
        """Test device type choices."""
        device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_002',
            device_name='Android Phone',
            device_type='android'
        )
        self.assertEqual(device.device_type, 'android')
        self.assertIn(device.device_type, ['ios', 'android', 'h5'])

    def test_base_model_inheritance(self):
        """Test that MobileDevice inherits from BaseModel."""
        device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_003',
            device_name='Test Device',
            device_type='ios',
            created_by=self.user
        )
        # BaseModel fields should exist
        self.assertIsNotNone(device.created_at)
        self.assertIsNone(device.deleted_at)
        self.assertFalse(device.is_deleted)
        self.assertEqual(device.created_by, self.user)

    def test_device_unbind_method(self):
        """Test device unbind method."""
        device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_004',
            device_name='Test Device',
            device_type='ios',
            is_bound=True
        )
        self.assertTrue(device.is_bound)

        device.unbind()
        device.refresh_from_db()
        self.assertFalse(device.is_bound)

    def test_device_update_last_activity(self):
        """Test updating last login timestamp."""
        device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_005',
            device_name='Test Device',
            device_type='ios'
        )
        old_last_login = device.last_login_at

        device.update_last_activity(ip='192.168.1.100')
        device.refresh_from_db()

        self.assertIsNotNone(device.last_login_at)
        self.assertEqual(device.last_login_ip, '192.168.1.100')

    def test_device_unique_constraint(self):
        """Test that device_id is unique."""
        MobileDevice.objects.create(
            user=self.user,
            device_id='device_006',
            device_name='Device 1',
            device_type='ios'
        )

        # Try to create another device with same device_id
        with self.assertRaises(Exception):
            MobileDevice.objects.create(
                user=self.user,
                device_id='device_006',  # Duplicate
                device_name='Device 2',
                device_type='android'
            )


class DeviceSecurityLogModelTest(TestCase):
    """Test cases for DeviceSecurityLog model."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(name='Test Org', code='TEST001')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_001',
            device_name='Test Device',
            device_type='ios'
        )

    def test_create_security_log(self):
        """Test creating a security log entry."""
        log = DeviceSecurityLog.objects.create(
            device=self.device,
            event_type='login',
            ip_address='192.168.1.100',
            location={'latitude': 40.7128, 'longitude': -74.0060},
            details={'user_agent': 'Mozilla/5.0'}
        )
        self.assertEqual(log.device, self.device)
        self.assertEqual(log.event_type, 'login')
        self.assertEqual(log.ip_address, '192.168.1.100')
        self.assertIsNotNone(log.location)

    def test_event_type_choices(self):
        """Test event type choices."""
        valid_types = ['login', 'logout', 'bind', 'unbind', 'sync_failed']
        for event_type in valid_types:
            log = DeviceSecurityLog.objects.create(
                device=self.device,
                event_type=event_type,
                ip_address='192.168.1.100'
            )
            self.assertEqual(log.event_type, event_type)

    def test_security_log_with_device_relationship(self):
        """Test security log relationship to device."""
        log = DeviceSecurityLog.objects.create(
            device=self.device,
            event_type='login',
            ip_address='192.168.1.100'
        )
        self.assertEqual(log.device.device_id, 'device_001')


class OfflineDataModelTest(TestCase):
    """Test cases for OfflineData model."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(name='Test Org', code='TEST001')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_001',
            device_name='Test Device',
            device_type='ios'
        )

    def test_create_offline_data(self):
        """Test creating offline data entry."""
        offline_data = OfflineData.objects.create(
            user=self.user,
            device=self.device,
            table_name='assets.Asset',
            record_id='asset_001',
            operation='update',
            data={'status': 'in_use'},
            client_version=1,
            client_created_at=timezone.now()
        )
        self.assertEqual(offline_data.table_name, 'assets.Asset')
        self.assertEqual(offline_data.operation, 'update')
        self.assertEqual(offline_data.sync_status, 'pending')
        self.assertIsNone(offline_data.synced_at)

    def test_operation_choices(self):
        """Test operation type choices."""
        operations = ['create', 'update', 'delete']
        for op in operations:
            offline_data = OfflineData.objects.create(
                user=self.user,
                device=self.device,
                table_name='assets.Asset',
                record_id=f'asset_{op}',
                operation=op,
                data={},
                client_version=1
            )
            self.assertEqual(offline_data.operation, op)

    def test_sync_status_choices(self):
        """Test sync status choices."""
        statuses = ['pending', 'processing', 'synced', 'conflict', 'failed']
        for status in statuses:
            offline_data = OfflineData.objects.create(
                user=self.user,
                device=self.device,
                table_name='assets.Asset',
                record_id=f'asset_{status}',
                operation='update',
                data={},
                client_version=1,
                sync_status=status
            )
            self.assertEqual(offline_data.sync_status, status)

    def test_mark_as_synced(self):
        """Test marking offline data as synced."""
        offline_data = OfflineData.objects.create(
            user=self.user,
            device=self.device,
            table_name='assets.Asset',
            record_id='asset_001',
            operation='update',
            data={},
            client_version=1,
            sync_status='pending'
        )

        offline_data.mark_as_synced(server_version=2)
        offline_data.refresh_from_db()

        self.assertEqual(offline_data.sync_status, 'synced')
        self.assertEqual(offline_data.server_version, 2)
        self.assertIsNotNone(offline_data.synced_at)


class SyncConflictModelTest(TestCase):
    """Test cases for SyncConflict model."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(name='Test Org', code='TEST001')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_001',
            device_name='Test Device',
            device_type='ios'
        )
        self.offline_data = OfflineData.objects.create(
            user=self.user,
            device=self.device,
            table_name='assets.Asset',
            record_id='asset_001',
            operation='update',
            data={'status': 'in_use'},
            client_version=1
        )

    def test_create_sync_conflict(self):
        """Test creating a sync conflict."""
        conflict = SyncConflict.objects.create(
            user=self.user,
            offline_data=self.offline_data,
            conflict_type='version_mismatch',
            table_name='assets.Asset',
            record_id='asset_001',
            local_data={'status': 'in_use'},
            server_data={'status': 'in_storage'}
        )
        self.assertEqual(conflict.conflict_type, 'version_mismatch')
        self.assertEqual(conflict.resolution, 'pending')
        self.assertEqual(conflict.table_name, 'assets.Asset')

    def test_conflict_type_choices(self):
        """Test conflict type choices."""
        conflict_types = ['version_mismatch', 'duplicate_create', 'concurrent_modify']
        for conflict_type in conflict_types:
            # Create separate offline data for each conflict
            offline_data = OfflineData.objects.create(
                user=self.user,
                device=self.device,
                table_name='assets.Asset',
                record_id=f'asset_{conflict_type}',
                operation='update',
                data={},
                client_version=1
            )
            conflict = SyncConflict.objects.create(
                user=self.user,
                offline_data=offline_data,
                conflict_type=conflict_type,
                table_name='assets.Asset',
                record_id=f'asset_{conflict_type}',
                local_data={},
                server_data={}
            )
            self.assertEqual(conflict.conflict_type, conflict_type)

    def test_resolution_choices(self):
        """Test resolution choices."""
        resolutions = ['pending', 'server_wins', 'client_wins', 'merge']
        for resolution in resolutions:
            # Create separate offline data for each conflict
            offline_data = OfflineData.objects.create(
                user=self.user,
                device=self.device,
                table_name='assets.Asset',
                record_id=f'asset_resolution_{resolution}',
                operation='update',
                data={},
                client_version=1
            )
            conflict = SyncConflict.objects.create(
                user=self.user,
                offline_data=offline_data,
                conflict_type='version_mismatch',
                table_name='assets.Asset',
                record_id=f'asset_resolution_{resolution}',
                local_data={},
                server_data={},
                resolution=resolution
            )
            self.assertEqual(conflict.resolution, resolution)

    def test_mark_resolved(self):
        """Test marking conflict as resolved."""
        conflict = SyncConflict.objects.create(
            user=self.user,
            offline_data=self.offline_data,
            conflict_type='version_mismatch',
            table_name='assets.Asset',
            record_id='asset_001',
            local_data={},
            server_data={}
        )

        conflict.mark_resolved('server_wins', merged_data={})
        conflict.refresh_from_db()

        self.assertEqual(conflict.resolution, 'server_wins')
        self.assertIsNotNone(conflict.resolved_at)


class SyncLogModelTest(TestCase):
    """Test cases for SyncLog model."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(name='Test Org', code='TEST001')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )
        self.device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_001',
            device_name='Test Device',
            device_type='ios'
        )

    def test_create_sync_log(self):
        """Test creating a sync log."""
        sync_log = SyncLog.objects.create(
            user=self.user,
            device=self.device,
            sync_type='full',
            sync_direction='bidirectional',
            status='running'
        )
        self.assertEqual(sync_log.sync_type, 'full')
        self.assertEqual(sync_log.sync_direction, 'bidirectional')
        self.assertEqual(sync_log.status, 'running')
        self.assertEqual(sync_log.upload_count, 0)
        self.assertEqual(sync_log.download_count, 0)
        self.assertEqual(sync_log.conflict_count, 0)

    def test_sync_type_choices(self):
        """Test sync type choices."""
        sync_types = ['full', 'incremental', 'initial']
        for sync_type in sync_types:
            sync_log = SyncLog.objects.create(
                user=self.user,
                device=self.device,
                sync_type=sync_type,
                sync_direction='upload',
                status='running'
            )
            self.assertEqual(sync_log.sync_type, sync_type)

    def test_sync_direction_choices(self):
        """Test sync direction choices."""
        directions = ['upload', 'download', 'bidirectional']
        for direction in directions:
            sync_log = SyncLog.objects.create(
                user=self.user,
                device=self.device,
                sync_type='full',
                sync_direction=direction,
                status='running'
            )
            self.assertEqual(sync_log.sync_direction, direction)

    def test_sync_status_choices(self):
        """Test sync status choices."""
        statuses = ['running', 'success', 'failed', 'partial_success']
        for status in statuses:
            sync_log = SyncLog.objects.create(
                user=self.user,
                device=self.device,
                sync_type='full',
                sync_direction='upload',
                status=status
            )
            self.assertEqual(sync_log.status, status)

    def test_calculate_duration(self):
        """Test calculating sync duration."""
        from datetime import timedelta

        started = timezone.now()
        finished = started + timedelta(seconds=5)

        sync_log = SyncLog.objects.create(
            user=self.user,
            device=self.device,
            sync_type='full',
            sync_direction='bidirectional',
            status='success',
            started_at=started,
            finished_at=finished
        )

        # Calculate duration
        sync_log.calculate_duration()
        sync_log.refresh_from_db()

        self.assertEqual(sync_log.duration, 5)


class ApprovalDelegateModelTest(TestCase):
    """Test cases for ApprovalDelegate model."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(name='Test Org', code='TEST001')
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            organization=self.org
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            organization=self.org
        )

    def test_create_approval_delegate(self):
        """Test creating an approval delegation."""
        delegation = ApprovalDelegate.objects.create(
            delegator=self.user1,
            delegate=self.user2,
            delegate_type='temporary',
            delegate_scope='all',
            start_time=timezone.now()
        )
        self.assertEqual(delegation.delegator, self.user1)
        self.assertEqual(delegation.delegate, self.user2)
        self.assertEqual(delegation.delegate_type, 'temporary')
        self.assertTrue(delegation.is_active)
        self.assertFalse(delegation.is_revoked)

    def test_delegate_type_choices(self):
        """Test delegate type choices."""
        delegate_types = ['temporary', 'permanent']
        for delegate_type in delegate_types:
            delegation = ApprovalDelegate.objects.create(
                delegator=self.user1,
                delegate=self.user2,
                delegate_type=delegate_type,
                delegate_scope='all',
                start_time=timezone.now()
            )
            self.assertEqual(delegation.delegate_type, delegate_type)

    def test_delegate_scope_choices(self):
        """Test delegate scope choices."""
        scopes = ['all', 'specific', 'department']
        for scope in scopes:
            delegation = ApprovalDelegate.objects.create(
                delegator=self.user1,
                delegate=self.user2,
                delegate_type='temporary',
                delegate_scope=scope,
                start_time=timezone.now()
            )
            self.assertEqual(delegation.delegate_scope, scope)

    def test_is_valid_method(self):
        """Test delegation validity check."""
        now = timezone.now()

        # Valid delegation
        delegation = ApprovalDelegate.objects.create(
            delegator=self.user1,
            delegate=self.user2,
            delegate_type='temporary',
            delegate_scope='all',
            start_time=now - timezone.timedelta(hours=1)
        )
        self.assertTrue(delegation.is_valid())

        # Inactive delegation
        delegation.is_active = False
        delegation.save()
        self.assertFalse(delegation.is_valid())

        # Revoked delegation
        delegation.is_active = True
        delegation.is_revoked = True
        delegation.save()
        self.assertFalse(delegation.is_valid())

    def test_delegation_time_range(self):
        """Test delegation with time range."""
        now = timezone.now()

        # Delegation not yet started
        delegation = ApprovalDelegate.objects.create(
            delegator=self.user1,
            delegate=self.user2,
            delegate_type='temporary',
            delegate_scope='all',
            start_time=now + timezone.timedelta(hours=1)
        )
        self.assertFalse(delegation.is_valid())

        # Update start time to make it valid
        delegation.start_time = now - timezone.timedelta(hours=1)
        delegation.save()
        self.assertTrue(delegation.is_valid())

        # Add end time in the past
        delegation.end_time = now - timezone.timedelta(minutes=30)
        delegation.save()
        self.assertFalse(delegation.is_valid())

    def test_revoke_delegation(self):
        """Test revoking a delegation."""
        delegation = ApprovalDelegate.objects.create(
            delegator=self.user1,
            delegate=self.user2,
            delegate_type='temporary',
            delegate_scope='all',
            start_time=timezone.now()
        )

        delegation.revoke(revoked_by=self.user1, reason='No longer needed')
        delegation.refresh_from_db()

        self.assertFalse(delegation.is_active)
        self.assertTrue(delegation.is_revoked)
        self.assertIsNotNone(delegation.revoked_at)
        self.assertEqual(delegation.revoked_by, self.user1)
        self.assertEqual(delegation.revoked_reason, 'No longer needed')
