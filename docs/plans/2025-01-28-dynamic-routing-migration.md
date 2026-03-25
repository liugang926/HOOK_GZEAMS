# Dynamic Routing Migration Plan

## Document Information
| Project | Description |
|---------|-------------|
| Plan Version | v1.0 |
| Created Date | 2026-01-28 |
| Status | Planning Phase |
| Target | Complete migration to dynamic routing |

---

## Executive Summary

The GZEAMS platform currently uses a **hybrid routing architecture** with both hardcoded URLs and dynamic routing. This plan outlines the complete migration to a unified dynamic routing system that aligns with the low-code platform's metadata-driven architecture.

### Current State
- **Dynamic Router**: `/api/system/objects/{code}/` - Working correctly
- **Hardcoded Routes**: 15+ module-specific URL patterns (e.g., `/api/assets/`, `/api/consumables/`)
- **Frontend**: Mixed - some use dynamic API, others use hardcoded paths

### Target State
- **Unified Dynamic Router**: All business objects accessed via `/api/system/objects/{code}/`
- **System Endpoints Preserved**: Auth, workflows, organizations, permissions, notifications, SSO
- **Frontend**: All module APIs use `dynamic.ts` client

---

## Phase 1: Analysis & Planning

### 1.1 Hardcoded URL Inventory

| Module | URL Pattern | BusinessObjects | Action |
|--------|------------|-----------------|--------|
| assets | `/api/assets/` | Asset, AssetCategory, AssetPickup, AssetTransfer, AssetReturn, AssetLoan, Supplier, Location, AssetStatusLog | Migrate to dynamic |
| consumables | `/api/consumables/` | Consumable, ConsumableCategory, ConsumableStock, ConsumablePurchase, ConsumableIssue | Migrate to dynamic |
| lifecycle | `/api/lifecycle/` | PurchaseRequest, AssetReceipt, Maintenance, MaintenancePlan, MaintenanceTask, DisposalRequest | Migrate to dynamic |
| inventory | `/api/inventory/` | InventoryTask, InventorySnapshot, InventoryDifference | Migrate to dynamic |
| software_licenses | `/api/software-licenses/` | Software, SoftwareLicense, LicenseAllocation | Migrate to dynamic |
| it_assets | `/api/it-assets/` | ITAsset, ITMaintenanceRecord, ConfigurationChange | Migrate to dynamic |
| leasing | `/api/leasing/` | LeasingContract, LeaseItem, RentPayment, LeaseReturn, LeaseExtension | Migrate to dynamic |
| insurance | `/api/insurance/` | InsuranceCompany, InsurancePolicy, InsuredAsset, PremiumPayment, ClaimRecord, PolicyRenewal | Migrate to dynamic |
| finance | `/api/finance/` | FinanceVoucher, VoucherEntry, VoucherTemplate | Migrate to dynamic |
| depreciation | `/api/depreciation/` | DepreciationConfig, DepreciationRecord, DepreciationRun | Migrate to dynamic |
| mobile | `/api/mobile/` | MobileDevice, DeviceSecurityLog, DataSync, SyncConflict, SyncLog, MobileApproval, ApprovalDelegate | Migrate to dynamic |
| auth | `/api/auth/` | N/A (authentication) | **Keep** |
| organizations | `/api/organizations/` | N/A (system) | **Keep** |
| permissions | `/api/permissions/` | N/A (system) | **Keep** |
| workflows | `/api/workflows/` | N/A (workflow system) | **Keep** |
| notifications | `/api/notifications/` | N/A (system) | **Keep** |
| sso | `/api/sso/` | N/A (SSO integration) | **Keep** |
| system | `/api/system/` | N/A (metadata) | **Keep** |

### 1.2 Frontend API Files to Update

| File | Hardcoded Paths | Priority |
|------|-----------------|----------|
| `src/api/assets.ts` | `/api/assets/`, `/assets/categories/`, `/assets/locations/` | High |
| `src/api/consumables.ts` | `/api/consumables/` | Medium |
| `src/api/inventory.ts` | `/api/inventory/` | Medium |
| `src/api/softwareLicenses.ts` | `/api/software-licenses/` | Low |
| `src/api/itAssets.ts` | `/api/it-assets/` | Low |
| `src/api/leasing.ts` | `/api/leasing/` | Low |
| `src/api/insurance.ts` | `/api/insurance/` | Low |
| `src/api/finance.ts` | `/api/finance/` | Low |
| `src/api/depreciation.ts` | `/api/depreciation/` | Low |

---

## Phase 2: Backend Migration

### 2.1 Remove Hardcoded URL Routes

**File**: `backend/config/urls.py`

**Lines to remove** (comment out first for rollback):
```python
# Phase 2: Remove these hardcoded routes (migrate to dynamic routing)
# path('api/assets/', include('apps.assets.urls')),
# path('api/consumables/', include('apps.consumables.urls')),
# path('api/lifecycle/', include('apps.lifecycle.urls')),
# path('api/', include('apps.inventory.urls')),  # Note: This catches /api/inventory/
# path('api/software-licenses/', include('apps.software_licenses.urls')),
# path('api/it-assets/', include('apps.it_assets.urls')),
# path('api/leasing/', include('apps.leasing.urls')),
# path('api/insurance/', include('apps.insurance.urls')),
# path('api/finance/', include('apps.finance.urls')),
# path('api/depreciation/', include('apps.depreciation.urls')),
# path('api/mobile/', include('apps.mobile.urls')),
```

**Routes to KEEP** (system-level, not business objects):
```python
path('api/auth/', include('apps.accounts.urls')),
path('api/organizations/', include('apps.organizations.urls')),
path('api/permissions/', include('apps.permissions.urls')),
path('api/workflows/', include('apps.workflows.urls')),
path('api/notifications/', include('apps.notifications.urls')),
path('api/sso/', include('apps.sso.urls')),
path('api/system/', include('apps.system.urls')),
```

### 2.2 Verify ObjectRegistry Mapping

**File**: `backend/apps/system/services/object_registry.py`

Ensure `_viewset_map` includes ALL ViewSets from removed URL patterns.

---

## Phase 3: Frontend Migration

### 3.1 Update Module API Files

**Strategy**: Replace module-specific API files with exports from `dynamic.ts`

**Example - `src/api/assets.ts`**:
```typescript
// OLD (remove):
// export const assetApi = createBaseApiService('/assets')
// export const assetCategoryApi = createBaseApiService('/assets/categories')

// NEW (use dynamic):
import { createObjectClient } from './dynamic'
export const assetApi = createObjectClient('Asset')
export const assetCategoryApi = createObjectClient('AssetCategory')
export const supplierApi = createObjectClient('Supplier')
export const locationApi = createObjectClient('Location')
```

### 3.2 Update Component Imports

**Files to check**:
- `src/views/it-assets/components/MaintenanceForm.vue`
- `src/views/it-assets/components/ITAssetForm.vue`
- `src/views/it-assets/components/ConfigurationChangeForm.vue`

**Change**: Import from `@/api/dynamic` instead of hardcoded paths

---

## Phase 4: Testing & Validation

### 4.1 Backend Tests
```bash
# Test dynamic endpoints for all migrated objects
for code in Asset AssetCategory Supplier Location Consumable InventoryTask Maintenance; do
  echo "Testing $code..."
  curl -s http://localhost:8000/api/system/objects/$code/ -H "Authorization: Bearer $TOKEN"
done
```

### 4.2 Frontend Tests
- Run Playwright test suite
- Test each module's CRUD operations
- Verify no 404 errors in console

### 4.3 Rollback Plan
If migration fails:
1. Uncomment removed URL patterns in `config/urls.py`
2. Restart backend server
3. No data loss (URL changes only)

---

## Phase 5: Cleanup

### 5.1 Delete Unused Files
After successful migration:
- Delete `backend/apps/{module}/urls.py` files (no longer needed)
- Update `apps/{module}/apps.py` to remove urls.py references

### 5.2 Update Documentation
- Update API documentation to reflect new URL pattern
- Update developer docs with dynamic routing examples

---

## Migration Order

| Step | Action | Risk | Time Estimate |
|------|--------|------|---------------|
| 1 | Comment out backend URL patterns | Low | 5 min |
| 2 | Test backend with dynamic routes | Medium | 15 min |
| 3 | Update frontend API files | Low | 30 min |
| 4 | Test frontend functionality | Medium | 30 min |
| 5 | Fix any issues found | Variable | 1-2 hours |
| 6 | Delete old URL files | Low | 10 min |
| 7 | Final testing | Medium | 30 min |

**Total Estimated Time**: 3-4 hours

---

## Success Criteria

- [x] All business objects accessible via `/api/system/objects/{code}/`
- [x] No 404 errors on frontend
- [x] All CRUD operations working
- [x] No hardcoded URL patterns for business objects
- [x] System endpoints (auth, workflows, etc.) preserved
- [x] All tests passing

---

**Last Updated**: 2026-01-28
**Next Review**: After Phase 2 completion
