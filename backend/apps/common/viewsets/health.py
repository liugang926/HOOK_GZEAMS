"""
Service health check endpoint.
"""
from __future__ import annotations

from datetime import datetime
from ipaddress import ip_address, ip_network
from secrets import compare_digest
from time import monotonic
from typing import Callable, Dict, Tuple
import os
import socket

from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.db.utils import DatabaseError
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.common.responses import BaseResponse

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
except ImportError:  # pragma: no cover - optional dependency in local/dev environments
    CONTENT_TYPE_LATEST = 'text/plain; version=0.0.4; charset=utf-8'

    class _NoopMetric:
        def labels(self, **_kwargs):
            return self

        def inc(self):
            return None

        def observe(self, _value):
            return None

    def Counter(*_args, **_kwargs):  # noqa: N802 - keep prometheus constructor naming
        return _NoopMetric()

    def Histogram(*_args, **_kwargs):  # noqa: N802 - keep prometheus constructor naming
        return _NoopMetric()

    def generate_latest():
        return (
            b'# HELP gzeams_health_probe_requests_total Total health probe requests by probe and outcome.\n'
            b'# TYPE gzeams_health_probe_requests_total counter\n'
            b'gzeams_health_probe_requests_total{probe="metrics",outcome="degraded"} 0\n'
            b'# HELP gzeams_health_dependency_check_duration_seconds Dependency check duration for health readiness checks.\n'
            b'# TYPE gzeams_health_dependency_check_duration_seconds histogram\n'
            b'gzeams_health_dependency_check_duration_seconds_bucket{dependency="database",le="+Inf"} 0\n'
            b'gzeams_health_dependency_check_duration_seconds_count{dependency="database"} 0\n'
            b'gzeams_health_dependency_check_duration_seconds_sum{dependency="database"} 0\n'
        )

_START_TIME = monotonic()
HEALTH_PROBE_REQUESTS_TOTAL = Counter(
    'gzeams_health_probe_requests_total',
    'Total health probe requests by probe and outcome.',
    ['probe', 'outcome'],
)
HEALTH_DEPENDENCY_CHECK_DURATION_SECONDS = Histogram(
    'gzeams_health_dependency_check_duration_seconds',
    'Dependency check duration for health readiness checks.',
    ['dependency'],
)
HEALTH_DEPENDENCY_CHECK_FAILURES_TOTAL = Counter(
    'gzeams_health_dependency_check_failures_total',
    'Total dependency check failures for health readiness checks.',
    ['dependency'],
)


def check_database() -> Tuple[bool, str]:
    """Verify database connectivity with a lightweight query."""
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute('SELECT 1')
        return True, 'ok'
    except DatabaseError as exc:
        return False, str(exc)


def check_cache() -> Tuple[bool, str]:
    """Verify cache write/read round-trip."""
    cache_key = f'healthcheck:{os.getpid()}'
    try:
        cache.set(cache_key, 'ok', timeout=5)
        if cache.get(cache_key) != 'ok':
            return False, 'cache round-trip mismatch'
        return True, 'ok'
    except Exception as exc:  # noqa: BLE001 - health checks should degrade gracefully
        return False, str(exc)


def build_runtime_context() -> Dict[str, object]:
    """Build shared runtime metadata for all health endpoints."""
    uptime_seconds = round(monotonic() - _START_TIME, 2)
    return {
        'service': 'gzeams-backend',
        'environment': os.getenv('DJANGO_SETTINGS_MODULE', ''),
        'timestamp': timezone.now().isoformat(),
        'hostname': socket.gethostname(),
        'pid': os.getpid(),
        'uptimeSeconds': uptime_seconds,
        'startedAt': datetime.fromtimestamp(
            timezone.now().timestamp() - uptime_seconds,
            tz=timezone.get_current_timezone(),
        ).isoformat(),
    }


def run_dependency_check(name: str, checker: Callable[[], Tuple[bool, str]]) -> Tuple[bool, str]:
    """Run a dependency check with metrics instrumentation."""
    started_at = monotonic()
    ok, detail = checker()
    HEALTH_DEPENDENCY_CHECK_DURATION_SECONDS.labels(dependency=name).observe(
        monotonic() - started_at
    )
    if not ok:
        HEALTH_DEPENDENCY_CHECK_FAILURES_TOTAL.labels(dependency=name).inc()
    return ok, detail


def get_metrics_client_ip(request) -> str:
    """Resolve metrics client IP, optionally trusting X-Forwarded-For."""
    trust_xff = getattr(settings, 'HEALTH_METRICS_TRUST_X_FORWARDED_FOR', False)
    if trust_xff:
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '').strip()


def is_metrics_client_allowed(client_ip: str) -> bool:
    """Check client IP against HEALTH_METRICS_ALLOWLIST entries."""
    if not client_ip:
        return False

    try:
        client = ip_address(client_ip)
    except ValueError:
        return False

    allowlist = getattr(settings, 'HEALTH_METRICS_ALLOWLIST', [])
    if isinstance(allowlist, str):
        allowlist = [entry.strip() for entry in allowlist.split(',') if entry.strip()]

    for entry in allowlist:
        try:
            if '/' in entry:
                if client in ip_network(entry, strict=False):
                    return True
            elif client == ip_address(entry):
                return True
        except ValueError:
            continue

    return False


def get_metrics_token_from_request(request) -> str:
    """Resolve metrics token from Authorization bearer or X-Metrics-Token header."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:].strip()
    return request.META.get('HTTP_X_METRICS_TOKEN', '').strip()


def is_metrics_token_allowed(request) -> bool:
    """
    Validate optional metrics token.

    When HEALTH_METRICS_TOKEN is unset, token validation is skipped.
    """
    expected_token = getattr(settings, 'HEALTH_METRICS_TOKEN', '')
    if not expected_token:
        return True
    supplied_token = get_metrics_token_from_request(request)
    return bool(supplied_token) and compare_digest(supplied_token, expected_token)


class LivenessAPIView(APIView):
    """
    Lightweight process-level heartbeat for liveness probes.

    This endpoint intentionally avoids dependency checks so orchestrators can
    distinguish between a dead process and a temporarily unavailable dependency.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        HEALTH_PROBE_REQUESTS_TOTAL.labels(probe='live', outcome='success').inc()
        data = {
            'status': 'live',
            'checks': {
                'process': {'status': 'ok', 'detail': 'running'},
            },
            **build_runtime_context(),
        }
        return BaseResponse.success(data=data, message='Service is alive')


class ReadinessAPIView(APIView):
    """
    Dependency-aware readiness endpoint for infrastructure probes.

    - Returns 200 when dependencies are reachable.
    - Returns 503 with dependency details when any check fails.
    """
    probe_name = 'ready'

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        db_ok, db_detail = run_dependency_check('database', check_database)
        cache_ok, cache_detail = run_dependency_check('cache', check_cache)

        checks: Dict[str, Dict[str, str]] = {
            'database': {'status': 'ok' if db_ok else 'error', 'detail': db_detail},
            'cache': {'status': 'ok' if cache_ok else 'error', 'detail': cache_detail},
        }
        overall_ok = db_ok and cache_ok

        data = {
            'status': 'ready' if overall_ok else 'not_ready',
            'checks': checks,
            **build_runtime_context(),
        }

        if overall_ok:
            HEALTH_PROBE_REQUESTS_TOTAL.labels(probe=self.probe_name, outcome='success').inc()
            return BaseResponse.success(data=data, message='Service is ready')

        HEALTH_PROBE_REQUESTS_TOTAL.labels(probe=self.probe_name, outcome='failure').inc()
        return BaseResponse.error(
            code='SERVICE_UNHEALTHY',
            message='Dependency checks failed',
            details=data,
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class HealthCheckAPIView(ReadinessAPIView):
    """Backward-compatible alias for legacy /api/health/ endpoint."""

    probe_name = 'health'


class HealthMetricsAPIView(APIView):
    """Prometheus metrics endpoint for health probes."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        client_ip = get_metrics_client_ip(request)
        if not is_metrics_client_allowed(client_ip):
            HEALTH_PROBE_REQUESTS_TOTAL.labels(probe='metrics', outcome='forbidden_ip').inc()
            return BaseResponse.error(
                code='METRICS_FORBIDDEN',
                message='Metrics endpoint access denied',
                details={'clientIp': client_ip},
                http_status=status.HTTP_403_FORBIDDEN,
            )

        if not is_metrics_token_allowed(request):
            HEALTH_PROBE_REQUESTS_TOTAL.labels(probe='metrics', outcome='forbidden_token').inc()
            return BaseResponse.error(
                code='METRICS_FORBIDDEN',
                message='Metrics endpoint access denied',
                details={'reason': 'token_invalid'},
                http_status=status.HTTP_403_FORBIDDEN,
            )

        HEALTH_PROBE_REQUESTS_TOTAL.labels(probe='metrics', outcome='success').inc()
        return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
