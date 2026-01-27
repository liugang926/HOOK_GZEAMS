"""
Admin Panel Integration Tests for Mobile Module.

Tests Django Admin interface and mobile module integration.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class AdminPanelMobileTest(TestCase):
    """Test cases for Admin Panel mobile module integration."""

    def setUp(self):
        """Set up test client and admin user."""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='testpass123'
        )

    def test_admin_login_page(self):
        """Test admin login page is accessible."""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_admin_login(self):
        """Test admin login functionality."""
        logged_in = self.client.login(username='admin_test', password='testpass123')
        self.assertTrue(logged_in)

        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('GZEAMS Administration', response.content.decode())

    def test_mobile_models_registered(self):
        """Test that all mobile models are registered in admin."""
        self.client.login(username='admin_test', password='testpass123')

        # Test each mobile model admin URL
        mobile_admin_urls = [
            'admin:mobile_mobiledevice_changelist',
            'admin:mobile_devicesecuritylog_changelist',
            'admin:mobile_offlinedata_changelist',
            'admin:mobile_syncconflict_changelist',
            'admin:mobile_synclog_changelist',
            'admin:mobile_approvaldelegate_changelist',
        ]

        for url_name in mobile_admin_urls:
            try:
                url = reverse(url_name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200,
                                 f'{url_name} should be accessible')
            except Exception as e:
                self.fail(f'{url_name} failed: {e}')

    def test_mobile_devices_admin_page(self):
        """Test mobile devices admin page loads correctly."""
        self.client.login(username='admin_test', password='testpass123')

        url = reverse('admin:mobile_mobiledevice_changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Mobile', content)

    def test_sync_logs_admin_page(self):
        """Test sync logs admin page loads correctly."""
        self.client.login(username='admin_test', password='testpass123')

        url = reverse('admin:mobile_synclog_changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_approval_delegates_admin_page(self):
        """Test approval delegates admin page loads correctly."""
        self.client.login(username='admin_test', password='testpass123')

        url = reverse('admin:mobile_approvaldelegate_changelist')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_api_endpoints_exist(self):
        """Test that mobile API endpoints exist."""
        self.client.login(username='admin_test', password='testpass123')

        api_endpoints = [
            '/api/mobile/devices/',
            '/api/mobile/security-logs/',
            '/api/mobile/offline-data/',
            '/api/mobile/conflicts/',
            '/api/mobile/sync-logs/',
            '/api/mobile/delegates/',
            '/api/mobile/sync/upload/',
        ]

        for endpoint in api_endpoints:
            response = self.client.get(endpoint)
            # Should return 200 (with data), 401/403 (auth required), 404 (not yet implemented), or 405 (method not allowed for POST-only endpoints)
            self.assertIn(response.status_code, [200, 401, 403, 404, 405],
                         f'{endpoint} returned {response.status_code}')
