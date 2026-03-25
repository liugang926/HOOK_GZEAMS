import { defineStore } from 'pinia'
import { ref } from 'vue'
import { withSWR } from '@/utils/cacheWrapper'

export const useDictStore = defineStore('dict', () => {
    const dicts = ref<Record<string, any[]>>({})

    const getDict = async (code: string) => {
        const data = await withSWR(
            `dict_${code}`,
            async () => {
                // TODO: Replace with real API call
                // const res = await getDictionary(code)
                // return res
                return [] // Mock
            },
            { staleTime: 1000 * 60 * 60, persist: true } // Cache for 1 hour
        )
        dicts.value[code] = data
        return data
    }

    return {
        dicts,
        getDict
    }
})
