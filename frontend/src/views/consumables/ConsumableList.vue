<template>
  <div class="consumable-list">
    <div class="page-header">
      <h3>耗材管理</h3>
      <div class="actions">
        <el-button
          type="success"
          @click="handleStockIn"
        >
          入库
        </el-button>
        <el-button
          type="warning"
          @click="handleStockOut"
        >
          领用/出库
        </el-button>
        <el-button
          type="primary"
          @click="handleCreate"
        >
          新建耗材
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <el-form
      inline
      :model="searchForm"
      class="search-form"
    >
      <el-form-item label="名称/编码">
        <el-input
          v-model="searchForm.search"
          placeholder="输入名称或编码"
        />
      </el-form-item>
      <el-form-item label="类别">
        <el-select
          v-model="searchForm.category"
          placeholder="全部"
          clearable
        >
          <el-option
            label="办公用品"
            value="office"
          />
          <el-option
            label="IT耗材"
            value="it"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          @click="fetchData"
        >
          查询
        </el-button>
      </el-form-item>
    </el-form>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
    >
      <el-table-column
        prop="code"
        label="编码"
        width="120"
      />
      <el-table-column
        prop="name"
        label="名称"
        width="150"
      />
      <el-table-column
        prop="category"
        label="类别"
        width="100"
      />
      <el-table-column
        prop="spec"
        label="规格型号"
        width="150"
      />
      <el-table-column
        prop="stock_quantity"
        label="当前库存"
        width="100"
      >
        <template #default="{ row }">
          <el-tag :type="getStockStatusType(row)">
            {{ row.stock_quantity }} {{ row.unit }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleEdit(row)"
          >
            编辑
          </el-button>
          <el-button
            link
            type="primary"
            @click="handleHistory(row)"
          >
            记录
          </el-button>
          <el-popconfirm
            title="确定删除吗？"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button
                link
                type="danger"
              >
                删除
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="searchForm.page"
      v-model:page-size="searchForm.pageSize"
      :total="total"
      layout="total, prev, pager, next"
      class="pagination"
      @current-change="fetchData"
    />

    <!-- Forms/Dialogs -->
    <ConsumableForm
      v-if="formVisible"
      :id="selectedId"
      v-model="formVisible"
      @success="fetchData"
    />
    <StockOperationDialog
      v-if="stockVisible"
      v-model="stockVisible"
      :type="stockType"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getConsumables, deleteConsumable } from '@/api/consumables'
import { ElMessage } from 'element-plus'
import ConsumableForm from './ConsumableForm.vue'
import StockOperationDialog from './StockOperationDialog.vue'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const searchForm = reactive({
    search: '',
    category: '',
    page: 1,
    pageSize: 10
})

const formVisible = ref(false)
const selectedId = ref<number | undefined>(undefined)

const stockVisible = ref(false)
const stockType = ref<'in' | 'out'>('in')

const fetchData = async () => {
    loading.value = true
    try {
        const res = await getConsumables(searchForm)
        tableData.value = res.results || res.items || []
        total.value = res.count || res.total || 0
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const handleCreate = () => {
    selectedId.value = undefined
    formVisible.value = true
}

const handleEdit = (row: any) => {
    selectedId.value = row.id
    formVisible.value = true
}

const handleDelete = async (row: any) => {
    try {
        await deleteConsumable(row.id)
        ElMessage.success('删除成功')
        fetchData()
    } catch (e) {
        ElMessage.error('删除失败')
    }
}

const handleStockIn = () => {
    stockType.value = 'in'
    stockVisible.value = true
}

const handleStockOut = () => {
    stockType.value = 'out'
    stockVisible.value = true
}

const handleHistory = (row: any) => {
    // Navigate to history or show dialog (TODO)
    ElMessage.info('查看记录功能待开发')
}

const getStockStatusType = (row: any) => {
    if (row.stock_quantity <= (row.warning_quantity || 0)) return 'danger'
    return 'success'
}

onMounted(() => {
    fetchData()
})
</script>

<style scoped>
.consumable-list { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.pagination { margin-top: 20px; text-align: right; }
</style>
