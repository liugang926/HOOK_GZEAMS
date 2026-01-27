import { ref } from 'vue'

export function useLoading(initValue = false) {
    const loading = ref(initValue)

    const withLoading = async (fn: () => Promise<any>) => {
        loading.value = true
        try {
            await fn()
        } finally {
            loading.value = false
        }
    }

    return { loading, withLoading }
}
