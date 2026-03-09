import { computed, type Ref } from 'vue'
import {
  Check,
  Edit,
  Document,
  Histogram,
  Calendar,
  Timer,
  Message,
  Link,
  Connection,
  User,
  OfficeBuilding,
  Folder,
  Picture,
  Select,
  CircleCheck,
  Ticket,
  FolderOpened
} from '@element-plus/icons-vue'
import { normalizeFieldType } from '@/utils/fieldType'
import type {
  DesignerAnyRecord,
  DesignerFieldDefinition,
  FieldGroup
} from '@/components/designer/designerTypes'

interface UseDesignerPaletteOptions {
  mode: Ref<string | undefined>
  availableFields: Ref<DesignerFieldDefinition[]>
  searchQuery: Ref<string>
}

const groupMetadata: Record<string, { label: string; icon: unknown; color: string }> = {
  text: { label: 'Text', icon: Edit, color: '#409eff' },
  textarea: { label: 'Textarea', icon: Document, color: '#409eff' },
  rich_text: { label: 'Rich Text', icon: Document, color: '#409eff' },
  number: { label: 'Number', icon: Histogram, color: '#67c23a' },
  boolean: { label: 'Boolean', icon: CircleCheck, color: '#67c23a' },
  date: { label: 'Date', icon: Calendar, color: '#e6a23c' },
  datetime: { label: 'DateTime', icon: Timer, color: '#e6a23c' },
  email: { label: 'Email', icon: Message, color: '#409eff' },
  url: { label: 'URL', icon: Link, color: '#409eff' },
  reference: { label: 'Reference', icon: Connection, color: '#909399' },
  user: { label: 'User', icon: User, color: '#f56c6c' },
  department: { label: 'Department', icon: OfficeBuilding, color: '#f56c6c' },
  file: { label: 'File', icon: Folder, color: '#e6a23c' },
  image: { label: 'Image', icon: Picture, color: '#e6a23c' },
  select: { label: 'Select', icon: Select, color: '#67c23a' },
  multi_select: { label: 'Multi Select', icon: Select, color: '#67c23a' },
  radio: { label: 'Radio', icon: CircleCheck, color: '#67c23a' },
  checkbox: { label: 'Checkbox', icon: Check, color: '#67c23a' },
  sub_table: { label: 'Sub Table', icon: FolderOpened, color: '#909399' },
  formula: { label: 'Formula', icon: Ticket, color: '#9c27b0' }
}

function getDesignerFieldCode(field: DesignerAnyRecord): string {
  return String(field.code || field.fieldCode || field.field_code || field.fieldName || '').trim()
}

function readDesignerBooleanFlag(field: DesignerAnyRecord, ...keys: string[]): boolean | undefined {
  for (const key of keys) {
    if (field?.[key] === undefined || field?.[key] === null) continue
    return Boolean(field[key])
  }
  return undefined
}

function isReverseRelationPaletteField(field: DesignerAnyRecord): boolean {
  return Boolean(
    field?.isReverseRelation ||
    field?.is_reverse_relation ||
    field?.reverseRelationField ||
    field?.reverse_relation_field ||
    normalizeFieldType(field?.fieldType || field?.field_type || field?.type || 'text') === 'related_object'
  )
}

export function useDesignerPalette(options: UseDesignerPaletteOptions) {
  const resolveDesignerFieldContext = (): 'form' | 'detail' | 'list' | 'search' => {
    const rawMode = String(options.mode.value || '').toLowerCase()
    if (rawMode === 'readonly' || rawMode === 'detail') return 'detail'
    if (rawMode === 'list') return 'list'
    if (rawMode === 'search') return 'search'
    return 'form'
  }

  const isDesignerVisibleField = (field: DesignerAnyRecord): boolean => {
    if (!field || typeof field !== 'object') return false
    if (!getDesignerFieldCode(field)) return false
    if (isReverseRelationPaletteField(field)) return false
    if (readDesignerBooleanFlag(field, 'isHidden', 'is_hidden') === true) return false

    const context = resolveDesignerFieldContext()
    if (context === 'detail') {
      return readDesignerBooleanFlag(field, 'showInDetail', 'show_in_detail') !== false
    }
    if (context === 'list') {
      return readDesignerBooleanFlag(field, 'showInList', 'show_in_list') !== false
    }
    if (context === 'search') {
      const showInFilter = readDesignerBooleanFlag(field, 'showInFilter', 'show_in_filter')
      if (showInFilter !== undefined) return showInFilter
      const searchable = readDesignerBooleanFlag(field, 'isSearchable', 'is_searchable')
      if (searchable !== undefined) return searchable
      return true
    }
    return readDesignerBooleanFlag(field, 'showInForm', 'show_in_form') !== false
  }

  const filterDesignerPaletteFields = (fields: DesignerAnyRecord[]): DesignerAnyRecord[] => {
    return (fields || []).filter((field) => isDesignerVisibleField(field))
  }

  const normalizeAvailableFields = (fields: DesignerAnyRecord[]): DesignerFieldDefinition[] => {
    return filterDesignerPaletteFields(fields).map((field) => ({
      ...field,
      code: getDesignerFieldCode(field),
      name: String(field.name || field.label || field.displayName || field.display_name || field.code || field.fieldName || '').trim(),
      fieldType: normalizeFieldType(field.fieldType || field.field_type || field.type || 'text')
    }))
  }

  const fieldGroups = computed<FieldGroup[]>(() => {
    const groups: Record<string, FieldGroup> = {}

    options.availableFields.value.forEach((field) => {
      let groupType = normalizeFieldType(field.fieldType || 'text')

      if (groupType === 'currency' || groupType === 'percent' || groupType === 'slider' || groupType === 'rate') {
        groupType = 'number'
      }
      if (groupType === 'year' || groupType === 'month' || groupType === 'time' || groupType === 'daterange') {
        groupType = 'date'
      }
      if (groupType === 'location' || groupType === 'asset') {
        groupType = 'reference'
      }

      const metadata = groupMetadata[groupType] || { label: groupType, icon: Edit, color: '#909399' }
      if (!groups[groupType]) {
        groups[groupType] = {
          type: groupType,
          label: metadata.label,
          icon: metadata.icon,
          color: metadata.color,
          fields: []
        }
      }
      groups[groupType].fields.push(field)
    })

    return Object.values(groups)
  })

  const filteredFieldGroups = computed(() => {
    if (!options.searchQuery.value) return fieldGroups.value
    const query = options.searchQuery.value.toLowerCase()
    return fieldGroups.value
      .map((group) => ({
        ...group,
        fields: group.fields.filter((field) =>
          field.name?.toLowerCase().includes(query) ||
          field.code?.toLowerCase().includes(query)
        )
      }))
      .filter((group) => group.fields.length > 0)
  })

  return {
    filteredFieldGroups,
    normalizeAvailableFields
  }
}
