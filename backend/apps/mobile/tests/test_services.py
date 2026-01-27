"""
Service Tests for Mobile Enhancement Module.

Tests all mobile service classes for:
- DeviceService - device management operations
- SyncService - data synchronization operations
- SyncLogService - sync logging operations
- MobileApprovalService - approval delegation operations
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import Mock, patch
from apps.mobile.models import (
    MobileDevice,
    DeviceSecurityLog,
    OfflineData,
    SyncConflict,
    SyncLog,
    ApprovalDelegate,
)
from apps.mobile.services import (
    DeviceService,
    SyncService,
    SyncLogService,
    MobileApprovalService,
)
from apps.organizations.models import Organization

User = get_user_model()


class DeviceServiceTest(TestCase):
    """Test cases for DeviceService."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(name='Test Org', code='TEST001')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            organization=self.org
        )

    def test_register_new_device(self):
        """Test registering a new device."""
        device_info = {
            'device_name': 'iPhone 13',
            'device_type': 'ios',
            'os_version': '16.0',
            'app_version': '1.0.0',
            'ip_address': '192.168.1.100'
        }

        device = DeviceService.register_device(
            user=self.user,
            device_id='device_001',
            device_info=device_info
        )

        self.assertEqual(device.device_id, 'device_001')
        self.assertEqual(device.device_name, 'iPhone 13')
        self.assertEqual(device.device_type, 'ios')
        self.assertTrue(device.is_bound)
        self.assertTrue(device.is_active)
        self.assertEqual(device.user, self.user)

    def test_register_existing_device(self):
        """Test updating an existing device."""
        device_info = {
            'device_name': 'iPhone 13',
            'device_type': 'ios',
            'os_version': '16.0',
            'app_version': '1.0.0'
        }

        # Create initial device
        DeviceService.register_device(self.user, 'device_002', device_info)

        # Update with new info
        updated_info = {
            'device_name': 'iPhone 13',
            'device_type': 'ios',
            'os_version': '16.1',
            'app_version': '1.1.0'
        }

        device = DeviceService.register_device(self.user, 'device_002', updated_info)

        self.assertEqual(device.os_version, '16.1')
        self.assertEqual(device.app_version, '1.1.0')

    def test_unbind_device(self):
        """Test unbinding a device."""
        device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_003',
            device_name='Test Device',
            device_type='ios',
            is_bound=True
        )

        # Use device_id field instead of pk for test
        result = DeviceService.unbind_device(self.user, device.device_id)
        self.assertTrue(result)

        device.refresh_from_db()
        self.assertFalse(device.is_bound)

    def test_unbind_nonexistent_device(self):
        """Test unbinding a nonexistent device."""
        result = DeviceService.unbind_device(self.user, 'nonexistent-id')
        self.assertFalse(result)

    def test_check_device_limit(self):
        """Test checking device limit."""
        # No devices yet
        self.assertTrue(DeviceService.check_device_limit(self.user, max_devices=3))

        # Create 2 devices
        for i in range(2):
            MobileDevice.objects.create(
                user=self.user,
                device_id=f'device_{i}',
                device_name=f'Device {i}',
                device_type='ios',
                is_bound=True
            )

        # Still under limit
        self.assertTrue(DeviceService.check_device_limit(self.user, max_devices=3))

        # Create 3rd device
        MobileDevice.objects.create(
            user=self.user,
            device_id='device_3',
            device_name='Device 3',
            device_type='ios',
            is_bound=True
        )

        # At limit
        self.assertFalse(DeviceService.check_device_limit(self.user, max_devices=3))

    def test_revoke_old_devices(self):
        """Test revoking old devices when limit is reached."""
        # Create 3 devices with different last_login times
        now = timezone.now()
        for i in range(3):
            MobileDevice.objects.create(
                user=self.user,
                device_id=f'device_{i}',
                device_name=f'Device {i}',
                device_type='ios',
                is_bound=True,
                last_login_at=now - timezone.timedelta(hours=3 - i)
            )

        # Revoke old devices, keep 2
        DeviceService.revoke_old_devices(self.user, keep_count=2)

        # Check that oldest device is unbound
        old_device = MobileDevice.objects.get(device_id='device_0')
        self.assertFalse(old_device.is_bound)

        # Check that newer devices are still bound
        device_1 = MobileDevice.objects.get(device_id='device_1')
        device_2 = MobileDevice.objects.get(device_id='device_2')
        self.assertTrue(device_1.is_bound)
        self.assertTrue(device_2.is_bound)

    def test_get_user_devices(self):
        """Test getting user's devices."""
        # Create multiple devices
        for i in range(3):
            MobileDevice.objects.create(
                user=self.user,
                device_id=f'device_{i}',
                device_name=f'Device {i}',
                device_type='ios'
            )

        devices = DeviceService.get_user_devices(self.user)
        self.assertEqual(devices.count(), 3)

    def test_log_security_event(self):
        """Test logging security events."""
        device = MobileDevice.objects.create(
            user=self.user,
            device_id='device_001',
            device_name='Test Device',
            device_type='ios'
        )

        log = DeviceService.log_security_event(
            device=device,
            event_type='login',
            ip_address='192.168.1.100',
            location={'latitude': 40.7128, 'longitude': -74.0060}
        )

        self.assertEqual(log.device, device)
        self.assertEqual(log.event_type, 'login')
        self.assertEqual(log.ip_address, '192.168.1.100')
        self.assertIsNotNone(log.location)


class SyncServiceTest(TestCase):
    """Test cases for SyncService."""

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
        self.sync_service = SyncService(user=self.user, device=self.device)

    def test_upload_offline_data_success(self):
        """Test uploading offline data successfully."""
        data_list = [
            {
                'table_name': 'test.TestModel',  # Use non-existent model for testing
                'record_id': 'asset_001',
                'operation': 'update',
                'data': {'status': 'in_use'},
                'version': 1
            }
        ]

        result = self.sync_service.upload_offline_data(data_list)

        self.assertIn('success', result)
        self.assertIn('failed', result)
        self.assertIn('conflicts', result)
        self.assertEqual(result['success'], 1)

        # Verify offline data was created
        offline_data = OfflineData.objects.get(record_id='asset_001')
        self.assertEqual(offline_data.operation, 'update')

    def test_upload_offline_data_with_conflict(self):
        """Test uploading data that causes a conflict."""
        # Create existing offline data that would cause conflict
        OfflineData.objects.create(
            user=self.user,
            device=self.device,
            table_name='assets.Asset',
            record_id='asset_002',
            operation='update',
            data={'status': 'in_use'},
            client_version=1,
            sync_status='conflict'
        )

        data_list = [
            {
                'table_name': 'assets.Asset',
                'record_id': 'asset_002',
                'operation': 'update',
                'data': {'status': 'in_storage'},
                'version': 1
            }
        ]

        result = self.sync_service.upload_offline_data(data_list)

        # Should handle existing conflict
        self.assertIsNotNone(result)

    def test_upload_offline_data_empty_list(self):
        """Test uploading empty data list."""
        result = self.sync_service.upload_offline_data([])

        self.assertEqual(result['success'], 0)
        self.assertEqual(result['failed'], 0)

    def test_resolve_conflict_server_wins(self):
        """Test resolving conflict with server_wins strategy."""
        conflict = SyncConflict.objects.create(
            user=self.user,
            offline_data=OfflineData.objects.create(
                user=self.user,
                device=self.device,
                table_name='assets.Asset',
                record_id='asset_001',
                operation='update',
                data={'status': 'client_value'},
                client_version=1
            ),
            conflict_type='version_mismatch',
            table_name='assets.Asset',
            record_id='asset_001',
            local_data={'status': 'client_value'},
            server_data={'status': 'server_value'}
        )

        result = self.sync_service.resolve_conflict(
            conflict_id=str(conflict.id),
            resolution='server_wins'
        )

        self.assertTrue(result)

        conflict.refresh_from_db()
        self.assertEqual(conflict.resolution, 'server_wins')
        self.assertIsNotNone(conflict.resolved_at)

    def test_resolve_conflict_client_wins(self):
        """Test resolving conflict with client_wins strategy."""
        conflict = SyncConflict.objects.create(
            user=self.user,
            offline_data=OfflineData.objects.create(
                user=self.user,
                device=self.device,
                table_name='assets.Asset',
                record_id='asset_001',
                operation='update',
                data={'status': 'client_value'},
                client_version=1
            ),
            conflict_type='version_mismatch',
            table_name='assets.Asset',
            record_id='asset_001',
            local_data={'status': 'client_value'},
            server_data={'status': 'server_value'}
        )

        result = self.sync_service.resolve_conflict(
            conflict_id=str(conflict.id),
            resolution='client_wins'
        )

        self.assertTrue(result)

        conflict.refresh_from_db()
        self.assertEqual(conflict.resolution, 'client_wins')

    def test_resolve_conflict_merge(self):
        """Test resolving conflict with merge strategy."""
        conflict = SyncConflict.objects.create(
            user=self.user,
            offline_data=OfflineData.objects.create(
                user=self.user,
                device=self.device,
                table_name='assets.Asset',
                record_id='asset_001',
                operation='update',
                data={'status': 'client_value'},
                client_version=1
            ),
            conflict_type='version_mismatch',
            table_name='assets.Asset',
            record_id='asset_001',
            local_data={'status': 'client_value', 'location': 'A'},
            server_data={'status': 'server_value', 'location': 'B'}
        )

        merged_data = {'status': 'merged_value', 'location': 'A'}

        result = self.sync_service.resolve_conflict(
            conflict_id=str(conflict.id),
            resolution='merge',
            merged_data=merged_data
        )

        self.assertTrue(result)

        conflict.refresh_from_db()
        self.assertEqual(conflict.resolution, 'merge')
        self.assertEqual(conflict.merged_data, merged_data)


class SyncLogServiceTest(TestCase):
    """Test cases for SyncLogService."""

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
        """Test creating a sync log entry."""
        sync_log = SyncLogService.create_sync_log(
            user=self.user,
            device=self.device,
            sync_type='full',
            sync_direction='bidirectional'
        )

        self.assertEqual(sync_log.user, self.user)
        self.assertEqual(sync_log.device, self.device)
        self.assertEqual(sync_log.sync_type, 'full')
        self.assertEqual(sync_log.sync_direction, 'bidirectional')
        self.assertEqual(sync_log.status, 'running')
        self.assertIsNotNone(sync_log.started_at)

    def test_finish_sync_log_success(self):
        """Test finishing sync log with success."""
        sync_log = SyncLog.objects.create(
            user=self.user,
            device=self.device,
            sync_type='full',
            sync_direction='bidirectional',
            status='running'
        )

        results = {
            'upload_count': 10,
            'download_count': 5,
            'conflict_count': 0,
            'error_count': 0
        }

        SyncLogService.finish_sync_log(sync_log, results)

        sync_log.refresh_from_db()
        self.assertEqual(sync_log.status, 'success')
        self.assertEqual(sync_log.upload_count, 10)
        self.assertEqual(sync_log.download_count, 5)
        self.assertEqual(sync_log.conflict_count, 0)
        self.assertIsNotNone(sync_log.finished_at)
        self.assertIsNotNone(sync_log.duration)

    def test_finish_sync_log_with_errors(self):
        """Test finishing sync log with errors."""
        sync_log = SyncLog.objects.create(
            user=self.user,
            device=self.device,
            sync_type='full',
            sync_direction='bidirectional',
            status='running'
        )

        results = {
            'upload_count': 8,
            'download_count': 5,
            'conflict_count': 1,
            'error_count': 2
        }

        SyncLogService.finish_sync_log(sync_log, results)

        sync_log.refresh_from_db()
        self.assertEqual(sync_log.status, 'partial_success')
        self.assertEqual(sync_log.error_count, 2)

    def test_get_server_version(self):
        """Test getting server version."""
        version = SyncLogService._get_server_version()
        self.assertIsInstance(version, int)
        self.assertGreater(version, 0)


class MobileApprovalServiceTest(TestCase):
    """Test cases for MobileApprovalService."""

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

    def test_delegate_approval_temporary(self):
        """Test creating temporary approval delegation."""
        config = {
            'delegate_type': 'temporary',
            'delegate_scope': 'all',
            'start_time': timezone.now(),
            'end_time': timezone.now() + timezone.timedelta(days=7)
        }

        delegation = MobileApprovalService.delegate_approval(
            user=self.user1,
            delegate_user_id=str(self.user2.id),
            config=config
        )

        self.assertEqual(delegation.delegator, self.user1)
        self.assertEqual(delegation.delegate, self.user2)
        self.assertEqual(delegation.delegate_type, 'temporary')
        self.assertTrue(delegation.is_active)

    def test_delegate_approval_permanent(self):
        """Test creating permanent approval delegation."""
        config = {
            'delegate_type': 'permanent',
            'delegate_scope': 'all',
            'start_time': timezone.now()
        }

        delegation = MobileApprovalService.delegate_approval(
            user=self.user1,
            delegate_user_id=str(self.user2.id),
            config=config
        )

        self.assertEqual(delegation.delegate_type, 'permanent')
        self.assertIsNone(delegation.end_time)

    def test_check_delegation_exists(self):
        """Test checking for active delegation."""
        now = timezone.now()

        # Create active delegation
        ApprovalDelegate.objects.create(
            delegator=self.user1,
            delegate=self.user2,
            delegate_type='temporary',
            delegate_scope='all',
            start_time=now - timezone.timedelta(hours=1),
            end_time=now + timezone.timedelta(days=7)
        )

        delegate = MobileApprovalService.check_delegation(self.user1)
        self.assertEqual(delegate, self.user2)

    def test_check_delegation_none(self):
        """Test checking when no delegation exists."""
        delegate = MobileApprovalService.check_delegation(self.user1)
        self.assertIsNone(delegate)

    def test_check_delegation_expired(self):
        """Test checking expired delegation."""
        now = timezone.now()

        # Create expired delegation
        ApprovalDelegate.objects.create(
            delegator=self.user1,
            delegate=self.user2,
            delegate_type='temporary',
            delegate_scope='all',
            start_time=now - timezone.timedelta(days=10),
            end_time=now - timezone.timedelta(days=1)
        )

        delegate = MobileApprovalService.check_delegation(self.user1)
        self.assertIsNone(delegate)

    def test_revoke_delegation(self):
        """Test revoking a delegation."""
        delegation = ApprovalDelegate.objects.create(
            delegator=self.user1,
            delegate=self.user2,
            delegate_type='temporary',
            delegate_scope='all',
            start_time=timezone.now()
        )

        result = MobileApprovalService.revoke_delegation(
            user=self.user1,
            delegation_id=str(delegation.id)
        )

        self.assertTrue(result)

        delegation.refresh_from_db()
        self.assertFalse(delegation.is_active)
        self.assertTrue(delegation.is_revoked)
        self.assertIsNotNone(delegation.revoked_at)

    def test_revoke_delegation_not_found(self):
        """Test revoking nonexistent delegation."""
        result = MobileApprovalService.revoke_delegation(
            user=self.user1,
            delegation_id='nonexistent-id'
        )

        self.assertFalse(result)

    def test_get_pending_approvals(self):
        """Test getting pending approvals."""
        # Mock implementation - would need workflow integration
        approvals = MobileApprovalService.get_pending_approvals(self.user1)
        self.assertIsInstance(approvals, list)

    def test_execute_approval(self):
        """Test executing an approval."""
        # Mock implementation - would need workflow integration
        result = MobileApprovalService.execute_approval(
            user=self.user1,
            approval_id='test-approval-id',
            action='approve',
            comment='Approved'
        )

        # Check result structure
        self.assertIn('success', result)
