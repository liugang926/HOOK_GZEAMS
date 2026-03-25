<template>
  <div class="translation-list">
    <!-- Page Header -->
    <section-block
      :title="$t('system.translations.title')"
      class="header-section"
    >
      <template #extra>
        <el-space>
          <el-button
            v-if="isFocusedObjectMode"
            type="primary"
            plain
            @click="handleCreateFocusedObjectTranslation"
          >
            <el-icon><Plus /></el-icon>
            {{ $t('system.translations.addFocusedObject') }}
          </el-button>
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
            {{ $t('common.actions.export') }}
          </el-button>
          <el-upload
            :show-file-list="false"
            :before-upload="handleImport"
            accept=".csv"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              {{ $t('common.actions.import') }}
            </el-button>
          </el-upload>
          <el-button
            type="primary"
            @click="handleCreate"
          >
            <el-icon><Plus /></el-icon>
            {{ $t('common.actions.add') }}
          </el-button>
        </el-space>
      </template>
    </section-block>

    <!-- Filters -->
    <el-card
      shadow="never"
      class="filter-card"
    >
      <el-form
        :model="filters"
        inline
      >
        <el-form-item :label="$t('system.translations.language')">
          <el-select
            v-model="filters.languageCode"
            style="width: 150px"
            @change="loadTranslations"
          >
            <el-option
              value=""
              :label="$t('common.all')"
            />
            <el-option
              v-for="lang in languages"
              :key="lang.code"
              :label="lang.name"
              :value="lang.code"
            >
              <span>{{ lang.flagEmoji }} {{ lang.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('system.translations.namespace')">
          <el-input
            v-model="filters.namespace"
            clearable
            @change="loadTranslations"
          />
        </el-form-item>
        <el-form-item :label="$t('system.translations.type')">
          <el-select
            v-model="filters.type"
            clearable
            style="width: 120px"
            @change="loadTranslations"
          >
            <el-option
              value="label"
              :label="$t('system.translations.types.label')"
            />
            <el-option
              value="message"
              :label="$t('system.translations.types.message')"
            />
            <el-option
              value="enum"
              :label="$t('system.translations.types.enum')"
            />
            <el-option
              value="object_field"
              :label="$t('system.translations.types.objectField')"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox
            v-model="filters.isSystem"
            @change="loadTranslations"
          >
            {{ $t('system.translations.systemOnly') }}
          </el-checkbox>
        </el-form-item>
      </el-form>
    </el-card>

    <el-alert
      v-if="focusTargetLabel"
      class="focus-alert"
      type="info"
      :closable="false"
      show-icon
    >
      <template #title>
        {{ $t('system.translations.focusObject', { target: focusTargetLabel }) }}
      </template>
      <template #default>
        <el-space>
          <span>{{ focusTargetCode }}</span>
          <span>{{ $t('system.translations.focusCoverage', { configured: configuredLanguageCount, total: activeLanguageCount }) }}</span>
          <el-button
            link
            type="primary"
            @click="clearObjectFocus"
          >
            {{ $t('system.translations.clearFocus') }}
          </el-button>
        </el-space>
      </template>
    </el-alert>

    <!-- Statistics -->
    <el-row
      :gutter="16"
      class="stats-row"
    >
      <el-col :span="6">
        <el-card shadow="never">
          <el-statistic
            :title="$t('system.translations.stats.total')"
            :value="stats.total"
          />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <el-statistic
            :title="$t('system.translations.stats.system')"
            :value="stats.system"
          />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <el-statistic
            :title="$t('system.translations.stats.user')"
            :value="stats.user"
          />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <el-statistic
            :title="$t('system.translations.stats.coverage')"
            :value="coverage"
            suffix="%"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- Translations Table -->
    <el-table
      v-loading="loading"
      :data="translations"
      stripe
      @row-click="handleEdit"
    >
      <el-table-column
        prop="namespace"
        :label="$t('system.translations.namespace')"
        width="150"
      />
      <el-table-column
        prop="key"
        :label="$t('system.translations.key')"
        min-width="200"
      >
        <template #default="{ row }">
          <span
            v-if="row.namespace"
            class="key-text"
          >{{ row.namespace }}:{{ row.key }}</span>
          <span
            v-else
            class="key-text object-ref"
          >
            {{ getContentTypeLabel(row.contentTypeModel) }} #{{ row.objectId }}.{{ row.fieldName }}
          </span>
        </template>
      </el-table-column>
      <el-table-column
        prop="text"
        :label="$t('system.translations.text')"
        min-width="250"
      />
      <el-table-column
        prop="languageCode"
        :label="$t('system.translations.language')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag size="small">
            {{ getLanguageFlag(row.languageCode) }} {{ row.languageCode }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="type"
        :label="$t('system.translations.type')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            size="small"
            :type="getTypeColor(row.type)"
          >
            {{ $t(`system.translations.types.${row.type}`) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="isSystem"
        :label="$t('system.translations.isSystem')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            v-if="row.isSystem"
            size="small"
            type="info"
          >
            {{ $t('common.yes') }}
          </el-tag>
          <el-tag
            v-else
            size="small"
            type="success"
          >
            {{ $t('common.no') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('common.actions')"
        width="120"
        fixed="right"
      >
        <template #default="{ row }">
          <el-space>
            <el-button
              link
              type="primary"
              size="small"
              @click.stop="handleEdit(row)"
            >
              {{ $t('common.actions.edit') }}
            </el-button>
            <el-popconfirm
              :title="$t('system.translations.deleteConfirm')"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button
                  link
                  type="danger"
                  size="small"
                  @click.stop
                >
                  {{ $t('common.actions.delete') }}
                </el-button>
              </template>
            </el-popconfirm>
          </el-space>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      :page-sizes="[20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="loadTranslations"
      @size-change="loadTranslations"
    />

    <!-- Translation Dialog -->
    <TranslationDialog
      v-model:visible="dialogVisible"
      :translation="currentTranslation"
      :preset="dialogPreset"
      :lock-object-target="isFocusedObjectMode"
      :languages="languages"
      @success="loadTranslations"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Download, Upload, Plus } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import SectionBlock from '@/components/common/SectionBlock.vue'
import TranslationDialog from '@/components/common/TranslationDialog.vue'
import { translationApi, languageApi } from '@/api/translations'
import type { Translation, Language } from '@/api/translations'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

// State
const loading = ref(false)
const translations = ref<Translation[]>([])
const languages = ref<Language[]>([])
const dialogVisible = ref(false)
const currentTranslation = ref<Translation | null>(null)

// Filters
const filters = reactive({
  languageCode: 'zh-CN',
  namespace: '',
  type: '',
  isSystem: false,
  contentTypeModel: '',
  objectId: '',
  fieldName: '',
})

// Pagination
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// Statistics
const stats = reactive({
  total: 0,
  system: 0,
  user: 0
})

const coverage = computed(() => {
  if (stats.total === 0) return 0
  return Math.round((stats.system / stats.total) * 100)
})

const isFocusedObjectMode = computed(() => !!filters.contentTypeModel && !!filters.objectId)
const focusTargetLabel = computed(() => String(route.query.focus_label || '').trim())
const focusTargetCode = computed(() => String(route.query.focus_code || '').trim())
const activeLanguageCount = computed(() => languages.value.length)
const configuredLanguageCount = computed(() => new Set(translations.value.map((row) => row.languageCode).filter(Boolean)).size)
const dialogPreset = computed(() => {
  if (!filters.contentTypeModel || !filters.objectId) return null
  return {
    contentTypeModel: filters.contentTypeModel,
    objectId: filters.objectId,
    fieldName: filters.fieldName || 'name',
    type: filters.type || 'object_field',
  }
})

const syncFiltersFromRoute = () => {
  filters.contentTypeModel = String(route.query.content_type_model || '').trim()
  filters.objectId = String(route.query.object_id || '').trim()
  filters.fieldName = String(route.query.field_name || '').trim()
  filters.type = String(route.query.type || '').trim()
  if (route.query.show_all_languages === '1' && filters.contentTypeModel && filters.objectId) {
    filters.languageCode = ''
  } else if (!filters.languageCode && languages.value.length > 0) {
    filters.languageCode = languages.value.find((lang) => lang.isDefault)?.code || 'zh-CN'
  }
  pagination.page = 1
}

// Load languages
const loadLanguages = async () => {
  const { data } = await languageApi.getActive()
  if (data) {
    languages.value = data
    if (!filters.languageCode && languages.value.length > 0) {
      filters.languageCode = languages.value.find((l: Language) => l.isDefault)?.code || 'zh-CN'
    }
  }
}

// Load translations
const loadTranslations = async () => {
  loading.value = true
  try {
    const { data } = await translationApi.list({
      language_code: filters.languageCode || undefined,
      namespace: filters.namespace || undefined,
      type: filters.type || undefined,
      is_system: filters.isSystem,
      content_type_model: filters.contentTypeModel || undefined,
      object_id: filters.objectId || undefined,
      field_name: filters.fieldName || undefined,
      page: pagination.page,
      page_size: pagination.pageSize
    })

    if (data) {
      translations.value = data.results || []
      pagination.total = data.count || 0
    }
  } finally {
    loading.value = false
  }
}

// Load statistics
const loadStats = async () => {
  try {
    const { data } = await translationApi.getStats()
    if (data?.total) {
      stats.total = (data.total.byLanguage as any[])?.reduce((sum: number, item: any) => sum + item.count, 0) || 0
      stats.system = data.total.systemVsUser?.system || 0
      stats.user = data.total.systemVsUser?.user || 0
    }
  } catch (e) {
    // Ignore stats error
  }
}

// Get language flag emoji
const getLanguageFlag = (code: string) => {
  const lang = languages.value.find((l: Language) => l.code === code)
  return lang?.flagEmoji || ''
}

// Get type color for tag
const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    label: 'primary',
    message: 'success',
    enum: 'warning',
    object_field: 'info'
  }
  return colors[type] || ''
}

const getContentTypeLabel = (contentTypeModel?: string) => {
  const model = String(contentTypeModel || '').trim()
  if (!model) return ''

  const labelMap: Record<string, string> = {
    businessobject: t('system.translations.contentTypes.businessObject'),
    dictionarytype: t('system.translations.contentTypes.dictionaryType'),
    dictionaryitem: t('system.translations.contentTypes.dictionaryItem'),
    modelfielddefinition: t('system.translations.contentTypes.modelFieldDefinition'),
    menugroup: t('system.translations.contentTypes.menuGroup'),
  }

  return labelMap[model] || model
}

// Create translation
const handleCreate = () => {
  currentTranslation.value = null
  dialogVisible.value = true
}

const handleCreateFocusedObjectTranslation = () => {
  currentTranslation.value = null
  dialogVisible.value = true
}

// Edit translation
const handleEdit = (row: Translation) => {
  currentTranslation.value = row
  dialogVisible.value = true
}

// Delete translation
const handleDelete = async (id: string) => {
  try {
    await translationApi.delete(id)
    ElMessage.success(t('system.translations.messages.deleteSuccess'))
    loadTranslations()
    loadStats()
  } catch (error) {
    ElMessage.error(t('system.translations.messages.deleteFailed'))
  }
}

// Export translations
const handleExport = async () => {
  try {
    const blob = await translationApi.export({
      language_code: filters.languageCode,
      namespace: filters.namespace || undefined
    })

    // Create download link
    const url = window.URL.createObjectURL(blob as any)
    const link = document.createElement('a')
    link.href = url
    link.download = `translations_${filters.languageCode}.csv`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success(t('system.translations.messages.exportSuccess'))
  } catch (error) {
    ElMessage.error(t('system.translations.messages.exportFailed'))
  }
}

// Import translations
const handleImport = async (file: File) => {
  try {
    const { data } = await translationApi.import(file)
    if (data) {
      ElMessage.success(
        t('system.translations.messages.importSummary', {
          created: data.summary.created,
          updated: data.summary.updated,
          failed: data.summary.failed
        })
      )
      loadTranslations()
      loadStats()
    }
  } catch (error) {
    ElMessage.error(t('system.translations.messages.importFailed'))
  }
  return false // Prevent auto upload
}

const clearObjectFocus = async () => {
  await router.replace({
    query: {
      ...route.query,
      content_type_model: undefined,
      object_id: undefined,
      field_name: undefined,
      type: undefined,
      show_all_languages: undefined,
      focus_label: undefined,
      focus_code: undefined,
    },
  })
}

// Initialize
onMounted(async () => {
  syncFiltersFromRoute()
  await loadLanguages()
  loadTranslations()
  loadStats()
})

watch(
  () => route.query,
  () => {
    syncFiltersFromRoute()
    loadTranslations()
  },
)
</script>

<style scoped lang="scss">
.translation-list {
  .header-section {
    margin-bottom: 16px;
  }

  .filter-card {
    margin-bottom: 16px;
  }

  .focus-alert {
    margin-bottom: 16px;
  }

  .stats-row {
    margin-bottom: 16px;
  }

  .key-text {
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 12px;
    color: var(--el-text-color-secondary);

    &.object-ref {
      color: var(--el-color-primary);
    }
  }

  .el-pagination {
    margin-top: 16px;
    justify-content: flex-end;
  }
}
</style>
