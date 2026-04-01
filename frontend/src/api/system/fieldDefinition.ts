import type { LayoutMode } from '@/types/layout'
import request from '@/utils/request'

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
    isEditable?: boolean
    relationDisplayMode?: 'inline' | 'tab' | 'dialog'
    relatedObject?: string
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
    layout_code?: string
    layoutName: string
    layout_name?: string
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
        workbench?: Record<string, unknown>
    }
    status: 'draft' | 'published' | 'archived'
    statusDisplay?: string
    version: string
    parentVersion?: string
    isDefault: boolean
    is_default?: boolean
    isActive: boolean
    is_active?: boolean
    isSystem?: boolean
    is_system?: boolean
    publishedAt?: string
    publishedBy?: string
    publishedByInfo?: {
        id: string
        username: string
    }
    businessObject?: string
    business_object?: string
    businessObjectName?: string
    business_object_name?: string
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
// =============================================================================
// Field Definition API
// =============================================================================

export interface FieldDefinitionPayload {
    businessObject?: string
    code?: string
    name?: string
    fieldType?: string
    isRequired?: boolean
    isUnique?: boolean
    isReadonly?: boolean
    isSearchable?: boolean
    showInList?: boolean
    showInDetail?: boolean
    showInFilter?: boolean
    showInForm?: boolean
    sortOrder?: number
    defaultValue?: any
    options?: Array<{ label: string; value: string; color?: string }>
    referenceObject?: string
    referenceDisplayField?: string
    decimalPlaces?: number
    minValue?: number | null
    maxValue?: number | null
    maxLength?: number
    placeholder?: string
    formula?: string
    description?: string
}

export const fieldDefinitionApi = {
    list(params?: Record<string, any>) {
        return request({
            url: '/system/field-definitions/',
            method: 'get',
            params
        })
    },

    byObject(objectCode: string) {
        return request({
            url: `/system/field-definitions/by-object/${objectCode}/`,
            method: 'get'
        })
    },

    detail(id: string) {
        return request({
            url: `/system/field-definitions/${id}/`,
            method: 'get'
        })
    },

    create(data: FieldDefinitionPayload) {
        return request({
            url: '/system/field-definitions/',
            method: 'post',
            data
        })
    },

    update(id: string, data: FieldDefinitionPayload) {
        return request({
            url: `/system/field-definitions/${id}/`,
            method: 'put',
            data
        })
    },

    partialUpdate(id: string, data: FieldDefinitionPayload) {
        return request({
            url: `/system/field-definitions/${id}/`,
            method: 'patch',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/system/field-definitions/${id}/`,
            method: 'delete'
        })
    }
}
