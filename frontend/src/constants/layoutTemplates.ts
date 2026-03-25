/**
 * Default Layout Templates
 *
 * Provides pre-configured layout templates for common business scenarios.
 * These templates serve as starting points for layout customization.
 *
 * Unified Layout System:
 * - All layouts use the same sections-based structure
 * - Display mode (edit/readonly/search) determines rendering behavior
 * - List layouts are auto-generated from FieldDefinition.show_in_list
 */

import type { LayoutMode } from '@/types/layout'

export interface LayoutTemplate {
  id: string
  name: string
  description: string
  mode: LayoutMode
  preview?: string
  config: Record<string, unknown>
}

/**
 * Default edit form template - for creating/editing records
 */
export const defaultEditTemplate: LayoutTemplate = {
  id: 'default_edit',
  name: 'Default Edit Form',
  description: 'Standard form layout with collapsible sections',
  mode: 'edit',
  config: {
    sections: [
      {
        id: 'section-main',
        type: 'card',
        title: 'Information',
        collapsible: true,
        collapsed: false,
        columnCount: 2,
        border: true,
        fields: []
      }
    ],
    actions: [
      { code: 'submit', label: 'Save', type: 'primary', position: 'bottom-right' },
      { code: 'cancel', label: 'Cancel', type: 'default', position: 'bottom-right' }
    ]
  }
}

/**
 * Readonly detail template - for viewing records
 */
export const defaultReadonlyTemplate: LayoutTemplate = {
  id: 'default_readonly',
  name: 'Default Detail View',
  description: 'Read-only view of record information',
  mode: 'readonly',
  config: {
    sections: [
      {
        id: 'section-main',
        type: 'card',
        title: 'Details',
        collapsible: false,
        collapsed: false,
        columnCount: 2,
        border: true,
        fields: []
      }
    ],
    actions: [
      { code: 'edit', label: 'Edit', type: 'primary', position: 'top-right' },
      { code: 'back', label: 'Back', type: 'default', position: 'top-right' }
    ]
  }
}

/**
 * Search form template - for filter/search forms
 */
export const defaultSearchTemplate: LayoutTemplate = {
  id: 'default_search',
  name: 'Default Search Form',
  description: 'Horizontal search form layout',
  mode: 'search',
  config: {
    sections: [
      {
        id: 'section-search',
        type: 'default',
        title: '',
        collapsible: false,
        collapsed: false,
        columnCount: 4,
        border: false,
        fields: []
      }
    ],
    actions: [
      { code: 'search', label: 'Search', type: 'primary', position: 'bottom-right' },
      { code: 'reset', label: 'Reset', type: 'default', position: 'bottom-right' }
    ],
    layout: 'horizontal',
    labelWidth: '100px'
  }
}

/**
 * Asset-specific templates (examples of customized layouts)
 */
export const assetEditTemplate: LayoutTemplate = {
  id: 'asset_edit',
  name: 'Asset Edit Form',
  description: 'Comprehensive asset creation/editing form',
  mode: 'edit',
  config: {
    sections: [
      {
        id: 'section-basic',
        type: 'card',
        title: 'Basic Information',
        collapsible: true,
        collapsed: false,
        columnCount: 2,
        border: true,
        fields: [
          { id: 'field-code', fieldCode: 'code', label: 'Asset Code', span: 12, required: true },
          { id: 'field-name', fieldCode: 'name', label: 'Asset Name', span: 12, required: true },
          { id: 'field-category', fieldCode: 'category', label: 'Category', span: 12 },
          { id: 'field-status', fieldCode: 'status', label: 'Status', span: 12 }
        ]
      },
      {
        id: 'section-detail',
        type: 'card',
        title: 'Detailed Information',
        collapsible: true,
        collapsed: true,
        columnCount: 2,
        border: true,
        fields: [
          { id: 'field-model', fieldCode: 'model', label: 'Model', span: 12 },
          { id: 'field-brand', fieldCode: 'brand', label: 'Brand', span: 12 },
          { id: 'field-purchase-date', fieldCode: 'purchase_date', label: 'Purchase Date', span: 12 },
          { id: 'field-purchase-price', fieldCode: 'purchase_price', label: 'Purchase Price', span: 12 }
        ]
      },
      {
        id: 'section-location',
        type: 'card',
        title: 'Location & Assignment',
        collapsible: true,
        collapsed: true,
        columnCount: 2,
        border: true,
        fields: [
          { id: 'field-department', fieldCode: 'department', label: 'Department', span: 12 },
          { id: 'field-custodian', fieldCode: 'custodian', label: 'Custodian', span: 12 },
          { id: 'field-location', fieldCode: 'location', label: 'Storage Location', span: 12 },
          { id: 'field-area', fieldCode: 'area', label: 'Area', span: 12 }
        ]
      }
    ],
    actions: [
      { code: 'submit', label: 'Save', type: 'primary', position: 'bottom-right' },
      { code: 'submit-another', label: 'Save & Add Another', type: 'default', position: 'bottom-right' },
      { code: 'cancel', label: 'Cancel', type: 'default', position: 'bottom-right' }
    ]
  }
}

/**
 * Tabbed detail template - for organized detail views
 */
export const tabbedDetailTemplate: LayoutTemplate = {
  id: 'tabbed_detail',
  name: 'Tabbed Detail View',
  description: 'Detail view with tabs for organizing information',
  mode: 'readonly',
  config: {
    sections: [
      {
        id: 'section-tabs',
        type: 'tab',
        tabs: [
          {
            id: 'tab-basic',
            title: 'Basic Info',
            fields: []
          },
          {
            id: 'tab-financial',
            title: 'Financial',
            fields: []
          },
          {
            id: 'tab-location',
            title: 'Location',
            fields: []
          },
          {
            id: 'tab-audit',
            title: 'Audit Trail',
            fields: []
          }
        ]
      }
    ]
  }
}

/**
 * All available templates grouped by mode
 */
export const layoutTemplatesByMode: Record<LayoutMode, LayoutTemplate[]> = {
  edit: [defaultEditTemplate, assetEditTemplate],
  readonly: [defaultReadonlyTemplate, tabbedDetailTemplate],
  search: [defaultSearchTemplate]
}

/**
 * Get template by ID
 */
export function getTemplateById(id: string): LayoutTemplate | undefined {
  for (const templates of Object.values(layoutTemplatesByMode)) {
    const template = templates.find(t => t.id === id)
    if (template) return template
  }
  return undefined
}

/**
 * Get templates for display mode
 */
export function getTemplatesByMode(mode: LayoutMode): LayoutTemplate[] {
  return layoutTemplatesByMode[mode] || []
}

/**
 * Get default template for display mode
 */
export function getDefaultTemplate(mode: LayoutMode): LayoutTemplate {
  const templates = getTemplatesByMode(mode)
  return templates[0] || {
    id: `default_${mode}`,
    name: 'Default Template',
    description: 'Default layout template',
    mode,
    config: { sections: [] }
  }
}

/**
 * Legacy type compatibility - maps old layout types to new modes
 * @deprecated Use LayoutMode directly
 */
export function legacyTypeToMode(layoutType: string): LayoutMode {
  const mapping: Record<string, LayoutMode> = {
    'form': 'edit',
    'detail': 'readonly',
    'search': 'search',
    'list': 'edit' // List layouts are auto-generated, map to edit for compatibility
  }
  return mapping[layoutType] || 'edit'
}

/**
 * Export all templates for backward compatibility
 * @deprecated Use layoutTemplatesByMode instead
 */
export const layoutTemplates = {
  edit: layoutTemplatesByMode.edit,
  list: [], // List layouts are auto-generated from FieldDefinition
  detail: layoutTemplatesByMode.readonly,
  search: layoutTemplatesByMode.search
}
