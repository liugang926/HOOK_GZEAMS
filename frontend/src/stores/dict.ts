import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDictStore = defineStore('dict', () => {
    const dicts = ref<Record<string, any[]>>({})

    const getDict = async (code: string) => {
        if (dicts.value[code]) return dicts.value[code]

        // TODO: Call API
        // const res = await getDictionary(code)
        // dicts.value[code] = res

        // Mock
        return []
    }

    return {
        dicts,
        getDict
    }
})
