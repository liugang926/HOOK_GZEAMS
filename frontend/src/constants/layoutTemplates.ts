/**
 * Default Layout Templates
 *
 * Provides pre-configured layout templates for common business scenarios.
 * These templates serve as starting points for layout customization.
 */

import type { LayoutType } from '@/utils/layoutValidation'

export interface LayoutTemplate {
  id: string
  name: string
  description: string
  layoutType: LayoutType
  preview?: string
  config: Record<string, unknown>
}

/**
 * Asset form template - comprehensive asset creation/editing form
 */
export const assetFormTemplate: LayoutTemplate = {
  id: 'asset_form_default',
  name: 'Asset Form Template',
  description: 'Standard asset creation and editing form with categorized sections',
  layoutType: 'form',
  config: {
    sections: [
      {
        id: 'section-basic',
        type: 'section',
        title: 'Basic Information',
        collapsible: true,
        collapsed: false,
        columns: 2,
        border: true,
        fields: [
          { id: 'field-code', field_code: 'code', label: 'Asset Code', span: 12, required: true },
          { id: 'field-name', field_code: 'name', label: 'Asset Name', span: 12, required: true },
          { id: 'field-category', field_code: 'category', label: 'Category', span: 12 },
          { id: 'field-status', field_code: 'status', label: 'Status', span: 12 }
        ]
      },
      {
        id: 'section-detail',
        type: 'section',
        title: 'Detailed Information',
        collapsible: true,
        collapsed: true,
        columns: 2,
        border: true,
        fields: [
          { id: 'field-model', field_code: 'model', label: 'Model', span: 12 },
          { id: 'field-brand', field_code: 'brand', label: 'Brand', span: 12 },
          { id: 'field-purchase-date', field_code: 'purchase_date', label: 'Purchase Date', span: 12 },
          { id: 'field-purchase-price', field_code: 'purchase_price', label: 'Purchase Price', span: 12 }
        ]
      },
      {
        id: 'section-location',
        type: 'section',
        title: 'Location & Assignment',
        collapsible: true,
        collapsed: true,
        columns: 2,
        border: true,
        fields: [
          { id: 'field-department', field_code: 'department', label: 'Department', span: 12 },
          { id: 'field-custodian', field_code: 'custodian', label: 'Custodian', span: 12 },
          { id: 'field-location', field_code: 'location', label: 'Storage Location', span: 12 },
          { id: 'field-area', field_code: 'area', label: 'Area', span: 12 }
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
 * Asset list template - standard asset list view
 */
export const assetListTemplate: LayoutTemplate = {
  id: 'asset_list_default',
  name: 'Asset List Template',
  description: 'Standard asset list with filtering and batch operations',
  layoutType: 'list',
  config: {
    columns: [
      { field_code: 'code', label: 'Asset Code', width: 120, fixed: 'left', sortable: true },
      { field_code: 'name', label: 'Asset Name', width: 200, sortable: true },
      { field_code: 'category', label: 'Category', width: 120 },
      { field_code: 'status', label: 'Status', width: 100 },
      { field_code: 'department', label: 'Department', width: 150 },
      { field_code: 'custodian', label: 'Custodian', width: 120 },
      { field_code: 'purchase_date', label: 'Purchase Date', width: 120 },
      { field_code: 'purchase_price', label: 'Purchase Price', width: 120 }
    ],
    actions: [
      { code: 'create', label: 'New Asset', type: 'primary', position: 'top-right' },
      { code: 'import', label: 'Import', type: 'default', position: 'top-right' },
      { code: 'export', label: 'Export', type: 'default', position: 'top-right' },
      { code: 'batch-delete', label: 'Batch Delete', type: 'danger', position: 'toolbar' }
    ],
    page_size: 20,
    show_pagination: true
  }
}

/**
 * Asset detail template - comprehensive asset detail view
 */
export const assetDetailTemplate: LayoutTemplate = {
  id: 'asset_detail_default',
  name: 'Asset Detail Template',
  description: 'Asset detail view with all information organized in tabs',
  layoutType: 'detail',
  config: {
    sections: [
      {
        id: 'section-tabs',
        type: 'tab',
        tabs: [
          {
            id: 'tab-basic',
            title: 'Basic Info',
            fields: [
              { id: 'field-code', field_code: 'code', label: 'Asset Code', span: 12, readonly: true },
              { id: 'field-name', field_code: 'name', label: 'Asset Name', span: 12 },
              { id: 'field-category', field_code: 'category', label: 'Category', span: 12 },
              { id: 'field-status', field_code: 'status', label: 'Status', span: 12 }
            ]
          },
          {
            id: 'tab-financial',
            title: 'Financial',
            fields: [
              { id: 'field-purchase-price', field_code: 'purchase_price', label: 'Purchase Price', span: 12 },
              { id: 'field-purchase-date', field_code: 'purchase_date', label: 'Purchase Date', span: 12 },
              { id: 'field-depreciation', field_code: 'depreciation', label: 'Depreciation', span: 12 },
              { id: 'field-net-value', field_code: 'net_value', label: 'Net Value', span: 12 }
            ]
          },
          {
            id: 'tab-location',
            title: 'Location',
            fields: [
              { id: 'field-department', field_code: 'department', label: 'Department', span: 12 },
              { id: 'field-custodian', field_code: 'custodian', label: 'Custodian', span: 12 },
              { id: 'field-location', field_code: 'location', label: 'Storage Location', span: 12 },
              { id: 'field-area', field_code: 'area', label: 'Area', span: 12 }
            ]
          },
          {
            id: 'tab-audit',
            title: 'Audit Trail',
            fields: [
              { id: 'field-created-by', field_code: 'created_by', label: 'Created By', span: 12, readonly: true },
              { id: 'field-created-at', field_code: 'created_at', label: 'Created At', span: 12, readonly: true },
              { id: 'field-updated-by', field_code: 'updated_by', label: 'Updated By', span: 12, readonly: true },
              { id: 'field-updated-at', field_code: 'updated_at', label: 'Updated At', span: 12, readonly: true }
            ]
          }
        ]
      }
    ]
  }
}

/**
 * Simple form template - minimal form layout
 */
export const simpleFormTemplate: LayoutTemplate = {
  id: 'simple_form_default',
  name: 'Simple Form Template',
  description: 'Minimal single-column form layout',
  layoutType: 'form',
  config: {
    sections: [
      {
        id: 'section-main',
        type: 'section',
        title: 'Information',
        collapsible: false,
        columns: 1,
        border: false,
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
 * Simple list template - minimal list layout
 */
export const simpleListTemplate: LayoutTemplate = {
  id: 'simple_list_default',
  name: 'Simple List Template',
  description: 'Minimal list layout with basic columns',
  layoutType: 'list',
  config: {
    columns: [],
    actions: [
      { code: 'create', label: 'New', type: 'primary', position: 'top-right' }
    ],
    page_size: 20,
    show_pagination: true
  }
}

/**
 * Search form template - for filter/search forms
 */
export const searchFormTemplate: LayoutTemplate = {
  id: 'search_form_default',
  name: 'Search Form Template',
  description: 'Horizontal search form layout',
  layoutType: 'search',
  config: {
    fields: [],
    layout: 'horizontal',
    label_width: '100px'
  }
}

/**
 * Two-column form template - side-by-side fields
 */
export const twoColumnFormTemplate: LayoutTemplate = {
  id: 'two_column_form_default',
  name: 'Two-Column Form Template',
  description: 'Form with two-column field layout',
  layoutType: 'form',
  config: {
    sections: [
      {
        id: 'section-main',
        type: 'section',
        title: 'Information',
        collapsible: true,
        collapsed: false,
        columns: 2,
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
 * Accordion form template - collapsible sections
 */
export const accordionFormTemplate: LayoutTemplate = {
  id: 'accordion_form_default',
  name: 'Accordion Form Template',
  description: 'Form with collapsible accordion sections',
  layoutType: 'form',
  config: {
    sections: [
      {
        id: 'section-accordion',
        type: 'collapse',
        items: [
          {
            id: 'collapse-1',
            title: 'Section 1',
            fields: []
          },
          {
            id: 'collapse-2',
            title: 'Section 2',
            fields: []
          }
        ]
      }
    ],
    actions: [
      { code: 'submit', label: 'Save', type: 'primary', position: 'bottom-right' },
      { code: 'cancel', label: 'Cancel', type: 'default', position: 'bottom-right' }
    ]
  }
}

/**
 * All available templates
 */
export const layoutTemplates: Record<string, LayoutTemplate[]> = {
  form: [assetFormTemplate, simpleFormTemplate, twoColumnFormTemplate, accordionFormTemplate],
  list: [assetListTemplate, simpleListTemplate],
  detail: [assetDetailTemplate],
  search: [searchFormTemplate]
}

/**
 * Get template by ID
 */
export function getTemplateById(id: string): LayoutTemplate | undefined {
  for (const templates of Object.values(layoutTemplates)) {
    const template = templates.find(t => t.id === id)
    if (template) return template
  }
  return undefined
}

/**
 * Get templates for layout type
 */
export function getTemplatesByType(layoutType: LayoutType): LayoutTemplate[] {
  return layoutTemplates[layoutType] || []
}

/**
 * Get default template for layout type
 */
export function getDefaultTemplate(layoutType: LayoutType): LayoutTemplate {
  const templates = getTemplatesByType(layoutType)
  return templates[0] || {
    id: `default_${layoutType}`,
    name: 'Default Template',
    description: 'Default layout template',
    layoutType,
    config: {}
  }
}
