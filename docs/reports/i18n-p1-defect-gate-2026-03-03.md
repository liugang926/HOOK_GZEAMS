# i18n P1 Defect Gate Report (2026-03-03)

## Scope

- Target: release-window active i18n P1 defects must be zero
- PRD reference: `docs/prd/prd-layout-object-i18n-optimization-2026-03-02.md` (AC-7)

## Data Source

- Ledger: `docs/reports/i18n-p1-defect-ledger.json`
- Policy:
  - `target = P1 active defects = 0`
  - `allowedActive = 0`
  - `releaseWindow = 2026-03-01 .. 2026-03-31`

## Gate Method

- Script: `frontend/scripts/i18n-p1-defect-gate.mjs`
- Commands:
  - `npm run i18n:defects:p1`
  - strict gate: `npm run i18n:defects:p1:strict`
- Pass rule:
  - `activeP1Defects <= allowedActive`

## Latest Result

- Date: `2026-03-03`
- Result:
  - `activeP1Defects = 0`
  - `allowedActive = 0`
  - `meetsTarget = true`

## CI Gate

- Workflow: `.github/workflows/ci.yml`
- Job: `frontend-lint`
- Step: `Run i18n P1 defect gate`
- Behavior: fail build when active P1 defects exceed policy threshold
