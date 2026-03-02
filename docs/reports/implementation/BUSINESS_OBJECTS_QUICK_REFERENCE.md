# Business Objects Management - Quick Reference Guide

## Test Summary

| Metric | Result |
|--------|--------|
| **Total Tests** | 19 |
| **Passed** | 17 ✅ |
| **Failed** | 2 ❌ |
| **Success Rate** | 89.5% |
| **Execution Time** | 58.4s |

---

## What Works ✅

### 1. Business Objects List Page
- ✅ Page loads at `/system/business-objects`
- ✅ Displays all 28 business objects (Asset, User, Department, etc.)
- ✅ Table columns correct: Name, Code, Description, Type, Field Count, Layout Count
- ✅ "字段管理" (Field Management) button works
- ✅ "布局管理" (Layout Management) button works

### 2. Field Definitions Page
- ✅ Navigates correctly from business objects list
- ✅ Displays field table with columns: Name, Code, Type, Required, Readonly, System
- ⚠️ **Uses mock data** - needs API integration

### 3. Layout Management Page
- ✅ All 4 tabs visible: Form, Detail, List, Search
- ✅ Each tab shows layouts (1 per tab for system defaults)
- ✅ Action buttons context-aware:
  - System layouts: "自定义" (Customize), "预览" (Preview)
  - Custom layouts: "设计" (Design), "编辑" (Edit), "发布" (Publish)
- ✅ Empty state handled correctly

### 4. Layout Designer
- ✅ Opens when clicking "设计" or "自定义"
- ✅ Dialog displays with title
- ✅ Toolbar visible with buttons
- ⚠️ **Component panel fields not loading in tests**

---

## What Doesn't Work ❌

### 1. Field Definitions Mock Data (HIGH PRIORITY)
**File**: `frontend/src/views/system/FieldDefinitionList.vue` (Lines 122-182)

**Problem**:
```typescript
// TODO: Replace with actual API call
// const res = await fieldDefinitionApi.byObject(objectCode.value)
tableData.value = [/* mock data */]
```

**Fix Required**:
```typescript
const loadFields = async () => {
  loading.value = true
  try {
    const res = await getFieldDefinitions(objectCode.value)
    tableData.value = res || []
  } catch (error) {
    console.error('Failed to load field definitions:', error)
    ElMessage.error('加载字段定义失败')
  } finally {
    loading.value = false
  }
}
```

---

### 2. LayoutDesigner ComponentPanel Fields (MEDIUM PRIORITY)
**Test Error**:
```
✗ No fields found in ComponentPanel
Error: strict mode violation: locator resolved to 2 elements
```

**Root Cause**: Test selectors too generic

**Fix Required**:
1. Add `data-testid` to ComponentPanel:
   ```vue
   <div class="component-panel" data-testid="component-panel">
     <div class="field-item" data-testid="field-{{field.code}}">
   ```

2. Update test selectors:
   ```typescript
   const fieldItems = page.locator('[data-testid^="field-"]');
   ```

3. Verify LayoutDesigner passes field definitions:
   ```typescript
   // In LayoutDesigner.vue
   const availableFields = ref<any[]>([])
   // Load from API before opening designer
   ```

---

## Quick Fix Guide

### Fix #1: Field Definitions API (5 minutes)

**File**: `frontend/src/views/system/FieldDefinitionList.vue`

**Find** (Line ~126):
```typescript
// TODO: Replace with actual API call
// const res = await fieldDefinitionApi.byObject(objectCode.value)
// tableData.value = res.data || res.results || []
```

**Replace with**:
```typescript
try {
  const res = await getFieldDefinitions(objectCode.value)
  tableData.value = res || []
} catch (error) {
  console.error('Failed to load field definitions:', error)
  ElMessage.error('加载字段定义失败')
  tableData.value = []
}
```

**Verify API function exists** in `frontend/src/api/system.ts` (Line ~184):
```typescript
export function getFieldDefinitions(objectCode: string) {
  return request({
    url: '/system/field-definitions/',
    method: 'get',
    params: {
      business_object__code: objectCode,
      ordering: 'sort_order'
    }
  })
}
```

---

### Fix #2: Test Selectors (10 minutes)

**File**: `test_business_objects_management.spec.ts`

**Find** (Line ~512):
```typescript
const fieldItems = page.locator('[class*="field-item"], [class*="field-list-item"], .field-name');
```

**Replace with**:
```typescript
const fieldItems = page.locator('.component-panel .field-item');
```

**Add waits** before checking:
```typescript
await page.waitForSelector('.component-panel', { timeout: 5000 });
const fieldItems = page.locator('.component-panel .field-item');
```

---

### Fix #3: Add Data Test IDs (15 minutes)

**File**: `frontend/src/components/designer/ComponentPanel.vue`

**Add** to template (Line ~189):
```vue
<div class="component-panel" data-testid="layout-designer-component-panel">
```

**Add** to field items (Line ~247):
```vue
<div
  v-for="field in fields"
  :key="field.id"
  :class="['field-item', { disabled: !canAddField(field) }]"
  data-testid="field-item-{{ field.code }}"
>
```

**File**: `frontend/src/components/designer/LayoutDesigner.vue`

**Add** to main container (Line ~2):
```vue
<div class="layout-designer" data-testid="layout-designer-main">
```

---

## Verification Steps

### 1. Verify Field Definitions API

```bash
# Test API endpoint manually
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/system/field-definitions/?business_object__code=Asset
```

**Expected Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "...",
      "code": "name",
      "name": "资产名称",
      "field_type": "text",
      ...
    }
  ]
}
```

---

### 2. Verify LayoutDesigner Loads Fields

1. Open browser to `http://localhost:5175/system/page-layouts?objectCode=Asset`
2. Open Browser DevTools (F12)
3. Go to Console tab
4. Click "自定义" button on any layout
5. In Console, type:
   ```javascript
   document.querySelector('.component-panel')
   ```
6. Check if component panel exists and contains fields

**Expected**:
- Component panel element should be found
- Should contain `.field-item` elements
- Each field item should have `data-code` attribute

---

### 3. Run Tests After Fixes

```bash
# Run all tests
npx playwright test test_business_objects_management.spec.ts

# Run specific test suite
npx playwright test test_business_objects_management.spec.ts -g "Field Associations"

# Run with UI
npx playwright test test_business_objects_management.spec.ts --ui
```

**Expected Results**:
- All 19 tests should pass
- No "strict mode violation" errors
- Fields should be visible in ComponentPanel tests

---

## Common Issues & Solutions

### Issue: "No fields available" in ComponentPanel

**Cause**: `fieldDefinitions` prop is empty or undefined

**Solution**:
1. Check LayoutDesigner loads fields:
   ```typescript
   // In LayoutDesigner.vue, onMounted
   const loadFields = async () => {
     try {
       const fields = await getFieldDefinitions(props.objectCode)
       availableFields.value = fields || []
     } catch (error) {
       console.error('Failed to load fields:', error)
     }
   }
   ```

2. Verify prop is passed to ComponentPanel:
   ```vue
   <ComponentPanel
     :field-definitions="availableFields"
     :layout-type="layoutType"
   />
   ```

---

### Issue: "Save button not found"

**Cause**: Designer dialog not fully loaded or button not rendered

**Solution**:
```typescript
// Add explicit wait in test
await page.waitForSelector('.designer-toolbar .el-button:has-text("保存")', {
  timeout: 5000
});

const saveButton = page.locator('.designer-toolbar .el-button:has-text("保存")');
await saveButton.click();
```

---

### Issue: "strict mode violation" error

**Cause**: Locator matches multiple elements

**Solution**:
1. Use more specific selectors
2. Use `.first()` or `.nth()` if multiple matches expected
3. Add `data-testid` attributes for unique identification

---

## Next Steps

1. **Immediate (Today)**:
   - [ ] Fix FieldDefinitionList.vue to use real API
   - [ ] Add data-testid attributes to designer components
   - [ ] Update test selectors
   - [ ] Re-run tests to verify fixes

2. **Short-term (This Week)**:
   - [ ] Add error handling for API failures
   - [ ] Implement loading states
   - [ ] Add integration tests for CRUD operations
   - [ ] Test with large datasets (100+ fields)

3. **Long-term (Next Sprint)**:
   - [ ] Add drag-and-drop tests
   - [ ] Test version history and rollback
   - [ ] Performance testing
   - [ ] Accessibility testing

---

## Files to Modify

| File | Lines | Changes |
|------|-------|---------|
| `frontend/src/views/system/FieldDefinitionList.vue` | 122-182 | Replace mock data with API call |
| `frontend/src/components/designer/ComponentPanel.vue` | 189, 247 | Add data-testid attributes |
| `frontend/src/components/designer/LayoutDesigner.vue` | 2 | Add data-testid to main container |
| `test_business_objects_management.spec.ts` | 512 | Update selectors, add waits |

---

## Resources

### API Endpoints
- **List Business Objects**: `GET /api/system/business-objects/`
- **Get Field Definitions**: `GET /api/system/field-definitions/?business_object__code={code}`
- **Get Page Layouts**: `GET /api/system/page-layouts/by-object/{objectCode}/`
- **Publish Layout**: `POST /api/system/page-layouts/{id}/publish/`

### Test Commands
```bash
# Run all business objects tests
npx playwright test test_business_objects_management.spec.ts

# Run with headed mode (see browser)
npx playwright test test_business_objects_management.spec.ts --headed

# Run with UI mode (debug)
npx playwright test test_business_objects_management.spec.ts --ui

# Run specific test
npx playwright test -g "should load the business objects list"

# Run tests for specific file
npx playwright test test_business_objects_management.spec.ts --project=chromium
```

### Documentation
- Full Test Report: `docs/reports/implementation/BUSINESS_OBJECTS_MANAGEMENT_TEST_REPORT.md`
- Test File: `test_business_objects_management.spec.ts`
- API Layer: `frontend/src/api/system.ts`

---

**Last Updated**: 2026-01-26
**Status**: 17/19 tests passing (89.5%)
**Priority Fixes**: 2 (1 HIGH, 1 MEDIUM)
