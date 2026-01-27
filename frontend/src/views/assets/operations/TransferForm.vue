<template>
  <div class="transfer-form">
    <div class="page-header">
      <el-page-header
        title="新建调拨单"
        @back="goBack"
      />
      <div class="header-actions">
        <!-- Only support create mode for now per original file logic which lacked edit support -->
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          提交申请
        </el-button>
        <el-button
          type="success"
          :loading="submitting"
          @click="handleSubmitAndApply"
        >
          提交审批
        </el-button>
      </div>
    </div>

    <el-card
      shadow="never"
      class="mt-4"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item
          label="选择资产"
          prop="assetId"
        >
          <div
            v-if="selectedAsset"
            class="selected-asset"
          >
            <span>{{ selectedAsset.name }} ({{ selectedAsset.code }})</span>
            <el-button
              link
              type="primary"
              @click="showAssetSelector"
            >
              重新选择
            </el-button>
          </div>
          <el-button
            v-else
            type="primary"
            plain
            @click="showAssetSelector"
          >
            点击选择资产
          </el-button>
        </el-form-item>

        <el-form-item
          label="调入位置"
          prop="toLocationId"
        >
          <!-- Placeholder for LocationTree -->
          <el-input
            v-model="form.toLocationId"
            placeholder="请输入目标位置ID"
          />
        </el-form-item>

        <el-form-item
          label="接收人"
          prop="toUserId"
        >
          <UserPicker
            v-model="form.toUserId"
            placeholder="请选择接收人"
          />
        </el-form-item>

        <el-form-item
          label="调拨原因"
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

    <AssetSelector
      v-model="assetSelectorVisible"
      :status-filter="['idle', 'in_use']"
      @confirm="handleAssetSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AssetSelector from './components/AssetSelector.vue'
import UserPicker from '@/components/common/UserPicker.vue'
import { transferApi } from '@/api/assets'
import { workflowInstanceApi } from '@/api/workflow'

const router = useRouter()
const formRef = ref()
const assetSelectorVisible = ref(false)
const selectedAsset = ref<any>(null)
const submitting = ref(false)

const form = reactive({
    assetId: '',
    toLocationId: '',
    toUserId: '',
    reason: ''
})

const rules = {
    assetId: [{ required: true, message: '请选择资产', trigger: 'change' }],
    toLocationId: [{ required: true, message: '请选择目标位置', trigger: 'change' }],
    reason: [{ required: true, message: '请填写原因', trigger: 'blur' }]
}

const showAssetSelector = () => {
    assetSelectorVisible.value = true
}

const handleAssetSelect = (assets: any[]) => {
    if (assets.length > 0) {
        // Transfer usually involves one asset per request or bulk? 
        // PRD implies single or list. API seems to take one assetId per call or we loop.
        // Let's assume single for now based on API definition transferApi.create taking assetId string.
        const asset = assets[0]
        selectedAsset.value = asset
        form.assetId = asset.id
        // If bulk needed, we can adapt later.
    }
}

const validateAndGetPayload = async () => {
    await formRef.value.validate()
    return {
        assetId: form.assetId,
        toLocationId: form.toLocationId,
        toUserId: form.toUserId,
        reason: form.reason
    }
}

const handleSubmit = async () => {
    try {
        const payload = await validateAndGetPayload()
        submitting.value = true
        await transferApi.create(payload)
        ElMessage.success('提交成功')
        goBack()
    } catch (e: any) {
        if (e.message !== 'Validation failed') {
           ElMessage.error(e.message || '提交失败')
        }
    } finally {
        submitting.value = false
    }
}

const handleSubmitAndApply = async () => {
    try {
        const payload = await validateAndGetPayload()
        submitting.value = true
        
        // Setup usually is create -> then start workflow with returned ID.
        // Assuming transferApi.create returns the transfer record with ID.
        const res = await transferApi.create(payload)
        const id = res.id || res // Adjust based on actual API return

        // Trigger workflow
        await workflowInstanceApi.startProcess({
            processKey: 'asset_transfer',
            businessKey: id,
            variables: {
                initiator: 'current_user'
            }
        })

        ElMessage.success('提交审批成功')
        goBack()
    } catch (e: any) {
        if (e.message !== 'Validation failed') {
            ElMessage.error(e.message || '提交审批失败')
        }
    } finally {
        submitting.value = false
    }
}

const goBack = () => {
    router.back()
}
</script>

<style scoped>
.transfer-form { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.mt-4 { margin-top: 20px; }
.selected-asset { display: flex; align-items: center; gap: 10px; }
</style>
