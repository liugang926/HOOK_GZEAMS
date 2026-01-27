import { defineStore } from 'pinia'
import { ref } from 'vue'
// import { getWorkflows } from '@/api/workflow'

export const useWorkflowStore = defineStore('workflow', () => {
    const workflows = ref<any[]>([])
    const loading = ref(false)

    const fetchWorkflows = async () => {
        loading.value = true
        try {
            // TODO: specific API call
            // const res = await getWorkflows()
            // workflows.value = res.items
        } finally {
            loading.value = false
        }
    }

    return {
        workflows,
        loading,
        fetchWorkflows
    }
})
