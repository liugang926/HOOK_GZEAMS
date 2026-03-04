"""
Tests for service health endpoint.
"""
from unittest.mock import patch

from django.test import override_settings
from rest_framework.test import APIRequestFactory

from apps.common.viewsets.health import (
    HealthCheckAPIView,
    HealthMetricsAPIView,
    LivenessAPIView,
    ReadinessAPIView,
)


@patch('apps.common.viewsets.health.check_database', return_value=(True, 'ok'))
@patch('apps.common.viewsets.health.check_cache', return_value=(True, 'ok'))
def test_health_check_returns_200_when_dependencies_are_ready(_mock_cache_check, _mock_db_check):
    request = APIRequestFactory().get('/api/health/')
    response = HealthCheckAPIView.as_view()(request)

    assert response.status_code == 200
    assert response.data['success'] is True
    assert response.data['data']['status'] == 'ready'
    assert response.data['data']['checks']['database']['status'] == 'ok'
    assert response.data['data']['checks']['cache']['status'] == 'ok'


@patch('apps.common.viewsets.health.check_database', return_value=(False, 'db down'))
@patch('apps.common.viewsets.health.check_cache', return_value=(True, 'ok'))
def test_health_check_returns_503_when_dependency_check_fails(
    _mock_cache_check,
    _mock_db_check,
):
    request = APIRequestFactory().get('/api/health/')
    response = HealthCheckAPIView.as_view()(request)

    assert response.status_code == 503
    assert response.data['success'] is False
    assert response.data['error']['code'] == 'SERVICE_UNHEALTHY'
    assert response.data['error']['details']['status'] == 'not_ready'
    assert response.data['error']['details']['checks']['database']['status'] == 'error'


@patch('apps.common.viewsets.health.check_database')
@patch('apps.common.viewsets.health.check_cache')
def test_liveness_returns_200_without_dependency_checks(_mock_cache_check, _mock_db_check):
    request = APIRequestFactory().get('/api/health/live/')
    response = LivenessAPIView.as_view()(request)

    assert response.status_code == 200
    assert response.data['success'] is True
    assert response.data['data']['status'] == 'live'
    _mock_db_check.assert_not_called()
    _mock_cache_check.assert_not_called()


@patch('apps.common.viewsets.health.check_database', return_value=(True, 'ok'))
@patch('apps.common.viewsets.health.check_cache', return_value=(True, 'ok'))
def test_readiness_returns_200_when_dependencies_are_ready(_mock_cache_check, _mock_db_check):
    request = APIRequestFactory().get('/api/health/ready/')
    response = ReadinessAPIView.as_view()(request)

    assert response.status_code == 200
    assert response.data['success'] is True
    assert response.data['data']['status'] == 'ready'


@override_settings(
    HEALTH_METRICS_ALLOWLIST=['127.0.0.1', '::1'],
    HEALTH_METRICS_TOKEN='',
)
def test_health_metrics_endpoint_exposes_prometheus_metrics():
    request = APIRequestFactory().get('/api/health/metrics/')
    response = HealthMetricsAPIView.as_view()(request)

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/plain')
    assert b'gzeams_health_probe_requests_total' in response.content
    assert b'gzeams_health_dependency_check_duration_seconds' in response.content


@override_settings(HEALTH_METRICS_ALLOWLIST=['10.0.0.0/8'])
def test_health_metrics_endpoint_rejects_disallowed_ip():
    request = APIRequestFactory().get('/api/health/metrics/', REMOTE_ADDR='192.168.1.10')
    response = HealthMetricsAPIView.as_view()(request)

    assert response.status_code == 403
    assert response.data['success'] is False
    assert response.data['error']['code'] == 'METRICS_FORBIDDEN'


@override_settings(
    HEALTH_METRICS_ALLOWLIST=['10.0.0.0/8'],
    HEALTH_METRICS_TRUST_X_FORWARDED_FOR=True,
    HEALTH_METRICS_TOKEN='',
)
def test_health_metrics_endpoint_allows_forwarded_ip_when_trusted():
    request = APIRequestFactory().get(
        '/api/health/metrics/',
        REMOTE_ADDR='192.168.1.10',
        HTTP_X_FORWARDED_FOR='10.1.2.3, 172.16.0.5',
    )
    response = HealthMetricsAPIView.as_view()(request)

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/plain')


@override_settings(
    HEALTH_METRICS_ALLOWLIST=['127.0.0.1'],
    HEALTH_METRICS_TOKEN='expected-token',
)
def test_health_metrics_endpoint_rejects_invalid_token():
    request = APIRequestFactory().get(
        '/api/health/metrics/',
        REMOTE_ADDR='127.0.0.1',
        HTTP_AUTHORIZATION='Bearer wrong-token',
    )
    response = HealthMetricsAPIView.as_view()(request)

    assert response.status_code == 403
    assert response.data['success'] is False
    assert response.data['error']['code'] == 'METRICS_FORBIDDEN'
    assert response.data['error']['details']['reason'] == 'token_invalid'


@override_settings(
    HEALTH_METRICS_ALLOWLIST=['127.0.0.1'],
    HEALTH_METRICS_TOKEN='expected-token',
)
def test_health_metrics_endpoint_allows_valid_bearer_token():
    request = APIRequestFactory().get(
        '/api/health/metrics/',
        REMOTE_ADDR='127.0.0.1',
        HTTP_AUTHORIZATION='Bearer expected-token',
    )
    response = HealthMetricsAPIView.as_view()(request)

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/plain')


@override_settings(
    HEALTH_METRICS_ALLOWLIST=['127.0.0.1'],
    HEALTH_METRICS_TOKEN='expected-token',
)
def test_health_metrics_endpoint_allows_valid_x_metrics_token():
    request = APIRequestFactory().get(
        '/api/health/metrics/',
        REMOTE_ADDR='127.0.0.1',
        HTTP_X_METRICS_TOKEN='expected-token',
    )
    response = HealthMetricsAPIView.as_view()(request)

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/plain')
