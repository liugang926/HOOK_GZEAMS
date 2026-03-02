# Frontend Report

Date: 2026-02-08

## Component Dependency Diagram

```
DynamicListPage.vue
  -> BaseListPage.vue
     -> ColumnManager.vue
     -> FieldRenderer.vue (common)
  -> FieldRenderer.vue (engine)
  -> api/dynamic.ts (createObjectClient)

DynamicFieldRenderer.vue
  -> api/assets.ts (assetApi, categoryApi, locationApi)
  -> api/users.ts (userApi)
  -> api/organizations.ts (orgApi, deptApi)
  -> utils/request.ts
  -> (template uses) image-upload, reference-picker, user-picker, dept-picker,
     rich-text-editor, code-editor, sub-table (global components)

FieldRenderer.vue (engine)
  -> fields/TextField.vue
  -> fields/NumberField.vue
  -> fields/DateField.vue
  -> fields/SelectField.vue
  -> fields/BooleanField.vue
  -> fields/ReferenceField.vue
  -> fields/UserSelectField.vue
  -> fields/DepartmentSelectField.vue
  -> fields/LocationSelectField.vue
  -> fields/AssetSelector.vue
  -> fields/DictionarySelect.vue
  -> fields/JsonField.vue
  -> fields/SubTableField.vue
  -> fields/FormulaField.vue
  -> fields/AttachmentUpload.vue
  -> fields/ImageField.vue
  -> fields/QRCodeField.vue
  -> fields/BarcodeField.vue
  -> fields/RichTextField.vue
  -> fields/CodeField.vue
  -> fields/ColorField.vue
  -> fields/RateField.vue
  -> fields/SliderField.vue
  -> fields/SwitchField.vue
```

## Style Coverage

- Total Vue components: 155
- Components with `<style>` blocks: 128 (82.6%)
- Components with `<style scoped>`: 127 (81.9%)

Notes:
- Counts are based on a static scan of `frontend/src/**/*.vue`.
- Style coverage here means presence of a `<style>` block; it does not measure actual CSS selector coverage.
