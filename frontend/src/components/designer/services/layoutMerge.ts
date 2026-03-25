/**
 * Layout Merge Service
 *
 * Merges default field metadata with differential configuration
 * to produce the final layout structure for rendering.
 *
 * Reference: docs/plans/2025-02-03-metadata-layout-implementation-plan.md
 */

import type {
  FieldMetadata,
  SectionConfig,
  DesignerTabConfig,
  DifferentialConfig,
  LayoutConfig
} from '@/types/metadata'

// ============================================================================
// Types
// ============================================================================

// Use DesignerTabConfig from metadata but expose as TabConfig locally
// for backward compatibility within this module
type TabConfig = DesignerTabConfig

function resolveSectionTitle(
  title: FieldMetadata['sectionTitle'],
  fallback: string
): string {
  if (typeof title === 'string' && title.trim()) return title.trim()
  if (title && typeof title === 'object') {
    const localized =
      title['zh-CN'] ??
      title['en-US'] ??
      title.title ??
      title.label
    if (typeof localized === 'string' && localized.trim()) {
      return localized.trim()
    }
  }
  return fallback
}

export interface MergedLayout {
  fields: FieldMetadata[]
  sections: SectionConfig[]
  tabs: DesignerTabConfig[]
}

// ============================================================================
// Public API
// ============================================================================

/**
 * Merge default field metadata with differential configuration
 *
 * @param defaultFields - The base field definitions from metadata
 * @param diffConfig - Custom overrides and ordering
 * @returns Merged layout configuration
 */
export function mergeLayoutWithDiff(
  defaultFields: FieldMetadata[],
  diffConfig: DifferentialConfig
): MergedLayout {
  const { fieldOrder, fieldOverrides, sections, tabs } = diffConfig

  // Apply custom field order, or use default sortOrder
  let orderedFields = [...defaultFields]
  if (fieldOrder && fieldOrder.length > 0) {
    const fieldMap = new Map(defaultFields.map(f => [f.code, f]))
    orderedFields = fieldOrder
      .map(code => fieldMap.get(code))
      .filter((f): f is FieldMetadata => f !== undefined)

    // Add any fields not in custom order
    const orderedCodes = new Set(fieldOrder)
    defaultFields.forEach(f => {
      if (!orderedCodes.has(f.code)) {
        orderedFields.push(f)
      }
    })
  } else {
    orderedFields.sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0))
  }

  // Apply field overrides
  const mergedFields = orderedFields.map(field => {
    const overrides = fieldOverrides?.[field.code]
    if (!overrides) return field

    return {
      ...field,
      ...(overrides.label !== undefined && { name: overrides.label }),
      ...(overrides.visible !== undefined && { showInForm: overrides.visible }),
      ...(overrides.readonly !== undefined && { readonly: overrides.readonly }),
      ...(overrides.required !== undefined && { isRequired: overrides.required }),
      ...(overrides.span !== undefined && { span: overrides.span })
    }
  })

  // Use provided sections or generate default
  const mergedSections = sections || generateDefaultSections(mergedFields)

  // Use provided tabs or generate default from reverse relations
  const mergedTabs = tabs || generateDefaultTabs(mergedFields)

  return {
    fields: mergedFields,
    sections: mergedSections,
    tabs: mergedTabs
  }
}

/**
 * Calculate differential config from current state vs base
 *
 * @param currentLayout - Current layout configuration
 * @param baseFields - Base field definitions
 * @returns Differential configuration
 */
export function calculateDifferentialConfig(
  currentLayout: LayoutConfig,
  baseFields: FieldMetadata[]
): DifferentialConfig {
  const diff: DifferentialConfig = {}

  // Calculate field order changes
  if (currentLayout.sections) {
    const fieldOrder: string[] = []
    currentLayout.sections.forEach(section => {
      if (section.fields) {
        section.fields.forEach(f => {
          // Handle both string field codes and LayoutField objects
          if (typeof f === 'string') {
            fieldOrder.push(f)
          } else if (typeof f === 'object' && 'code' in f) {
            fieldOrder.push(f.code as string)
          }
        })
      }
    })

    // Check if order differs from default sortOrder
    const defaultOrder = [...baseFields]
      .sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0))
      .map(f => f.code)

    if (fieldOrder.join(',') !== defaultOrder.join(',')) {
      diff.fieldOrder = fieldOrder
    }
  }

  return diff
}

// ============================================================================
// Default Generation Functions
// ============================================================================

/**
 * Generate default section layout from fields
 */
function generateDefaultSections(fields: FieldMetadata[]): SectionConfig[] {
  // Filter out reverse relations for sections
  const editableFields = fields.filter(f => !f.isReverseRelation)

  if (editableFields.length === 0) {
    return []
  }

  // Group by sectionName if available, otherwise use defaults
  const groupedFields = new Map<string, { fields: string[]; title?: string }>()

  editableFields.forEach(field => {
    const sectionName = field.sectionName || 'basic'
    if (!groupedFields.has(sectionName)) {
      groupedFields.set(sectionName, {
        fields: [],
        title: resolveSectionTitle(field.sectionTitle, sectionName)
      })
    }
    const section = groupedFields.get(sectionName)!
    section.fields.push(field.code)
    if (!section.title && field.sectionTitle) {
      section.title = resolveSectionTitle(field.sectionTitle, sectionName)
    }
  })

  // Convert to section configs
  const sections: SectionConfig[] = []

  let isFirst = true
  for (const [sectionId, sectionData] of groupedFields.entries()) {
    sections.push({
      id: sectionId,
      title: sectionData.title || sectionId,
      fields: sectionData.fields,
      collapsed: !isFirst // First section is expanded by default
    })
    isFirst = false
  }

  return sections
}

/**
 * Generate default tabs from reverse relation fields
 */
function generateDefaultTabs(fields: FieldMetadata[]): TabConfig[] {
  // Filter reverse relations
  const relations = fields.filter(f => f.isReverseRelation)

  if (relations.length === 0) {
    return []
  }

  // Group by relation display mode
  const tabRelations: Record<string, string[]> = {}

  relations.forEach(relation => {
    const mode = relation.relationDisplayMode || 'tab_readonly'
    if (mode === 'tab_readonly' || mode === 'inline_readonly') {
      if (!tabRelations[relation.code]) {
        tabRelations[relation.code] = []
      }
      tabRelations[relation.code].push(relation.code)
    }
  })

  // Convert to tab configs
  return Object.entries(tabRelations).map(([relationCode, relationList]) => {
    const relation = relations.find(r => r.code === relationCode)
    return {
      id: relationCode,
      title: relation?.name || toTitleCase(relationCode),
      relations: relationList,
      disabled: false
    }
  })
}

/**
 * Convert snake_case or kebab-case to Title Case
 */
function toTitleCase(str: string): string {
  return str
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
    .trim()
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get field by code from merged layout
 */
export function getFieldByCode(layout: MergedLayout, code: string): FieldMetadata | undefined {
  return layout.fields.find(f => f.code === code)
}

/**
 * Get section by id from merged layout
 */
export function getSectionById(layout: MergedLayout, id: string): SectionConfig | undefined {
  return layout.sections.find(s => s.id === id)
}

/**
 * Get tab by id from merged layout
 */
export function getTabById(layout: MergedLayout, id: string): TabConfig | undefined {
  return layout.tabs.find(t => t.id === id)
}

/**
 * Check if a field is visible in a section
 */
export function isFieldVisible(layout: MergedLayout, fieldCode: string): boolean {
  const field = getFieldByCode(layout, fieldCode)
  if (!field) return false

  // Check section membership
  for (const section of layout.sections) {
    if (section.fields.includes(fieldCode)) {
      return true
    }
  }

  // Check tab membership
  for (const tab of layout.tabs) {
    if (tab.fields?.includes(fieldCode)) {
      return true
    }
  }

  return false
}
