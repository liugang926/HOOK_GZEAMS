"""
API tests for SLA alert configuration endpoints.
"""

import json
import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.common.middleware import clear_current_organization

User = get_user_model()


class TestSLAAlertConfigAPI(TestCase):
    """Test SLA alert configuration read and update APIs."""

    def setUp(self):
        """Create an authenticated client and isolated alert rules file."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='sla-alert-admin',
            email='sla-alert-admin@example.com',
            password='test-pass-123',
            is_staff=True,
        )
        self.client.force_authenticate(user=self.user)

        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_config_path = Path(self.temp_dir.name) / 'alert_rules.json'
        source_config_path = Path(__file__).resolve().parents[1] / 'configs' / 'alert_rules.json'
        shutil.copyfile(source_config_path, self.temp_config_path)

        self.settings_override = override_settings(
            WORKFLOW_ALERT_RULES_PATH=str(self.temp_config_path)
        )
        self.settings_override.enable()

    def tearDown(self):
        """Reset organization context and temporary configuration state."""
        self.settings_override.disable()
        self.temp_dir.cleanup()
        clear_current_organization()
        super().tearDown()

    def test_get_alert_configuration_returns_current_configuration(self):
        """GET returns the current alert configuration payload."""
        response = self.client.get('/api/sla/alerts/config')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('alert_rules', response.data['data'])
        self.assertIn('notification_channels', response.data['data'])

    def test_post_alert_configuration_updates_thresholds_and_persists_file(self):
        """POST updates alert thresholds and writes the result to disk."""
        payload = {
            'alert_rules': {
                'sla_compliance': {
                    'metrics': {
                        'sla_compliance_rate': {
                            'warning_threshold': 85,
                            'critical_threshold': 75,
                        }
                    }
                },
                'workflow_performance': {
                    'metrics': {
                        'api_response_time': {
                            'warning_threshold': 350,
                            'critical_threshold': 550,
                        }
                    }
                },
            }
        }

        response = self.client.post('/api/sla/alerts/config', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(
            response.data['data']['alert_rules']['sla_compliance']['metrics'][
                'sla_compliance_rate'
            ]['warning_threshold'],
            85,
        )
        self.assertEqual(
            response.data['data']['alert_rules']['workflow_performance']['metrics'][
                'api_response_time'
            ]['critical_threshold'],
            550,
        )

        with self.temp_config_path.open('r', encoding='utf-8') as config_file:
            saved_configuration = json.load(config_file)

        self.assertEqual(
            saved_configuration['alert_rules']['sla_compliance']['metrics'][
                'sla_compliance_rate'
            ]['critical_threshold'],
            75,
        )
        self.assertEqual(
            saved_configuration['alert_rules']['workflow_performance']['metrics'][
                'api_response_time'
            ]['warning_threshold'],
            350,
        )

    def test_post_alert_configuration_rejects_thresholds_below_minimum(self):
        """POST rejects threshold updates that violate the minimum allowed value."""
        payload = {
            'alert_rules': {
                'workflow_performance': {
                    'metrics': {
                        'api_response_time': {
                            'warning_threshold': 0,
                        }
                    }
                }
            }
        }

        response = self.client.post('/api/sla/alerts/config', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('warning_threshold', str(response.data['error']['details']))
