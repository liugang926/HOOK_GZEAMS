<template>
  <div class="field-permission-config">
    <el-table
      :data="fields"
      border
      size="small"
      :show-header="true"
    >
      <el-table-column
        prop="label"
        :label="t('workflow.designer.field')"
        width="140"
      />
      <el-table-column
        prop="code"
        :label="t('workflow.designer.code')"
        width="120"
      />
      <el-table-column
        :label="t('workflow.designer.permission')"
        width="140"
      >
        <template #default="{ row }">
          <el-select
            v-model="row.permission"
            size="small"
          >
            <el-option
              :label="t('workflow.permissions.editable')"
              value="editable"
            />
            <el-option
              :label="t('workflow.permissions.readOnly')"
              value="read_only"
            />
            <el-option
              :label="t('workflow.permissions.hidden')"
              value="hidden"
            />
          </el-select>
        </template>
      </el-table-column>
    </el-table>

    <div class="batch-actions">
      <el-button
        size="small"
        @click="setAll('editable')"
      >
        {{ t('workflow.designer.setAllEditable') }}
      </el-button>
      <el-button
        size="small"
        @click="setAll('read_only')"
      >
        {{ t('workflow.designer.setAllReadOnly') }}
      </el-button>
      <el-button
        size="small"
        @click="setAll('hidden')"
      >
        {{ t('workflow.designer.setAllHidden') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getFieldDefinitions } from '@/api/system'

const { t } = useI18n()

interface Props {
  modelValue: Record<string, string>
  businessObject: string
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, string>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

interface Field {
  code: string
  label: string
  permission: string
}

const fields = ref<Field[]>([])

onMounted(async () => {
  try {
    const res = await getFieldDefinitions(props.businessObject)
    fields.value = res.map((field: any) => ({
      code: field.code,
      label: field.name,
      permission: props.modelValue?.[field.code] || 'editable'
    }))
  } catch (error) {
    console.error('获取字段定义失败', error)
  }
})

const setAll = (permission: string) => {
  fields.value.forEach(f => f.permission = permission)
}

watch(fields, (newVal) => {
  const permissions: Record<string, string> = {}
  newVal.forEach(f => {
    permissions[f.code] = f.permission
  })
  emit('update:modelValue', permissions)
}, { deep: true })
</script>

<style scoped>
.field-permission-config {
  padding: 5px 0;
}

.batch-actions {
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
}
</style>
