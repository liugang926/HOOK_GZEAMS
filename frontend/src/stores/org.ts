import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getDepartments } from '@/api/system'

export const useOrgStore = defineStore('org', () => {
    const departments = ref<any[]>([])
    const loading = ref(false)

    const fetchDepartments = async () => {
        if (departments.value.length > 0) return

        loading.value = true
        try {
            const res = await getDepartments()
            departments.value = res.results || res.items || res
        } catch (e) {
            console.error(e)
        } finally {
            loading.value = false
        }
    }

    return {
        departments,
        fetchDepartments
    }
})
