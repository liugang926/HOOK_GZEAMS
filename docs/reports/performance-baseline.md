# Sprint 3 Performance Baseline

## Document Information

| Item | Value |
|------|-------|
| Report Version | v1.0 |
| Created Date | 2026-03-24 |
| Sprint | Sprint 3 Task 2 |
| Author/Agent | Codex |
| Scope | Workflow API benchmarks, database query targets, cache goals, frontend bundle budgets |

## API Endpoint Response Time Targets

| Endpoint | Scenario | Target |
|----------|----------|--------|
| `/api/workflows/definitions/` | Paginated workflow list, `page_size=20` | <= 250 ms |
| `/api/workflows/tasks/{id}/` | Single task detail view | <= 200 ms |
| `/api/workflows/statistics/` | Workflow overview statistics | <= 300 ms uncached, <= 150 ms cached |

## Database Query Benchmarks

| Area | Benchmark Target | Notes |
|------|------------------|-------|
| Workflow list | <= 6 queries per request | Includes pagination count and page fetch |
| Task detail | <= 8 queries per request | Includes task, instance, definition, assignee, and approval summary |
| Statistics overview | <= 10 queries per request | Current baseline for aggregate counters without cache |
| Cached statistics overview | <= 2 queries per request | Expected after Redis cache hit |

## Cache Hit Rate Goals

| Cache Area | Goal |
|------------|------|
| Workflow statistics cache | >= 95% hit rate |
| General workflow cache traffic | >= 90% hit rate |
| Cache availability | >= 99% during business hours |

## Frontend Bundle Size Limits

| Asset Type | Limit | Reference |
|------------|-------|-----------|
| Largest JavaScript chunk | <= 750 KiB | Matches `build:report:strict` default JS budget |
| Largest CSS chunk | <= 350 KiB | Matches `build:report:strict` default CSS budget |
| Vite warning threshold | 950 KiB | Matches `chunkSizeWarningLimit` in `frontend/vite.config.ts` |
| First screen interactive target | <= 3000 ms | Matches existing `perf:baseline` target |

## Automation Mapping

- Backend benchmark tests: `backend/apps/workflows/tests/test_performance_benchmark.py`
- Cache statistics source: `backend/apps/common/services/redis_service.py`
- Frontend bundle reporting: `frontend/scripts/build-chunk-report.mjs`
