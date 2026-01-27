import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { CrudOptions } from '@/types/models'

export function useCrud(options: CrudOptions) {
    const loading = ref(false)
    const listData = ref<any[]>([])
    const total = ref(0)

    // List
    const fetchList = async (params: any = {}) => {
        loading.value = true
        try {
            const res = await options.api.list(params)
            if (res.results) {
                listData.value = res.results
                total.value = res.count || 0
            } else if (Array.isArray(res)) {
                listData.value = res
                total.value = res.length
            }
        } catch (error) {
            console.error(`Failed to fetch ${options.name} list:`, error)
        } finally {
            loading.value = false
        }
    }

    // Delete
    const handleDelete = async (row: any) => {
        if (!options.api.delete) return

        try {
            await ElMessageBox.confirm(
                `Confirm to delete ${options.name} "${row.name || row.code || ''}"?`,
                'Confirm Delete',
                {
                    type: 'warning',
                    confirmButtonText: 'Confirm',
                    cancelButtonText: 'Cancel'
                }
            )

            await options.api.delete(row.id)
            ElMessage.success('Delete successful')
            // Recommend caller to refresh list
            return true
        } catch (error: any) {
            if (error !== 'cancel') {
                ElMessage.error('Delete failed')
                console.error(error)
            }
            return false
        }
    }

    // Batch Delete
    const handleBatchDelete = async (rows: any[]) => {
        if (!options.api.batchDelete || rows.length === 0) return

        try {
            await ElMessageBox.confirm(
                `Confirm to delete selected ${rows.length} items?`,
                'Confirm Batch Delete',
                {
                    type: 'warning',
                    confirmButtonText: 'Confirm',
                    cancelButtonText: 'Cancel'
                }
            )

            const ids = rows.map(r => r.id)
            await options.api.batchDelete(ids)
            ElMessage.success(`Successfully deleted ${rows.length} items`)
            return true
        } catch (error: any) {
            if (error !== 'cancel') {
                ElMessage.error('Batch delete failed')
                console.error(error)
            }
            return false
        }
    }

    // Export
    const handleExport = async (params: any = {}) => {
        if (!options.api.export) return

        try {
            const blob = await options.api.export(params)
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = `${options.name}_Export_${new Date().toLocaleDateString()}.xlsx`
            link.click()
            window.URL.revokeObjectURL(url)
            ElMessage.success('Export successful')
        } catch (error) {
            ElMessage.error('Export failed')
            console.error(error)
        }
    }

    // Batch Export
    const handleBatchExport = async (rows: any[]) => {
        if (!options.api.export || rows.length === 0) {
            ElMessage.warning('Please select items to export')
            return
        }

        try {
            const ids = rows.map(r => r.id)
            // Use generic 'ids' param. If API needs specific key, wrapper should handle it.
            await handleExport({ ids: ids })
        } catch (error) {
            // Error handled in handleExport
        }
    }

    return {
        loading,
        listData,
        total,
        fetchList,
        handleDelete,
        handleBatchDelete,
        handleExport,
        handleBatchExport
    }
}
