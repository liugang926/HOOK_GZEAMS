import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'

type ListItemRecord = Record<string, unknown>
type ListQueryRecord = Record<string, unknown>

function resolveErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}

function resolveItemId(item: unknown): string {
  if (!item || typeof item !== 'object') return ''
  const value = (item as Record<string, unknown>).id
  return value == null ? '' : String(value)
}

export interface UseListPageOptions<TItem = ListItemRecord, TQuery extends ListQueryRecord = ListQueryRecord> {
  fetchMethod?: (query: TQuery) => Promise<{ items?: TItem[]; total?: number }>
  deleteMethod?: (id: string) => Promise<unknown>
  batchDeleteMethod?: (ids: string[]) => Promise<unknown>
  defaultFilter?: Partial<TQuery>
  manualLoad?: boolean
}

export function useListPage<TItem = ListItemRecord, TQuery extends ListQueryRecord = ListQueryRecord>(
  options: UseListPageOptions<TItem, TQuery> = {}
) {
  const {
    fetchMethod,
    deleteMethod,
    batchDeleteMethod,
    defaultFilter = {},
    manualLoad = false,
  } = options

  const { t } = useI18n()
  const loading = ref(false)
  const list = ref<TItem[]>([])
  const total = ref(0)
  const selection = ref<TItem[]>([])

  const query = reactive({
    page: 1,
    size: 20,
    ...defaultFilter,
  }) as TQuery & { page: number; size: number }

  const getList = async () => {
    if (!fetchMethod) return

    loading.value = true
    try {
      const result = await fetchMethod(query)
      list.value = result?.items || []
      total.value = Number(result?.total || 0)
    } catch (error) {
      console.error('Failed to load list:', error)
      ElMessage.error(t('common.messages.loadFailed'))
    } finally {
      loading.value = false
    }
  }

  const handleQuery = () => {
    query.page = 1
    void getList()
  }

  const handleReset = () => {
    const mutableQuery = query as Record<string, unknown>
    for (const [key, value] of Object.entries(defaultFilter)) {
      mutableQuery[key] = value
    }
    query.page = 1
    void getList()
  }

  const handlePageChange = (page: number) => {
    query.page = page
    void getList()
  }

  const handleSizeChange = (size: number) => {
    query.size = size
    query.page = 1
    void getList()
  }

  const handleSelectionChange = (value: TItem[]) => {
    selection.value = value
  }

  const handleDelete = (id: string) => {
    if (!deleteMethod) return

    void ElMessageBox.confirm(
      t('common.messages.confirmDelete'),
      t('common.actions.confirm'),
      { type: 'warning' }
    ).then(async () => {
      loading.value = true
      try {
        await deleteMethod(id)
        ElMessage.success(t('common.messages.deleteSuccess'))
        if (list.value.length === 1 && query.page > 1) {
          query.page -= 1
        }
        await getList()
      } catch (error: unknown) {
        console.error(error)
        ElMessage.error(resolveErrorMessage(error, t('common.messages.deleteFailed')))
      } finally {
        loading.value = false
      }
    }).catch(() => undefined)
  }

  const handleBatchDelete = () => {
    if (!batchDeleteMethod) return
    if (selection.value.length === 0) {
      ElMessage.warning(t('common.messages.pleaseSelectData'))
      return
    }

    void ElMessageBox.confirm(
      t('common.messages.confirmDelete', { count: selection.value.length }),
      t('common.actions.confirm'),
      { type: 'warning' }
    ).then(async () => {
      loading.value = true
      try {
        const ids = selection.value
          .map((item) => resolveItemId(item))
          .filter(Boolean)
        await batchDeleteMethod(ids)
        ElMessage.success(t('common.messages.deleteSuccess'))
        selection.value = []
        await getList()
      } catch (error: unknown) {
        console.error(error)
        ElMessage.error(resolveErrorMessage(error, t('common.messages.deleteFailed')))
      } finally {
        loading.value = false
      }
    }).catch(() => undefined)
  }

  onMounted(() => {
    if (!manualLoad) {
      void getList()
    }
  })

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
    handleBatchDelete,
  }
}
