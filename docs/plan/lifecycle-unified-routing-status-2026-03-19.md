# Lifecycle Unified Routing Status (2026-03-19)

## Summary

Lifecycle frontend pages have converged onto the unified object engine.

- List routes: `/objects/:code`
- Create routes: `/objects/:code/create`
- Detail routes: `/objects/:code/:id`
- Edit routes: `/objects/:code/:id/edit` or aggregate edit-form routing where applicable

The following dedicated lifecycle list/detail pages have been retired from runtime code:

- `frontend/src/views/lifecycle/PurchaseRequestList.vue`
- `frontend/src/views/lifecycle/AssetReceiptList.vue`
- `frontend/src/views/lifecycle/MaintenanceList.vue`
- `frontend/src/views/lifecycle/MaintenancePlanList.vue`
- `frontend/src/views/lifecycle/MaintenanceTaskList.vue`
- `frontend/src/views/lifecycle/DisposalRequestList.vue`
- `frontend/src/views/lifecycle/AssetWarrantyList.vue`
- `frontend/src/views/lifecycle/PurchaseRequestDetail.vue`
- `frontend/src/views/lifecycle/AssetReceiptDetail.vue`
- `frontend/src/views/lifecycle/MaintenanceDetail.vue`
- `frontend/src/views/lifecycle/MaintenancePlanDetail.vue`
- `frontend/src/views/lifecycle/MaintenanceTaskDetail.vue`
- `frontend/src/views/lifecycle/DisposalRequestDetail.vue`
- `frontend/src/views/lifecycle/AssetWarrantyDetail.vue`

## Interpretation Guide

- Historical planning and PRD documents that still mention the retired pages should be read as pre-convergence design history.
- Current implementation authority is the unified object stack in:
  - `frontend/src/views/dynamic/`
  - `frontend/src/views/dynamic/workspace/`
  - `frontend/src/platform/lifecycle/`
  - `frontend/src/router/index.ts`

## Current Compatibility Scope

- Legacy lifecycle URLs under `/assets/lifecycle/...` are retained only as router compatibility redirects.
- Runtime breadcrumbs, navigation, list/detail rendering, and lifecycle actions now resolve through canonical object routes.
