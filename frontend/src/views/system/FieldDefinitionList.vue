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
        <h3>{{ $t('system.fieldDefinition.title', { name: objectName }) }}</h3>
      </div>
      <el-button
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
          <el-button
            link
            type="primary"
            :disabled="row.isSystem"
            @click="handleEdit(row)"
          >
            {{ $t('common.actions.edit') }}
          </el-button>
          <el-popconfirm
            v-if="!row.isSystem"
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
      :data="currentRow"
      :object-code="objectCode"
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
import { businessObjectApi } from '@/api/system'
import { useFieldTypes } from '@/composables/useFieldTypes'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const fieldTypes = useFieldTypes()

const objectCode = computed(() => route.params.objectCode as string || route.query.objectCode as string || '')
const objectName = ref(route.query.objectName as string || t('system.businessObject.title'))
const loading = ref(false)
const tableData = ref<any[]>([])
const dialogVisible = ref(false)
const currentRow = ref<any>(null)

// Field type mapping - use composable or i18n directly
const getFieldTypeLabel = (type: string) => {
  // Try to find label in system.fieldDefinition.types
  const key = `system.fieldDefinition.types.${type}`
  const label = t(key)
  return label !== key ? label : type
}

// Load field definitions from API
// Backend returns camelCase directly via djangorestframework-camel-case
const loadFields = async () => {
  if (!objectCode.value) {
    ElMessage.warning(t('system.fieldDefinition.messages.noObjectCode'))
    return
  }

  loading.value = true
  try {
    // The response interceptor unwraps the API response, so we get the data directly
    const data = await businessObjectApi.getFields(objectCode.value) as any
    if (data?.fields) {
      // Transform API response to table format
      tableData.value = data.fields.map((field: any) => ({
        id: field.fieldName,
        code: field.fieldName,
        name: field.displayName,
        fieldType: field.fieldType,
        isRequired: field.isRequired,
        isReadonly: field.isReadonly || !field.isEditable,
        isSystem: !field.isEditable || field.fieldName === 'id',
        sortOrder: field.sortOrder,
        description: field.displayNameEn || '',
        showInList: field.showInList,
        showInForm: field.showInForm,
        showInDetail: field.showInDetail,
        referenceModelPath: field.referenceModelPath
      }))

      // Update object name from response
      if (data.object_name && objectName.value === t('system.businessObject.title')) {
        objectName.value = data.object_name
      }
    } else {
      ElMessage.warning(t('system.fieldDefinition.messages.noData'))
    }
  } catch (error: any) {
    console.error('Failed to load field definitions:', error)
    const errorMsg = error?.response?.data?.error?.message || error?.message || t('system.fieldDefinition.messages.loadFailed')
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}

const loadData = () => {
  loadFields()
}

const handleBack = () => {
  router.push({ name: 'BusinessObjectList' })
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    // TODO: Replace with actual API call
    // await fieldDefinitionApi.delete(row.id)
    ElMessage.success(t('common.messages.deleteSuccess'))
    await loadData()
  } catch (error) {
    ElMessage.error(t('common.messages.deleteFailed'))
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
</style>
