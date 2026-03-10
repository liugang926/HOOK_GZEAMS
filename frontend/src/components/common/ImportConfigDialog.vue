<!--
  ImportConfigDialog.vue

  Pre-import configuration dialog that lets users:
  1. Choose import strategy (Create / Upsert / Skip Duplicates)
  2. Select the match field for upsert/skip modes
  3. See import progress with real-time feedback

  Usage:
    <ImportConfigDialog
      v-model="showImportConfig"
      :parse-result="parseResult"
      :fields="exportableFields"
      :object-code="objectCode"
      :field-source="fieldSource"
      @complete="handleImportComplete"
    />
-->
<template>
  <el-dialog
    v-model="visible"
    :title="t('reports.import.configTitle', '导入配置')"
    width="560px"
    :close-on-click-modal="!importing"
    :show-close="!importing"
    destroy-on-close
  >
    <!-- Strategy Selection -->
    <div
      v-if="!importing"
      class="import-config"
    >
      <el-form
        label-position="top"
        class="import-config-form"
      >
        <el-form-item :label="t('reports.import.dataCount', '数据行数')">
          <el-tag
            type="info"
            size="large"
          >
            {{ parseResult.data.length }} {{ t('reports.import.rows', '行') }}
          </el-tag>
        </el-form-item>

        <el-form-item :label="t('reports.import.strategy', '导入策略')">
          <el-radio-group
            v-model="strategy"
            class="strategy-group"
          >
            <el-radio-button value="create">
              {{ t('reports.import.strategyCreate', '仅新建') }}
            </el-radio-button>
            <el-radio-button value="upsert">
              {{ t('reports.import.strategyUpsert', '匹配更新') }}
            </el-radio-button>
            <el-radio-button value="skip_duplicates">
              {{ t('reports.import.strategySkip', '跳过已存在') }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="strategy !== 'create'"
          :label="t('reports.import.matchField', '匹配字段')"
        >
          <el-select
            v-model="matchField"
            :placeholder="t('reports.import.selectMatchField', '选择匹配字段')"
            style="width: 100%"
          >
            <el-option
              v-for="field in matchableFields"
              :key="field.code"
              :label="field.label"
              :value="field.code"
            />
          </el-select>
          <div class="match-field-hint">
            {{ strategy === 'upsert'
              ? t('reports.import.upsertHint', '根据此字段查找已有记录，存在则更新，不存在则新建')
              : t('reports.import.skipHint', '根据此字段查找，已存在的记录将被跳过')
            }}
          </div>
        </el-form-item>

        <el-alert
          v-if="hasReferenceFields"
          type="info"
          :closable="false"
          show-icon
          class="ref-alert"
        >
          {{ t('reports.import.referenceHint', '引用字段（如部门、人员）将自动按名称匹配，无需手动填写 ID') }}
        </el-alert>
      </el-form>
    </div>

    <!-- Progress -->
    <div
      v-else
      class="import-progress"
    >
      <el-progress
        :percentage="progressPercent"
        :status="progressStatus"
        :stroke-width="20"
        text-inside
      />

      <div class="progress-stats">
        <el-statistic
          :title="t('reports.import.progressCreated', '新建')"
          :value="progress.created"
        />
        <el-statistic
          v-if="strategy !== 'create'"
          :title="t('reports.import.progressUpdated', '更新')"
          :value="progress.updated"
        />
        <el-statistic
          v-if="strategy === 'skip_duplicates'"
          :title="t('reports.import.progressSkipped', '跳过')"
          :value="progress.skipped"
        />
        <el-statistic
          :title="t('reports.import.progressFailed', '失败')"
          :value="progress.failed"
          class="stat-failed"
        />
      </div>

      <!-- Error list -->
      <el-table
        v-if="progress.errors.length > 0"
        :data="progress.errors"
        size="small"
        max-height="200"
        border
        class="error-table"
      >
        <el-table-column
          :label="t('reports.import.errorRow', '行')"
          prop="row"
          width="60"
        />
        <el-table-column
          :label="t('reports.import.errorMsg', '错误')"
          prop="message"
        />
      </el-table>
    </div>

    <template #footer>
      <el-button
        :disabled="importing"
        @click="visible = false"
      >
        {{ importing ? t('common.actions.close') : t('common.actions.cancel') }}
      </el-button>
      <el-button
        v-if="!importing && !completed"
        type="primary"
        :disabled="strategy !== 'create' && !matchField"
        @click="startImport"
      >
        {{ t('reports.import.startImport', '开始导入') }}
        ({{ parseResult.data.length }})
      </el-button>
      <el-button
        v-if="completed"
        type="primary"
        @click="handleComplete"
      >
        {{ t('common.actions.confirm') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ImportResult } from '@/utils/importService'
import { useImportProcessor, type ImportStrategy } from '@/composables/useImportProcessor'

const props = defineProps<{
  modelValue: boolean
  parseResult: ImportResult
  fields: Array<{ code: string; label: string }>
  objectCode: string
  fieldSource: any // Ref<any[]> — the raw field metadata
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'complete', result: { created: number; updated: number; skipped: number; failed: number }): void
}>()

const { t } = useI18n()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const strategy = ref<ImportStrategy>('create')
const matchField = ref('')
const completed = ref(false)

const matchableFields = computed(() => {
  return (props.fields || []).filter(f => f.code && f.label)
})

const hasReferenceFields = computed(() => {
  return referenceFields.value.length > 0
})

const { importing, progress, processImport, referenceFields } = useImportProcessor({
  objectCode: () => props.objectCode,
  fields: computed(() => props.fieldSource?.value ?? props.fieldSource ?? [])
})

const progressPercent = computed(() => {
  if (progress.value.total === 0) return 0
  return Math.round((progress.value.current / progress.value.total) * 100)
})

const progressStatus = computed(() => {
  if (!completed.value) return undefined
  if (progress.value.failed === 0) return 'success' as const
  if (progress.value.failed === progress.value.total) return 'exception' as const
  return 'warning' as const
})

async function startImport() {
  completed.value = false
  await processImport(
    props.parseResult.data,
    strategy.value,
    strategy.value !== 'create' ? matchField.value : undefined
  )
  completed.value = true
}

function handleComplete() {
  emit('complete', {
    created: progress.value.created,
    updated: progress.value.updated,
    skipped: progress.value.skipped,
    failed: progress.value.failed
  })
  visible.value = false
}
</script>

<style scoped lang="scss">
.import-config-form {
  :deep(.el-form-item__label) {
    font-weight: 600;
  }
}

.strategy-group {
  width: 100%;
  display: flex;

  :deep(.el-radio-button) {
    flex: 1;

    .el-radio-button__inner {
      width: 100%;
    }
  }
}

.match-field-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.ref-alert {
  margin-top: 8px;
}

.import-progress {
  .progress-stats {
    display: flex;
    gap: 24px;
    margin: 20px 0;
    justify-content: center;

    .stat-failed :deep(.el-statistic__number) {
      color: var(--el-color-danger);
    }
  }

  .error-table {
    margin-top: 12px;
  }
}
</style>
