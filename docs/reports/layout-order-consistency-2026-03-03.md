# Layout Order Consistency Report (2026-03-03)

## Scope

- Target: designer preview and runtime field ordering consistency
- Contract fixture: `frontend/src/platform/layout/layoutOrderConsistency.contract.test.ts`
- PRD reference: `docs/prd/prd-layout-object-i18n-optimization-2026-03-02.md` (AC-2)

## Metric Method

- Script: `frontend/scripts/layout-order-consistency-metrics.mjs`
- Command:
  - `npm run layout:order:consistency`
  - strict gate: `npm run layout:order:consistency:strict`
- Formula:
  - `consistency = passedCases / totalCases * 100`

## Scenario Set

1. Section field order consistency (`form/edit`)
2. Tab and collapse container order consistency
3. List-column order consistency (`list`)
4. Fallback metadata sort-order consistency (no layout sections)
5. Mixed code naming style consistency (`code/fieldCode/fieldName`)

## Latest Result

- Date: `2026-03-03`
- Result:
  - `totalCases = 5`
  - `passedCases = 5`
  - `failedCases = 0`
  - `consistency = 100%`
  - `threshold = 100%`
  - `meetsThreshold = true`

## CI Gate

- Workflow: `.github/workflows/ci.yml`
- Job: `frontend-unit`
- Step: `Run layout order consistency gate`
- Behavior: fail build when consistency `< 100%`
