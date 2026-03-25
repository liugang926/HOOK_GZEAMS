<template>
  <div
    v-loading="loading"
    class="dynamic-list-page"
  >
    <el-alert
      v-if="objectMetadata && hasNoBusinessFields"
      class="list-health-alert"
      type="warning"
      :closable="false"
      :title="t('system.businessObject.messages.noBusinessFields')"
      show-icon
    />

    <div
      v-if="!loadError && canView"
      class="dynamic-list-page__shell"
    >
      <ObjectWorkspaceHero
        variant="list"
        :object-code="objectCode"
        :icon="objectMetadata?.icon || ''"
        :eyebrow="moduleLabel"
        :title="objectDisplayName || t('common.status.loading') || '...'"
        :description="listHeroDescription"
        :chips="heroChips"
        :stats="heroStats"
      />

      <section class="list-panel">
        <header class="list-panel__header">
          <div>
            <p class="list-panel__kicker">
              {{ listModeLabel }}
            </p>
            <h2 class="list-panel__title">
              {{ listPanelTitle }}
            </h2>
          </div>
          <p class="list-panel__text">
            {{ listPanelDescription }}
          </p>
        </header>

        <BaseListPage
          ref="tableRef"
          :title="objectDisplayName || t('common.status.loading') || '...'"
          :api="fetchData"
          :table-columns="tableColumns"
          :search-fields="unifiedSearchFields"
          :batch-actions="batchActions"
          :object-code="objectCode"
          :object-icon="objectMetadata?.icon"
          toolbar-placement="table"
          @row-click="handleRowClick"
        >
          <!-- Toolbar slot for create button -->
          <template #toolbar>
            <div
              v-if="quickFilters.length > 0"
              class="dynamic-list-toolbar-group"
            >
              <el-button
                v-for="filter in quickFilters"
                :key="filter.key"
                size="small"
                :type="filter.active ? (filter.type || 'primary') : 'default'"
                :icon="filter.icon"
                @click="setQuickFilter(filter.key)"
              >
                {{ t(filter.labelKey) }}
              </el-button>
            </div>
            <el-button
              v-if="canAdd"
              type="primary"
              @click="handleCreate"
            >
              {{ t('common.actions.create') }}
            </el-button>
            <ExportButton
              v-if="defaultExportColumns.length > 0"
              :columns="defaultExportColumns"
              :fetch-all="(params: any) => apiClient.list({ ...params, ...currentSearchParams })"
              :filename="objectDisplayName || objectCode"
            />
            <el-button
              v-if="exportableFields.length > 0"
              @click="showFieldSelector = true"
            >
              {{ t('reports.export.customExport', '自定义导出') }}
            </el-button>
            <ImportButton
              v-if="canAdd && defaultExportColumns.length > 0"
              :columns="defaultExportColumns"
              :required="requiredFieldCodes"
              :filename="objectDisplayName || objectCode"
              @import="handleImport"
            />
            <el-button
              v-if="objectCode"
              @click="handleLayoutSettings"
            >
              {{ t('system.businessObject.actions.layouts') }}
            </el-button>
          </template>

          <template #search-__unifiedKeyword="{ getValue, setValue, search }">
            <div class="unified-search">
              <el-select
                :model-value="getValue('__unifiedField') ?? '__all'"
                class="unified-search-field"
                clearable
                :placeholder="t('common.select')"
                @update:model-value="setValue('__unifiedField', $event || '__all')"
              >
                <el-option
                  :label="unifiedAllFieldsLabel"
                  value="__all"
                />
                <el-option
                  v-for="option in unifiedSearchFieldOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
              <el-input
                :model-value="getValue('__unifiedKeyword') || ''"
                class="unified-search-keyword"
                clearable
                :placeholder="searchKeywordPlaceholder"
                @update:model-value="setValue('__unifiedKeyword', $event || '')"
                @keyup.enter="search()"
              />
            </div>
          </template>

          <!-- Dynamic slot rendering for custom fields -->
          <template
            v-for="field in slotFields"
            #[field.slotName]="slotProps"
            :key="field.fieldCode"
          >
            <FieldRenderer
              :field="getFieldDefinition(field)"
              :model-value="getSlotFieldValue((slotProps as any).row, field)"
              :form-data="(slotProps as any).row"
              :disabled="true"
            />
          </template>

          <!-- Status badge slot -->
          <template
            v-if="hasStatusField"
            #status="{ row }"
          >
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>

          <!-- Actions slot -->
          <template #actions="{ row }">
            <el-button
              link
              type="primary"
              @click.stop="handleView(row)"
            >
              {{ t('common.actions.view') }}
            </el-button>
            <el-button
              v-for="action in getRowActions(row)"
              :key="`${row.id}-${action.key}`"
              link
              :type="action.type || 'primary'"
              @click.stop="handleRowAction(action.key, row)"
            >
              {{ action.label }}
            </el-button>
            <el-button
              v-if="canChange"
              link
              type="primary"
              @click.stop="handleEdit(row)"
            >
              {{ t('common.actions.edit') }}
            </el-button>
            <el-button
              v-if="canDelete"
              link
              type="danger"
              @click.stop="handleDelete(row)"
            >
              {{ t('common.actions.delete') }}
            </el-button>
          </template>
        </BaseListPage>
      </section>
    </div>

    <el-result
      v-else-if="!loadError && !canView"
      icon="warning"
      :title="t('common.messages.permissionDenied')"
      :sub-title="t('common.messages.permissionDeniedHint')"
    >
      <template #extra>
        <el-button @click="$router.back()">
          {{ t('common.actions.back') }}
        </el-button>
      </template>
    </el-result>

    <!-- Error state for failed metadata loads -->
    <el-result
      v-else-if="loadError"
      icon="error"
      :title="t('common.messages.loadFailed')"
      :sub-title="loadError"
    >
      <template #extra>
        <el-button
          type="primary"
          @click="retryLoad"
        >
          {{ t('common.actions.refresh') }}
        </el-button>
        <el-button @click="$router.back()">
          {{ t('common.actions.back') }}
        </el-button>
      </template>
    </el-result>

    <!-- Loading skeleton -->
    <el-skeleton
      v-else
      :rows="5"
      animated
    />
    
    <!-- Context Drawer for Create/Edit -->
    <ContextDrawer
      v-model="drawerVisible"
      :object-code="objectCode"
      :record-id="activeRecordId"
      @success="handleDrawerSuccess"
    />

    <!-- Export Field Selector Dialog -->
    <ExportFieldSelector
      v-model="showFieldSelector"
      :fields="exportableFields"
      :object-name="objectDisplayName || objectCode"
      @confirm="handleCustomExport"
    />

    <!-- Import Config + Progress Dialog -->
    <ImportConfigDialog
      v-model="showImportConfig"
      :parse-result="importParseResult"
      :fields="exportableFields"
      :object-code="objectCode"
      :field-source="orderedVisibleFieldsSource"
      @complete="handleImportComplete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import BaseListPage from '@/components/common/BaseListPage.vue'
import ObjectWorkspaceHero from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'
import FieldRenderer from '@/components/engine/FieldRenderer.vue'
import ContextDrawer from '@/components/common/ContextDrawer.vue'
import ExportButton from '@/components/common/ExportButton.vue'
import ImportButton from '@/components/common/ImportButton.vue'
import ExportFieldSelector from '@/components/common/ExportFieldSelector.vue'
import ImportConfigDialog from '@/components/common/ImportConfigDialog.vue'
import { useExportColumns } from '@/composables/useExportColumns'
import { createObjectClient } from '@/api/dynamic'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'
import {
  buildDynamicListUnifiedSearchFields,
  extractDynamicListRouteFilters,
  resolveDynamicListEffectivePermissions,
  shouldRefreshDynamicListOnPathChange,
  useDynamicListInteractions,
  useDynamicListMetadata,
  useDynamicListSchema,
  useDynamicListWorkspace,
} from '@/views/dynamic/workspace'
import type { SearchField } from '@/types/common'

const route = useRoute()
const router = useRouter()
const { t, te, locale } = useI18n()

// Get object code from route
const objectCode = ref<string>((route.params.code as string) || '')
const tableRef = ref()
const isZhLocale = computed(() => String(locale?.value || '').toLowerCase().startsWith('zh'))

const apiClient = computed(() => createObjectClient(objectCode.value))
const {
  loadError,
  loadMetadata,
  loading,
  objectMetadata,
  retryLoad,
  runtimeColumns,
  runtimeFields,
  runtimeLayoutConfig,
  runtimePermissions,
} = useDynamicListMetadata({
  objectCode,
  apiClient,
  t: t as (key: string) => string,
})

const objectDisplayName = computed(() => {
  return resolveObjectDisplayName(
    objectCode.value,
    objectMetadata.value?.name || '',
    t as (key: string) => string,
    te
  )
})

const searchKeywordPlaceholder = computed(() => {
  return t('common.selectors.searchKeyword')
})

const unifiedAllFieldsLabel = computed(() => {
  return t('common.selectors.allFields')
})

const routeFilters = computed<Record<string, any>>(() => {
  return extractDynamicListRouteFilters(route.query)
})

// Watch route changes to refresh data when navigating back from form page
watch(() => route.params.code, (newCode) => {
  if (newCode && newCode !== objectCode.value) {
    objectCode.value = newCode as string
    loadMetadata()
    // Refresh table data via BaseListPage
    tableRef.value?.refresh()
  }
}, { immediate: false })

// Also watch the full route for navigation within the same object
// (e.g., returning from create/edit form)
watch(() => route.path, (newPath, oldPath) => {
  if (shouldRefreshDynamicListOnPathChange({
    newPath,
    oldPath,
    objectCode: objectCode.value,
  })) {
    tableRef.value?.refresh()
  }
}, { immediate: false })

watch(
  () => route.query,
  (newQuery, oldQuery) => {
    if (JSON.stringify(newQuery) !== JSON.stringify(oldQuery)) {
      tableRef.value?.refresh()
    }
  },
  { deep: true }
)

const effectivePermissions = computed(() => {
  return resolveDynamicListEffectivePermissions(
    runtimePermissions.value,
    objectMetadata.value?.permissions,
  )
})

const canView = computed(() => effectivePermissions.value.view !== false)
const canAdd = computed(() => effectivePermissions.value.add !== false)
const canChange = computed(() => effectivePermissions.value.change !== false)
const canDelete = computed(() => effectivePermissions.value.delete !== false)

const {
  hasNoBusinessFields,
  orderedVisibleFieldsSource,
  rawSearchFields,
  tableColumns,
  unifiedSearchFieldOptions,
  visibleFieldsSource,
} = useDynamicListSchema({
  objectMetadata,
  runtimeColumns,
  runtimeFields,
  runtimeLayoutConfig,
})

const {
  moduleLabel,
  listModeLabel,
  listHeroDescription,
  listPanelTitle,
  listPanelDescription,
  heroChips,
  heroStats,
} = useDynamicListWorkspace({
  isZhLocale,
  objectCode,
  objectMetadata,
  objectDisplayName,
  canAdd,
  tableColumns,
  unifiedSearchFieldOptions,
})

const unifiedSearchFields = computed<SearchField[]>(() => {
  return buildDynamicListUnifiedSearchFields(
    rawSearchFields.value,
    t('common.actions.search'),
  )
})


// ── Export / Import ────────────────────────────────────────────────────────

const {
  exportableFields,
  defaultExportColumns,
  requiredFieldCodes,
  buildExportColumns
} = useExportColumns(orderedVisibleFieldsSource)

const {
  activeRecordId,
  batchActions,
  currentSearchParams,
  drawerVisible,
  fetchData,
  getFieldDefinition,
  getRowActions,
  getSlotFieldValue,
  getStatusLabel,
  getStatusType,
  handleCreate,
  handleCustomExport,
  handleDelete,
  handleDrawerSuccess,
  handleEdit,
  handleImport,
  handleImportComplete,
  handleLayoutSettings,
  handleRowAction,
  handleRowClick,
  handleView,
  hasStatusField,
  importParseResult,
  quickFilters,
  setQuickFilter,
  showFieldSelector,
  showImportConfig,
  slotFields
} = useDynamicListInteractions({
  t: t as (key: string, params?: Record<string, unknown>) => string,
  te,
  router,
  objectCode,
  objectDisplayName,
  apiClient,
  tableRef,
  canDelete,
  unifiedSearchFieldOptions,
  visibleFieldsSource,
  orderedVisibleFieldsSource,
  buildExportColumns,
  routeFilters,
})

onMounted(() => {
  loadMetadata()
})
</script>

<style scoped lang="scss">
@use '@/views/dynamic/styles/dynamic-list-page' as listPage;

@include listPage.dynamic-list-page-styles();

.dynamic-list-toolbar-group {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-right: 8px;
}
</style>


