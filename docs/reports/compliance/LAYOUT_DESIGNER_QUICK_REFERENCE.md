# Layout Designer - Missing Features Quick Reference

## Critical Missing Features (Must Fix)

| # | Feature | PRD Location | File to Edit |
|---|---------|-------------|--------------|
| 1 | Import JSON Config | PRD lines 397-410 | `LayoutDesigner.vue` |
| 2 | Export JSON Config | PRD lines 422-437 | `LayoutDesigner.vue` |
| 3 | ComponentPanel Props Mismatch | - | `ComponentPanel.vue`, `LayoutDesigner.vue` |

## Important Missing Features (Should Fix)

| # | Feature | PRD Location | File to Edit |
|---|---------|-------------|--------------|
| 4 | Keyboard Shortcuts (Ctrl+Z/Y) | PRD line 221-228 | `LayoutDesigner.vue` |
| 5 | Delete Key Shortcut | PRD line 131 | `LayoutDesigner.vue` |
| 6 | Right-Click Context Menu | PRD line 128-130 | `CanvasArea.vue` |
| 7 | Responsive Preview Toggle | PRD lines 134-138, 304-316 | `CanvasArea.vue` |
| 8 | Field `visible_rules` Property | PRD lines 157-164 | `PropertyPanel.vue` |
| 9 | Field `custom_class` Property | PRD line 165 | `PropertyPanel.vue` |
| 10 | Field `help_text` Property | PRD line 156 | `PropertyPanel.vue` |
| 11 | Field `width` (label width) Property | PRD line 148 | `PropertyPanel.vue` |
| 12 | Section `background_color` Property | PRD line 177 | `PropertyPanel.vue` |
| 13 | Section `icon` Property | PRD line 178 | `PropertyPanel.vue` |
| 14 | Section `custom_class` Property | PRD line 180 | `PropertyPanel.vue` |

## Nice-to-Have Features

| # | Feature | PRD Location | Notes |
|---|---------|-------------|-------|
| 15 | Layout Events (`on_load`, `before_submit`, `after_submit`) | PRD lines 544-548 | Requires sandbox for security |
| 16 | Pinia Store for State Management | PRD line 51 | Current local state is sufficient |
| 17 | Separate Vue Components (instead of TSX) | PRD lines 645-1207 | Refactor for maintainability |

---

## Quick Fix Instructions

### Fix #1: Props Mismatch in ComponentPanel

**File**: `LayoutDesigner.vue` (line ~51)
```vue
<!-- Change from: -->
<ComponentPanel
  :layout-type="layoutType"
  :field-definitions="availableFields"
  @add-section="handleAddSection"
  @add-field="handleAddField"
/>

<!-- To: -->
<ComponentPanel
  :layout-type="layoutType"
  :available-fields="availableFields"
  @add-section="handleAddSection"
  @add-field="handleAddField"
/>
```

**File**: `ComponentPanel.vue` (line ~19)
```typescript
// Change from:
const props = defineProps<{
  fieldDefinitions?: FieldDefinition[]
  layoutType: 'form' | 'list' | 'detail' | 'search'
}>()

// To:
const props = defineProps<{
  availableFields?: FieldDefinition[]  // Match prop name
  layoutType: 'form' | 'list' | 'detail' | 'search'
}>()
```

### Fix #2: Add Import/Export Buttons

**File**: `LayoutDesigner.vue` (add to toolbar, line ~38)
```vue
<el-button-group style="margin-left: 16px">
  <el-button @click="handleImport">
    <el-icon><Upload /></el-icon>
    导入
  </el-button>
  <el-button @click="handleExport">
    <el-icon><Download /></el-icon>
    导出
  </el-button>
</el-button-group>
```

**Add functions to script:**
```javascript
import { Upload, Download } from '@element-plus/icons-vue'

async function handleImport() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    try {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return

      const text = await file.text()
      const config = JSON.parse(text)

      const result = validateLayoutConfig(config, props.layoutType)
      if (!result.valid) {
        ElMessage.error(`布局配置无效: ${result.errors.map(e => e.message).join(', ')}`)
        return
      }

      layoutConfig.value = config
      history.push(config, 'Import layout')
      ElMessage.success('布局导入成功')
    } catch (err) {
      ElMessage.error('导入失败: 无效的JSON文件')
    }
  }
  input.click()
}

function handleExport() {
  const dataStr = JSON.stringify(layoutConfig.value, null, 2)
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `layout-${props.objectCode || 'custom'}-${props.layoutType}-${Date.now()}.json`
  link.click()

  URL.revokeObjectURL(url)
  ElMessage.success('布局导出成功')
}
```

### Fix #3: Add Keyboard Shortcuts

**File**: `LayoutDesigner.vue` (add to onMounted)
```javascript
import { onUnmounted } from 'vue'

function handleKeydown(e: KeyboardEvent) {
  // Ignore if typing in input
  if ((e.target as HTMLElement).tagName === 'INPUT' ||
      (e.target as HTMLElement).tagName === 'TEXTAREA') {
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
  loadLayout()
  loadAvailableFields()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
```

### Fix #4: Add Missing Field Properties

**File**: `PropertyPanel.vue` (add to field properties form, after line ~244)
```vue
<!-- Help Text -->
<el-form-item label="Help Text">
  <el-input
    :model-value="formData.help_text"
    @update:model-value="handleFieldUpdate('help_text', $event)"
    placeholder="Field help text tooltip"
  />
</el-form-item>

<!-- Label Width -->
<el-form-item label="Label Width">
  <el-input
    :model-value="formData.width"
    @update:model-value="handleFieldUpdate('width', $event)"
    placeholder="e.g. 120px"
  />
</el-form-item>

<!-- Custom CSS Class -->
<el-form-item label="Custom Class">
  <el-input
    :model-value="formData.custom_class"
    @update:model-value="handleFieldUpdate('custom_class', $event)"
    placeholder="css-class-name"
  />
</el-form-item>
```

---

## Testing Checklist

After implementing fixes, verify:

- [ ] Can import a layout JSON file
- [ ] Can export current layout to JSON
- [ ] Ctrl+Z undoes last action
- [ ] Ctrl+Y redoes undone action
- [ ] Delete key removes selected element
- [ ] Field properties show all options from PRD
- [ ] Section properties show background color and icon options
- [ ] Preview mode works without errors
- [ ] Validation catches invalid configurations
- [ ] Save and publish operations complete successfully
