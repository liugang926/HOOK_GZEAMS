<template>
  <div class="loan-form">
    <div class="page-header">
      <el-page-header
        :title="isEdit ? '编辑借出单' : '新建借出单'"
        @back="goBack"
      />
      <div class="header-actions">
        <el-button
          v-if="!isEdit || form.status === 'draft'"
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          保存
        </el-button>
        <el-button
          v-if="!isEdit || form.status === 'draft'"
          type="success"
          :loading="submitting"
          @click="handleSubmitAndApprove"
        >
          提交审批
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
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              label="借用人"
              prop="borrowerId"
            >
              <UserPicker
                v-model="form.borrowerId"
                placeholder="请选择借用人"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              label="借出日期"
              prop="loanDate"
            >
              <el-date-picker
                v-model="form.loanDate"
                type="date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              label="预计归还日期"
              prop="expectedReturnDate"
            >
              <el-date-picker
                v-model="form.expectedReturnDate"
                type="date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否需要押金">
              <el-switch v-model="form.requiresDeposit" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row
          v-if="form.requiresDeposit"
          :gutter="20"
        >
          <el-col :span="12">
            <el-form-item
              label="押金金额"
              prop="depositAmount"
            >
              <el-input-number
                v-model="form.depositAmount"
                :min="0"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item
          label="借出原因"
          prop="reason"
        >
          <el-input
            v-model="form.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入借出原因"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card
      shadow="never"
      class="mt-4"
      header="借出资产明细"
    >
      <div class="mb-4">
        <el-button
          type="primary"
          :icon="Plus"
          @click="showAssetSelector"
        >
          添加资产
        </el-button>
      </div>
      <el-table
        :data="form.items"
        border
      >
        <el-table-column
          prop="asset.code"
          label="资产编码"
          width="150"
        />
        <el-table-column
          prop="asset.name"
          label="资产名称"
        />
        <el-table-column
          prop="asset.categoryName"
          label="分类"
          width="120"
        />
        <el-table-column
          label="数量"
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
        <el-table-column label="备注">
          <template #default="{ row }">
            <el-input v-model="row.remark" />
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
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
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import AssetSelector from './components/AssetSelector.vue'
import UserPicker from '@/components/common/UserPicker.vue'
import { createLoan, updateLoan, getLoanDetail } from '@/api/assets/loans'
import { workflowInstanceApi } from '@/api/workflow'

const route = useRoute()
const router = useRouter()

const formRef = ref()
const assetSelectorVisible = ref(false)
const submitting = ref(false)

const form = reactive({
    id: null,
    status: 'draft',
    borrowerId: '',
    loanDate: new Date().toISOString().split('T')[0],
    expectedReturnDate: '',
    requiresDeposit: false,
    depositAmount: 0,
    reason: '',
    items: [] as any[]
})

const rules = {
    borrowerId: [{ required: true, message: '请选择借用人', trigger: 'change' }],
    loanDate: [{ required: true, message: '请选择借出日期', trigger: 'change' }],
    expectedReturnDate: [{ required: true, message: '请选择预计归还日期', trigger: 'change' }],
    reason: [{ required: true, message: '请填写借出原因', trigger: 'blur' }]
}

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
        ElMessage.warning('请至少添加一项资产')
        throw new Error('Validation failed')
    }

    const payload: any = {
        borrower_id: form.borrowerId,
        loan_date: form.loanDate,
        expected_return_date: form.expectedReturnDate,
        reason: form.reason,
        items: form.items.map((i: any) => ({
            asset_id: i.asset.id,
            remark: i.remark
        }))
    }

    if (form.requiresDeposit) {
        payload.deposit_amount = form.depositAmount
    }

    return payload
}

const handleSubmit = async () => {
    try {
        const payload = await validateAndGetPayload()
        submitting.value = true

        if (isEdit.value) {
            await updateLoan(String(route.params.id), payload)
            ElMessage.success('更新成功')
        } else {
            await createLoan(payload)
            ElMessage.success('保存成功')
        }
        goBack()
    } catch (e: any) {
        if (e.message !== 'Validation failed') {
            console.error(e)
            ElMessage.error(e.message || '操作失败')
        }
    } finally {
        submitting.value = false
    }
}

const handleSubmitAndApprove = async () => {
    try {
        const payload = await validateAndGetPayload()
        submitting.value = true

        let id = form.id
        if (isEdit.value) {
            await updateLoan(String(route.params.id), payload)
        } else {
            const res = await createLoan(payload)
            id = res.id
        }

        // Trigger workflow start
        await workflowInstanceApi.startProcess({
            processKey: 'asset_loan',
            businessKey: id,
            variables: {
                initiator: 'current_user',
                borrowerId: form.borrowerId
            }
        })

        ElMessage.success('提交审批成功')
        goBack()
    } catch (e: any) {
        if (e.message !== 'Validation failed') {
            console.error(e)
            ElMessage.error(e.message || '提交审批失败')
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
        try {
            const data = await getLoanDetail(String(route.params.id))
            form.id = data.id
            form.status = data.status
            form.borrowerId = data.borrower?.id
            form.loanDate = data.loan_date
            form.expectedReturnDate = data.expected_return_date
            form.requiresDeposit = data.requires_deposit || false
            form.depositAmount = data.deposit_amount || 0
            form.reason = data.reason
            form.items = (data.items || []).map((i: any) => ({
                asset: i.asset,
                assetId: i.asset.id,
                quantity: 1,
                remark: i.remark
            }))
        } catch (e) {
            console.error(e)
            ElMessage.error('加载失败')
        }
    }
})
</script>

<style scoped>
.loan-form {
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
