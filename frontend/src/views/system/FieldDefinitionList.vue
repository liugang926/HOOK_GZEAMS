<template>
  <div class="field-definition-list">
    <div class="page-header">
      <div class="header-left">
        <el-button
          link
          @click="handleBack"
        >
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h3>{{ $t('system.fieldDefinition.title', { name: objectDisplayName }) }}</h3>
      </div>
      <el-tooltip
        v-if="!canManageFields"
        :content="getHardcodedReadonlyMessage()"
        placement="top"
      >
        <span class="action-disabled-wrapper">
          <el-button
            type="primary"
            :disabled="true"
          >
            {{ $t('system.fieldDefinition.create') }}
          </el-button>
        </span>
      </el-tooltip>
      <el-button
        v-else
        type="primary"
        @click="handleCreate"
      >
        {{ $t('system.fieldDefinition.create') }}
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      row-key="id"
    >
      <el-table-column
        prop="sortOrder"
        :label="$t('system.fieldDefinition.columns.sortOrder')"
        width="70"
        align="center"
      />
      <el-table-column
        prop="name"
        :label="$t('system.fieldDefinition.columns.name')"
        width="150"
      />
      <el-table-column
        prop="code"
        :label="$t('system.fieldDefinition.columns.code')"
        width="150"
      />
      <el-table-column
        :label="$t('system.fieldDefinition.columns.type')"
        width="120"
        align="center"
      >
        <template #default="{ row }">
          <el-tag size="small">
            {{ getFieldTypeLabel(row.fieldType) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="description"
        :label="$t('system.fieldDefinition.columns.description')"
        show-overflow-tooltip
      />
      <el-table-column
        :label="$t('system.fieldDefinition.columns.required')"
        width="70"
        align="center"
      >
        <template #default="{ row }">
          <el-icon
            v-if="row.isRequired"
            color="#f56c6c"
          >
            <Check />
          </el-icon>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('system.fieldDefinition.columns.readonly')"
        width="70"
        align="center"
      >
        <template #default="{ row }">
          <el-icon v-if="row.isReadonly">
            <Lock />
          </el-icon>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('system.fieldDefinition.columns.system')"
        width="90"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            v-if="row.isSystem"
            type="info"
            size="small"
          >
            {{ $t('system.fieldDefinition.tags.system') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('common.labels.operation')"
        width="150"
        fixed="right"
      >
        <template #default="{ row }">
          <el-tooltip
            v-if="getEditDisabledReason(row)"
            :content="getEditDisabledReason(row)"
            placement="top"
          >
            <span class="action-disabled-wrapper">
              <el-button
                link
                type="primary"
                :disabled="true"
              >
                {{ $t('common.actions.edit') }}
              </el-button>
            </span>
          </el-tooltip>
          <el-button
            v-else
            link
            type="primary"
            @click="handleEdit(row)"
          >
            {{ $t('common.actions.edit') }}
          </el-button>
          <el-tooltip
            v-if="getDeleteDisabledReason(row)"
            :content="getDeleteDisabledReason(row)"
            placement="top"
          >
            <span class="action-disabled-wrapper">
              <el-button
                link
                type="danger"
                :disabled="true"
              >
                {{ $t('common.actions.delete') }}
              </el-button>
            </span>
          </el-tooltip>
          <el-popconfirm
            v-else
            :title="$t('system.fieldDefinition.messages.confirmDelete')"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button
                link
                type="danger"
              >
                {{ $t('common.actions.delete') }}
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Field Definition Form Dialog -->
    <FieldDefinitionForm
      v-model:visible="dialogVisible"
      :data="currentRowData"
      :object-code="objectCode"
      :object-id="objectId"
      :is-hardcoded="isHardcodedObject"
      @success="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Check, Lock } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import FieldDefinitionForm from './components/FieldDefinitionForm.vue'
import { businessObjectApi, fieldDefinitionApi } from '@/api/system'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'

const { t, te } = useI18n()
const route = useRoute()
const router = useRouter()

const objectCode = computed(() => route.params.objectCode as string || route.query.objectCode as string || '')
const objectName = ref(route.query.objectName as string || t('system.businessObject.title'))
const objectDisplayName = computed(() => {
  return resolveObjectDisplayName(
    objectCode.value,
    objectName.value,
    t as (key: string) => string,
    te
  )
})
const loading = ref(false)
type FieldTableRow = {
  id: string
  code: string
  name: string
  fieldType: string
  isRequired: boolean
  isReadonly: boolean
  isSystem: boolean
  sortOrder: number
  description: string
  showInList?: boolean
  showInForm?: boolean
  showInDetail?: boolean
  referenceModelPath?: string
}

type RawField = Record<string, unknown>
type ObjectMetaPayload = { id?: string; name?: string; isHardcoded?: boolean; is_hardcoded?: boolean }
type FieldListPayload = { object_name?: string; objectName?: string; editableFields?: unknown[]; editable_fields?: unknown[]; fields?: unknown[]; results?: unknown[] }

const tableData = ref<FieldTableRow[]>([])
const dialogVisible = ref(false)
const currentRow = ref<FieldTableRow | null>(null)
const currentRowData = computed(() => currentRow.value ?? undefined)
const objectId = ref('')
const isHardcodedObject = ref(false)
const canManageFields = computed(() => !isHardcodedObject.value)

const RELATION_SUFFIX_RE = /(_items|_records|_logs|_snapshots|_scans|_differences|_allocations)$/i
const SYSTEM_FIELD_CODE_SET = new Set([
  'id',
  'created_at',
  'created_by',
  'updated_at',
  'updated_by',
  'deleted_at',
  'deleted_by',
  'is_deleted',
  'version',
  'organization',
  'organization_id',
  'tenant_id'
])

const toFieldCode = (field: RawField): string =>
  String(field.code || field.fieldCode || field.field_code || field.fieldName || '').trim()

const toFieldName = (field: RawField): string =>
  String(field.name || field.label || field.displayName || field.fieldName || toFieldCode(field)).trim()

function isReverseRelationField(field: RawField): boolean {
  if (!field || typeof field !== 'object') return false
  if (field.isReverseRelation === true || field.is_reverse_relation === true) return true
  if (field.reverseRelationModel || field.reverse_relation_model) return true
  if (field.reverseRelationField || field.reverse_relation_field) return true
  if (field.relationDisplayMode || field.relation_display_mode) return true

  // Fallback guard for legacy payloads that miss explicit relation flags.
  const code = toFieldCode(field)
  const name = toFieldName(field)
  const editable = field.isEditable ?? field.is_editable
  if (RELATION_SUFFIX_RE.test(code) && editable === false && name.toLowerCase() === code.toLowerCase()) {
    return true
  }
  return false
}

function isBuiltinSystemFieldCode(code: string): boolean {
  const normalized = String(code || '').trim().toLowerCase()
  if (!normalized) return false
  if (SYSTEM_FIELD_CODE_SET.has(normalized)) return true

  // Compatibility with camelCase and id-suffixed audit names.
  if (normalized === 'createdat' || normalized === 'createdby' || normalized === 'createdbyid') return true
  if (normalized === 'updatedat' || normalized === 'updatedby' || normalized === 'updatedbyid') return true
  if (normalized === 'deletedat' || normalized === 'deletedby' || normalized === 'deletedbyid') return true
  return false
}

const toBooleanOrDefault = (value: unknown, fallback = false): boolean => {
  if (typeof value === 'boolean') return value
  return fallback
}

const toOptionalBoolean = (value: unknown): boolean | undefined => {
  if (typeof value === 'boolean') return value
  return undefined
}

const toOptionalString = (value: unknown): string | undefined => {
  if (value === null || value === undefined || value === '') return undefined
  return String(value)
}

function normalizeFieldRows(source: unknown): FieldTableRow[] {
  const dataSource = source as { data?: unknown } | unknown
  const payload = (typeof dataSource === 'object' && dataSource !== null && 'data' in dataSource)
    ? (dataSource as { data?: unknown }).data
    : dataSource
  const directRows = Array.isArray(payload) ? payload : null
  const fieldPayload = (payload && typeof payload === 'object' ? payload : {}) as FieldListPayload
  const editableFields =
    fieldPayload.editableFields ||
    fieldPayload.editable_fields ||
    fieldPayload.fields ||
    fieldPayload.results ||
    []
  const rawFields = directRows || (Array.isArray(editableFields) ? editableFields : [])

  return rawFields
    .filter((field): field is RawField => typeof field === 'object' && field !== null)
    .filter((field) => !isReverseRelationField(field))
    .map((field): FieldTableRow => {
      const code = toFieldCode(field)
      const name = toFieldName(field)
      const sortOrder = Number(field.sortOrder ?? field.sort_order ?? 0)
      const isEditable = field.isEditable ?? field.is_editable
      const backendIsSystem = field.isSystem ?? field.is_system
      const isSystem = toBooleanOrDefault(backendIsSystem, isEditable === false || isBuiltinSystemFieldCode(code))
      return {
        id: toOptionalString(field.id) || code,
        code,
        name,
        fieldType: toOptionalString(field.fieldType) || toOptionalString(field.field_type) || 'text',
        isRequired: toBooleanOrDefault(field.isRequired ?? field.is_required, false),
        isReadonly: toBooleanOrDefault(field.isReadonly ?? field.is_readonly, isSystem ? true : isEditable === false),
        isSystem,
        sortOrder: Number.isFinite(sortOrder) ? sortOrder : 0,
        description: toOptionalString(field.description) || toOptionalString(field.helpText) || toOptionalString(field.displayNameEn) || '',
        showInList: toOptionalBoolean(field.showInList ?? field.show_in_list),
        showInForm: toOptionalBoolean(field.showInForm ?? field.show_in_form),
        showInDetail: toOptionalBoolean(field.showInDetail ?? field.show_in_detail),
        referenceModelPath: toOptionalString(field.referenceModelPath) || toOptionalString(field.reference_model_path)
      }
    })
    .sort((a, b) => {
      const sortGap = Number(a.sortOrder || 0) - Number(b.sortOrder || 0)
      if (sortGap !== 0) return sortGap
      return String(a.code || '').localeCompare(String(b.code || ''))
    })
}

// Field type mapping - use composable or i18n directly
const getFieldTypeLabel = (type: string) => {
  // Try to find label in system.fieldDefinition.types
  const key = `system.fieldDefinition.types.${type}`
  const label = t(key)
  return label !== key ? label : type
}

const getSystemFieldReadonlyMessage = (): string => {
  const key = 'system.fieldDefinition.messages.systemFieldReadOnly'
  const message = t(key)
  return message !== key ? message : 'System fields cannot be edited or deleted.'
}

const getHardcodedReadonlyMessage = (): string => {
  const key = 'system.fieldDefinition.messages.hardcodedReadonly'
  const message = t(key)
  return message !== key ? message : 'Hardcoded object fields are read-only.'
}

const getMissingObjectMetaMessage = (): string => {
  const key = 'system.fieldDefinition.messages.missingObjectMeta'
  const message = t(key)
  return message !== key ? message : 'Missing business object metadata. Please refresh and try again.'
}

const getEditDisabledReason = (row: FieldTableRow): string => {
  if (!canManageFields.value) return getHardcodedReadonlyMessage()
  if (row?.isSystem) return getSystemFieldReadonlyMessage()
  return ''
}

const getDeleteDisabledReason = (row: FieldTableRow): string => {
  if (!canManageFields.value) return getHardcodedReadonlyMessage()
  if (row?.isSystem) return getSystemFieldReadonlyMessage()
  return ''
}

// Load field definitions from API
// Backend returns camelCase directly via djangorestframework-camel-case
const loadObjectMeta = async () => {
  if (!objectCode.value) return

  try {
    const detail = await businessObjectApi.detail(objectCode.value) as unknown
    const detailObj = detail as { data?: unknown } | unknown
    const payload = (typeof detailObj === 'object' && detailObj !== null && 'data' in detailObj
      ? (detailObj as { data?: unknown }).data
      : detailObj) as ObjectMetaPayload
    objectId.value = String(payload?.id || '')
    isHardcodedObject.value = Boolean(payload?.isHardcoded ?? payload?.is_hardcoded)
    if (payload?.name) {
      objectName.value = payload.name
    }
  } catch (error) {
    // Fail-safe to read-only if metadata endpoint is unavailable.
    objectId.value = ''
    isHardcodedObject.value = true
  }
}

const loadFields = async () => {
  if (!objectCode.value) {
    ElMessage.warning(t('system.fieldDefinition.messages.noObjectCode'))
    return
  }

  loading.value = true
  try {
    if (canManageFields.value) {
      const data = await fieldDefinitionApi.byObject(objectCode.value) as unknown
      tableData.value = normalizeFieldRows(data)
    } else {
      // Hardcoded objects are read-only and come from model metadata.
      const data = await businessObjectApi.getFieldsWithContext(objectCode.value, 'form', { includeRelations: false }) as unknown
      const rows = normalizeFieldRows(data)
      tableData.value = rows

      // Backward compatibility: fallback to legacy endpoint if object router returns empty shape.
      if (rows.length === 0) {
        const legacyData = await businessObjectApi.getFields(objectCode.value, { context: 'form', include_relations: false }) as unknown
        tableData.value = normalizeFieldRows(legacyData)
      }

      if (tableData.value.length > 0) {
        const dataObj = data as { data?: unknown } | unknown
        const payload = (typeof dataObj === 'object' && dataObj !== null && 'data' in dataObj
          ? (dataObj as { data?: unknown }).data
          : dataObj) as FieldListPayload
        const objectNameFromApi = payload?.object_name || payload?.objectName
        if (objectNameFromApi && objectName.value === t('system.businessObject.title')) {
          objectName.value = objectNameFromApi
        }
      }
    }
    if (tableData.value.length === 0) {
      ElMessage.warning(t('system.fieldDefinition.messages.noData'))
    }
  } catch (error: unknown) {
    console.error('Failed to load field definitions:', error)
    const apiError = error as { response?: { data?: { error?: { message?: string } } }; message?: string }
    const errorMsg = apiError?.response?.data?.error?.message || apiError?.message || t('system.fieldDefinition.messages.loadFailed')
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}

const loadData = async () => {
  await loadObjectMeta()
  await loadFields()
}

const handleBack = () => {
  router.push({ name: 'BusinessObjectList' })
}

const handleCreate = () => {
  if (!canManageFields.value) {
    ElMessage.warning(getHardcodedReadonlyMessage())
    return
  }
  if (!objectId.value) {
    ElMessage.error(getMissingObjectMetaMessage())
    return
  }
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: FieldTableRow) => {
  if (!canManageFields.value) {
    ElMessage.warning(getHardcodedReadonlyMessage())
    return
  }
  if (row?.isSystem) {
    ElMessage.warning(getSystemFieldReadonlyMessage())
    return
  }
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (_row: FieldTableRow) => {
  if (!canManageFields.value) {
    ElMessage.warning(getHardcodedReadonlyMessage())
    return
  }
  if (_row?.isSystem) {
    ElMessage.warning(getSystemFieldReadonlyMessage())
    return
  }
  try {
    await fieldDefinitionApi.delete(_row.id)
    ElMessage.success(t('common.messages.deleteSuccess'))
    await loadData()
  } catch (error: unknown) {
    const apiError = error as { response?: { data?: { error?: { message?: string } } }; message?: string }
    const errorMsg = apiError?.response?.data?.error?.message || apiError?.message || t('common.messages.deleteFailed')
    ElMessage.error(errorMsg)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.field-definition-list {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.page-header h3 {
  margin: 0;
  font-size: 18px;
}
.action-disabled-wrapper {
  display: inline-flex;
}
</style>
