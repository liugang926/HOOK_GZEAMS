# PRD Acceptance Matrix (Layout/Object Runtime i18n Optimization)
# PRD 验收矩阵（布局与对象运行时国际化优化）

Last updated: 2026-03-03

| ID | Acceptance Criteria | Status | Evidence (Code/Test) | Notes |
| --- | --- | --- | --- | --- |
| AC-1 | Dynamic page i18n coverage >= 95% | In Progress | Frontend i18n hardcode gate: `frontend/scripts/i18n-hardcode-check.mjs`; CI step in `.github/workflows/ci.yml` | Coverage metric not yet auto-calculated; governance gate is active. |
| AC-2 | Designer preview and runtime field order consistency = 100% | In Progress | Runtime/detail model alignment tests in frontend layout contract suites; backend runtime payload unification in `backend/apps/system/viewsets/object_router.py` | Existing regression suites are running; percentage metric pending dashboarding. |
| AC-3 | New code path field key uses `field_code` = 100% | In Progress | `field_code_strict_mode` flag + compatibility layer in `ObjectRouter`; tests in `backend/apps/system/tests/test_object_router_user_locale_runtime.py` | Strict mode behavior covered; legacy `code` key still emitted when strict mode off. |
| AC-4 | `preferred_language` takes effect after save and re-login | Done | APIs: `/api/system/objects/User/me/`, `/api/system/objects/User/me/profile/`; test `test_user_me_profile_reads_and_updates_preferred_language` | Runtime now resolves locale with profile fallback when header missing. |
| AC-5 | Related tables fully metadata-driven (no object hardcoded templates) | Done | `frontend/src/components/common/RelatedObjectTable.vue` switched to metadata-driven list-field columns (`/api/system/objects/{code}/fields/?context=list`); test `frontend/src/__tests__/unit/components/common/RelatedObjectTable.spec.ts`; guard script `frontend/scripts/related-table-metadata-audit.mjs` integrated into CI | Object-specific related-table column templates removed; CI now prevents regression to object hardcoded mappings. |
| AC-6 | Sub-table first screen render < 1.5s for <=200 rows | In Progress | Benchmark test `frontend/src/__tests__/unit/components/engine/SubTableField.performance.spec.ts` asserts `< 1500ms` for 200 rows (current run ~1.03s) | Unit-level benchmark is automated; full browser E2E perf telemetry is still pending. |
| AC-7 | P1 i18n defects = 0 | In Progress | Added locale fallback tests and i18n scanning gates | Requires release-cycle defect tracking data. |
| AC-8 | CI i18n scan pass rate = 100%, no hardcoded language leakage | In Progress | `npm run i18n:check` + `npm run i18n:parity:strict` added to CI frontend-lint job | Parity gate is incremental (new issues only) to avoid historical debt blocking. |

## Key Delivered Items

- Backend locale priority enforcement:
  - query (`locale/lang`) > `Accept-Language` > `preferred_language` > default/context
  - file: `backend/apps/system/viewsets/object_router.py`
- Backend locale/i18n fallback tests:
  - file: `backend/apps/system/tests/test_object_router_user_locale_runtime.py`
- Frontend locale flow hardening:
  - local cache/profile/default flow in `frontend/src/stores/locale.ts` and `frontend/src/stores/user.ts`
- Frontend no-hardcode governance:
  - hardcode scan: `frontend/scripts/i18n-hardcode-check.mjs`
  - locale parity gate: `frontend/scripts/i18n-locale-parity-check.mjs`
- Related-table metadata migration:
  - file: `frontend/src/components/common/RelatedObjectTable.vue`
  - test: `frontend/src/__tests__/unit/components/common/RelatedObjectTable.spec.ts`
  - guard: `frontend/scripts/related-table-metadata-audit.mjs` + `.github/workflows/ci.yml`
- Sub-table performance baseline automation:
  - test: `frontend/src/__tests__/unit/components/engine/SubTableField.performance.spec.ts`

## Open Gaps (Next)

1. Add automated i18n coverage metric generation (not just gate).
2. Add browser E2E performance telemetry for sub-table first paint (<=200 rows, <1.5s).
