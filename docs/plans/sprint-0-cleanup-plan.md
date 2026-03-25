# Sprint 0 Cleanup Plan

## Document Info
| Item | Value |
|------|------|
| Version | v1.0 |
| Date | 2026-03-24 |
| Scope | Sprint 0 stabilization and cleanup |
| Author | Codex |
| Source | `docs/prd/project-status-prd-2026-03-24.md` |

## Objective
Stabilize the workflow frontend before Sprint 5 by removing contract drift, cleaning root-level temp artifacts, and normalizing workflow navigation behavior.

## Sprint 0 Scope
| Workstream | PRD Issue | Status | Notes |
|------|------|------|------|
| Workflow page type safety | 33 TypeScript issues in new workflow pages | In progress | Touched workflow list views now use explicit row mapping and response normalization. |
| Route normalization | `/workflow` vs `/workflows` drift | Pending | UI navigation should use named routes; backend-generated deep links still need one canonical page route strategy. |
| Root cleanup | Root temp files and screenshots | Completed | Requested `check_*.py`, root `*.png`, and `test-*.json` patterns are now absent. |
| API contract fixes | `items` vs `results`, mixed camel/snake case | In progress | Workflow list pages now tolerate both response shapes while the backend contract is finalized. |

## Critical Findings
1. The new `frontend/src/views/workflows/*` pages were written against unstable payload shapes and depended on `any`, which masked contract drift.
2. `WorkflowDefinitionList.vue` referenced a missing `WorkflowForm.vue` component. This was a real runtime risk hidden by the fact that the page set is still not routed into the active app shell.
3. Hardcoded path strings made the workflow pages sensitive to route drift and deep-link inconsistencies.
4. Root temp artifacts were cluttering the repository and obscuring meaningful workspace changes.

## Actions Completed Now
1. Hardened `frontend/src/views/workflows/definitions/WorkflowDefinitionList.vue` with normalized row mapping, named-route navigation, and removal of the broken `WorkflowForm.vue` dependency.
2. Hardened `frontend/src/views/workflows/instances/WorkflowInstanceList.vue` with normalized list parsing, camelCase local row models, and named-route navigation.
3. Hardened `frontend/src/views/workflows/tasks/TaskList.vue` with normalized task parsing, unread/statistics handling, assignee normalization, and named-route navigation.
4. Added `frontend/src/views/workflows/shared/listContracts.ts` to centralize paginated response normalization and mixed camelCase/snake_case field access.
5. Verified the requested root cleanup patterns now return no matches.

## Remaining Sprint 0 Work
### 1. Route Normalization
1. Choose one canonical frontend page namespace for workflow screens.
2. Keep API endpoints under `/api/workflows/*` and decouple page navigation from raw strings by using named routes and a single deep-link builder.
3. Update notification/deep-link generators so they resolve to the same canonical frontend page routes.
4. Either register the new `src/views/workflows/*` pages in the router or retire them to avoid more false-positive builds.

### 2. API Contract Finalization
1. Standardize workflow list endpoints on DRF pagination: `count`, `next`, `previous`, `results`.
2. Standardize secondary payloads such as `statistics` and `unreadCount`.
3. Remove temporary response-shape fallbacks in the UI once backend responses are stable and covered by tests.

### 3. Cleanup Guardrails
1. Add or confirm `.gitignore` rules for temporary screenshots and ad hoc check scripts.
2. Add a lightweight repo hygiene check in CI or pre-commit for root temp artifacts.

## Acceptance Criteria
1. `frontend` app typecheck passes with `npm run typecheck:app`.
2. Workflow list views no longer depend on `any` for API payload handling.
3. Workflow page navigation uses named routes instead of hardcoded path strings in the touched pages.
4. Root query `find . -maxdepth 1 \( -name 'check_*.py' -o -name '*.png' -o -name 'test-*.json' \)` returns no results.
5. Canonical workflow deep-link behavior is documented and implemented across router usage and backend-generated links.

## Verification Commands
```bash
cd frontend
npm run typecheck:app -- --pretty false
./node_modules/.bin/eslint src/views/workflows/definitions/WorkflowDefinitionList.vue \
  src/views/workflows/instances/WorkflowInstanceList.vue \
  src/views/workflows/tasks/TaskList.vue \
  src/views/workflows/shared/listContracts.ts

cd ..
find . -maxdepth 1 \( -name 'check_*.py' -o -name '*.png' -o -name 'test-*.json' \) | sort
```

## Risks
1. The repo still has unrelated strict TypeScript debt in test files, so `npm run typecheck:strict` remains noisy and is not a reliable Sprint 0 gate by itself.
2. The new workflow views are still isolated from the active router, so routing integration must be finished before treating them as production-ready.
3. Temporary UI-side response normalization should not become permanent API ambiguity.

## Recommended Next Sequence
1. Register or retire the orphaned workflow pages.
2. Normalize deep-link generation and route naming across backend and frontend.
3. Lock backend workflow list contracts and add one E2E smoke test for definitions, instances, and tasks.
