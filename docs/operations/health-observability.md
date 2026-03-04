# Health And Observability Runbook

This runbook defines how to use the GZEAMS health endpoints and metrics endpoint in production.

## Endpoints

- `GET /api/health/live/`
  - Purpose: process heartbeat only (no dependency checks).
  - Use for: container liveness probe.
  - Expected: `200` when process is running.

- `GET /api/health/ready/`
  - Purpose: dependency readiness (database + cache).
  - Use for: readiness probe and traffic gating.
  - Expected: `200` when dependencies are reachable, `503` otherwise.

- `GET /api/health/`
  - Purpose: backward-compatible alias for readiness.
  - Expected: same behavior as `/api/health/ready/`.

- `GET /api/health/metrics/`
  - Purpose: Prometheus metrics export.
  - Security: protected by IP allowlist and optional token.
  - Expected: `200` with `text/plain` body when authorized, `403` when denied.

## Security Controls For Metrics

Environment variables:

- `HEALTH_METRICS_ALLOWLIST`
  - Comma-separated IP/CIDR list.
  - Example: `10.0.0.0/8,192.168.10.15,127.0.0.1,::1`

- `HEALTH_METRICS_TRUST_X_FORWARDED_FOR`
  - `true` only when traffic always passes through trusted reverse proxies.
  - In direct-exposure setups keep `false`.

- `HEALTH_METRICS_TOKEN`
  - Shared secret for metrics endpoint.
  - Accepts either:
    - `Authorization: Bearer <token>`
    - `X-Metrics-Token: <token>`

Production settings enforce `HEALTH_METRICS_ALLOWLIST` and `HEALTH_METRICS_TOKEN`.

## Prometheus Scrape Example

Use bearer token mode:

```yaml
scrape_configs:
  - job_name: gzeams-backend
    scheme: http
    metrics_path: /api/health/metrics/
    static_configs:
      - targets:
          - gzeams-backend:8000
    authorization:
      type: Bearer
      credentials: ${GZEAMS_HEALTH_METRICS_TOKEN}
```

If you run Prometheus outside the allowlist range, add its source IP/CIDR to `HEALTH_METRICS_ALLOWLIST`.

## Kubernetes Probe Example

```yaml
livenessProbe:
  httpGet:
    path: /api/health/live/
    port: 8000
  initialDelaySeconds: 20
  periodSeconds: 15
  timeoutSeconds: 3

readinessProbe:
  httpGet:
    path: /api/health/ready/
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 3
```

## Local Verification

```bash
# Liveness
curl -i http://127.0.0.1:8000/api/health/live/

# Readiness
curl -i http://127.0.0.1:8000/api/health/ready/

# Metrics with bearer token
curl -i \
  -H "Authorization: Bearer ${HEALTH_METRICS_TOKEN}" \
  http://127.0.0.1:8000/api/health/metrics/
```

## Exposed Metrics

- `gzeams_health_probe_requests_total{probe,outcome}`
- `gzeams_health_dependency_check_duration_seconds{dependency}`
- `gzeams_health_dependency_check_failures_total{dependency}`

