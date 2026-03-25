# PRD Acceptance Matrix (Layout/Object Runtime i18n Optimization)
# PRD 验收矩阵（布局与对象运行时国际化优化）

Last updated: 2026-03-03

| ID | Acceptance Criteria | Status | Evidence (Code/Test) | Notes |
| --- | --- | --- | --- | --- |
| AC-1 | Dynamic page i18n coverage >= 95% | Done | Coverage metric script `frontend/scripts/i18n-coverage-metrics.mjs`; npm gate `npm run i18n:coverage:all:strict`; CI step in `.github/workflows/ci.yml` | Latest local metric (`2026-03-03`): dynamic scope coverage `100%` (`i18nRefs=166`, `hardcoded=0`, threshold `95%`). |
| AC-2 | Designer preview and runtime field order consistency = 100% | Done | Contract test `frontend/src/platform/layout/layoutOrderConsistency.contract.test.ts`; metric gate script `frontend/scripts/layout-order-consistency-metrics.mjs`; npm gate `npm run layout:order:consistency:strict`; CI step in `.github/workflows/ci.yml` (`frontend-unit`) | Latest local metric (`2026-03-03`): `totalCases=5`, `passedCases=5`, consistency `100%` (threshold `100%`). |
| AC-3 | New code path field key uses `field_code` = 100% | Done | Runtime path now enforces strict identifiers (`field_code` only, rendered as `fieldCode`): `backend/apps/system/viewsets/object_router.py`; tests `backend/apps/system/tests/test_object_router_runtime_and_batch_get.py::test_object_router_runtime_returns_layout_and_fields`, `backend/apps/system/tests/test_object_router_user_locale_runtime.py::test_fields_strict_mode_returns_field_code_only` | Legacy `/fields` endpoint keeps `code` compatibility by default (`test_fields_default_mode_keeps_legacy_code_for_compatibility`), while new runtime path is strict by default. |
| AC-4 | `preferred_language` takes effect after save and re-login | Done | APIs: `/api/system/objects/User/me/`, `/api/system/objects/User/me/profile/`; test `test_user_me_profile_reads_and_updates_preferred_language` | Runtime now resolves locale with profile fallback when header missing. |
| AC-5 | Related tables fully metadata-driven (no object hardcoded templates) | Done | `frontend/src/components/common/RelatedObjectTable.vue` switched to metadata-driven list-field columns (`/api/system/objects/{code}/fields/?context=list`); test `frontend/src/__tests__/unit/components/common/RelatedObjectTable.spec.ts`; guard script `frontend/scripts/related-table-metadata-audit.mjs` integrated into CI | Object-specific related-table column templates removed; CI now prevents regression to object hardcoded mappings. |
| AC-6 | Sub-table first screen render < 1.5s for <=200 rows | Done | Unit benchmark `frontend/src/__tests__/unit/components/engine/SubTableField.performance.spec.ts`; browser telemetry `frontend/e2e/objects/subtable-first-render-performance.spec.ts` with `<1500ms` assertion; CI blocking gate `npm run test:e2e:subtable-perf` in `.github/workflows/ci.yml` | Field renderer now uses paged sub-table mount for large row sets; local browser run is within threshold and CI is now hard-gated to prevent regressions. |
| AC-7 | P1 i18n defects = 0 | Done | Defect ledger `docs/reports/i18n-p1-defect-ledger.json`; gate script `frontend/scripts/i18n-p1-defect-gate.mjs`; npm gate `npm run i18n:defects:p1:strict`; CI step in `.github/workflows/ci.yml` (`frontend-lint`) | Latest local gate result (`2026-03-03`): `activeP1Defects=0`, `allowedActive=0`, `meetsTarget=true`. |
| AC-8 | CI i18n scan pass rate = 100%, no hardcoded language leakage | Done | `npm run i18n:check` + `npm run i18n:check:dynamic:all:strict` + `npm run i18n:coverage:all:strict` + `npm run i18n:parity:all:strict` in CI frontend-lint job | Hardcode guard now covers template text literals and script placeholder literals; dynamic runtime full scope is hard-gated for both zero-hardcode and >=95% coverage. |

## Key Delivered Items

- Backend locale priority enforcement:
  - query (`locale/lang`) > `Accept-Language` > `preferred_language` > default/context
  - file: `backend/apps/system/viewsets/object_router.py`
- Backend locale/i18n fallback tests:
  - file: `backend/apps/system/tests/test_object_router_user_locale_runtime.py`
- Backend reference payload sanitization and validator hardening:
  - files: `backend/apps/system/services/dynamic_data_service.py`, `backend/apps/common/validators/dynamic_field.py`
  - tests: `backend/apps/system/tests/test_dynamic_data_service_reference_sanitize.py`, `backend/apps/common/tests/test_dynamic_field_validator.py`
- Frontend locale flow hardening:
  - local cache/profile/default flow in `frontend/src/stores/locale.ts` and `frontend/src/stores/user.ts`
- Frontend no-hardcode governance:
  - hardcode scan: `frontend/scripts/i18n-hardcode-check.mjs`
  - dynamic coverage metric: `frontend/scripts/i18n-coverage-metrics.mjs`
  - dynamic coverage trend: `frontend/scripts/i18n-coverage-trend.mjs` + `docs/reports/history/i18n-dynamic-coverage-history.json`
  - locale parity gate: `frontend/scripts/i18n-locale-parity-check.mjs`
- Designer/runtime order consistency gate:
  - contract: `frontend/src/platform/layout/layoutOrderConsistency.contract.test.ts`
  - metric: `frontend/scripts/layout-order-consistency-metrics.mjs`
  - CI gate: `.github/workflows/ci.yml` (`npm run layout:order:consistency:strict`)
- Related-table metadata migration:
  - file: `frontend/src/components/common/RelatedObjectTable.vue`
  - test: `frontend/src/__tests__/unit/components/common/RelatedObjectTable.spec.ts`
  - guard: `frontend/scripts/related-table-metadata-audit.mjs` + `.github/workflows/ci.yml`
- Sub-table performance baseline automation:
  - test: `frontend/src/__tests__/unit/components/engine/SubTableField.performance.spec.ts`
  - browser telemetry: `frontend/e2e/objects/subtable-first-render-performance.spec.ts`
  - browser telemetry trend: `frontend/scripts/subtable-telemetry-trend.mjs` + `docs/reports/history/subtable-first-render-history.json`
  - CI blocking gate: `.github/workflows/ci.yml` (`npm run subtable:telemetry:trend:strict`)

## Open Gaps (Next)

1. Add dashboard integration for trend artifacts (history chart rendering in a single PRD observability page).
2. Split browser telemetry trend by project (`chromium/firefox/webkit`) once cross-browser perf baseline is stabilized.
