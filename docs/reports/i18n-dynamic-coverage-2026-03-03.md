# i18n Dynamic Coverage Report (2026-03-03)

## Scope

- Target: Dynamic runtime UI surface
  - `frontend/src/views/dynamic/**`
  - `frontend/src/components/engine/**`
  - `frontend/src/platform/layout/**`
  - `frontend/src/components/common/BaseListPage.vue`
  - `frontend/src/components/common/BaseFormPage.vue`
  - `frontend/src/components/common/BaseDetailPage.vue`
  - `frontend/src/components/common/RelatedObjectTable.vue`
- PRD reference: `docs/prd/prd-layout-object-i18n-optimization-2026-03-02.md` (AC-1)

## Metric Method

- Script: `frontend/scripts/i18n-coverage-metrics.mjs`
- Formula:
  - `coverage = i18nRefs / (i18nRefs + hardcodedTotal) * 100`
- Hardcoded detectors:
  - quoted CJK literals
  - `ElMessage/ElMessageBox` raw literal messages
  - static UI attributes (`label/title/placeholder/...`) in Vue template
  - Vue template text literals (plain visible text nodes)
  - script-level placeholder literals (`placeholder/startPlaceholder/endPlaceholder: '...'`)
- Threshold: `95%`

## Latest Result

- Command: `npm run i18n:coverage:all`
- Result:
  - `filesScanned = 77`
  - `i18nRefs = 166`
  - `hardcodedTotal = 0`
  - `coverage = 100%`
  - `meetsThreshold = true`

## Cleanup Batch (Option 2)

- Removed remaining static runtime copy in:
  - `frontend/src/components/engine/fields/AttachmentUpload.vue`
  - `frontend/src/components/engine/FieldRenderer.vue`
  - `frontend/src/components/common/FieldRenderer.vue`
- Added bilingual keys in `common.json` (`en-US` / `zh-CN`) for upload/clear/progress and upload error hints.
- Tightened guard:
  - `frontend/scripts/i18n-hardcode-check.mjs` now detects:
    - Vue template plain text literals
    - script-level placeholder literals

## CI Gate

- Script: `npm run i18n:coverage:all:strict`
- Workflow step: `.github/workflows/ci.yml` in `frontend-lint`
- Behavior: fail build when dynamic i18n coverage `< 95%`
- Complementary zero-hardcode gate:
  - Script: `npm run i18n:check:dynamic:all:strict`
  - Behavior: fail build on any dynamic runtime hardcoded literal detected by `i18n-hardcode-check.mjs`

## Trend Snapshot Automation

- Trend script: `frontend/scripts/i18n-coverage-trend.mjs`
- npm:
  - `npm run i18n:coverage:trend`
  - `npm run i18n:coverage:trend:strict`
- History dataset: `docs/reports/history/i18n-dynamic-coverage-history.json`
- Latest trend snapshot: `docs/reports/i18n-dynamic-coverage-trend-latest.md`
- CI step: `.github/workflows/ci.yml` (`Generate i18n dynamic coverage trend snapshot`)
