# Layout Designer Field Loading Fix PRD

## Document Information

| Project | Description |
|---------|-------------|
| **PRD Version** | v1.0 |
| **Creation Date** | 2026-02-04 |
| **Author** | Claude (AI Assistant) |
| **Related PRDs** | `2026-02-03-layout-designer-enhancement.md`, `2025-02-04-composables-api-layer-prd.md` |
| **Priority** | **P0 - Critical** |

---

## 1. Executive Summary

### 1.1 Problem Statement

The WYSIWYG Layout Designer (`WysiwygLayoutDesigner.vue`) is currently unable to properly load and display **all available fields** for a business object (e.g., Asset). This prevents users from seeing the complete field list in the left field panel and causes inconsistencies between the layout designer view and the actual form/card view.

### 1.2 Root Cause Analysis

After browser automation testing, the following root causes have been identified:

| Issue | Current Behavior | Expected Behavior | Impact |
|-------|-----------------|-------------------|--------|
| **API Endpoint Mismatch** | Uses `/system/objects/${code}/fields/` | Should use `/system/business-objects/fields/` | Returns wrong data structure or 404 |
| **Data Structure Incompatibility** | Expects `{code, name}` but API returns `{fieldName, displayName}` | Unified field structure | Fields don't render properly |
| **Incomplete Field Loading** | Only shows ~30 fields | Should show all 58 fields for Asset | Users can't access all available fields |

### 1.3 Asset Object Field Breakdown (Current State)

```
Total Fields: 58
├── Editable Business Fields: 30+
│   ├── Basic Info: asset_code, asset_name, specification, brand, model
│   ├── Category: category, category_path
│   ├── Financial: original_value, net_value, depreciation_rate
│   ├── Supplier: supplier, purchase_date, warranty_expiry
│   └── Usage: department, location, user, status
├── System Fields: 11
│   └── id, organization, created_at, updated_at, created_by, etc.
└── Reverse Relations: 17
    └── status_logs, pickup_items, transfer_items, etc.
```

**Default Layout Config contains only 28 fields** - this is correct behavior (not all fields need to be in the default layout).

---

## 2. Functional Requirements

### 2.1 FR-1: Fix API Endpoint for Field Loading

**Priority:** P0 - Critical

**Description:** The `loadAvailableFields()` function in `WysiwygLayoutDesigner.vue` must use the correct API endpoint.

**Current Implementation (WRONG):**
```typescript
// WysiwygLayoutDesigner.vue:1486
const result = await businessObjectApi.getFieldsWithContext(props.objectCode, 'form')
// Calls: /system/objects/${code}/fields/
```

**Required Fix:**
```typescript
// Use the correct endpoint
const result = await businessObjectApi.getFields(props.objectCode, { context: 'form' })
// Calls: /system/business-objects/fields/?object_code=Asset&context=form
```

**Acceptance Criteria:**
- [ ] API call succeeds without errors
- [ ] Returns `editableFields` array with all 58 fields for Asset object
- [ ] Returns fields with correct structure: `{code, name, fieldType, ...}`

### 2.2 FR-2: Normalize Field Data Structure

**Priority:** P0 - Critical

**Description:** Handle different API response formats by normalizing field data structure.

**API Response Structure:**
```json
{
  "success": true,
  "data": {
    "editableFields": [
      {
        "code": "asset_code",
        "name": "Asset Code",
        "fieldType": "text",
        "isRequired": true,
        "showInForm": true,
        "showInList": true,
        "showInDetail": true
      }
    ],
    "reverseRelations": [...],
    "context": "form"
  }
}
```

**Required Normalization:**
```typescript
function normalizeFieldData(apiField: any): AvailableField {
  return {
    id: apiField.id || apiField.code,
    code: apiField.code || apiField.fieldCode || apiField.fieldName,
    name: apiField.name || apiField.displayName || apiField.label,
    fieldType: apiField.fieldType || apiField.type,
    isRequired: apiField.isRequired ?? apiField.required ?? false,
    isReadonly: apiField.isReadonly ?? apiField.readonly ?? false,
    showInForm: apiField.showInForm !== false,
    showInList: apiField.showInList !== false,
    showInDetail: apiField.showInDetail !== false,
    isHidden: apiField.isHidden || false
  }
}
```

**Acceptance Criteria:**
- [ ] Fields from API display with correct labels in field panel
- [ ] Field codes match actual field names in database
- [ ] Field types are correctly mapped to UI components
- [ ] All 58 fields for Asset object appear in field panel

### 2.3 FR-3: Update useLayoutFields Composable

**Priority:** P1 - High

**Description:** Ensure `useLayoutFields.ts` uses the correct API and data structure.

**Current Issue:** Already uses `businessObjectApi.getFieldsWithContext()` which calls wrong endpoint.

**Required Fix:**
```typescript
// frontend/src/composables/useLayoutFields.ts:183
// Change from:
const response = await businessObjectApi.getFieldsWithContext(
  objectCode,
  'form',
  { includeRelations: options.includeRelations !== false }
)

// To:
const response = await businessObjectApi.getFields(
  objectCode,
  { context: 'form', include_relations: options.includeRelations !== false }
)
```

**Acceptance Criteria:**
- [ ] `useLayoutFields` composable loads all available fields
- [ ] Field grouping works correctly (text, number, date, selection, reference, media, system)
- [ ] Search functionality filters fields properly
- [ ] Cache refresh works correctly

### 2.4 FR-4: Update useFieldMetadata Composable

**Priority:** P1 - High

**Description:** Ensure `useFieldMetadata.ts` uses the correct API endpoint.

**Required Fix:**
```typescript
// frontend/src/composables/useFieldMetadata.ts:157
// Change from:
const response = await businessObjectApi.getFieldsWithContext(
  objectCode,
  ctx,
  { includeRelations: options.includeRelations !== false }
)

// To:
const response = await businessObjectApi.getFields(
  objectCode,
  { context: ctx, include_relations: options.includeRelations !== false }
)
```

**Acceptance Criteria:**
- [ ] `useFieldMetadata` composable loads all fields correctly
- [ ] Editable fields and reverse relations are properly separated
- [ ] Context filtering works (form/detail/list)

---

## 3. Public Model Reference

### 3.1 Frontend Components

| Component | Base Class/Mixin | Reference |
|-----------|------------------|-----------|
| `WysiwygLayoutDesigner.vue` | N/A (Vue 3 Composition API) | `frontend/src/components/designer/WysiwygLayoutDesigner.vue` |
| `useLayoutFields.ts` | N/A (Composable) | `frontend/src/composables/useLayoutFields.ts` |
| `useFieldMetadata.ts` | N/A (Composable) | `frontend/src/composables/useFieldMetadata.ts` |

### 3.2 API Layer

| Module | Method | Reference |
|--------|--------|-----------|
| `businessObjectApi` | `getFields(code, params)` | `frontend/src/api/system.ts:160` |
| `businessObjectApi` | `getFieldsWithContext(code, context, options)` | `frontend/src/api/system.ts:173` |

---

## 4. Implementation Plan

### Phase 1: API Endpoint Fix (P0 - Critical)

| Task | File | Lines | Description |
|------|------|-------|-------------|
| Fix `loadAvailableFields()` | `WysiwygLayoutDesigner.vue` | 1480-1501 | Change to use `businessObjectApi.getFields()` |
| Add data normalization | `WysiwygLayoutDesigner.vue` | New function | Add `normalizeFieldData()` function |
| Update `useLayoutFields` | `useLayoutFields.ts` | 183 | Use `getFields()` instead of `getFieldsWithContext()` |
| Update `useFieldMetadata` | `useFieldMetadata.ts` | 157 | Use `getFields()` instead of `getFieldsWithContext()` |

### Phase 2: Testing & Verification (P0 - Critical)

| Task | Description | Acceptance |
|------|-------------|------------|
| Browser automation test | Create Playwright test to verify field loading | All 58 fields visible |
| Field panel verification | Confirm all fields appear in left panel | Field groups populated |
| Canvas rendering test | Verify dragged fields render correctly | Fields show correct labels |

### Phase 3: Consistency Verification (P1 - High)

| Task | Description | Acceptance |
|------|-------------|------------|
| Compare with Asset form view | Ensure designer matches actual form | Consistent field rendering |
| Test with other objects | Verify works for all business objects | Works for Maintenance, etc. |

---

## 5. API Specification

### 5.1 Get Business Object Fields

**Endpoint:** `GET /api/system/business-objects/fields/`

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `object_code` | string | Yes | Business object code (e.g., 'Asset') |
| `context` | string | No | Rendering context: 'form' (default), 'detail', 'list' |
| `include_relations` | boolean | No | Include reverse relation fields (default: true) |

**Request Example:**
```http
GET /api/system/business-objects/fields/?object_code=Asset&context=form&include_relations=true
Authorization: Bearer <token>
X-Organization-ID: 1
```

**Success Response:**
```json
{
  "success": true,
  "message": "Fields retrieved successfully",
  "data": {
    "editableFields": [
      {
        "id": "uuid-asset-code",
        "code": "asset_code",
        "name": "Asset Code",
        "fieldType": "text",
        "isRequired": true,
        "isReadonly": false,
        "isSystem": false,
        "isEditable": true,
        "showInForm": true,
        "showInList": true,
        "showInDetail": true,
        "isHidden": false,
        "sortOrder": 1
      }
      // ... 30+ more editable fields
    ],
    "reverseRelations": [
      {
        "id": "uuid-status-logs",
        "code": "status_logs",
        "name": "Status Change Logs",
        "fieldType": "relation",
        "relationDisplayMode": "inline"
      }
      // ... 17 more reverse relations
    ],
    "context": "form"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Business object 'Asset' not found"
  }
}
```

### 5.2 Alternative Endpoint (Deprecated)

**Endpoint:** `GET /api/system/objects/{code}/fields/`

**Status:** This endpoint may not be implemented or may return different data structure.

**Recommendation:** Do not use this endpoint for field metadata retrieval.

---

## 6. Testing Strategy

### 6.1 Unit Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `loadAvailableFields()` | Test field loading function | Returns 58 fields for Asset |
| `normalizeFieldData()` | Test data normalization | Correct field structure |
| Field grouping | Test `useLayoutFields` grouping | 8 groups created |

### 6.2 Integration Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| API endpoint | Test `/system/business-objects/fields/` | Returns all fields |
| Auth headers | Test with valid token | Success response |
| Org filtering | Test with different orgs | Correct data isolation |

### 6.3 Browser Automation Tests (Playwright)

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Field panel loading | Navigate to layout designer, count fields | 58 fields visible |
| Field drag-and-drop | Drag field from panel to canvas | Field appears in canvas |
| Field rendering | Verify field labels and values | Correct display |

**Test File:** `frontend/e2e/layout-designer-field-loading.spec.ts`

```typescript
test('verify all Asset fields load in designer', async ({ page }) => {
  // Navigate to layout designer
  await page.goto('/system/layouts/asset-form/edit')
  await page.waitForLoadState('networkidle')

  // Count fields in panel
  const fieldCount = await page.locator('.field-panel .field-item').count()
  expect(fieldCount).toBeGreaterThanOrEqual(58)

  // Verify specific fields exist
  await expect(page.locator('.field-item:has-text("asset_code")')).toBeVisible()
  await expect(page.locator('.field-item:has-text("asset_name")')).toBeVisible()
  // ... more field checks
})
```

---

## 7. Success Criteria

### 7.1 Must Have (P0)

- [ ] All 58 Asset fields load and display in left field panel
- [ ] Fields are grouped correctly by type (text, number, date, selection, reference, media, system)
- [ ] Dragging a field to canvas works correctly
- [ ] Dropped field renders with correct label
- [ ] No "示例文本" (example text) placeholders appear in canvas

### 7.2 Should Have (P1)

- [ ] Field search functionality works
- [ ] Field panel loading indicator displays
- [ ] Error handling shows user-friendly message
- [ ] Layout designer matches Asset form view

### 7.3 Nice to Have (P2)

- [ ] Recently used fields appear at top
- [ ] Field panel remembers expanded groups
- [ ] Bulk field selection for adding multiple fields

---

## 8. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API endpoint changes break other components | High | Low | Test with all business objects |
| Field structure varies between objects | Medium | Medium | Add robust normalization |
| Backend performance with 58+ fields | Low | Low | Add pagination if needed |

---

## 9. References

| Document | Description |
|----------|-------------|
| `2026-02-03-layout-designer-enhancement.md` | Original layout designer enhancement PRD |
| `2025-02-04-composables-api-layer-prd.md` | Composables API layer PRD |
| `debug_layout_designer.spec.ts` | Browser automation debug test |
| `frontend/src/api/system.ts` | API type definitions and methods |
| `frontend/src/composables/useLayoutFields.ts` | Layout fields composable |
| `frontend/src/composables/useFieldMetadata.ts` | Field metadata composable |

---

## 10. Change History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-02-04 | 1.0 | Claude (AI) | Initial PRD creation |
