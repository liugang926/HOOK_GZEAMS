<template>
  <div class="return-form">
    <div class="page-header">
      <el-page-header
        :title="$t('assets.return.createTitle')"
        @back="goBack"
      />
      <div class="header-actions">
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ $t('common.actions.submit') }}
        </el-button>
        <el-button
          type="success"
          :loading="submitting"
          @click="handleSubmitAndApply"
        >
          {{ $t('assets.return.messages.submitApproveSuccess') }}
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
          :label="$t('assets.return.form.selectAsset')"
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
              {{ $t('assets.return.form.reselectAsset') }}
            </el-button>
          </div>
          <el-button
            v-else
            type="primary"
            plain
            @click="showAssetSelector"
          >
            {{ $t('assets.return.form.selectAssetButton') }}
          </el-button>
        </el-form-item>

        <el-form-item
          :label="$t('assets.return.form.returnDate')"
          prop="returnDate"
        >
          <el-date-picker
            v-model="form.returnDate"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item
          :label="$t('assets.return.form.reason')"
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
      :status-filter="['in_use']"
      @confirm="handleAssetSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import AssetSelector from './components/AssetSelector.vue'
import { returnApi } from '@/api/assets/return'
import { workflowInstanceApi } from '@/api/workflow'

const router = useRouter()
const { t } = useI18n()
const formRef = ref()
const assetSelectorVisible = ref(false)
const selectedAsset = ref<any>(null)
const submitting = ref(false)

const form = reactive({
    assetId: '',
    returnDate: new Date().toISOString().split('T')[0],
    reason: ''
})

const rules = computed(() => ({
    assetId: [{ required: true, message: t('assets.return.form.selectAsset'), trigger: 'change' }],
    returnDate: [{ required: true, message: t('form.validation.required'), trigger: 'change' }],
    reason: [{ required: true, message: t('assets.return.form.reasonPlaceholder'), trigger: 'blur' }]
}))

const showAssetSelector = () => {
    assetSelectorVisible.value = true
}

const handleAssetSelect = (assets: any[]) => {
    if (assets.length > 0) {
        const asset = assets[0]
        selectedAsset.value = asset
        form.assetId = asset.id
    }
}

const validateAndGetPayload = async () => {
    await formRef.value.validate()
    return {
        assetId: form.assetId,
        returnDate: form.returnDate,
        reason: form.reason
    }
}

const handleSubmit = async () => {
    try {
        const payload = await validateAndGetPayload()
        submitting.value = true
        await returnApi.create(payload)
        ElMessage.success(t('assets.return.messages.submitSuccess'))
        goBack()
    } catch (e: any) {
        if (e.message !== 'Validation failed') {
            ElMessage.error(e.message || t('assets.return.messages.submitFailed'))
        }
    } finally {
        submitting.value = false
    }
}

const handleSubmitAndApply = async () => {
    try {
        const payload = await validateAndGetPayload()
        submitting.value = true

        const res = await returnApi.create(payload) as any
        const id = res.id || res

        await workflowInstanceApi.startProcess({
            processKey: 'asset_return',
            businessKey: id,
            variables: {
                initiator: 'current_user'
            }
        })
        
        ElMessage.success(t('assets.return.messages.submitApproveSuccess'))
        goBack()
    } catch (e: any) {
        if (e.message !== 'Validation failed') {
            ElMessage.error(e.message || t('assets.return.messages.submitApproveFailed'))
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
.return-form { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.mt-4 { margin-top: 20px; }
.selected-asset { display: flex; align-items: center; gap: 10px; }
</style>
