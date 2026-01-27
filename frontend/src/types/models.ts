export interface FormField {
    prop: string
    label: string
    type: 'input' | 'select' | 'date' | 'number' | 'switch' | 'textarea' | 'tree-select' | 'slot' | 'divider'
    placeholder?: string
    rules?: any[]
    options?: Array<{ label: string; value: any }>
    defaultValue?: any
    width?: string | number
    span?: number // For grid layout (24 cols)
    disabled?: boolean
    required?: boolean
    visible?: boolean
    props?: Record<string, any> // Additional props
}

export interface FormSchema {
    fields: FormField[]
    labelWidth?: string
    gutter?: number
}

// ... existing types
export interface StatusOption {
    value: string | number
    label: string
    type?: 'success' | 'warning' | 'danger' | 'info' | 'primary'
}

export interface CrudOptions {
    api: {
        list: (params?: any) => Promise<any>
        get?: (id: string | number) => Promise<any>
        create?: (data: any) => Promise<any>
        update?: (id: string | number, data: any) => Promise<any>
        delete?: (id: string | number) => Promise<any>
        batchDelete?: (ids: (string | number)[]) => Promise<any>
        export?: (params?: any) => Promise<any>
    }
    name: string
    listTitle?: string
}
