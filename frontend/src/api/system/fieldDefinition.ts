import type { LayoutMode } from '@/types/layout'

// =============================================================================
// Field Definition & Layout Types
// =============================================================================

/**
 * Field definition metadata
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface FieldDefinition {
    id: string
    code: string
    name: string
    fieldType: string
    isRequired: boolean
    isReadonly: boolean
    isUnique: boolean
    defaultValue?: any
    referenceObject?: string
    referenceDisplayField?: string
    options?: Array<{ label: string; value: string }>
    componentProps?: Record<string, any>
    helpText?: string
    label?: string
    span?: number
    sortOrder?: number
    description?: string
    showInForm?: boolean
    showInList?: boolean
    showInDetail?: boolean
    isHidden?: boolean
    readonly?: boolean
}

/**
 * Available field for layout designer
 * Extends FieldDefinition with UI-specific properties
 * Used in useLayoutFields composable
 */
export interface AvailableField extends FieldDefinition {
    fieldTypeDisplay?: string
    showInForm?: boolean
    showInList?: boolean
    showInDetail?: boolean
    isHidden?: boolean
    relationDisplayMode?: 'inline' | 'tab' | 'dialog'
    width?: string
    visible?: boolean
}

/**
 * Field group for organizing fields in designer UI
 * Used in useLayoutFields composable for categorization
 */
export interface FieldGroup {
    type: string
    label: string
    icon: string
    fields: AvailableField[]
}

/**
 * Page layout configuration
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface PageLayout {
    id: string
    layoutCode: string
    layoutName: string
    /** @deprecated Use mode instead */
    layoutType?: 'form' | 'list' | 'detail' | 'search'
    layoutTypeDisplay?: string
    /** Layout display mode - determines how fields are rendered */
    mode?: LayoutMode
    description?: string
    layoutConfig: {
        sections?: Array<{
            id: string
            type?: string
            title?: string
            fields?: Array<{
                id: string
                fieldCode: string
                label: string
                span: number
                readonly?: boolean
                visible?: boolean
                required?: boolean
            }>
            columns?: number
            collapsible?: boolean
            collapsed?: boolean
        }>
        columns?: Array<{
            fieldCode: string
            label: string
            width?: number
            fixed?: string
            sortable?: boolean
        }>
        actions?: Array<{
            code: string
            label: string
            type: string
            position: string
        }>
    }
    status: 'draft' | 'published' | 'archived'
    statusDisplay?: string
    version: string
    parentVersion?: string
    isDefault: boolean
    isActive: boolean
    isSystem?: boolean
    publishedAt?: string
    publishedBy?: string
    publishedByInfo?: {
        id: string
        username: string
    }
    businessObject?: string
    businessObjectName?: string
    historyCount?: number
}

/**
 * Layout version history
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface LayoutHistory {
    id: string
    layout: string
    version: string
    configSnapshot: any
    action: 'publish' | 'update' | 'rollback'
    actionDisplay?: string
    changeSummary?: string
    publishedBy?: string
    publishedByInfo?: {
        id: string
        username: string
    }
    createdAt: string
}
