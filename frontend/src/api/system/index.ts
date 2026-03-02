/**
 * System API - Barrel Re-export
 *
 * This file re-exports all system API modules for backward compatibility.
 * All existing `import { ... } from '@/api/system'` will continue to work.
 *
 * For new code, prefer importing from specific modules:
 *   import { menuApi } from '@/api/system/menu'
 *   import { businessObjectApi } from '@/api/system/businessObject'
 */

// Menu
export { menuApi } from './menu'
export type { MenuItem, MenuGroup, MenuResponse } from './menu'

// Business Object
export { businessObjectApi } from './businessObject'
export type { BusinessObject, FieldTypeGroup, FieldTypeOption, FieldTypeConfig } from './businessObject'

// Field Definition & Layout Types
export type {
    FieldDefinition,
    AvailableField,
    FieldGroup,
    PageLayout,
    LayoutHistory
} from './fieldDefinition'

// Legacy Helper Functions
export {
    getBusinessObject,
    getFieldDefinitions,
    getPageLayout,
    getDynamicData,
    createDynamicData,
    updateDynamicData,
    searchReferenceData,
    getDepartments,
    getDepartmentTree,
    getDepartmentDetail,
    createDepartment,
    updateDepartment,
    partialUpdateDepartment,
    deleteDepartment,
    getUsers
} from './helpers'

// Dictionary
export { dictionaryTypeApi, dictionaryItemApi } from './dictionary'
export type { DictionaryType, DictionaryItem } from './dictionary'

// Sequence Rule
export { sequenceRuleApi } from './sequenceRule'
export type { SequenceRule } from './sequenceRule'

// System Configuration
export { systemConfigApi } from './systemConfig'
export type { SystemConfig } from './systemConfig'

// Page Layout
export { pageLayoutApi } from './pageLayout'

// Column Configuration
export { columnConfigApi } from './columnConfig'
export type { ColumnItem, ColumnConfig } from './columnConfig'

// Tab Configuration
export { tabConfigApi } from './tabConfig'
export type { TabItem, TabConfig } from './tabConfig'
