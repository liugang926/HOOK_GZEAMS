import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getDepartments } from '@/api/system'
import { withSWR } from '@/utils/cacheWrapper'

export const useOrgStore = defineStore('org', () => {
    const departments = ref<any[]>([])
    const loading = ref(false)

    const fetchDepartments = async () => {
        loading.value = true
        try {
            const data = await withSWR(
                'departments_all',
                async () => {
                    const res = await getDepartments()
                    return res.results || res.items || res
                },
                { staleTime: 1000 * 60 * 30, persist: true } // Cache for 30 minutes
            )
            departments.value = data
        } catch (e) {
            console.error(e)
        } finally {
            loading.value = false
        }
    }

    return {
        departments,
        loading,
        fetchDepartments
    }
})
