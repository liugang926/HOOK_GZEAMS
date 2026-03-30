<template>
  <div class="tag-list-page">
    <section class="tag-stat-grid">
      <article
        v-for="card in statisticCards"
        :key="card.key"
        class="tag-stat-card"
      >
        <p class="tag-stat-card__label">
          {{ card.label }}
        </p>
        <p class="tag-stat-card__value">
          {{ card.value }}
        </p>
      </article>
    </section>

    <BaseListPage
      ref="listRef"
      :title="t('system.tag.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchTags"
      :batch-actions="batchActions"
      :selectable="true"
      object-code="SystemTag"
    >
      <template #toolbar>
        <el-button
          type="primary"
          @click="handleCreate"
        >
          {{ t('system.tag.create') }}
        </el-button>
      </template>

      <template #cell-name="{ row }">
        <div class="tag-name-cell">
          <span
            class="tag-name-cell__swatch"
            :style="{ backgroundColor: row.color || '#409EFF' }"
          />
          <div class="tag-name-cell__content">
            <div class="tag-name-cell__title">
              {{ row.name }}
            </div>
            <div
              v-if="row.description"
              class="tag-name-cell__description"
            >
              {{ row.description }}
            </div>
          </div>
        </div>
      </template>

      <template #cell-color="{ row }">
        <el-tag
          effect="plain"
          class="tag-color-chip"
          :style="buildColorChipStyle(row.color)"
        >
          {{ row.color }}
        </el-tag>
      </template>

      <template #actions="{ row }">
        <el-button
          v-if="canManageAssetAssignments(row)"
          link
          type="primary"
          @click.stop="openAssignmentDialog([row])"
        >
          {{ t('system.tag.actions.manageAssets') }}
        </el-button>
        <el-button
          link
          type="primary"
          @click.stop="handleViewRecords(row)"
        >
          {{ t('system.tag.actions.viewRecords') }}
        </el-button>
        <el-button
          link
          type="primary"
          @click.stop="handleEdit(row)"
        >
          {{ t('common.actions.edit') }}
        </el-button>
        <el-popconfirm
          :title="t('system.tag.messages.confirmDelete', { name: row.name })"
          @confirm="handleDelete(row)"
        >
          <template #reference>
            <el-button
              link
              type="danger"
            >
              {{ t('common.actions.delete') }}
            </el-button>
          </template>
        </el-popconfirm>
      </template>
    </BaseListPage>

    <el-dialog
      v-model="formDialogVisible"
      :title="formDialogTitle"
      width="560px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formModel"
        :rules="formRules"
        label-width="110px"
      >
        <el-form-item
          :label="t('system.tag.form.name')"
          prop="name"
        >
          <el-input
            v-model="formModel.name"
            :placeholder="t('system.tag.form.namePlaceholder')"
          />
        </el-form-item>

        <el-form-item
          :label="t('system.tag.form.bizType')"
          prop="bizType"
        >
          <el-select
            v-model="formModel.bizType"
            clearable
            filterable
            class="full-width"
            :placeholder="t('system.tag.form.bizTypePlaceholder')"
          >
            <el-option
              :label="t('system.tag.bizTypes.all')"
              value=""
            />
            <el-option
              v-for="option in businessObjectOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            >
              <div class="biz-type-option">
                <span>{{ option.label }}</span>
                <span
                  v-if="option.nameEn"
                  class="biz-type-option__meta"
                >
                  {{ option.nameEn }}
                </span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item
          :label="t('system.tag.form.color')"
          prop="color"
        >
          <div class="tag-color-field">
            <el-color-picker v-model="formModel.color" />
            <el-input v-model="formModel.color" />
          </div>
        </el-form-item>

        <el-form-item :label="t('system.tag.form.description')">
          <el-input
            v-model="formModel.description"
            type="textarea"
            :rows="4"
            :placeholder="t('system.tag.form.descriptionPlaceholder')"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">
          {{ t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="formSubmitting"
          @click="handleSubmitForm"
        >
          {{ t('common.actions.save') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="assignmentDialogVisible"
      :title="t('system.tag.assignment.title')"
      width="680px"
      destroy-on-close
    >
      <el-alert
        :title="t('system.tag.assignment.summary')"
        type="info"
        :closable="false"
        class="assignment-alert"
      />

      <div class="assignment-tags">
        <span class="assignment-tags__label">
          {{ t('system.tag.assignment.selectedTags') }}
        </span>
        <el-tag
          v-for="tag in assignmentTags"
          :key="tag.id"
          effect="plain"
          class="assignment-tags__item"
          :style="buildColorChipStyle(tag.color)"
        >
          {{ tag.name }}
        </el-tag>
      </div>

      <el-form label-width="110px">
        <el-form-item :label="t('system.tag.assignment.assets')">
          <el-select
            v-model="selectedAssetIds"
            multiple
            clearable
            filterable
            remote
            reserve-keyword
            class="full-width"
            :loading="assetOptionsLoading"
            :placeholder="t('system.tag.assignment.assetPlaceholder')"
            :remote-method="handleAssetSearch"
          >
            <el-option
              v-for="option in assetOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            >
              <div class="asset-option">
                <span>{{ option.label }}</span>
                <span class="asset-option__meta">{{ option.meta }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="assignmentDialogVisible = false">
          {{ t('common.actions.cancel') }}
        </el-button>
        <el-button
          :loading="assignmentSubmitting"
          @click="handleRemoveAssignments"
        >
          {{ t('common.actions.remove') }}
        </el-button>
        <el-button
          type="primary"
          :loading="assignmentSubmitting"
          @click="handleApplyAssignments"
        >
          {{ t('common.actions.apply') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

import BaseListPage from '@/components/common/BaseListPage.vue'
import { assetApi } from '@/api/assets'
import { tagApi } from '@/api/tags'
import type { SearchField, TableColumn } from '@/types/common'
import type {
  Tag,
  TagBusinessObjectOption,
  TagStatistics,
} from '@/types/tags'

interface BatchAction {
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  icon?: any
  action: (selectedRows: any[]) => void | Promise<void>
  confirm?: boolean
  confirmMessage?: string
}

interface TagFormState {
  name: string
  color: string
  bizType: string
  description: string
}

interface AssetOption {
  label: string
  value: string
  meta: string
}

const router = useRouter()
const { t } = useI18n()

const listRef = ref<InstanceType<typeof BaseListPage> | null>(null)
const formRef = ref<FormInstance>()

const statistics = ref<TagStatistics>({
  total: 0,
  used: 0,
  unused: 0,
  byBizType: [],
  topTags: [],
})
const businessObjectOptions = ref<TagBusinessObjectOption[]>([])
const formDialogVisible = ref(false)
const formSubmitting = ref(false)
const currentTag = ref<Tag | null>(null)
const assignmentDialogVisible = ref(false)
const assignmentSubmitting = ref(false)
const assignmentTags = ref<Tag[]>([])
const selectedAssetIds = ref<string[]>([])
const assetOptionsLoading = ref(false)
const assetOptions = ref<AssetOption[]>([])

const createDefaultFormState = (): TagFormState => ({
  name: '',
  color: '#409EFF',
  bizType: '',
  description: '',
})

const formModel = reactive<TagFormState>(createDefaultFormState())

const formRules = computed<FormRules>(() => ({
  name: [
    {
      required: true,
      message: t('system.tag.validation.nameRequired'),
      trigger: 'blur',
    },
  ],
  color: [
    {
      required: true,
      message: t('system.tag.validation.colorRequired'),
      trigger: 'change',
    },
  ],
}))

const formDialogTitle = computed(() => (
  currentTag.value ? t('system.tag.edit') : t('system.tag.create')
))

const businessObjectLabelMap = computed<Record<string, string>>(() => {
  const entries = businessObjectOptions.value.map((item) => [item.value, item.label] as const)
  return Object.fromEntries(entries)
})

const searchFields = computed<SearchField[]>(() => [
  {
    field: 'search',
    label: t('system.tag.search.keyword'),
    type: 'input',
    placeholder: t('system.tag.search.keywordPlaceholder'),
  },
  {
    field: 'bizType',
    label: t('system.tag.form.bizType'),
    type: 'select',
    options: [
      { label: t('system.tag.bizTypes.all'), value: '' },
      ...businessObjectOptions.value.map((item) => ({
        label: item.label,
        value: item.value,
      })),
    ],
  },
  {
    field: 'hasAssignments',
    label: t('system.tag.search.usageStatus'),
    type: 'select',
    options: [
      { label: t('system.tag.search.used'), value: true },
      { label: t('system.tag.search.unused'), value: false },
    ],
  },
])

const columns = computed<TableColumn[]>(() => [
  { prop: 'name', label: t('system.tag.columns.name'), minWidth: 240, slot: true },
  { prop: 'bizType', label: t('system.tag.columns.bizType'), minWidth: 160, format: (value: string) => resolveBizTypeLabel(value) },
  { prop: 'color', label: t('system.tag.columns.color'), width: 150, align: 'center', slot: true },
  { prop: 'usageCount', label: t('system.tag.columns.usageCount'), width: 120, align: 'center' },
  { prop: 'createdAt', label: t('system.tag.columns.createdAt'), width: 180 },
  { prop: 'actions', label: t('common.labels.operation'), width: 260, fixed: 'right', slot: true },
])

const batchActions = computed<BatchAction[]>(() => [
  {
    label: t('system.tag.actions.batchManageAssets'),
    type: 'primary',
    action: async (rows: Tag[]) => {
      openAssignmentDialog(rows)
    },
  },
  {
    label: t('common.actions.batchDelete'),
    type: 'danger',
    confirm: true,
    confirmMessage: t('system.tag.messages.confirmBatchDelete'),
    action: async (rows: Tag[]) => {
      await handleBatchDelete(rows)
    },
  },
])

const statisticCards = computed(() => {
  const assetScopedCount = statistics.value.byBizType
    .filter((item) => item.bizType === '' || item.bizType === 'Asset')
    .reduce((total, item) => total + Number(item.count || 0), 0)

  return [
    { key: 'total', label: t('system.tag.statistics.total'), value: statistics.value.total },
    { key: 'used', label: t('system.tag.statistics.used'), value: statistics.value.used },
    { key: 'unused', label: t('system.tag.statistics.unused'), value: statistics.value.unused },
    { key: 'assetScope', label: t('system.tag.statistics.assetScope'), value: assetScopedCount },
  ]
})

const buildColorChipStyle = (color?: string) => ({
  color: color || '#409EFF',
  borderColor: color || '#409EFF',
})

const resolveBizTypeLabel = (bizType?: string) => {
  if (!bizType) {
    return t('system.tag.bizTypes.all')
  }
  return businessObjectLabelMap.value[bizType] || bizType
}

const canManageAssetAssignments = (tag: Tag) => !tag.bizType || tag.bizType === 'Asset'

const resetForm = () => {
  Object.assign(formModel, createDefaultFormState())
  formRef.value?.clearValidate()
}

const refreshList = () => {
  listRef.value?.refresh()
}

const loadStatistics = async () => {
  try {
    statistics.value = await tagApi.statistics()
  } catch (error) {
    ElMessage.error(t('system.tag.messages.statsLoadFailed'))
  }
}

const loadBusinessObjectOptions = async () => {
  try {
    businessObjectOptions.value = await tagApi.getBusinessObjectOptions()
  } catch (error) {
    ElMessage.error(t('system.tag.messages.optionsLoadFailed'))
  }
}

const fetchTags = async (params: Record<string, any>) => {
  try {
    const response = await tagApi.list({
      ...params,
      page_size: params.pageSize,
    })
    return {
      results: response.results || [],
      count: response.count || 0,
    }
  } catch (error) {
    ElMessage.error(t('system.tag.messages.loadFailed'))
    return {
      results: [],
      count: 0,
    }
  }
}

const handleCreate = () => {
  currentTag.value = null
  resetForm()
  formDialogVisible.value = true
}

const handleEdit = (tag: Tag) => {
  currentTag.value = tag
  Object.assign(formModel, {
    name: tag.name,
    color: tag.color || '#409EFF',
    bizType: tag.bizType || '',
    description: tag.description || '',
  })
  formDialogVisible.value = true
}

const handleSubmitForm = async () => {
  const form = formRef.value
  if (!form) return

  const valid = await form.validate().catch(() => false)
  if (!valid) return

  formSubmitting.value = true
  try {
    const payload = {
      name: formModel.name.trim(),
      color: formModel.color,
      bizType: formModel.bizType,
      description: formModel.description.trim(),
    }

    if (currentTag.value?.id) {
      await tagApi.update(currentTag.value.id, payload)
    } else {
      await tagApi.create(payload)
    }

    ElMessage.success(t('system.tag.messages.saveSuccess'))
    formDialogVisible.value = false
    refreshList()
    await loadStatistics()
  } catch (error) {
    ElMessage.error(t('system.tag.messages.saveFailed'))
  } finally {
    formSubmitting.value = false
  }
}

const handleDelete = async (tag: Tag) => {
  try {
    await tagApi.delete(tag.id)
    ElMessage.success(t('system.tag.messages.deleteSuccess'))
    refreshList()
    await loadStatistics()
  } catch (error) {
    ElMessage.error(t('system.tag.messages.deleteFailed'))
  }
}

const handleBatchDelete = async (rows: Tag[]) => {
  if (!rows.length) return

  try {
    await tagApi.batchDelete(rows.map((row) => row.id))
    ElMessage.success(t('system.tag.messages.deleteSuccess'))
    await loadStatistics()
  } catch (error) {
    ElMessage.error(t('system.tag.messages.deleteFailed'))
  }
}

const handleViewRecords = (tag: Tag) => {
  const targetCode = tag.bizType || 'Asset'
  router.push({
    path: `/objects/${targetCode}`,
    query: {
      tagIds: tag.id,
    },
  })
}

const mergeAssetOptions = (rows: AssetOption[]) => {
  const map = new Map<string, AssetOption>()
  assetOptions.value.forEach((item) => map.set(item.value, item))
  rows.forEach((item) => map.set(item.value, item))
  assetOptions.value = Array.from(map.values())
}

const loadAssetOptions = async (keyword = '') => {
  assetOptionsLoading.value = true
  try {
    const response: any = await assetApi.list({
      search: keyword,
      page: 1,
      page_size: 20,
    })
    const rows = (response.results || []).map((item: any) => ({
      label: `${item.assetCode || item.assetName} · ${item.assetName || item.assetCode}`,
      value: item.id,
      meta: `${item.assetCode || '-'} / ${item.assetStatusDisplay || item.assetStatus || '-'}`,
    }))
    mergeAssetOptions(rows)
  } finally {
    assetOptionsLoading.value = false
  }
}

const handleAssetSearch = async (keyword: string) => {
  await loadAssetOptions(keyword)
}

const openAssignmentDialog = async (rows: Tag[]) => {
  if (!rows.length) {
    return
  }

  if (rows.some((row) => !canManageAssetAssignments(row))) {
    ElMessage.warning(t('system.tag.messages.assetOnly'))
    return
  }

  assignmentTags.value = rows
  selectedAssetIds.value = []
  assetOptions.value = []
  assignmentDialogVisible.value = true
  await loadAssetOptions('')
}

const ensureAssetSelection = () => {
  if (selectedAssetIds.value.length) {
    return true
  }
  ElMessage.warning(t('system.tag.messages.selectAssets'))
  return false
}

const handleApplyAssignments = async () => {
  if (!ensureAssetSelection()) return

  assignmentSubmitting.value = true
  try {
    await tagApi.apply({
      tagIds: assignmentTags.value.map((item) => item.id),
      objectIds: selectedAssetIds.value,
      bizType: 'Asset',
    })
    ElMessage.success(t('system.tag.messages.applySuccess'))
    assignmentDialogVisible.value = false
    refreshList()
    await loadStatistics()
  } catch (error) {
    ElMessage.error(t('system.tag.messages.applyFailed'))
  } finally {
    assignmentSubmitting.value = false
  }
}

const handleRemoveAssignments = async () => {
  if (!ensureAssetSelection()) return

  assignmentSubmitting.value = true
  try {
    await tagApi.remove({
      tagIds: assignmentTags.value.map((item) => item.id),
      objectIds: selectedAssetIds.value,
      bizType: 'Asset',
    })
    ElMessage.success(t('system.tag.messages.removeSuccess'))
    assignmentDialogVisible.value = false
    refreshList()
    await loadStatistics()
  } catch (error) {
    ElMessage.error(t('system.tag.messages.removeFailed'))
  } finally {
    assignmentSubmitting.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    loadBusinessObjectOptions(),
    loadStatistics(),
  ])
})
</script>

<style scoped lang="scss">
.tag-list-page {
  padding: 20px;
}

.tag-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.tag-stat-card {
  padding: 18px 20px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  background: linear-gradient(135deg, #ffffff, #f8fbff);
}

.tag-stat-card__label {
  margin: 0 0 8px;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
}

.tag-stat-card__value {
  margin: 0;
  color: #0f172a;
  font-size: 28px;
  font-weight: 700;
}

.tag-name-cell {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.tag-name-cell__swatch {
  width: 12px;
  height: 12px;
  margin-top: 4px;
  border-radius: 999px;
  flex-shrink: 0;
}

.tag-name-cell__content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tag-name-cell__title {
  color: #0f172a;
  font-weight: 600;
}

.tag-name-cell__description {
  color: #64748b;
  font-size: 13px;
  line-height: 1.4;
}

.tag-color-chip {
  min-width: 112px;
  justify-content: center;
}

.full-width {
  width: 100%;
}

.tag-color-field {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  width: 100%;
}

.biz-type-option,
.asset-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.biz-type-option__meta,
.asset-option__meta {
  color: #94a3b8;
  font-size: 12px;
}

.assignment-alert {
  margin-bottom: 16px;
}

.assignment-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 18px;
}

.assignment-tags__label {
  color: #475569;
  font-size: 13px;
  font-weight: 600;
}

.assignment-tags__item {
  margin-right: 0;
}

@media (max-width: 900px) {
  .tag-stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .tag-list-page {
    padding: 16px;
  }

  .tag-stat-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .tag-color-field {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
