<!--
  ImportButton.vue

  Drop-in import button for list/management pages.

  Usage:
    <ImportButton
      :columns="importColumns"
      :required="['assetNo', 'name']"
      filename="asset"
      @import="handleImport"
    />
-->
<template>
  <el-dropdown
    trigger="click"
    :disabled="importing"
    @visible-change="handleDropdownVisibleChange"
    @command="handleCommand"
  >
    <el-button
      :loading="importing"
      :icon="Upload"
      @mouseenter="warmUpSpreadsheet"
      @focus="warmUpSpreadsheet"
    >
      {{ $t('common.actions.import') }}
      <el-icon class="el-icon--right">
        <ArrowDown />
      </el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="template">
          {{ $t('reports.import.downloadTemplate') }}
        </el-dropdown-item>
        <el-dropdown-item
          command="upload"
          divided
        >
          {{ $t('reports.import.selectFile') }}
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>

  <!-- Hidden file picker -->
  <input
    ref="fileInputRef"
    type="file"
    accept=".xlsx,.xls,.csv"
    style="display:none"
    @change="handleFileChange"
  >

  <!-- Error dialog -->
  <el-dialog
    v-model="errorDialog"
    :title="$t('reports.import.errorTitle')"
    width="600px"
    destroy-on-close
  >
    <el-alert
      v-if="parseResult.unknownHeaders.length"
      type="warning"
      :closable="false"
      style="margin-bottom:12px"
    >
      {{ $t('reports.import.unknownHeaders') }}: {{ parseResult.unknownHeaders.join(', ') }}
    </el-alert>
    <el-alert
      v-if="parseResult.missingHeaders.length"
      type="info"
      :closable="false"
      style="margin-bottom:12px"
    >
      {{ $t('reports.import.missingHeaders') }}: {{ parseResult.missingHeaders.join(', ') }}
    </el-alert>

    <el-table
      v-if="parseResult.errors.length"
      :data="parseResult.errors"
      border
      size="small"
      max-height="300"
    >
      <el-table-column
        :label="$t('reports.import.errorRow')"
        prop="row"
        width="80"
      />
      <el-table-column
        :label="$t('reports.import.errorCol')"
        prop="col"
        width="120"
      />
      <el-table-column
        :label="$t('reports.import.errorMsg')"
        prop="message"
      />
    </el-table>

    <div
      v-if="parseResult.errors.length === 0"
      style="color:#67C23A"
    >
      {{ $t('reports.import.noErrors') }}
    </div>

    <template #footer>
      <el-button @click="errorDialog = false">
        {{ $t('common.actions.cancel') }}
      </el-button>
      <el-button
        v-if="parseResult.errors.length === 0 && parseResult.data.length > 0"
        type="primary"
        :loading="importing"
        @click="confirmImport"
      >
        {{ $t('reports.import.confirmImport', { count: parseResult.data.length }) }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Upload, ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { parseExcelFile, downloadImportTemplate, type ImportResult } from '@/utils/importService'
import type { ExportColumn } from '@/utils/exportService'
import { prefetchXlsx } from '@/utils/xlsxLoader'

const { t } = useI18n()

// 鈹€鈹€鈹€ Props 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
interface Props {
  /** Column definitions (same config as ExportButton) */
  columns: ExportColumn[]
  /** Props that must have a value in every imported row */
  required?: string[]
  /** Used for the template filename */
  filename?: string
  /** Optional example data row for the template */
  exampleRow?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  required: () => [],
  filename: 'import'
})

// 鈹€鈹€鈹€ Emits 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const emit = defineEmits<{
  (e: 'import', result: ImportResult): void
}>()

// 鈹€鈹€鈹€ State 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const importing = ref(false)
const errorDialog = ref(false)
const fileInputRef = ref<HTMLInputElement>()
const parseResult = reactive<ImportResult>({
  data: [],
  errors: [],
  unknownHeaders: [],
  missingHeaders: []
})

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
  if (command === 'template') {
    try {
      importing.value = true
      await downloadImportTemplate(props.filename, props.columns, props.exampleRow)
      ElMessage.success(t('reports.export.successMessage'))
    } catch (err) {
      console.error('Import template download failed:', err)
      ElMessage.error(t('reports.import.parseError'))
    } finally {
      importing.value = false
    }
  } else if (command === 'upload') {
    fileInputRef.value?.click()
  }
}

const handleFileChange = async (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  // Reset input so the same file can be re-selected
  ;(e.target as HTMLInputElement).value = ''

  importing.value = true
  try {
    const result = await parseExcelFile(file, props.columns, { required: props.required })
    Object.assign(parseResult, result)

    if (result.errors.length > 0 || result.unknownHeaders.length > 0 || result.missingHeaders.length > 0) {
      errorDialog.value = true
    } else if (result.data.length === 0) {
      ElMessage.warning(t('reports.import.emptyFile'))
    } else {
      // No errors 鈥?confirm immediately
      confirmImport()
    }
  } catch (err: any) {
    ElMessage.error(t('reports.import.parseError'))
    console.error('Import parse error:', err)
  } finally {
    importing.value = false
  }
}

const confirmImport = () => {
  errorDialog.value = false
  emit('import', { ...parseResult })
  ElMessage.success(t('reports.import.readyMessage', { count: parseResult.data.length }))
}
</script>

