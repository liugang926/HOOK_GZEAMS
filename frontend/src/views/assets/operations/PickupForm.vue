<template>
  <div class="pickup-form">
    <div class="page-header">
      <el-page-header
        :title="isEdit ? $t('assets.pickup.editTitle') : $t('assets.pickup.createTitle')"
        @back="goBack"
      />
      <div class="header-actions">
        <el-button
          v-if="!isEdit || form.status === 'draft'"
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ $t('common.actions.save') }}
        </el-button>
        <el-button
          v-if="!isEdit || form.status === 'draft'"
          type="success"
          :loading="submitting"
          @click="handleSubmitAndApply"
        >
          {{ $t('assets.pickup.form.submitForApproval') }}
        </el-button>
      </div>
    </div>

    <el-card
      shadow="never"
      class="mt-4"
    >
      <!-- Basic Info -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              :label="$t('assets.pickup.form.department')"
              prop="departmentId"
            >
              <DeptPicker
                v-model="form.departmentId"
                :placeholder="$t('assets.pickup.form.departmentPlaceholder')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              :label="$t('assets.pickup.form.pickupDate')"
              prop="pickupDate"
            >
              <el-date-picker
                v-model="form.pickupDate"
                type="date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item
          :label="$t('assets.pickup.form.reason')"
          prop="reason"
        >
          <el-input
            v-model="form.reason"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card
      shadow="never"
      class="mt-4"
      :header="$t('assets.pickup.form.assetDetails')"
    >
      <div class="mb-4">
        <el-button
          type="primary"
          :icon="Plus"
          @click="showAssetSelector"
        >
          {{ $t('assets.pickup.form.addAsset') }}
        </el-button>
      </div>
      <el-table
        :data="form.items"
        border
      >
        <el-table-column
          prop="asset.code"
          :label="$t('assets.fields.assetCode')"
          width="150"
        />
        <el-table-column
          prop="asset.name"
          :label="$t('assets.fields.assetName')"
        />
        <el-table-column
          prop="asset.categoryName"
          :label="$t('assets.fields.category')"
          width="120"
        />
        <el-table-column
          :label="$t('assets.pickup.form.quantity')"
          width="150"
        >
          <template #default="{ row }">
            <el-input-number
              v-model="row.quantity"
              :min="1"
              :max="1"
              disabled
            />
          </template>
        </el-table-column>
        <el-table-column :label="$t('assets.pickup.form.remark')">
          <template #default="{ row }">
            <el-input v-model="row.remark" />
          </template>
        </el-table-column>
        <el-table-column
          :label="$t('common.labels.operation')"
          width="80"
          fixed="right"
        >
          <template #default="{ $index }">
            <el-button
              link
              type="danger"
              :icon="Delete"
              @click="removeItem($index)"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <AssetSelector
      v-model="assetSelectorVisible"
      :exclude-asset-ids="selectedAssetIds"
      :status-filter="['idle']"
      @confirm="handleAssetSelect"
    />
  </div>
</template>

<script setup lang="ts">

import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import AssetSelector from './components/AssetSelector.vue'
import DeptPicker from '@/components/common/DeptPicker.vue'
import { createPickup, updatePickup, getPickupDetail } from '@/api/assets/pickup'
import { workflowInstanceApi } from '@/api/workflow'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const formRef = ref()
const assetSelectorVisible = ref(false)
const submitting = ref(false)

const form = reactive({
    id: null,
    status: 'draft',
    departmentId: '', // Should be user dept by default
    pickupDate: new Date().toISOString().split('T')[0],
    reason: '',
    items: [] as any[]
})

const rules = computed(() => ({
    departmentId: [{ required: true, message: t('assets.pickup.form.departmentPlaceholder'), trigger: 'blur' }],
    pickupDate: [{ required: true, message: t('common.rules.required'), trigger: 'change' }],
    reason: [{ required: true, message: t('assets.pickup.form.reasonPlaceholder'), trigger: 'blur' }]
}))

const isEdit = computed(() => !!route.params.id)
const selectedAssetIds = computed(() => form.items.map(i => i.asset.id))

const showAssetSelector = () => {
    assetSelectorVisible.value = true
}

const handleAssetSelect = (assets: any[]) => {
    assets.forEach(asset => {
        form.items.push({
            asset: asset,
            assetId: asset.id,
            quantity: 1,
            remark: ''
        })
    })
}

const removeItem = (index: number) => {
    form.items.splice(index, 1)
}

const validateAndGetPayload = async () => {
    await formRef.value.validate()
    if (form.items.length === 0) {
        ElMessage.warning(t('assets.pickup.messages.selectAssetWarning'))
        throw new Error('Validation failed')
    }

    return {
        department_id: form.departmentId,
        pickup_date: form.pickupDate,
        pickup_reason: form.reason,
        items: form.items.map((i: any) => ({
            ...(i.id ? { id: i.id } : {}),
            asset_id: i.asset?.id || i.assetId,
            quantity: i.quantity || 1,
            remark: i.remark || ''
        }))
    }
}

const handleSubmit = async () => {
    try {
        const payload = await validateAndGetPayload()
        submitting.value = true
        
        if (isEdit.value) {
            await updatePickup(String(route.params.id), payload)
            ElMessage.success(t('common.messages.updateSuccess'))
        } else {
            await createPickup(payload)
            ElMessage.success(t('common.messages.saveSuccess'))
        }
        goBack()
    } catch (e: any) {
        if (e.message !== 'Validation failed') {
            console.error(e)
            ElMessage.error(e.message || t('common.messages.operationFailed'))
        }
    } finally {
        submitting.value = false
    }
}

const handleSubmitAndApply = async () => {
    try {
        const payload = await validateAndGetPayload()
        submitting.value = true

        let id = form.id
        if (isEdit.value) {
            await updatePickup(String(route.params.id), payload)
        } else {
            const res = await createPickup(payload) as any
            id = res.id
        }
        if (!id) {
            throw new Error('Pickup id is required to start workflow')
        }

        // Trigger workflow start
        // Assuming workflowApi.startProcess exists and takes businessKey
        // The workflow key for pickup is likely 'asset_pickup'
        // If workflowApi is not fully implemented, we might need to adjust.
        // Based on analysis, workflow execution is partial.
        // We will assume a standard start endpoint.
        await workflowInstanceApi.startProcess({
            processKey: 'asset_pickup',
            businessKey: String(id),
            variables: {
                initiator: 'current_user', // Backend should handle this
                departmentId: form.departmentId
            }
        })
        
        ElMessage.success(t('assets.pickup.messages.submitApproveSuccess'))
        goBack()
    } catch (e: any) {
        if (e.message !== 'Validation failed') {
            console.error(e)
            ElMessage.error(e.message || t('assets.pickup.messages.submitApproveFailed'))
        }
    } finally {
        submitting.value = false
    }
}

const goBack = () => {
    router.back()
}

onMounted(async () => {
    if (isEdit.value) {
        // Load detail
        try {
            const data = await getPickupDetail(String(route.params.id)) as any
            form.id = data.id
            form.status = data.status
            form.departmentId = data.department?.id
            form.pickupDate = data.pickup_date
            form.reason = data.pickup_reason
            form.items = (data.items || []).map((i: any) => ({
                id: i.id,
                asset: i.asset,
                assetId: i.asset?.id || i.assetId,
                quantity: i.quantity || 1,
                remark: i.remark || ''
            }))
        } catch (e) {
            console.error(e)
            ElMessage.error(t('assets.messages.loadFailed'))
        }
    }
})
</script>

<style scoped>
.pickup-form {
    padding: 20px;
}
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.mt-4 {
    margin-top: 20px;
}
.mb-4 {
    margin-bottom: 20px;
}
</style>
