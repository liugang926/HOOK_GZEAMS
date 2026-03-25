# SubTable First Render Telemetry (2026-03-03)

## Scope

- Target: `SubTableField` first-screen render for `<=200` rows
- PRD reference: `docs/prd/prd-layout-object-i18n-optimization-2026-03-02.md` (AC-6)

## Automated Coverage

- Unit benchmark (gating):
  - Test: `frontend/src/__tests__/unit/components/engine/SubTableField.performance.spec.ts`
  - Assertion: `< 1500ms` for 200 rows
  - Latest local run: passed (`~641ms`)

- Browser telemetry (blocking gate):
  - Test: `frontend/e2e/objects/subtable-first-render-performance.spec.ts`
  - Script: `npm run test:e2e:subtable-perf`
  - CI mode: blocking gate (`npm run test:e2e:subtable-perf`)
  - Latest local run: passed with threshold assertion enabled (`elapsedMs < 1500`)
  - Historical baseline (before pagination optimization): `elapsedMs = 3832` (above target `1500`)

## Optimization Applied

- `SubTableField` now applies paged rendering for large datasets (default page size `20`).
- New regression test: `frontend/src/__tests__/unit/components/engine/SubTableField.pagination.spec.ts`
- Effect: avoids mounting 200-row full table in first screen while preserving full model data.

## Current Status

- AC-6 is **Done**.
- Unit-level render budget is within target.
- Browser-level local run is within target after pagination optimization; CI now blocks regressions with the same threshold assertion.

## Trend Snapshot Automation

- Trend script: `frontend/scripts/subtable-telemetry-trend.mjs`
- npm:
  - `npm run subtable:telemetry:trend`
  - `npm run subtable:telemetry:trend:strict`
- History dataset: `docs/reports/history/subtable-first-render-history.json`
- Latest trend snapshot: `docs/reports/subtable-first-render-trend-latest.md`
- CI gate command: `npm run subtable:telemetry:trend:strict`

## Next Actions

1. Split telemetry trend snapshots by browser project (`chromium/firefox/webkit`) once baseline stability is confirmed.
2. Tune pagination page size only if production telemetry indicates regression pressure on specific browsers.
