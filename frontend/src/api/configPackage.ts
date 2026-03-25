/**
 * Configuration Package API Client
 * Provides functions for config package lifecycle management
 */

import request from '@/utils/request'

const BASE_URL = '/system/config-packages'

export interface ConfigPackage {
    id: string
    name: string
    version: string
    description?: string
    package_type: 'full' | 'partial' | 'diff'
    package_type_display?: string
    included_objects: string[]
    object_count?: number
    exported_by?: string
    exported_by_name?: string
    exported_at: string
    source_environment: string
    checksum: string
    is_valid: boolean
    validation_errors: string[]
}

export interface ConfigImportLog {
    id: string
    package: string
    package_name: string
    package_version: string
    imported_by?: string
    imported_by_name?: string
    imported_at: string
    target_environment: string
    import_strategy: 'merge' | 'replace' | 'skip'
    strategy_display?: string
    status: 'pending' | 'in_progress' | 'success' | 'partial' | 'failed' | 'rolled_back'
    status_display?: string
    import_result: Record<string, any>
    objects_created: number
    objects_updated: number
    objects_skipped: number
    objects_failed: number
    can_rollback: boolean
    rolled_back_at?: string
    error_message?: string
}

export interface ExportRequest {
    name: string
    version: string
    description?: string
    object_codes: string[]
    package_type?: 'full' | 'partial' | 'diff'
}

export interface ImportRequest {
    package_id?: string
    config_data?: Record<string, any>
    strategy?: 'merge' | 'replace' | 'skip'
    target_environment?: string
}

export interface DiffResult {
    items: Array<{
        object_code: string
        item_type: string
        item_key: string
        change_type: 'added' | 'modified' | 'deleted'
        old_value?: any
        new_value?: any
    }>
    summary: {
        added: number
        modified: number
        deleted: number
    }
}

/**
 * Composable for configuration package API
 */
export function useConfigPackageApi() {
    /**
     * Get all configuration packages
     */
    async function getPackages(params?: Record<string, any>): Promise<ConfigPackage[]> {
        const response = await request({
            url: `${BASE_URL}/`,
            method: 'get',
            params
        })
        return response.data?.results || response.data || []
    }

    /**
     * Get a single package by ID
     */
    async function getPackageById(id: string): Promise<ConfigPackage> {
        const response = await request({
            url: `${BASE_URL}/${id}/`,
            method: 'get'
        })
        return response.data
    }

    /**
     * Export business objects to a new package
     */
    async function exportPackage(data: ExportRequest): Promise<{
        package: ConfigPackage
        summary: {
            objects: number
            fields: number
            layouts: number
            rules: number
        }
    }> {
        const response = await request({
            url: `${BASE_URL}/export/`,
            method: 'post',
            data
        })
        return response.data
    }

    /**
     * Import a configuration package
     */
    async function importPackage(data: ImportRequest): Promise<{
        success: boolean
        import_log: ConfigImportLog
        summary: {
            created: number
            updated: number
            skipped: number
            failed: number
        }
        errors: string[]
    }> {
        const response = await request({
            url: `${BASE_URL}/import/`,
            method: 'post',
            data
        })
        return response.data
    }

    /**
     * Download package as JSON file
     */
    async function downloadPackage(id: string): Promise<void> {
        const response = await request({
            url: `${BASE_URL}/${id}/download/`,
            method: 'get',
            responseType: 'blob'
        })

        // Create download link
        const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `config_package_${id}.json`
        link.click()
        window.URL.revokeObjectURL(url)
    }

    /**
     * Compare two packages
     */
    async function diffPackages(packageId: string, compareWithId: string): Promise<DiffResult> {
        const response = await request({
            url: `${BASE_URL}/${packageId}/diff/`,
            method: 'post',
            data: { compare_with: compareWithId }
        })
        return response.data
    }

    /**
     * Delete a package
     */
    async function deletePackage(id: string): Promise<void> {
        await request({
            url: `${BASE_URL}/${id}/`,
            method: 'delete'
        })
    }

    /**
     * Get import log history
     */
    async function getImportLogs(params?: Record<string, any>): Promise<ConfigImportLog[]> {
        const response = await request({
            url: '/system/config-imports/',
            method: 'get',
            params
        })
        return response.data?.results || response.data || []
    }

    /**
     * Rollback an import
     */
    async function rollbackImport(importLogId: string): Promise<{ success: boolean; message: string }> {
        const response = await request({
            url: `/system/config-imports/${importLogId}/rollback/`,
            method: 'post'
        })
        return response.data
    }

    return {
        getPackages,
        getPackageById,
        exportPackage,
        importPackage,
        downloadPackage,
        diffPackages,
        deletePackage,
        getImportLogs,
        rollbackImport
    }
}

export default useConfigPackageApi
