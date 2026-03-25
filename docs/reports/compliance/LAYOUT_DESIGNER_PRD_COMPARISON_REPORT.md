# Layout Designer PRD vs Implementation Comparison Report

## Document Information
| Project | Description |
|---------|-------------|
| Report Version | v1.0 |
| Created Date | 2026-01-26 |
| PRD Reference | `docs/plans/common_base_features/03_layouts/layout_designer.md` |
| Implementation Path | `frontend/src/components/designer/` |
| Author | Code Reviewer |

---

## Executive Summary

The Layout Designer implementation is **substantially complete** but has several **missing features** and **architectural deviations** from the PRD specification. The core drag-and-drop functionality, three-panel layout, and basic property editing are implemented, but advanced features like import/export, keyboard shortcuts, context menus, and complete validation are missing.

**Overall Implementation Status**: ~70% complete

---

## 1. Feature Comparison Matrix

| PRD Feature | Implementation Status | Notes |
|------------|----------------------|-------|
| **Three-Panel Layout** | Implemented | ComponentPanel, CanvasArea, PropertyPanel all present |
| **Toolbar** | Partially Implemented | Missing Import/Export, Clear, History buttons |
| **Undo/Redo** | Implemented | Using `useLayoutHistory` composable |
| **Save Draft** | Implemented | `handleSave()` function present |
| **Publish** | Implemented | `handlePublish()` function present |
| **Preview Mode** | Implemented | Toggle preview mode works |
| **Validation** | Implemented | Using `layoutValidation.ts` utilities |
| **Version History** | Partially Implemented | Dialog exists but backend integration incomplete |
| **Rollback** | Implemented | `handleRollback()` function present |
| **Import/Export** | Missing | Not implemented |
| **Keyboard Shortcuts** | Missing | No Ctrl+Z, Ctrl+Y, Delete bindings |
| **Context Menu** | Missing | Right-click menu not implemented |
| **Responsive Preview** | Missing | Desktop/tablet/mobile switchers not present |
| **Field Search** | Implemented | Search box in ComponentPanel |
| **Field Grouping** | Implemented | Fields grouped by type |
| **Drag & Drop** | Partially Implemented | Uses Sortable.js, some issues with cross-container moves |

---

## 2. Component Architecture Comparison

### 2.1 Expected Components (from PRD)

```
LayoutDesigner/
├── components/
│   ├── DesignerToolbar.vue        # Toolbar
│   ├── ComponentPanel.vue         # Left panel
│   ├── CanvasArea.vue             # Center canvas
│   ├── PropertyPanel.vue          # Right panel
│   ├── FieldElement.vue           # Field badge
│   ├── SectionBlock.vue           # Section component
│   ├── TabPanel.vue               # Tab component
│   └── ColumnLayout.vue           # Column component
├── composables/
│   ├── useDraggable.js            # Drag logic
│   ├── useLayoutHistory.js        # Undo/redo
│   └── useLayoutValidation.js     # Validation
├── stores/
│   └── layoutDesigner.js          # Pinia store
└── utils/
    ├── layoutSchema.js            # Schema definition
    └── layoutConverter.js         # Format conversion
```

### 2.2 Actual Components

```
frontend/src/components/designer/
├── LayoutDesigner.vue             # Main component (contains toolbar inline)
├── ComponentPanel.vue             # Left panel
├── CanvasArea.vue                 # Center canvas
└── PropertyPanel.vue              # Right panel

frontend/src/composables/
└── useLayoutHistory.ts            # Undo/redo (implemented)

frontend/src/utils/
└── layoutValidation.ts            # Validation utilities (implemented)
```

**Deviation**: The PRD specifies a more modular architecture with separate components for `FieldElement`, `SectionBlock`, `TabPanel`, `ColumnLayout`, and a Pinia store. The actual implementation uses inline rendering functions within `CanvasArea.vue` (TSX render functions) instead of separate Vue components.

---

## 3. Detailed Feature Analysis

### 3.1 Toolbar Features (PRD Section 3.1)

| Feature | PRD Requirement | Implementation | Status |
|---------|---------------|----------------|--------|
| Save Draft | Button with icon | Implemented | OK |
| Publish | Button with icon | Implemented | OK |
| Preview | Button with icon | Implemented | OK |
| Undo/Redo | Button group with disabled states | Implemented | OK |
| Clear | Button to clear canvas | Partial (has `handleReset`) | Warning |
| Import | File upload for JSON config | Missing | Critical |
| Export | Download JSON config | Missing | Critical |
| Breadcrumb | Navigation path | Different implementation (inline info) | OK |

**Code Location**: `LayoutDesigner.vue` lines 4-44

**Missing Code for Import/Export**:
```javascript
// These functions from PRD (lines 398-437) are not implemented:
const handleImport = () => { /* ... */ }
const handleExport = () => { /* ... */ }
```

### 3.2 Component Panel (PRD Section 2.2)

| Feature | PRD Requirement | Implementation | Status |
|---------|---------------|----------------|--------|
| Field List | From FieldDefinition | Implemented | OK |
| Field Search | Filter by name/code/type | Implemented | OK |
| Field Grouping | By type | Implemented | OK |
| Used Field Badge | Checkbox for used fields | Implemented | OK |
| Layout Components | Draggable section types | Implemented | OK |
| Drag to Canvas | Sortable.js integration | Implemented | OK |

**Code Location**: `ComponentPanel.vue` lines 1-557

**Issues**:
- `fieldDefinitions` prop vs `availableFields` prop mismatch (property naming inconsistency)

### 3.3 Canvas Area (PRD Section 2.3)

| Feature | PRD Requirement | Implementation | Status |
|---------|---------------|----------------|--------|
| Visual Editing | Real-time preview | Implemented | OK |
| Field Sorting | Drag and drop reordering | Implemented | OK |
| Column Adjustment | 2/3/4 column layouts | Implemented | OK |
| Section Nesting | Up to 3 levels | Implemented | OK |
| Selection Highlight | Click to select | Implemented | OK |
| Context Menu | Right-click actions | Missing | Warning |
| Keyboard Shortcuts | Ctrl+Z/Y/Delete | Missing | Warning |
| Responsive Preview | Desktop/Tablet/Mobile | Missing | Warning |

**Code Location**: `CanvasArea.vue` lines 1-986

**Architecture Deviation**: Uses TSX render functions instead of separate Vue components:
```typescript
// PRD expects: <SectionBlock />, <TabPanel />, etc.
// Actual: renderSection(), renderTabSection(), etc. functions
```

### 3.4 Property Panel (PRD Section 2.4)

| Feature | PRD Requirement | Implementation | Status |
|---------|---------------|----------------|--------|
| Field Properties | label, width, span, placeholder, etc. | Implemented | OK |
| Section Properties | title, columns, collapsible, border | Implemented | OK |
| Tab Properties | title, position, style | Partial (missing position/style) | Warning |
| Column Properties | span adjustment | Implemented | OK |
| Dynamic Form | Based on element type | Implemented | OK |
| Reset to Default | Reset button | Implemented | OK |

**Code Location**: `PropertyPanel.vue` lines 1-674

**Missing Properties** (from PRD lines 146-194):
- `background_color` for sections
- `icon` for sections/tabs
- `custom_class` for fields/sections
- `help_text` for fields
- `width` (label width) for fields
- `visible_rules` (conditional visibility)

### 3.5 Layout Configuration Data Structure (PRD Section 4)

The implementation correctly follows the PRD data structure:

```javascript
// PRD Specification (lines 445-556)
{
  sections: [
    {
      id: "section-1",
      type: "section",
      title: "基本信息",
      collapsible: true,
      collapsed: false,
      columns: 2,
      border: true,
      fields: [...]
    },
    // ... tabs, collapse, column sections
  ],
  actions: [...],
  events: {...}  // Missing in implementation
}
```

**Missing**: `events` object (on_load, before_submit, after_submit scripts)

---

## 4. Missing Features Summary

### 4.1 Critical Missing Features

1. **Import/Export Configuration**
   - PRD lines 397-437
   - No implementation found
   - Impact: Cannot backup/share layouts

2. **Keyboard Shortcuts**
   - PRD lines 129-131
   - No event listeners for Ctrl+Z, Ctrl+Y, Delete
   - Impact: Poor UX for power users

3. **Context Menu**
   - PRD lines 128-130
   - No right-click menu implementation
   - Impact: Less intuitive editing

4. **Responsive Preview Switcher**
   - PRD lines 134-138
   - No desktop/tablet/mobile toggle
   - Impact: Cannot preview mobile layouts

### 4.2 Important Missing Features

5. **Advanced Field Properties**
   - `visible_rules`: Conditional visibility formulas
   - `custom_class`: Custom CSS classes
   - `help_text`: Field help tooltips
   - `width`: Label width setting

6. **Section Advanced Properties**
   - `background_color`: Section background
   - `icon`: Section icon
   - `custom_class`: Section styling

7. **Layout Events**
   - `on_load`, `before_submit`, `after_submit` scripts
   - PRD lines 544-548

8. **Pinia Store**
   - PRD specifies Pinia for state management
   - Implementation uses local component state only
   - Impact: Harder to share state between components

### 4.3 Minor Missing Features

9. **Layout Actions Configuration**
   - PRD defines `actions` array for layout-level buttons
   - Not implemented in PropertyPanel

10. **Clear Canvas Button**
    - PRD specifies "Clear" button in toolbar
    - `handleReset()` exists but may need UI confirmation refinement

---

## 5. Code Quality Issues

### 5.1 ComponentPanel.vue

**Issue 1: Props Naming Mismatch**
```vue
<!-- PRD/Usage expects: available-fields -->
<!-- Component defines: fieldDefinitions -->
<ComponentPanel
  :layout-type="layoutType"
  :field-definitions="availableFields"  <!-- Should be :available-fields -->
/>
```

**Issue 2: Duplicate Script Block**
```vue
<!-- Lines 302-312: Separate script block for icon registration -->
<!-- This is unusual pattern - should be in main setup -->
<script lang="ts">
import { Edit, Document, ... } from '@element-plus/icons-vue'
export default {
  components: { Edit, Document, ... }
}
</script>
```

### 5.2 LayoutDesigner.vue

**Issue 1: Props vs Expected Usage**
```typescript
// PropertyPanel expects `selectedItem` prop
// But emits different event structure
<PropertyPanel
  :selected-item="selectedItem"
  :available-fields="availableFields"  <!-- This prop doesn't exist in PropertyPanel -->
  @update="handleUpdateProperty"
/>
```

**Issue 2: CanvasArea TSX Complexity**
- Using render functions in TSX makes the code harder to maintain
- PRD suggests separate Vue components for better modularity

### 5.3 Missing Type Safety

```typescript
// Many `any` types used instead of proper interfaces
const availableFields = ref<any[]>([])
const layoutHistory = ref<any[]>([])
```

---

## 6. Backend Integration Status

| API Endpoint | PRD Specification | Implementation Status |
|-------------|------------------|----------------------|
| `POST /api/system/page-layouts/` | Create layout | Implemented |
| `PATCH/PUT /api/system/page-layouts/{id}` | Update layout | Implemented |
| `POST /api/system/page-layouts/{id}/save_draft/` | Save draft | Uses `partialUpdate` |
| `POST /api/system/page-layouts/{id}/publish/` | Publish | Implemented |
| `GET /api/system/page-layouts/{id}/versions/` | Version history | Implemented |
| `POST /api/system/page-layouts/{id}/rollback/` | Rollback | Implemented |
| `POST /api/system/page-layouts/import_config/` | Import | Missing |
| `GET /api/system/page-layouts/default/` | Get default | Not used |

---

## 7. Recommendations

### 7.1 Priority 1: Critical Fixes

1. **Fix Props Mismatches**
   - Align `ComponentPanel` props with usage
   - Ensure `PropertyPanel` receives expected props

2. **Add Import/Export**
   - Implement `handleImport()` and `handleExport()`
   - Add buttons to toolbar

3. **Fix Drag-and-Drop Issues**
   - Complete cross-container move logic
   - Ensure Sortable.js cleanup

### 7.2 Priority 2: Important Enhancements

4. **Add Keyboard Shortcuts**
   ```javascript
   onMounted(() => {
     document.addEventListener('keydown', handleKeydown)
   })

   function handleKeydown(e) {
     if (e.ctrlKey && e.key === 'z') { e.preventDefault(); undo() }
     if (e.ctrlKey && e.key === 'y') { e.preventDefault(); redo() }
     if (e.key === 'Delete' && selectedId.value) { handleDelete(selectedId.value) }
   }
   ```

5. **Add Missing Properties**
   - `visible_rules`, `custom_class`, `help_text` for fields
   - `background_color`, `icon` for sections

6. **Implement Responsive Preview**
   - Add toggle for desktop/tablet/mobile
   - Apply CSS classes to canvas wrapper

### 7.3 Priority 3: Architectural Improvements

7. **Extract Sub-components**
   - Create `FieldElement.vue`, `SectionBlock.vue`, etc.
   - Replace TSX render functions with Vue components

8. **Add Pinia Store** (optional)
   - For better state management if needed
   - Currently local state is sufficient

9. **Add Layout Events Support**
   - Allow scripts for `on_load`, `before_submit`, `after_submit`
   - Security consideration: sandbox execution

---

## 8. File Manifest

| File Path | Lines of Code | Status | Notes |
|-----------|--------------|--------|-------|
| `frontend/src/components/designer/LayoutDesigner.vue` | 942 | Complete | Main component with inline toolbar |
| `frontend/src/components/designer/ComponentPanel.vue` | 557 | Needs Fix | Props mismatch issue |
| `frontend/src/components/designer/CanvasArea.vue` | 986 | Complete | TSX render functions |
| `frontend/src/components/designer/PropertyPanel.vue` | 674 | Complete | Dynamic property forms |
| `frontend/src/composables/useLayoutHistory.ts` | 133 | Complete | Undo/redo functionality |
| `frontend/src/utils/layoutValidation.ts` | 476 | Complete | Schema validation |
| `frontend/src/views/system/PageLayoutList.vue` | 672 | Complete | Layout list page |

**Total**: 4,444 lines of code

---

## 9. Conclusion

The Layout Designer implementation demonstrates **solid foundational work** with the core three-panel architecture, drag-and-drop functionality, and basic property editing all functional. However, the implementation falls short of the PRD specification in several areas:

**Strengths**:
- Clean three-panel layout
- Comprehensive validation utilities
- Good undo/redo history management
- Responsive property panel

**Weaknesses**:
- Missing import/export functionality
- No keyboard shortcuts or context menus
- Incomplete property options (visible_rules, custom_class, etc.)
- TSX render functions instead of Vue components (architectural deviation)
- Some props naming mismatches between components

**Estimated Completion**: 70%

**Recommended Next Steps**:
1. Fix props mismatches (ComponentPanel)
2. Add import/export functionality
3. Implement keyboard shortcuts
4. Add missing property options
5. Consider refactoring TSX to Vue components for maintainability

---

## Appendix: Code Snippets for Missing Features

### A. Import Function (from PRD)

```javascript
const handleImport = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    const text = await file.text()
    const config = JSON.parse(text)

    const validation = validateLayoutSchema(config)
    if (!validation.valid) {
      ElMessage.error(`布局配置无效: ${validation.errors.join(', ')}`)
      return
    }

    layoutConfig.value = config
    ElMessage.success('布局导入成功')
  }
  input.click()
}
```

### B. Export Function (from PRD)

```javascript
const handleExport = () => {
  const dataStr = JSON.stringify(layoutConfig.value, null, 2)
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `layout-${businessObject.value}-${Date.now()}.json`
  link.click()

  URL.revokeObjectURL(url)
  ElMessage.success('布局导出成功')
}
```

### C. Keyboard Shortcuts Handler

```javascript
function handleKeydown(e: KeyboardEvent) {
  // Ignore if in input/textarea
  if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
    return
  }

  if (e.ctrlKey && e.key === 'z') {
    e.preventDefault()
    undo()
  } else if (e.ctrlKey && e.key === 'y') {
    e.preventDefault()
    redo()
  } else if (e.key === 'Delete' && selectedId.value) {
    e.preventDefault()
    handleDelete(selectedId.value)
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
```
