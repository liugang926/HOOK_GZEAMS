import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

type FormRecord = Record<string, unknown>

function resolveErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}

export interface UseFormPageOptions<TForm extends FormRecord = FormRecord> {
  fetchDetailMethod?: (id: string) => Promise<TForm>
  createMethod?: (data: TForm) => Promise<unknown>
  updateMethod?: (id: string, data: TForm) => Promise<unknown>
  redirectPath?: string
  manualLoad?: boolean
  normalizeDetail?: (payload: unknown) => TForm
}

export function useFormPage<TForm extends FormRecord = FormRecord>(
  options: UseFormPageOptions<TForm> = {}
) {
  const {
    fetchDetailMethod,
    createMethod,
    updateMethod,
    redirectPath,
    manualLoad = false,
    normalizeDetail,
  } = options

  const route = useRoute()
  const router = useRouter()
  const { t } = useI18n()

  const loading = ref(false)
  const submitting = ref(false)
  const form = ref<TForm>({} as TForm)
  const isEdit = computed(() => Boolean(route.params.id))
  const id = computed(() => String(route.params.id || ''))

  const getDetail = async () => {
    if (!fetchDetailMethod || !isEdit.value || !id.value) return

    loading.value = true
    try {
      const payload = await fetchDetailMethod(id.value)
      form.value = normalizeDetail ? normalizeDetail(payload) : payload
    } catch (error) {
      console.error('Failed to load detail:', error)
      ElMessage.error(t('common.messages.loadFailed'))
    } finally {
      loading.value = false
    }
  }

  const handleSubmit = async (data: TForm) => {
    submitting.value = true
    try {
      if (isEdit.value) {
        if (!updateMethod) throw new Error('Update method not provided')
        await updateMethod(id.value, data)
        ElMessage.success(t('common.messages.updateSuccess'))
      } else {
        if (!createMethod) throw new Error('Create method not provided')
        await createMethod(data)
        ElMessage.success(t('common.messages.createSuccess'))
      }

      handleBack()
    } catch (error: unknown) {
      console.error(error)
      ElMessage.error(resolveErrorMessage(error, t('common.messages.operationFailed')))
    } finally {
      submitting.value = false
    }
  }

  const handleBack = () => {
    if (redirectPath) {
      router.push(redirectPath)
      return
    }
    router.back()
  }

  onMounted(() => {
    if (!manualLoad && isEdit.value) {
      void getDetail()
    }
  })

  return {
    loading,
    submitting,
    form,
    isEdit,
    id,
    getDetail,
    handleSubmit,
    handleBack,
  }
}
