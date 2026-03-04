<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? $t('system.businessObject.editTitle') : $t('system.businessObject.createTitle')"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-tabs v-model="activeTab">
      <el-tab-pane
        :label="$t('system.businessObject.tabs.basic')"
        name="basic"
      >
        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-width="120px"
        >
          <el-form-item
            :label="$t('system.businessObject.fields.code')"
            prop="code"
          >
            <el-input
              v-model="formData.code"
              :placeholder="$t('system.businessObject.placeholders.code')"
              :disabled="isEdit"
            />
          </el-form-item>

          <el-form-item
            :label="$t('system.businessObject.fields.name')"
            prop="name"
          >
            <el-input
              v-model="formData.name"
              :placeholder="$t('system.businessObject.placeholders.name')"
            />
          </el-form-item>

          <el-form-item
            :label="$t('system.businessObject.fields.description')"
            prop="description"
          >
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="3"
              :placeholder="$t('system.businessObject.placeholders.description')"
            />
          </el-form-item>

          <el-form-item
            :label="$t('system.businessObject.fields.tableName')"
            prop="tableName"
          >
            <el-input
              v-model="formData.tableName"
              :placeholder="$t('system.businessObject.placeholders.tableName')"
            />
          </el-form-item>

          <el-form-item :label="$t('system.businessObject.fields.pkField')">
            <el-input
              v-model="formData.pkField"
              :placeholder="$t('system.businessObject.placeholders.pkField')"
            />
          </el-form-item>

          <el-form-item :label="$t('system.businessObject.fields.enableWorkflow')">
            <el-switch v-model="formData.enableWorkflow" />
            <span class="form-tip">{{ $t('system.businessObject.tips.workflow') }}</span>
          </el-form-item>

          <el-form-item :label="$t('system.businessObject.fields.enableVersion')">
            <el-switch v-model="formData.enableVersion" />
            <span class="form-tip">{{ $t('system.businessObject.tips.version') }}</span>
          </el-form-item>

          <el-form-item :label="$t('system.businessObject.fields.enableSoftDelete')">
            <el-switch v-model="formData.enableSoftDelete" />
            <span class="form-tip">{{ $t('system.businessObject.tips.softDelete') }}</span>
          </el-form-item>

          <el-form-item :label="$t('system.businessObject.fields.isSystem')">
            <el-switch
              v-model="formData.isSystem"
              :disabled="isEdit"
            />
            <span class="form-tip">{{ $t('system.businessObject.tips.system') }}</span>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane
        :label="$t('system.businessObject.tabs.actions')"
        name="actions"
      >
        <div class="info-box">
          <p>{{ $t('system.businessObject.info.customActions') }}</p>
          <p>{{ $t('system.businessObject.info.customActionsExample') }}</p>
        </div>
        <el-input
          type="textarea"
          :rows="15"
          :model-value="JSON.stringify(formData.actions || [], null, 2)"
          placeholder="[{&quot;code&quot;: &quot;...&quot;, &quot;label&quot;: &quot;...&quot;}]"
          @change="(val: string) => {
            try {
              formData.actions = JSON.parse(val)
            } catch (e) {
              // Ignore parse error
            }
          }"
        />
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <el-button @click="handleClose">
        {{ $t('common.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? $t('common.actions.save') : $t('common.actions.create') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  visible: boolean
  data?: any
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const activeTab = ref('basic')

const isEdit = computed(() => !!props.data?.id)

const formData = ref({
  code: '',
  name: '',
  description: '',
  tableName: '',
  pkField: 'id',
  enableWorkflow: false,
  enableVersion: false,
  enableSoftDelete: true,
  isSystem: false,
  actions: [] as any[]
})

const rules = computed<FormRules>(() => ({
  code: [
    { required: true, message: t('system.businessObject.validation.codeRequired'), trigger: 'blur' },
    { pattern: /^[A-Z][a-zA-Z0-9]*$/, message: t('system.businessObject.validation.codePattern'), trigger: 'blur' }
  ],
  name: [
    { required: true, message: t('system.businessObject.validation.nameRequired'), trigger: 'blur' }
  ],
  tableName: [
    { required: true, message: t('system.businessObject.validation.tableNameRequired'), trigger: 'blur' }
  ]
}))

watch(() => props.visible, (val) => {
  if (val && props.data) {
    // Edit mode - populate form
    Object.assign(formData.value, props.data)
  } else if (val) {
    // Create mode - reset form
    formRef.value?.resetFields()
    formData.value = {
      code: '',
      name: '',
      description: '',
      tableName: '',
      pkField: 'id',
      enableWorkflow: false,
      enableVersion: false,
      enableSoftDelete: true,
      isSystem: false,
      actions: []
    }
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    submitting.value = true
    try {
      // TODO: Replace with actual API call
      if (isEdit.value) {
        // await businessObjectApi.update(props.data.id, formData.value)
      } else {
        // await businessObjectApi.create(formData.value)
      }
      ElMessage.success(isEdit.value ? t('common.messages.operationSuccess') : t('common.messages.operationSuccess'))
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error(t('common.messages.operationFailed'))
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
.info-box {
  background-color: #f4f4f5;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
  font-size: 13px;
  color: #606266;
}
.info-box p {
  margin: 5px 0;
}
</style>
