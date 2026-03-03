import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * useListPage Hook
 * 
 * Provides common logic for list pages:
 * - Data loading with pagination
 * - Searching/Filtering
 * - Selection management
 * - Delete/Batch delete operations
 * 
 * @param {Object} options Configuration options
 * @param {Function} options.fetchMethod API method to fetch list data (must return { items: [], total: 0 })
 * @param {Function} options.deleteMethod API method to delete single item
 * @param {Function} options.batchDeleteMethod API method to batch delete items
 * @param {Object} options.defaultFilter Default filter values
 * @param {boolean} options.manualLoad If true, data won't be loaded on mount
 */
export function useListPage(options = {}) {
    const {
        fetchMethod,
        deleteMethod,
        batchDeleteMethod,
        defaultFilter = {},
        manualLoad = false
    } = options

    // ============================================================================
    // State
    // ============================================================================

    const loading = ref(false)
    const { t } = useI18n()
    const list = ref([])
    const total = ref(0)
    const selection = ref([])

    const query = reactive({
        page: 1,
        size: 20,
        ...defaultFilter
    })

    // ============================================================================
    // Actions
    // ============================================================================

    /**
     * Fetch data
     */
    const getList = async () => {
        if (!fetchMethod) return

        loading.value = true
        try {
            const { items, total: totalCount } = await fetchMethod(query)
            list.value = items || []
            total.value = totalCount || 0
        } catch (error) {
            console.error('Failed to load list:', error)
            ElMessage.error(t('common.messages.loadFailed'))
        } finally {
            loading.value = false
        }
    }

    /**
     * Handle search/filter
     */
    const handleQuery = () => {
        query.page = 1
        getList()
    }

    /**
     * Handle reset
     */
    const handleReset = () => {
        // Reset query to defaults (except page/size if desired, but usually reset all)
        Object.keys(defaultFilter).forEach(key => {
            query[key] = defaultFilter[key]
        })
        // Also reset other keys in query if they were added dynamically? 
        // For simplicity, we just reset page and reload. 
        // Ideally query is a ref to a fresh object or we manually clear.
        // Here we assume query structure tracks fields.
        query.page = 1
        getList()
    }

    /**
     * Handle page change
     */
    const handlePageChange = (page) => {
        query.page = page
        getList()
    }

    /**
     * Handle size change
     */
    const handleSizeChange = (size) => {
        query.size = size
        query.page = 1 // Reset to first page
        getList()
    }

    /**
     * Handle selection change
     */
    const handleSelectionChange = (val) => {
        selection.value = val
    }

    /**
     * Handle single deletion
     */
    const handleDelete = (id) => {
        if (!deleteMethod) return

        ElMessageBox.confirm(t('common.messages.confirmDelete'), t('common.actions.confirm'), {
            type: 'warning'
        }).then(async () => {
            loading.value = true
            try {
                await deleteMethod(id)
                ElMessage.success(t('common.messages.deleteSuccess'))
                // Refresh list
                if (list.value.length === 1 && query.page > 1) {
                    query.page--
                }
                getList()
            } catch (error) {
                console.error(error)
                ElMessage.error(error.message || t('common.messages.deleteFailed'))
            } finally {
                loading.value = false
            }
        }).catch(() => { })
    }

    /**
     * Handle batch deletion
     */
    const handleBatchDelete = () => {
        if (!batchDeleteMethod) return
        if (selection.value.length === 0) {
            ElMessage.warning(t('common.messages.pleaseSelectData'))
            return
        }

        ElMessageBox.confirm(
            t('common.messages.confirmDelete', { count: selection.value.length }),
            t('common.actions.confirm'),
            {
            type: 'warning'
            }
        ).then(async () => {
            loading.value = true
            try {
                const ids = selection.value.map(item => item.id)
                await batchDeleteMethod(ids)
                ElMessage.success(t('common.messages.deleteSuccess'))
                selection.value = [] // Clear selection
                getList()
            } catch (error) {
                console.error(error)
                ElMessage.error(error.message || t('common.messages.deleteFailed'))
            } finally {
                loading.value = false
            }
        }).catch(() => { })
    }

    // ============================================================================
    // Lifecycle
    // ============================================================================

    onMounted(() => {
        if (!manualLoad) {
            getList()
        }
    })

    // ============================================================================
    // Return
    // ============================================================================

    return {
        loading,
        list,
        total,
        query,
        selection,
        getList,
        handleQuery,
        handleReset,
        handlePageChange,
        handleSizeChange,
        handleSelectionChange,
        handleDelete,
        handleBatchDelete
    }
}
