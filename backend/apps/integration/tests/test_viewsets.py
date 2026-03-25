"""
Tests for integration viewsets.
"""
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.common.middleware import clear_current_organization, set_current_organization
from apps.integration.models import IntegrationConfig
from apps.integration.viewsets.config_viewsets import IntegrationConfigViewSet
from apps.organizations.models import Organization


def _build_stats_view_response(user, query_params=None):
    factory = APIRequestFactory()
    view = IntegrationConfigViewSet.as_view({'get': 'stats'})
    request = factory.get('/api/integration/configs/stats/', data=query_params or {})
    force_authenticate(request, user=user)
    return view(request)


@pytest.mark.django_db
class TestIntegrationConfigViewSetStats:
    def test_stats_returns_aggregated_health_counts(self, organization, user):
        IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='M18',
            health_status='healthy',
            is_enabled=True,
            created_by=user,
        )
        IntegrationConfig.objects.create(
            organization=organization,
            system_type='sap',
            system_name='SAP',
            health_status='degraded',
            is_enabled=True,
            created_by=user,
        )
        IntegrationConfig.objects.create(
            organization=organization,
            system_type='kingdee',
            system_name='Kingdee',
            health_status='unhealthy',
            is_enabled=False,
            created_by=user,
        )

        try:
            set_current_organization(str(organization.id))
            response = _build_stats_view_response(user)
        finally:
            clear_current_organization()

        assert response.status_code == 200
        assert response.data['success'] is True
        assert response.data['data'] == {
            'total': 3,
            'healthy': 1,
            'degraded': 1,
            'unhealthy': 1,
        }

    def test_stats_applies_filters_and_respects_current_organization(self, organization, user):
        other_org = Organization.objects.create(
            name='Other Org',
            code='OTHER_ORG',
            is_active=True,
        )

        IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='M18',
            health_status='healthy',
            is_enabled=True,
            created_by=user,
        )
        IntegrationConfig.objects.create(
            organization=organization,
            system_type='sap',
            system_name='SAP',
            health_status='unhealthy',
            is_enabled=True,
            created_by=user,
        )
        IntegrationConfig.objects.create(
            organization=other_org,
            system_type='odoo',
            system_name='Odoo Other Org',
            health_status='unhealthy',
            is_enabled=True,
            created_by=user,
        )

        try:
            set_current_organization(str(organization.id))
            response = _build_stats_view_response(
                user,
                {'health_status': 'unhealthy', 'is_enabled': 'true'},
            )
        finally:
            clear_current_organization()

        assert response.status_code == 200
        assert response.data['success'] is True
        assert response.data['data'] == {
            'total': 1,
            'healthy': 0,
            'degraded': 0,
            'unhealthy': 1,
        }
