<template>
  <div
    v-loading="loading"
    class="module-workbench"
  >
    <div class="header-row">
      <div>
        <h2>{{ t('system.moduleWorkbench.title') }}</h2>
        <p>{{ t('system.moduleWorkbench.subtitle') }}</p>
      </div>
      <el-button
        type="primary"
        @click="loadData"
      >
        {{ t('common.actions.refresh') }}
      </el-button>
    </div>

    <el-row :gutter="12">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="metric-label">
            {{ t('system.moduleWorkbench.metrics.backendObjects') }}
          </div>
          <div class="metric-value">
            {{ allObjects.length }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="metric-label">
            {{ t('system.moduleWorkbench.metrics.menuCovered') }}
          </div>
          <div class="metric-value">
            {{ coveredObjects.length }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="metric-label">
            {{ t('system.moduleWorkbench.metrics.missingEntries') }}
          </div>
          <div class="metric-value warning">
            {{ missingObjects.length }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="metric-label">
            {{ t('system.moduleWorkbench.metrics.invalidMenuCodes') }}
          </div>
          <div class="metric-value danger">
            {{ orphanMenuCodes.length }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card
      class="section-card"
      shadow="never"
    >
      <template #header>
        <div class="card-header">
          <span>{{ t('system.moduleWorkbench.sections.missingFrontendEntries') }}</span>
          <el-tag
            v-if="missingObjects.length"
            type="warning"
          >
            {{ missingObjects.length }}
          </el-tag>
        </div>
      </template>

      <el-empty
        v-if="!missingObjects.length"
        :description="t('system.moduleWorkbench.empty.noMissingEntries')"
      />

      <el-table
        v-else
        :data="missingObjectsWithReadiness"
        stripe
      >
        <el-table-column
          prop="code"
          :label="t('system.moduleWorkbench.columns.objectCode')"
          min-width="180"
        />
        <el-table-column
          prop="name"
          :label="t('system.moduleWorkbench.columns.name')"
          min-width="180"
        >
          <template #default="{ row }">
            {{ getObjectDisplayName(row.code, row.name) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="djangoModelPath"
          :label="t('system.moduleWorkbench.columns.modelPath')"
          min-width="260"
          show-overflow-tooltip
        />
        <el-table-column
          :label="t('system.moduleWorkbench.columns.type')"
          width="120"
        >
          <template #default="{ row }">
            <el-tag :type="row.isHardcoded ? 'info' : 'success'">
              {{ row.isHardcoded ? t('system.moduleWorkbench.type.system') : t('system.moduleWorkbench.type.custom') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          :label="t('system.moduleWorkbench.columns.readiness')"
          width="180"
        >
          <template #default="{ row }">
            <el-tag
              v-if="row.readiness === 'ready'"
              type="success"
            >
              {{ t('system.moduleWorkbench.readiness.ready') }}
            </el-tag>
            <el-tag
              v-else-if="row.readiness === 'empty_fields'"
              type="warning"
            >
              {{ t('system.moduleWorkbench.readiness.emptyFields') }}
            </el-tag>
            <el-tag
              v-else-if="row.readiness === 'checking'"
              type="info"
            >
              {{ t('system.moduleWorkbench.readiness.checking') }}
            </el-tag>
            <el-tag
              v-else
              type="danger"
            >
              {{ t('system.moduleWorkbench.readiness.unavailable') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          :label="t('system.moduleWorkbench.columns.actions')"
          width="200"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              :disabled="row.readiness !== 'ready'"
              @click="openList(row.code)"
            >
              {{ t('system.moduleWorkbench.actions.list') }}
            </el-button>
            <el-button
              link
              type="primary"
              :disabled="row.readiness !== 'ready'"
              @click="openCreate(row.code)"
            >
              {{ t('common.actions.create') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card
      class="section-card"
      shadow="never"
    >
      <template #header>
        <div class="card-header">
          <span>{{ t('system.moduleWorkbench.sections.allObjects') }}</span>
          <el-input
            v-model="keyword"
            clearable
            class="search-input"
            :placeholder="t('system.moduleWorkbench.searchPlaceholder')"
          />
        </div>
      </template>

      <el-table
        :data="filteredAllObjects"
        stripe
      >
        <el-table-column
          prop="code"
          :label="t('system.moduleWorkbench.columns.objectCode')"
          min-width="180"
        />
        <el-table-column
          prop="name"
          :label="t('system.moduleWorkbench.columns.name')"
          min-width="180"
        >
          <template #default="{ row }">
            {{ getObjectDisplayName(row.code, row.name) }}
          </template>
        </el-table-column>
        <el-table-column
          :label="t('system.moduleWorkbench.columns.coverage')"
          width="120"
        >
          <template #default="{ row }">
            <el-tag :type="isCovered(row.code) ? 'success' : 'warning'">
              {{ isCovered(row.code) ? t('system.moduleWorkbench.coverage.covered') : t('system.moduleWorkbench.coverage.missing') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          :label="t('system.moduleWorkbench.columns.actions')"
          width="200"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="openList(row.code)"
            >
              {{ t('system.moduleWorkbench.actions.list') }}
            </el-button>
            <el-button
              link
              type="primary"
              @click="openCreate(row.code)"
            >
              {{ t('common.actions.create') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card
      class="section-card"
      shadow="never"
    >
      <template #header>
        <div class="card-header">
          <span>{{ t('system.moduleWorkbench.sections.invalidMenuObjectCodes') }}</span>
          <el-tag
            v-if="orphanMenuCodes.length"
            type="danger"
          >
            {{ orphanMenuCodes.length }}
          </el-tag>
        </div>
      </template>

      <el-empty
        v-if="!orphanMenuCodes.length"
        :description="t('system.moduleWorkbench.empty.noInvalidMenuCodes')"
      />

      <el-table
        v-else
        :data="orphanMenuRows"
        stripe
      >
        <el-table-column
          prop="code"
          :label="t('system.moduleWorkbench.columns.code')"
          min-width="200"
        />
        <el-table-column
          :label="t('system.moduleWorkbench.columns.menuName')"
          min-width="240"
        >
          <template #default="{ row }">
            {{ getMenuDisplayName(row) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="url"
          :label="t('system.moduleWorkbench.columns.url')"
          min-width="260"
          show-overflow-tooltip
        />
      </el-table>
    </el-card>

    <el-card
      class="section-card"
      shadow="never"
    >
      <template #header>
        <div class="card-header">
          <span>{{ t('system.moduleWorkbench.sections.brokenMenuUrls') }}</span>
          <el-tag
            v-if="brokenMenuRows.length"
            type="danger"
          >
            {{ brokenMenuRows.length }}
          </el-tag>
        </div>
      </template>

      <el-empty
        v-if="!brokenMenuRows.length"
        :description="t('system.moduleWorkbench.empty.noBrokenMenuUrls')"
      />

      <el-table
        v-else
        :data="brokenMenuRows"
        stripe
      >
        <el-table-column
          :label="t('system.moduleWorkbench.columns.menuName')"
          min-width="240"
        >
          <template #default="{ row }">
            {{ getMenuDisplayName(row) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="code"
          :label="t('system.moduleWorkbench.columns.code')"
          min-width="200"
        />
        <el-table-column
          prop="url"
          :label="t('system.moduleWorkbench.columns.url')"
          min-width="300"
          show-overflow-tooltip
        />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { dynamicApi } from '@/api/dynamic'
import { businessObjectApi, menuApi, type BusinessObject, type MenuItem } from '@/api/system'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'
import { filterSystemFields } from '@/utils/transform'

interface MenuCoverageItem extends MenuItem {
  code: string
  translationKey?: string
}

type ReadinessState = 'ready' | 'empty_fields' | 'unavailable' | 'checking'

type AnyRecord = Record<string, unknown>

const router = useRouter()
const { t, te } = useI18n()
const loading = ref(false)
const keyword = ref('')
const allObjects = ref<BusinessObject[]>([])
const menuItems = ref<MenuCoverageItem[]>([])
const readinessByCode = ref<Record<string, { readiness: ReadinessState; fieldCount: number; error?: string }>>({})

const unwrapPayload = (value: unknown): AnyRecord => {
  if (!value || typeof value !== 'object') return {}
  const raw = value as AnyRecord
  const data = raw.data
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    return data as AnyRecord
  }
  return raw
}

const normalizeObjects = (payload: AnyRecord): BusinessObject[] => {
  const source: AnyRecord[] = []
  if (Array.isArray(payload)) source.push(...payload)
  if (Array.isArray(payload?.results)) source.push(...payload.results)
  if (Array.isArray(payload?.hardcoded)) source.push(...payload.hardcoded)
  if (Array.isArray(payload?.custom)) source.push(...payload.custom)

  const normalized: BusinessObject[] = []
  const seen = new Set<string>()
  for (const item of source) {
    const code = String(item?.code || '').trim()
    if (!code || seen.has(code)) continue
    seen.add(code)
    normalized.push({
      id: String(item?.id || code),
      code,
      name: String(item?.name || code),
      nameEn: String(item?.nameEn || ''),
      description: String(item?.description || ''),
      enableWorkflow: item?.enableWorkflow === true,
      enableVersion: item?.enableVersion === true,
      enableSoftDelete: item?.enableSoftDelete !== false,
      isHardcoded: item?.isHardcoded === true || item?.type === 'hardcoded',
      djangoModelPath: String(item?.djangoModelPath || item?.modelPath || ''),
      tableName: String(item?.tableName || ''),
      fieldCount: Number(item?.fieldCount || 0),
      layoutCount: Number(item?.layoutCount || 0)
    })
  }
  return normalized.sort((a, b) => a.code.localeCompare(b.code))
}

const extractObjectCodeFromUrl = (url: string): string => {
  const value = String(url || '').trim()
  if (!value) return ''
  const match = value.match(/^\/objects\/([^/?#]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

const normalizeMenuItems = (payload: AnyRecord): MenuCoverageItem[] => {
  const items: AnyRecord[] = []
  if (Array.isArray(payload?.items)) items.push(...payload.items)
  if (Array.isArray(payload?.groups)) {
    payload.groups.forEach((group: AnyRecord) => {
      if (Array.isArray(group?.items)) items.push(...group.items)
    })
  }

  const normalized: MenuCoverageItem[] = []
  for (const item of items) {
    const url = String(item?.url || '').trim()
    const directCode = String(item?.code || '').trim()
    const code = directCode || extractObjectCodeFromUrl(url)
    if (!code) continue
    normalized.push({
      code,
      name: String(item?.name || code),
      nameEn: String(item?.nameEn || ''),
      url,
      icon: String(item?.icon || ''),
      order: Number(item?.order || 0),
      group: String(item?.group || ''),
      groupCode: String(item?.groupCode || ''),
      groupTranslationKey: String(item?.groupTranslationKey || ''),
      translationKey: String(item?.translationKey || ''),
      badge: item?.badge
    })
  }
  return normalized
}

const menuObjectCodes = computed(() => {
  return Array.from(new Set(menuItems.value.map((item) => item.code)))
})

const objectMenuItems = computed(() => {
  return menuItems.value.filter((item) => extractObjectCodeFromUrl(item.url))
})

const objectMenuCodes = computed(() => {
  return Array.from(new Set(objectMenuItems.value.map((item) => item.code)))
})

const allObjectCodeSet = computed(() => {
  return new Set(allObjects.value.map((item) => item.code))
})

const coveredObjects = computed(() => {
  const covered = new Set(menuObjectCodes.value)
  return allObjects.value.filter((item) => covered.has(item.code))
})

const missingObjects = computed(() => {
  const covered = new Set(menuObjectCodes.value)
  return allObjects.value.filter((item) => !covered.has(item.code))
})

const missingObjectsWithReadiness = computed(() => {
  return missingObjects.value.map((item) => {
    const readinessInfo = readinessByCode.value[item.code] || {
      readiness: 'checking' as ReadinessState,
      fieldCount: 0
    }
    return {
      ...item,
      ...readinessInfo
    }
  })
})

const orphanMenuCodes = computed(() => {
  const objectSet = allObjectCodeSet.value
  return objectMenuCodes.value.filter((code) => !objectSet.has(code)).sort((a, b) => a.localeCompare(b))
})

const orphanMenuRows = computed(() => {
  const invalid = new Set(orphanMenuCodes.value)
  return objectMenuItems.value.filter((item) => invalid.has(item.code))
})

const isExternalUrl = (url: string): boolean => {
  return /^https?:\/\//i.test(url)
}

const canResolveMenuUrl = (rawUrl: string): boolean => {
  const value = String(rawUrl || '').trim()
  if (!value || isExternalUrl(value)) return true
  const url = value.startsWith('/') ? value : `/${value}`
  const matchedPaths = router.resolve(url).matched.map((record: { path: string }) => record.path)
  return matchedPaths.some((path: string) => path !== '/:pathMatch(.*)*')
}

const brokenMenuRows = computed(() => {
  return menuItems.value.filter((item) => !canResolveMenuUrl(item.url))
})

const filteredAllObjects = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return allObjects.value
  return allObjects.value.filter((item) => {
    const displayName = getObjectDisplayName(item.code, item.name).toLowerCase()
    return item.code.toLowerCase().includes(query) || item.name.toLowerCase().includes(query) || displayName.includes(query)
  })
})

const getObjectDisplayName = (code: string, fallbackName: string): string => {
  return resolveObjectDisplayName(
    code,
    fallbackName,
    t as (key: string) => string,
    te
  )
}

const getMenuDisplayName = (item: MenuCoverageItem): string => {
  const translationKey = String(item.translationKey || '').trim()
  if (translationKey && te(translationKey)) {
    return t(translationKey)
  }

  const objectCode = extractObjectCodeFromUrl(item.url) || item.code
  return getObjectDisplayName(objectCode, item.name)
}

const isCovered = (code: string): boolean => {
  return menuObjectCodes.value.includes(code)
}

const openList = (code: string) => {
  router.push(`/objects/${code}`)
}

const openCreate = (code: string) => {
  router.push(`/objects/${code}/create`)
}

const loadData = async () => {
  loading.value = true
  try {
    const [objectResponse, menuResponse] = await Promise.all([
      businessObjectApi.list({ pageSize: 500 }),
      menuApi.get()
    ])
    allObjects.value = normalizeObjects(unwrapPayload(objectResponse))
    menuItems.value = normalizeMenuItems(unwrapPayload(menuResponse))
    await checkMissingObjectReadiness()
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : t('system.moduleWorkbench.messages.loadFailed')
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

const updateReadiness = (code: string, value: { readiness: ReadinessState; fieldCount: number; error?: string }) => {
  readinessByCode.value = {
    ...readinessByCode.value,
    [code]: value
  }
}

const checkMissingObjectReadiness = async () => {
  const codes = missingObjects.value.map((item) => item.code)
  if (!codes.length) {
    readinessByCode.value = {}
    return
  }

  for (const code of codes) {
    updateReadiness(code, { readiness: 'checking', fieldCount: 0 })
  }

  await Promise.all(codes.map(async (code) => {
    try {
      const metadata = await dynamicApi.getMetadata(code)
      const metadataPayload = unwrapPayload(metadata)
      const fields = Array.isArray(metadataPayload.fields)
        ? (metadataPayload.fields as AnyRecord[])
        : []
      const businessFields = filterSystemFields(fields)
      const fieldCount = businessFields.length
      const readiness: ReadinessState = fieldCount > 0 ? 'ready' : 'empty_fields'
      updateReadiness(code, { readiness, fieldCount })
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : t('system.moduleWorkbench.messages.metadataUnavailable')
      updateReadiness(code, { readiness: 'unavailable', fieldCount: 0, error: message })
    }
  }))
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.module-workbench {
  .header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;

    h2 {
      margin: 0 0 6px;
    }

    p {
      margin: 0;
      color: #606266;
      font-size: 13px;
    }
  }

  .metric-label {
    color: #909399;
    font-size: 13px;
  }

  .metric-value {
    margin-top: 4px;
    font-size: 28px;
    font-weight: 600;

    &.warning {
      color: #e6a23c;
    }

    &.danger {
      color: #f56c6c;
    }
  }

  .section-card {
    margin-top: 12px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }

  .search-input {
    width: 260px;
  }
}
</style>
