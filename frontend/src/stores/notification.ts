import { defineStore } from 'pinia'
import { ref } from 'vue'
import { workflowNodeApi } from '@/api/workflow'

export const useNotificationStore = defineStore('notification', () => {
    const count = ref(0)
    const recentTasks = ref<any[]>([])
    const loading = ref(false)
    let timer: ReturnType<typeof setInterval> | null = null

    const fetchCount = async () => {
        try {
            // For MVP, we use getMyTasks count as notification count
            // A dedicated /notifications/count endpoint would be better in future
            const res = await workflowNodeApi.getMyTasks({ page: 1, pageSize: 5, status: 'pending' })
            count.value = res.count
            recentTasks.value = res.results
        } catch (error) {
            console.error('Failed to fetch notifications', error)
        }
    }

    const startPolling = () => {
        fetchCount()
        if (!timer) {
            timer = setInterval(fetchCount, 60000) // Poll every 1 min
        }
    }

    const stopPolling = () => {
        if (timer) {
            clearInterval(timer)
            timer = null
        }
    }

    return {
        count,
        recentTasks,
        loading,
        fetchCount,
        startPolling,
        stopPolling
    }
})
