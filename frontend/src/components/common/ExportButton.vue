<!--
  ExportButton.vue

  Drop-in export button for any list page.

  Usage:
    <ExportButton
      :columns="exportColumns"
      :data="tableData"
      :fetch-all="() => myApi(currentFilters)"
      filename="asset-list"
    />
-->
<template>
  <el-dropdown
    trigger="click"
    :disabled="exporting"
    @visible-change="handleDropdownVisibleChange"
    @command="handleCommand"
  >
    <el-button
      :loading="exporting"
      :icon="Download"
      @mouseenter="warmUpSpreadsheet"
      @focus="warmUpSpreadsheet"
    >
      {{ $t('common.actions.export') }}
      <el-icon class="el-icon--right">
        <ArrowDown />
      </el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <!-- Export current page data -->
        <el-dropdown-item
          command="current-xlsx"
          :disabled="!data || data.length === 0"
        >
          {{ $t('reports.export.currentPageXlsx') }}
        </el-dropdown-item>
        <el-dropdown-item
          command="current-csv"
          :disabled="!data || data.length === 0"
        >
          {{ $t('reports.export.currentPageCsv') }}
        </el-dropdown-item>
        <el-dropdown-item
          v-if="fetchAll"
          divided
          command="all-xlsx"
        >
          {{ $t('reports.export.allPagesXlsx') }}
        </el-dropdown-item>
        <el-dropdown-item
          v-if="fetchAll"
          command="all-csv"
        >
          {{ $t('reports.export.allPagesCsv') }}
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Download, ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { exportToExcel, exportToCSV, exportAllPages, type ExportColumn } from '@/utils/exportService'
import { prefetchXlsx } from '@/utils/xlsxLoader'

const { t } = useI18n()

// 鈹€鈹€鈹€ Props 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
interface Props {
  /** Column definitions 鈥?label is what appears in the Excel header */
  columns: ExportColumn[]
  /** Currently visible page data (used for current-page export) */
  data?: any[]
  /**
   * Optional async function to fetch all records for full export.
   * Should return { results: any[], count: number } or an array.
   * If not provided, only current-page export options are shown.
   */
  fetchAll?: (params?: any) => Promise<any>
  /** Download filename (without extension) */
  filename?: string
  /** Sheet name in the Excel workbook */
  sheetName?: string
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  filename: 'export',
  sheetName: 'Sheet1'
})

// 鈹€鈹€鈹€ State 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const exporting = ref(false)

const warmUpSpreadsheet = () => {
  prefetchXlsx()
}

const handleDropdownVisibleChange = (visible: boolean) => {
  if (visible) {
    warmUpSpreadsheet()
  }
}

// 鈹€鈹€鈹€ Handlers 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const handleCommand = async (command: string) => {
  exporting.value = true
  try {
    switch (command) {
      case 'current-xlsx':
        await exportToExcel(props.filename, props.columns, props.data ?? [], { sheetName: props.sheetName })
        ElMessage.success(t('reports.export.successMessage'))
        break

      case 'current-csv':
        await exportToCSV(props.filename, props.columns, props.data ?? [])
        ElMessage.success(t('reports.export.successMessage'))
        break

      case 'all-xlsx':
        if (!props.fetchAll) break
        await exportAllPages(
          props.filename,
          props.columns,
          props.fetchAll,
          {},
          { sheetName: props.sheetName }
        )
        ElMessage.success(t('reports.export.successMessage'))
        break

      case 'all-csv': {
        if (!props.fetchAll) break
        // For CSV all-pages, collect data first then export
        const firstRes = await props.fetchAll({ page: 1, page_size: 200 })
        const all: any[] = firstRes?.results ?? (Array.isArray(firstRes) ? firstRes : [])
        const total: number = firstRes?.count ?? all.length
        if (total > all.length) {
          const pages = Math.ceil(total / 200)
          const rest = await Promise.all(
            Array.from({ length: pages - 1 }, (_, i) =>
              props.fetchAll!({ page: i + 2, page_size: 200 }).then(
                (r: any) => r?.results ?? []
              )
            )
          )
          all.push(...rest.flat())
        }
        await exportToCSV(props.filename, props.columns, all)
        ElMessage.success(t('reports.export.successMessage'))
        break
      }
    }
  } catch (e: any) {
    ElMessage.error(t('reports.export.errorMessage'))
    console.error('Export failed:', e)
  } finally {
    exporting.value = false
  }
}
</script>

