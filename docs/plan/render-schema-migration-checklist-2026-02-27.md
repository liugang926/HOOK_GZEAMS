# RenderSchema Migration Checklist (Wave 1-2)

## Goal
Unify list/detail/edit rendering onto one metadata contract (`RenderSchema`) so mode differences are behavioral only.

## Completed in Wave 1
- Added shared schema builder:
  - `frontend/src/platform/layout/renderSchema.ts`
- Added shared ordering policy:
  - `frontend/src/platform/layout/runtimeFieldPolicy.ts`
- Added unit tests:
  - `frontend/src/platform/layout/renderSchema.test.ts`
  - `frontend/src/platform/layout/runtimeFieldPolicy.test.ts`
- Integrated first runtime consumer:
  - `frontend/src/components/common/DynamicDetailPage.vue`
- Stabilized form initialization policy:
  - create-only default value injection
  - stable field ordering in metadata fallback

## Completed in Wave 2 (current)
- Added RenderSchema projection adapter for list-layout compatibility:
  - `frontend/src/platform/layout/renderSchemaProjector.ts`
  - `projectListLayoutConfigForRenderSchema(...)`
- Migrated `DynamicListPage` to prefer RenderSchema-based projections for:
  - table columns
  - search fields
  - metadata field ordering
- Added safe RenderSchema fallback in `DynamicForm`:
  - when runtime layout resolves with no renderable fields, fallback to projected runtime layout from RenderSchema

## Completed in Wave 3 (in progress)
- Migrated `DynamicFormRenderer` to support `schema` as primary runtime input.
- Switched runtime `useDynamicForm` + `DynamicForm` render path to RenderSchema projection (mode-driven shared contract).
- Preserved tab/collapse grouping in RenderSchema -> RuntimeLayout projection.
- Refactored `runtimeListLayoutAdapter` to reuse RenderSchema projector, removing duplicated section traversal logic.
- Simplified `layoutAdapter` to a compatibility layer over RenderSchema projector.
- Extracted shared detail projection utility:
  - `frontend/src/platform/layout/detailSchemaProjector.ts`
  - `DynamicDetailPage` now consumes shared projector instead of local section traversal.
- Added runtime render contract tests:
  - `frontend/src/platform/layout/runtime-render.contract.test.ts`
  - covers `runtime payload -> contract check -> RenderSchema -> projector` pipeline.
- Added 25-core-type mode matrix regression checks:
  - `frontend/src/platform/layout/fieldCapabilityMatrix.test.ts`
- Wired runtime contract suite into CI frontend-unit job:
  - `frontend/package.json` script `test:contract:runtime`
  - `.github/workflows/ci.yml` step `Run runtime contract regression suite`

## Remaining (next)
- Remove duplicated container traversal logic in:
  - `DynamicDetailPage`
  - `layoutAdapter`
  - list column adapters
- Add `RenderSchema` contract tests against backend runtime payloads.
- Add performance snapshot benchmarks:
  - first render
  - schema transform time
  - large object (200+ fields)
- Final cleanup:
  - deprecate direct `layoutConfig` consumers
  - keep a single adapter layer for legacy data.

## Exit Criteria
- No page directly traverses raw `layoutConfig.sections`.
- All 25 core field types pass shared mode-capability checks through one pipeline.
- `test:e2e:smoke` and contract tests pass in CI.
