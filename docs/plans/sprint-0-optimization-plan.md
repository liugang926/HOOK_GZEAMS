# Sprint 0 Optimization Plan

**Date**: 2026-03-24
**Source PRD**: `docs/prd/project-status-prd-2026-03-24.md`
**Scope**: Workflow frontend stabilization, root cleanup, and repo hygiene

## Objectives

1. Normalize the Sprint 4 workflow UI to the current frontend routing and API response contract.
2. Remove temporary files from the project root.
3. Prevent the same root-level pollution from being committed again.

## Files To Modify

### Planning
- `docs/plans/sprint-0-optimization-plan.md`

### Workflow frontend fixes
- `frontend/src/views/workflows/definitions/WorkflowDefinitionList.vue`
- `frontend/src/views/workflows/instances/WorkflowInstanceList.vue`
- `frontend/src/views/workflows/tasks/TaskList.vue`
- `frontend/src/router/index.ts`
- `frontend/src/stores/notification.ts`

### Repository hygiene
- `.gitignore`

## Files To Remove From Project Root

### Temporary scripts
- `check_api_endpoints.py`
- `check_api_endpoints_simple.py`

### Temporary screenshots and test images
- `business-object-list.png`
- `login-after.png`
- `login-before.png`
- `login-filled.png`
- `login_page.png`
- `tmp-asset-edit-495b.png`
- `tmp-field-def-list-asset.png`

### Temporary JSON data
- `test-token.json`

## Planned Code Changes

### 1. Workflow response contract alignment
- Verify all list pages in `frontend/src/views/workflows/` read paginated data from `response.results`.
- Verify all list pages in `frontend/src/views/workflows/` read totals from `response.count`.
- Remove any remaining view-level assumptions that list payloads are nested under `response.data.items` or `response.data.total`.

### 2. Workflow route normalization
- Standardize in-app navigation to `/workflow/*` for task and approval detail routes.
- Add router aliases or redirects for legacy `/workflows/*` deep links where needed so notification and bookmarked links do not 404.
- Keep admin workflow management routes unchanged unless a concrete mismatch is found, because the current router still owns `admin/workflows/*`.

### 3. Root cleanup
- Enumerate matching temporary files in the repository root.
- Remove the matched files only from the root directory, without touching similarly named files elsewhere.

### 4. `.gitignore` hardening
- Add explicit root-level patterns for:
  - `check_*.py`
  - `*.png` temporary screenshots used for manual verification
  - `test-*.json`
- Preserve existing ignore rules and avoid rewriting unrelated user changes.

## Execution Order

1. Save this plan file.
2. Update workflow views to match the current API contract and route conventions.
3. Update router compatibility for legacy plural workflow links.
4. List and remove temporary files from the project root.
5. Extend `.gitignore` to block the same artifact classes in the future.
6. Run targeted verification:
   - route reference search
   - root file cleanup check
   - frontend type check filtered to workflow files

## Verification Checklist

- `frontend/src/views/workflows/` uses `results` and `count` for paginated data.
- `/workflows/*` deep-link risk is mitigated for frontend routes.
- Matching temporary root files are removed.
- `.gitignore` contains the new root-level protection rules.
