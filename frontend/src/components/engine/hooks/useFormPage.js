import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

/**
 * useFormPage Hook
 * 
 * Provides common logic for form pages:
 * - Detail data loading (for edit mode)
 * - Form submission
 * - Routing handling (get ID, go back)
 * 
 * @param {Object} options Configuration options
 * @param {Function} options.fetchDetailMethod API method to fetch detail
 * @param {Function} options.createMethod API method to create
 * @param {Function} options.updateMethod API method to update
 * @param {string} options.redirectPath Path to redirect after success (default: back)
 * @param {boolean} options.manualLoad If true, data won't be loaded on mount
 */
export function useFormPage(options = {}) {
    const {
        fetchDetailMethod,
        createMethod,
        updateMethod,
        redirectPath,
        manualLoad = false
    } = options

    // ============================================================================
    // State
    // ============================================================================

    const route = useRoute()
    const router = useRouter()

    const loading = ref(false)
    const submitting = ref(false)
    const form = ref({})
    const isEdit = computed(() => !!route.params.id)
    const id = computed(() => route.params.id)

    // ============================================================================
    // Actions
    // ============================================================================

    /**
     * Get detail data
     */
    const getDetail = async () => {
        if (!fetchDetailMethod || !isEdit.value) return

        loading.value = true
        try {
            const data = await fetchDetailMethod(route.params.id)
            form.value = data
        } catch (error) {
            console.error('Failed to load detail:', error)
            ElMessage.error('获取详情失败')
        } finally {
            loading.value = false
        }
    }

    /**
     * Handle submit
     * @param {Object} data Form data to submit
     */
    const handleSubmit = async (data) => {
        submitting.value = true
        try {
            if (isEdit.value) {
                if (!updateMethod) throw new Error('Update method not provided')
                await updateMethod(route.params.id, data)
                ElMessage.success('更新成功')
            } else {
                if (!createMethod) throw new Error('Create method not provided')
                await createMethod(data)
                ElMessage.success('创建成功')
            }

            handleBack()
        } catch (error) {
            console.error(error)
            ElMessage.error(error.message || '操作失败')
        } finally {
            submitting.value = false
        }
    }

    /**
     * Handle back navigation
     */
    const handleBack = () => {
        if (redirectPath) {
            router.push(redirectPath)
        } else {
            router.back()
        }
    }

    // ============================================================================
    // Lifecycle
    // ============================================================================

    onMounted(() => {
        if (!manualLoad && isEdit.value) {
            getDetail()
        }
    })

    // ============================================================================
    // Return
    // ============================================================================

    return {
        loading,
        submitting,
        form,
        isEdit,
        id,
        getDetail,
        handleSubmit,
        handleBack
    }
}
