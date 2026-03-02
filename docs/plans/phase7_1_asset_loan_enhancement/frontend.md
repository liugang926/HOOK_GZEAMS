# Phase 7.1: 资产借用/外借增强 - 前端实现

## 1. 功能概述

### 1.1 前端组件结构

```
frontend/src/views/loans/
├── AssetLoanList.vue           # 借用单列表（扩展）
├── AssetLoanForm.vue           # 借用单表单（扩展）
├── AssetLoanDetail.vue         # 借用单详情（扩展）
├── ExternalLoanForm.vue        # 对外借用表单（新增）
├── LoanDepositList.vue         # 押金记录列表（新增）
├── LoanFeeRuleList.vue         # 计费规则列表（新增）
├── LoanFeeRuleForm.vue         # 计费规则表单（新增）
├── BorrowerCreditList.vue      # 信用记录列表（新增）
├── BorrowerCreditDetail.vue    # 信用记录详情（新增）
└── components/
    ├── BorrowerTypeSelector.vue    # 借用类型选择器（新增）
    ├── ExternalPersonSelector.vue  # 外部人员选择器（新增）
    ├── DepositInfoCard.vue         # 押金信息卡片（新增）
    ├── OverdueFeeCard.vue          # 超期费用卡片（新增）
    ├── CreditScoreDisplay.vue      # 信用分展示（新增）
    └── CreditHistoryTimeline.vue   # 信用历史时间线（新增）

frontend/src/api/
├── loans.js                    # 借用相关API（扩展）
├── deposits.js                 # 押金相关API（新增）
├── feeRules.js                 # 计费规则API（新增）
└── credits.js                  # 信用相关API（新增）

frontend/src/stores/
└── loans.js                    # 借用状态管理（Pinia）
```

### 1.2 公共组件引用

| 组件类型 | 使用组件 | 引用路径 | 说明 |
|---------|---------|---------|------|
| 列表页面 | BaseListPage | @/components/common/BaseListPage.vue | 标准列表页 |
| 表单页面 | BaseFormPage | @/components/common/BaseFormPage.vue | 标准表单页 |
| 详情页面 | BaseDetailPage | @/components/common/BaseDetailPage.vue | 标准详情页 |
| 用户选择 | UserPicker | @/components/common/UserPicker.vue | 用户选择器 |
| 资产选择 | AssetPicker | @/components/assets/AssetPicker.vue | 资产选择器 |
| 文件上传 | FileUpload | @/components/common/FileUpload.vue | 文件上传 |

---

## 2. 借用单列表（扩展）

### 2.1 AssetLoanList.vue

**组件说明**：扩展现有借用单列表，支持内外借用筛选、超期标识、押金/费用显示。

```vue
<template>
  <BaseListPage
    title="资产借用"
    :columns="columns"
    :data-source="loadLoans"
    :search-fields="searchFields"
    @row-click="handleRowClick"
  >
    <template #toolbar>
      <el-button
        type="primary"
        @click="handleCreate('internal')"
      >
        <el-icon><Plus /></el-icon>
        内部借用
      </el-button>
      <el-button
        type="warning"
        @click="handleCreate('external')"
      >
        <el-icon><Plus /></el-icon>
        对外借用
      </el-button>
    </template>

    <template #borrower_type="{ row }">
      <el-tag
        :type="row.borrower_type === 'internal' ? 'success' : 'warning'"
        size="small"
      >
        {{ row.borrower_type === 'internal' ? '内部' : '外部' }}
      </el-tag>
    </template>

    <template #borrower_name="{ row }">
      <div class="borrower-info">
        <span class="name">{{ row.borrower_name }}</span>
        <span v-if="row.borrower_company" class="company">
          {{ row.borrower_company }}
        </span>
      </div>
    </template>

    <template #status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusText(row.status) }}
      </el-tag>
      <el-tag
        v-if="row.is_overdue"
        type="danger"
        size="small"
        class="ml-1"
      >
        超期 {{ row.overdue_days }} 天
      </el-tag>
    </template>

    <template #deposit_status="{ row }">
      <div v-if="row.enable_deposit && row.deposit_status">
        <span>押金: ¥{{ row.deposit_status.amount }}</span>
        <el-tag
          :type="row.deposit_status.status === 'collected' ? 'success' : 'info'"
          size="small"
          class="ml-1"
        >
          {{ row.deposit_status.status === 'collected' ? '已收' : '已退' }}
        </el-tag>
      </div>
      <span v-else-if="row.enable_deposit">未收取</span>
    </template>

    <template #overdue_fee="{ row }">
      <span v-if="row.enable_overdue_fee && row.overdue_fee_total !== '0.00'">
        ¥{{ row.overdue_fee_total }}
      </span>
    </template>

    <template #actions="{ row }">
      <el-button
        link
        type="primary"
        @click.stop="handleView(row)"
      >
        查看
      </el-button>
      <el-dropdown
        v-if="canEdit(row)"
        @command="handleCommand($event, row)"
      >
        <el-button link type="primary">
          更多<el-icon><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              v-if="row.status === 'approved'"
              command="lend"
            >
              确认借出
            </el-dropdown-item>
            <el-dropdown-item
              v-if="row.status === 'borrowed' || row.status === 'overdue'"
              command="return"
            >
              确认归还
            </el-dropdown-item>
            <el-dropdown-item
              v-if="row.enable_deposit && row.deposit_status?.status === 'collected'"
              command="refund"
            >
              退还押金
            </el-dropdown-item>
            <el-dropdown-item command="credit">
              查看信用
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </template>
  </BaseListPage>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, ArrowDown } from '@element-plus/icons-vue'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { getLoans, checkOverdueLoans } from '@/api/loans'

const router = useRouter()

// 列配置
const columns = ref([
  { prop: 'loan_no', label: '借用单号', width: 140 },
  { prop: 'borrower_type', label: '类型', width: 80, slot: true },
  { prop: 'borrower_name', label: '借用人', width: 150, slot: true },
  { prop: 'borrow_date', label: '借用日期', width: 110 },
  { prop: 'expected_return_date', label: '应还日期', width: 110 },
  { prop: 'status', label: '状态', width: 120, slot: true },
  { prop: 'deposit_status', label: '押金', width: 120, slot: true },
  { prop: 'overdue_fee', label: '超期费用', width: 100, slot: true },
  { prop: 'created_at', label: '创建时间', width: 160 }
])

// 搜索字段
const searchFields = ref([
  {
    prop: 'borrower_type',
    label: '借用类型',
    type: 'select',
    options: [
      { label: '全部', value: '' },
      { label: '内部借用', value: 'internal' },
      { label: '对外借用', value: 'external' }
    ]
  },
  {
    prop: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '全部', value: '' },
      { label: '草稿', value: 'draft' },
      { label: '待审批', value: 'pending' },
      { label: '已批准', value: 'approved' },
      { label: '借出中', value: 'borrowed' },
      { label: '已超期', value: 'overdue' },
      { label: '已归还', value: 'returned' }
    ]
  },
  {
    prop: 'is_overdue',
    label: '是否超期',
    type: 'select',
    options: [
      { label: '全部', value: '' },
      { label: '已超期', value: 'true' },
      { label: '未超期', value: 'false' }
    ]
  },
  {
    prop: 'borrow_date_from',
    label: '借用日期起',
    type: 'date'
  },
  {
    prop: 'borrow_date_to',
    label: '借用日期止',
    type: 'date'
  },
  {
    prop: 'keyword',
    label: '关键词',
    type: 'input',
    placeholder: '借用单号/借用人/资产名称'
  }
])

// 加载数据
const loadLoans = async (params) => {
  const response = await getLoans(params)
  return response.data
}

// 状态处理
const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    pending: 'warning',
    approved: 'primary',
    borrowed: 'success',
    overdue: 'danger',
    returned: 'info',
    rejected: 'danger',
    cancelled: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    draft: '草稿',
    pending: '待审批',
    approved: '已批准',
    borrowed: '借出中',
    overdue: '已超期',
    returned: '已归还',
    rejected: '已拒绝',
    cancelled: '已取消'
  }
  return textMap[status] || status
}

// 权限判断
const canEdit = (row) => {
  return ['draft', 'pending', 'approved', 'borrowed', 'overdue'].includes(row.status)
}

// 操作处理
const handleCreate = (type) => {
  if (type === 'external') {
    router.push({ name: 'ExternalLoanCreate' })
  } else {
    router.push({ name: 'AssetLoanCreate' })
  }
}

const handleView = (row) => {
  router.push({
    name: 'AssetLoanDetail',
    params: { id: row.id }
  })
}

const handleRowClick = (row) => {
  handleView(row)
}

const handleCommand = (command, row) => {
  const commands = {
    lend: () => handleLend(row),
    return: () => handleReturn(row),
    refund: () => handleRefundDeposit(row),
    credit: () => handleViewCredit(row)
  }
  commands[command]?.()
}

const handleLend = (row) => {
  router.push({
    name: 'AssetLoanLend',
    params: { id: row.id }
  })
}

const handleReturn = (row) => {
  router.push({
    name: 'AssetLoanReturn',
    params: { id: row.id }
  })
}

const handleRefundDeposit = (row) => {
  router.push({
    name: 'DepositRefund',
    params: { loanId: row.id }
  })
}

const handleViewCredit = (row) => {
  router.push({
    name: 'BorrowerCreditDetail',
    query: { loan_id: row.id }
  })
}
</script>

<style scoped>
.borrower-info {
  display: flex;
  flex-direction: column;
}

.borrower-info .company {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.ml-1 {
  margin-left: 4px;
}
</style>
```

---

## 3. 对外借用表单（新增）

### 3.1 ExternalLoanForm.vue

**组件说明**：创建对外借用单，包含外部人员选择、押金设置、计费设置。

```vue
<template>
  <BaseFormPage
    title="创建对外借用"
    :loading="loading"
    @submit="handleSubmit"
    @cancel="handleCancel"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <!-- 外部人员选择 -->
      <SectionBlock title="借用人信息">
        <el-form-item label="外部人员" prop="borrower_external_id" required>
          <ExternalPersonSelector
            v-model="formData.borrower_external_id"
            :organization="currentOrganization"
            @change="handlePersonChange"
          />
          <el-button
            type="primary"
            link
            class="ml-2"
            @click="showCreatePerson = true"
          >
            新建外部人员
          </el-button>
        </el-form-item>

        <el-form-item label="借用人信息">
          <div v-if="selectedPerson" class="person-info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="姓名">
                {{ selectedPerson.person_name }}
              </el-descriptions-item>
              <el-descriptions-item label="类型">
                {{ selectedPerson.person_type }}
              </el-descriptions-item>
              <el-descriptions-item label="联系电话">
                {{ selectedPerson.phone }}
              </el-descriptions-item>
              <el-descriptions-item label="身份证/信用代码">
                {{ maskIdCard(selectedPerson.id_card) }}
              </el-descriptions-item>
              <el-descriptions-item label="单位" v-if="selectedPerson.company_name">
                {{ selectedPerson.company_name }}
              </el-descriptions-item>
              <el-descriptions-item label="银行账户" v-if="selectedPerson.bank_account">
                {{ selectedPerson.bank_name }} {{ maskBankAccount(selectedPerson.bank_account) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <el-empty v-else description="请选择外部人员" :image-size="80" />
        </el-form-item>

        <!-- 信用信息展示 -->
        <el-form-item v-if="borrowerCredit" label="信用状况">
          <CreditScoreDisplay
            :credit="borrowerCredit"
            :show-history="true"
            @view-history="showCreditHistory = true"
          />
        </el-form-item>
      </SectionBlock>

      <!-- 借用信息 -->
      <SectionBlock title="借用信息">
        <el-form-item label="借用日期" prop="borrow_date" required>
          <el-date-picker
            v-model="formData.borrow_date"
            type="date"
            :disabled-date="disablePastDate"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="预计归还日期" prop="expected_return_date" required>
          <el-date-picker
            v-model="formData.expected_return_date"
            type="date"
            :disabled-date="disableBeforeBorrowDate"
            value-format="YYYY-MM-DD"
          />
          <div class="hint">
            借用期限: {{ loanDays }} 天
          </div>
        </el-form-item>

        <el-form-item label="借用原因" prop="loan_reason">
          <el-input
            v-model="formData.loan_reason"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </SectionBlock>

      <!-- 资产选择 -->
      <SectionBlock title="借用资产">
        <AssetLoanItems
          v-model="formData.items"
          :organization="currentOrganization"
          :status="['idle', 'in_use']"
        />
      </SectionBlock>

      <!-- 押金设置 -->
      <SectionBlock title="押金设置">
        <el-form-item label="是否收取押金">
          <el-switch
            v-model="formData.enable_deposit"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>

        <template v-if="formData.enable_deposit">
          <el-form-item label="押金金额" prop="deposit_amount">
            <el-input-number
              v-model="formData.deposit_amount"
              :min="0"
              :precision="2"
              :step="100"
              controls-position="right"
            />
            <span class="ml-2">元</span>
          </el-form-item>

          <el-form-item label="押金说明">
            <el-input
              v-model="formData.deposit_note"
              type="textarea"
              :rows="2"
              placeholder="如：资产价值较高，收取押金以确保按时归还"
            />
          </el-form-item>
        </template>
      </SectionBlock>

      <!-- 超期计费设置 -->
      <SectionBlock title="超期计费设置">
        <el-form-item label="是否启用计费">
          <el-switch
            v-model="formData.enable_overdue_fee"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>

        <template v-if="formData.enable_overdue_fee">
          <el-form-item label="计费规则" prop="fee_rule_id">
            <FeeRuleSelector
              v-model="formData.fee_rule_id"
              :apply-to="['external']"
            />
          </el-form-item>

          <el-alert
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              启用超期计费后，系统将自动计算超期天数并按规则计费。
              计费从预计归还日期次日开始计算。
            </template>
          </el-alert>
        </template>
      </SectionBlock>
    </el-form>

    <!-- 新建外部人员对话框 -->
    <ExternalPersonForm
      v-model="showCreatePerson"
      @created="handlePersonCreated"
    />

    <!-- 信用历史对话框 -->
    <CreditHistoryDialog
      v-model="showCreditHistory"
      :borrower-type="'external'"
      :borrower-external-id="formData.borrower_external_id"
    />
  </BaseFormPage>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseFormPage from '@/components/common/BaseFormPage.vue'
import SectionBlock from '@/components/common/SectionBlock.vue'
import ExternalPersonSelector from '@/views/loans/components/ExternalPersonSelector.vue'
import AssetLoanItems from '@/views/loans/components/AssetLoanItems.vue'
import CreditScoreDisplay from '@/views/loans/components/CreditScoreDisplay.vue'
import FeeRuleSelector from '@/views/loans/components/FeeRuleSelector.vue'
import ExternalPersonForm from '@/views/system/components/ExternalPersonForm.vue'
import CreditHistoryDialog from '@/views/loans/components/CreditHistoryDialog.vue'
import { createExternalLoan, checkCreditEligibility } from '@/api/loans'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const currentOrganization = computed(() => userStore.organization)

const formRef = ref(null)
const loading = ref(false)
const showCreatePerson = ref(false)
const showCreditHistory = ref(false)
const selectedPerson = ref(null)
const borrowerCredit = ref(null)

const formData = ref({
  borrower_external_id: '',
  borrow_date: new Date().toISOString().split('T')[0],
  expected_return_date: '',
  loan_reason: '',
  items: [],
  enable_deposit: false,
  deposit_amount: 5000,
  deposit_note: '',
  enable_overdue_fee: true,
  fee_rule_id: null
})

const rules = {
  borrower_external_id: [
    { required: true, message: '请选择借用人' }
  ],
  borrow_date: [
    { required: true, message: '请选择借用日期' }
  ],
  expected_return_date: [
    { required: true, message: '请选择预计归还日期' }
  ],
  items: [
    { required: true, message: '请选择借用资产' },
    { type: 'array', min: 1, message: '至少选择一项资产' }
  ],
  deposit_amount: [
    { required: true, message: '请输入押金金额' }
  ]
}

// 计算借用天数
const loanDays = computed(() => {
  if (!formData.value.borrow_date || !formData.value.expected_return_date) {
    return 0
  }
  const start = new Date(formData.value.borrow_date)
  const end = new Date(formData.value.expected_return_date)
  return Math.ceil((end - start) / (1000 * 60 * 60 * 24))
})

// 日期禁用
const disablePastDate = (date) => {
  return date < new Date().setHours(0, 0, 0, 0)
}

const disableBeforeBorrowDate = (date) => {
  if (!formData.value.borrow_date) return false
  return date < new Date(formData.value.borrow_date)
}

// 外部人员变更
const handlePersonChange = async (personId, personData) => {
  selectedPerson.value = personData

  // 检查借用资格
  try {
    const response = await checkCreditEligibility({
      borrower_type: 'external',
      borrower_external_id: personId
    })

    borrowerCredit.value = response.data

    // 资格检查
    if (!response.data.eligible) {
      await ElMessageBox.alert(
        response.data.reason,
        '借用资格检查',
        { type: 'warning' }
      )
    }
  } catch (error) {
    console.error('检查借用资格失败:', error)
  }
}

// 新建人员回调
const handlePersonCreated = (person) => {
  formData.value.borrower_external_id = person.id
  selectedPerson.value = person.dynamic_fields
  handlePersonChange(person.id, person.dynamic_fields)
}

// 脱敏显示
const maskIdCard = (id) => {
  if (!id) return ''
  if (id.length === 18) {
    return id.substring(0, 6) + '********' + id.substring(14)
  }
  return id.substring(0, 8) + '********'
}

const maskBankAccount = (account) => {
  if (!account) return ''
  return account.substring(0, 4) + ' **** **** ' + account.substring(account.length - 4)
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()

    // 资格二次确认
    if (borrowerCredit.value && !borrowerCredit.value.eligible) {
      await ElMessageBox.confirm(
        '该借用人信用状态不佳，是否继续创建借用单？',
        '确认操作',
        { type: 'warning' }
      )
    }

    loading.value = true

    const data = {
      ...formData.value,
      items: formData.value.items.map(item => ({
        asset: item.asset.id,
        quantity: item.quantity || 1,
        remark: item.remark || ''
      }))
    }

    const response = await createExternalLoan(data)

    ElMessage.success('对外借用单创建成功')

    // 跳转到详情页
    router.push({
      name: 'AssetLoanDetail',
      params: { id: response.data.id }
    })
  } catch (error) {
    if (error.errors) {
      // 表单验证错误
      return
    }
    ElMessage.error(error.message || '创建失败')
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  router.back()
}
</script>

<style scoped>
.hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.ml-2 {
  margin-left: 8px;
}

.person-info {
  width: 100%;
}
</style>
```

---

## 4. 外部人员选择器（新增）

### 4.1 ExternalPersonSelector.vue

**组件说明**：选择外部人员组件，支持搜索和新建。

```vue
<template>
  <div class="external-person-selector">
    <el-select
      :model-value="modelValue"
      :placeholder="placeholder"
      :filterable="true"
      :remote="true"
      :remote-method="searchPersons"
      :loading="loading"
      :clearable="clearable"
      :disabled="disabled"
      value-key="id"
      @change="handleChange"
    >
      <el-option
        v-for="person in options"
        :key="person.id"
        :label="person.label"
        :value="person.id"
      >
        <div class="person-option">
          <span class="name">{{ person.dynamic_fields.person_name }}</span>
          <span class="type">{{ person.dynamic_fields.person_type }}</span>
          <span class="phone">{{ person.dynamic_fields.phone }}</span>
        </div>
      </el-option>
      <template #footer>
        <el-button
          text
          style="width: 100%"
          @click="handleCreate"
        >
          <el-icon><Plus /></el-icon>
          新建外部人员
        </el-button>
      </template>
    </el-select>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { getDynamicDataList } from '@/api/system'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请选择外部人员'
  },
  clearable: {
    type: Boolean,
    default: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  organization: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const loading = ref(false)
const options = ref([])

// 加载外部人员列表
const loadPersons = async (keyword = '') => {
  try {
    loading.value = true

    const params = {
      business_object: 'ExternalPerson',
      page: 1,
      page_size: 50
    }

    if (keyword) {
      params.search = keyword
    }

    const response = await getDynamicDataList(params)

    options.value = response.data.results.map(person => ({
      id: person.id,
      data_no: person.data_no,
      dynamic_fields: person.dynamic_fields,
      label: `${person.dynamic_fields.person_name} (${person.dynamic_fields.person_type})`
    }))
  } catch (error) {
    console.error('加载外部人员失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const searchPersons = (keyword) => {
  loadPersons(keyword)
}

// 变更处理
const handleChange = (value) => {
  emit('update:modelValue', value)
  const person = options.value.find(p => p.id === value)
  emit('change', value, person?.dynamic_fields)
}

// 新建处理
const handleCreate = () => {
  emit('create')
}

onMounted(() => {
  loadPersons()
})
</script>

<style scoped>
.person-option {
  display: flex;
  align-items: center;
  gap: 12px;
}

.person-option .name {
  flex: 1;
  font-weight: 500;
}

.person-option .type {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  padding: 2px 6px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}

.person-option .phone {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
```

---

## 5. 押金管理组件（新增）

### 5.1 DepositInfoCard.vue

**组件说明**：押金信息展示卡片，支持收取和退还操作。

```vue
<template>
  <el-card class="deposit-info-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>押金信息</span>
        <el-switch
          v-model="enableDeposit"
          size="small"
          @change="handleEnableChange"
        />
      </div>
    </template>

    <template v-if="enableDeposit">
      <!-- 已收取 -->
      <div v-if="deposit" class="deposit-collected">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="押金单号">
            {{ deposit.deposit_no }}
          </el-descriptions-item>
          <el-descriptions-item label="收取金额">
            <span class="amount">¥{{ deposit.deposit_amount }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="收取日期">
            {{ deposit.deposit_date }}
          </el-descriptions-item>
          <el-descriptions-item label="收取方式">
            <el-tag size="small">
              {{ getPaymentMethodText(deposit.payment_method) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="收款账户" v-if="deposit.payment_account">
            {{ deposit.payment_account }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(deposit.deposit_status)">
              {{ getStatusText(deposit.deposit_status) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="deposit.deposit_status === 'collected'" class="actions">
          <el-button
            type="primary"
            @click="handleRefund"
            :disabled="!canRefund"
          >
            退还押金
          </el-button>
          <el-button @click="handleViewVoucher">
            查看凭证
          </el-button>
        </div>

        <div v-if="deposit.deposit_status === 'refunded'" class="refunded-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="退还金额">
              <span class="amount">¥{{ deposit.refunded_amount }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="退还日期">
              {{ deposit.refunded_date }}
            </el-descriptions-item>
            <el-descriptions-item label="退还原因" :span="2">
              {{ deposit.refund_reason }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <!-- 未收取 -->
      <div v-else class="deposit-not-collected">
        <el-empty
          description="尚未收取押金"
          :image-size="60"
        />
        <el-button
          type="primary"
          @click="handleCollect"
        >
          收取押金
        </el-button>
      </div>
    </template>

    <el-empty v-else description="未启用押金" :image-size="60" />

    <!-- 收取押金对话框 -->
    <CollectDepositDialog
      v-model="showCollectDialog"
      :loan="loan"
      @success="handleCollectSuccess"
    />

    <!-- 退还押金对话框 -->
    <RefundDepositDialog
      v-model="showRefundDialog"
      :loan="loan"
      :deposit="deposit"
      @success="handleRefundSuccess"
    />
  </el-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import CollectDepositDialog from './CollectDepositDialog.vue'
import RefundDepositDialog from './RefundDepositDialog.vue'

const props = defineProps({
  loan: {
    type: Object,
    required: true
  },
  deposit: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['refresh'])

const enableDeposit = ref(props.loan.enable_deposit)
const showCollectDialog = ref(false)
const showRefundDialog = ref(false)

// 是否可以退还
const canRefund = computed(() => {
  return ['returned', 'cancelled'].includes(props.loan.status)
})

const getPaymentMethodText = (method) => {
  const map = {
    cash: '现金',
    transfer: '转账',
    check: '支票',
    other: '其他'
  }
  return map[method] || method
}

const getStatusType = (status) => {
  const map = {
    collected: 'success',
    refunded: 'info',
    cancelled: 'warning'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    collected: '已收取',
    refunded: '已退还',
    cancelled: '已作废'
  }
  return map[status] || status
}

const handleEnableChange = () => {
  // 更新借用单的enable_deposit字段
  emit('refresh')
}

const handleCollect = () => {
  showCollectDialog.value = true
}

const handleRefund = () => {
  showRefundDialog.value = true
}

const handleCollectSuccess = () => {
  ElMessage.success('押金收取成功')
  emit('refresh')
}

const handleRefundSuccess = () => {
  ElMessage.success('押金退还成功')
  emit('refresh')
}

const handleViewVoucher = () => {
  if (props.deposit.refund_voucher) {
    window.open(props.deposit.refund_voucher, '_blank')
  } else {
    ElMessage.info('暂无凭证')
  }
}
</script>

<style scoped>
.deposit-info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.amount {
  font-size: 18px;
  font-weight: bold;
  color: var(--el-color-primary);
}

.actions {
  margin-top: 16px;
  text-align: center;
}

.refunded-info {
  margin-top: 16px;
}

.deposit-not-collected {
  text-align: center;
  padding: 20px 0;
}
</style>
```

---

## 6. 信用展示组件（新增）

### 6.1 CreditScoreDisplay.vue

**组件说明**：信用分展示组件，包含分数、等级、历史趋势。

```vue
<template>
  <div class="credit-score-display">
    <div class="score-main">
      <div class="score-circle" :class="scoreClass">
        <div class="score-value">{{ credit.credit_score }}</div>
        <div class="score-label">信用分</div>
      </div>
      <div class="score-info">
        <div class="level" :class="levelClass">
          {{ credit.credit_level_display }}
        </div>
        <div class="stats">
          <span>累计借用 {{ credit.total_loan_count }} 次</span>
          <span>·</span>
          <span>正常归还 {{ credit.normal_return_count }} 次</span>
        </div>
      </div>
    </div>

    <div class="score-details" v-if="showDetails">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="detail-item">
            <div class="value">{{ credit.overdue_count }}</div>
            <div class="label">超期次数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="detail-item warning">
            <div class="value">{{ credit.damage_count }}</div>
            <div class="label">损坏次数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="detail-item danger">
            <div class="value">{{ credit.lost_count }}</div>
            <div class="label">遗失次数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="detail-item">
            <div class="value">{{ credit.total_overdue_days }}</div>
            <div class="label">累计超期天数</div>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="score-actions" v-if="showHistory">
      <el-button link type="primary" @click="$emit('view-history')">
        查看历史记录
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  credit: {
    type: Object,
    required: true
  },
  showDetails: {
    type: Boolean,
    default: true
  },
  showHistory: {
    type: Boolean,
    default: true
  }
})

defineEmits(['view-history'])

const scoreClass = computed(() => {
  const score = props.credit.credit_score
  if (score >= 90) return 'excellent'
  if (score >= 75) return 'good'
  if (score >= 60) return 'normal'
  if (score >= 40) return 'poor'
  return 'blacklisted'
})

const levelClass = computed(() => {
  const level = props.credit.credit_level
  const map = {
    excellent: 'excellent',
    good: 'good',
    normal: 'normal',
    poor: 'poor',
    blacklisted: 'blacklisted'
  }
  return map[level] || ''
})
</script>

<style scoped>
.credit-score-display {
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.score-main {
  display: flex;
  align-items: center;
  gap: 20px;
}

.score-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 4px solid;
}

.score-circle.excellent {
  border-color: var(--el-color-success);
  background: rgba(var(--el-color-success-rgb), 0.1);
}

.score-circle.good {
  border-color: var(--el-color-primary);
  background: rgba(var(--el-color-primary-rgb), 0.1);
}

.score-circle.normal {
  border-color: var(--el-color-warning);
  background: rgba(var(--el-color-warning-rgb), 0.1);
}

.score-circle.poor {
  border-color: var(--el-color-danger);
  background: rgba(var(--el-color-danger-rgb), 0.1);
}

.score-circle.blacklisted {
  border-color: #000;
  background: rgba(0, 0, 0, 0.1);
}

.score-value {
  font-size: 28px;
  font-weight: bold;
  line-height: 1;
}

.score-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.score-info {
  flex: 1;
}

.level {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 8px;
}

.level.excellent {
  color: var(--el-color-success);
}

.level.good {
  color: var(--el-color-primary);
}

.level.normal {
  color: var(--el-color-warning);
}

.level.poor,
.level.blacklisted {
  color: var(--el-color-danger);
}

.stats {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.stats span {
  margin: 0 4px;
}

.score-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color);
}

.detail-item {
  text-align: center;
  padding: 12px;
  background: var(--el-bg-color);
  border-radius: 8px;
}

.detail-item .value {
  font-size: 20px;
  font-weight: bold;
  line-height: 1;
}

.detail-item .label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.detail-item.warning .value {
  color: var(--el-color-warning);
}

.detail-item.danger .value {
  color: var(--el-color-danger);
}

.score-actions {
  margin-top: 12px;
  text-align: center;
}
</style>
```

---

## 7. 信用历史时间线（新增）

### 7.1 CreditHistoryTimeline.vue

**组件说明**：信用历史时间线展示。

```vue
<template>
  <div class="credit-history-timeline">
    <el-timeline>
      <el-timeline-item
        v-for="item in history"
        :key="item.id"
        :timestamp="item.event_date"
        :type="getTimelineType(item.event_type)"
        placement="top"
      >
        <div class="timeline-item">
          <div class="event-type">
            <el-tag :type="getEventTypeColor(item.event_type)" size="small">
              {{ item.event_type_display }}
            </el-tag>
            <span v-if="item.score_change !== 0" class="score-change">
              <span :class="{ positive: item.score_change > 0, negative: item.score_change < 0 }">
                {{ item.score_change > 0 ? '+' : '' }}{{ item.score_change }}
              </span>
            </span>
          </div>
          <div class="event-description">{{ item.event_description }}</div>
          <div v-if="item.loan_no" class="related-info">
            <el-link type="primary" :href="`/loans/${item.loan}`" target="_blank">
              {{ item.loan_no }}
            </el-link>
            <span v-if="item.asset_name">· {{ item.asset_name }}</span>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>

    <el-empty
      v-if="history.length === 0"
      description="暂无信用记录"
      :image-size="80"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  history: {
    type: Array,
    default: () => []
  }
})

const getTimelineType = (eventType) => {
  const positiveEvents = ['returned_normal']
  const negativeEvents = ['returned_overdue_long', 'returned_overdue_severe', 'asset_damaged_minor', 'asset_damaged_severe', 'asset_lost']

  if (positiveEvents.includes(eventType)) return 'success'
  if (negativeEvents.includes(eventType)) return 'danger'
  return 'primary'
}

const getEventTypeColor = (eventType) => {
  const map = {
    returned_normal: 'success',
    returned_overdue_short: 'warning',
    returned_overdue_long: 'warning',
    returned_overdue_severe: 'danger',
    asset_damaged_minor: 'warning',
    asset_damaged_severe: 'danger',
    asset_lost: 'danger',
    credit_manual_adjust: 'info'
  }
  return map[eventType] || ''
}
</script>

<style scoped>
.credit-history-timeline {
  padding: 16px 0;
}

.timeline-item {
  padding-bottom: 8px;
}

.event-type {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.score-change {
  font-weight: bold;
}

.score-change.positive {
  color: var(--el-color-success);
}

.score-change.negative {
  color: var(--el-color-danger);
}

.event-description {
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
}

.related-info {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
```

---

## 8. API封装

### 8.1 loans.js（扩展）

```javascript
// frontend/src/api/loans.js
import request from '@/utils/request'

// 借用单列表
export function getLoans(params) {
  return request({
    url: '/loans/asset-loans/',
    method: 'get',
    params
  })
}

// 借用单详情
export function getLoanDetail(id) {
  return request({
    url: `/loans/asset-loans/${id}/`,
    method: 'get'
  })
}

// 创建内部借用
export function createLoan(data) {
  return request({
    url: '/loans/asset-loans/',
    method: 'post',
    data
  })
}

// 创建对外借用
export function createExternalLoan(data) {
  return request({
    url: '/loans/asset-loans/external/',
    method: 'post',
    data
  })
}

// 更新借用单
export function updateLoan(id, data) {
  return request({
    url: `/loans/asset-loans/${id}/`,
    method: 'put',
    data
  })
}

// 确认借出
export function confirmLend(id, data) {
  return request({
    url: `/loans/asset-loans/${id}/lend/`,
    method: 'post',
    data
  })
}

// 确认归还
export function confirmReturn(id, data) {
  return request({
    url: `/loans/asset-loans/${id}/return/`,
    method: 'post',
    data
  })
}

// 收取押金
export function collectDeposit(id, data) {
  return request({
    url: `/loans/asset-loans/${id}/collect-deposit/`,
    method: 'post',
    data
  })
}

// 退还押金
export function refundDeposit(id, data) {
  return request({
    url: `/loans/asset-loans/${id}/refund-deposit/`,
    method: 'post',
    data
  })
}

// 计算超期费用
export function calculateOverdueFee(id) {
  return request({
    url: `/loans/asset-loans/${id}/calculate-overdue-fee/`,
    method: 'post'
  })
}

// 获取借用人信用
export function getBorrowerCredit(id) {
  return request({
    url: `/loans/asset-loans/${id}/borrower-credit/`,
    method: 'get'
  })
}

// 更新信用分
export function updateCredit(id, data) {
  return request({
    url: `/loans/asset-loans/${id}/update-credit/`,
    method: 'post',
    data
  })
}

// 批量计算超期费用
export function batchCalculateFee(data) {
  return request({
    url: '/loans/asset-loans/batch-calculate-fee/',
    method: 'post',
    data
  })
}
```

### 8.2 deposits.js（新增）

```javascript
// frontend/src/api/deposits.js
import request from '@/utils/request'

// 押金记录列表
export function getDeposits(params) {
  return request({
    url: '/loans/deposits/',
    method: 'get',
    params
  })
}

// 押金汇总
export function getDepositSummary() {
  return request({
    url: '/loans/deposits/summary/',
    method: 'get'
  })
}

// 押金详情
export function getDepositDetail(id) {
  return request({
    url: `/loans/deposits/${id}/`,
    method: 'get'
  })
}

// 批量退还押金
export function batchRefundDeposit(data) {
  return request({
    url: '/loans/deposits/batch-refund/',
    method: 'post',
    data
  })
}
```

### 8.3 credits.js（新增）

```javascript
// frontend/src/api/credits.js
import request from '@/utils/request'

// 信用记录列表
export function getCredits(params) {
  return request({
    url: '/loans/credits/',
    method: 'get',
    params
  })
}

// 获取我的信用
export function getMyCredit() {
  return request({
    url: '/loans/credits/my-credit/',
    method: 'get'
  })
}

// 信用记录详情
export function getCreditDetail(id) {
  return request({
    url: `/loans/credits/${id}/`,
    method: 'get'
  })
}

// 信用历史
export function getCreditHistory(id, params) {
  return request({
    url: `/loans/credits/${id}/history/`,
    method: 'get',
    params
  })
}

// 检查借用资格
export function checkCreditEligibility(data) {
  return request({
    url: '/loans/credits/check-eligibility/',
    method: 'post',
    data
  })
}
```

---

## 9. 路由配置

```javascript
// frontend/src/router/modules/loans.js
export default {
  path: '/loans',
  name: 'Loans',
  component: () => import('@/layouts/DefaultLayout.vue'),
  meta: { title: '资产借用', icon: 'Notebook' },
  children: [
    {
      path: '',
      name: 'AssetLoanList',
      component: () => import('@/views/loans/AssetLoanList.vue'),
      meta: { title: '借用单列表', cache: true }
    },
    {
      path: 'create',
      name: 'AssetLoanCreate',
      component: () => import('@/views/loans/AssetLoanForm.vue'),
      meta: { title: '创建内部借用', activeMenu: '/loans' }
    },
    {
      path: 'external/create',
      name: 'ExternalLoanCreate',
      component: () => import('@/views/loans/ExternalLoanForm.vue'),
      meta: { title: '创建对外借用', activeMenu: '/loans' }
    },
    {
      path: ':id',
      name: 'AssetLoanDetail',
      component: () => import('@/views/loans/AssetLoanDetail.vue'),
      meta: { title: '借用单详情', activeMenu: '/loans', cache: true }
    },
    {
      path: ':id/lend',
      name: 'AssetLoanLend',
      component: () => import('@/views/loans/AssetLoanLend.vue'),
      meta: { title: '确认借出', activeMenu: '/loans' }
    },
    {
      path: ':id/return',
      name: 'AssetLoanReturn',
      component: () => import('@/views/loans/AssetLoanReturn.vue'),
      meta: { title: '确认归还', activeMenu: '/loans' }
    },
    {
      path: 'deposits',
      name: 'LoanDepositList',
      component: () => import('@/views/loans/LoanDepositList.vue'),
      meta: { title: '押金记录', activeMenu: '/loans' }
    },
    {
      path: 'credits',
      name: 'BorrowerCreditList',
      component: () => import('@/views/loans/BorrowerCreditList.vue'),
      meta: { title: '信用记录', activeMenu: '/loans' }
    },
    {
      path: 'credits/:id',
      name: 'BorrowerCreditDetail',
      component: () => import('@/views/loans/BorrowerCreditDetail.vue'),
      meta: { title: '信用详情', activeMenu: '/loans' }
    },
    {
      path: 'fee-rules',
      name: 'LoanFeeRuleList',
      component: () => import('@/views/loans/LoanFeeRuleList.vue'),
      meta: { title: '计费规则', activeMenu: '/loans' }
    }
  ]
}
```

---

## 10. 状态管理（Pinia）

```javascript
// frontend/src/stores/loans.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getLoans, getLoanDetail } from '@/api/loans'

export const useLoanStore = defineStore('loans', () => {
  // 状态
  const loanList = ref([])
  const currentLoan = ref(null)
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    pageSize: 20,
    total: 0
  })

  // 计算属性
  const overdueLoans = computed(() => {
    return loanList.value.filter(loan => loan.is_overdue)
  })

  const externalLoans = computed(() => {
    return loanList.value.filter(loan => loan.borrower_type === 'external')
  })

  // Actions
  const fetchLoans = async (params = {}) => {
    loading.value = true
    try {
      const response = await getLoans({
        page: pagination.value.page,
        page_size: pagination.value.pageSize,
        ...params
      })

      loanList.value = response.data.results
      pagination.value.total = response.data.count
    } catch (error) {
      console.error('获取借用单列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  const fetchLoanDetail = async (id) => {
    loading.value = true
    try {
      const response = await getLoanDetail(id)
      currentLoan.value = response.data
      return response.data
    } catch (error) {
      console.error('获取借用单详情失败:', error)
    } finally {
      loading.value = false
    }
  }

  const clearCurrentLoan = () => {
    currentLoan.value = null
  }

  return {
    // 状态
    loanList,
    currentLoan,
    loading,
    pagination,

    // 计算属性
    overdueLoans,
    externalLoans,

    // Actions
    fetchLoans,
    fetchLoanDetail,
    clearCurrentLoan
  }
})
```
