<template>
  <el-dialog
    :model-value="visible"
    :title="`${dictionaryType?.name || ''} - 字典项管理`"
    width="900px"
    @update:model-value="handleClose"
  >
    <!-- Toolbar -->
    <div class="toolbar">
      <el-button
        type="primary"
        size="small"
        @click="handleCreate"
      >
        添加字典项
      </el-button>
      <el-button
        size="small"
        @click="handleBatchSort"
      >
        批量排序
      </el-button>
    </div>

    <!-- Dictionary Items Table -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
      :row-class-name="getRowClassName"
    >
      <el-table-column
        prop="code"
        label="字典项编码"
        width="150"
      />
      <el-table-column
        label="显示名称"
        width="200"
      >
        <template #default="{ row }">
          <div class="item-name">
            <span
              v-if="row.color"
              class="color-dot"
              :style="{ backgroundColor: row.color }"
            />
            <span
              v-if="row.icon"
              class="item-icon"
            >
              <el-icon><component :is="row.icon" /></el-icon>
            </span>
            {{ row.name }}
            <el-tag
              v-if="row.is_default"
              type="info"
              size="small"
            >
              默认
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column
        prop="name_en"
        label="英文名称"
        width="150"
      />
      <el-table-column
        prop="description"
        label="描述"
        min-width="150"
        show-overflow-tooltip
      />
      <el-table-column
        label="状态"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="handleToggleActive(row)"
          />
        </template>
      </el-table-column>
      <el-table-column
        prop="sort_order"
        label="排序"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-input-number
            v-model="row.sort_order"
            :min="0"
            :max="9999"
            size="small"
            controls-position="right"
            @change="handleSortOrderChange(row)"
          />
        </template>
      </el-table-column>
      <el-table-column
        label="操作"
        width="150"
        fixed="right"
      >
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
            type="danger"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button @click="handleClose">
        关闭
      </el-button>
    </template>

    <!-- Dictionary Item Form Dialog -->
    <DictionaryItemForm
      v-model:visible="formDialogVisible"
      :dictionary-type-code="dictionaryType?.code || ''"
      :data="currentRow"
      @success="fetchData"
    />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { DictionaryType, DictionaryItem } from '@/api/system'
import { dictionaryItemApi } from '@/api/system'
import DictionaryItemForm from './DictionaryItemForm.vue'

interface Props {
  visible: boolean
  dictionaryType: DictionaryType | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)
const tableData = ref<DictionaryItem[]>([])
const formDialogVisible = ref(false)
const currentRow = ref<DictionaryItem | null>(null)

const getRowClassName = ({ row }: { row: DictionaryItem }) => {
  return row.is_active ? '' : 'row-disabled'
}

const fetchData = async () => {
  if (!props.dictionaryType) return

  loading.value = true
  try {
    const res = await dictionaryItemApi.list({
      dictionary_type: props.dictionaryType.id,
      ordering: 'sort_order'
    }) as any

    tableData.value = res.results || []
  } catch (error) {
    ElMessage.error('加载字典项失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  currentRow.value = null
  formDialogVisible.value = true
}

const handleEdit = (row: DictionaryItem) => {
  currentRow.value = row
  formDialogVisible.value = true
}

const handleToggleActive = async (row: DictionaryItem) => {
  try {
    await dictionaryItemApi.partialUpdate(row.id, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    ElMessage.error('操作失败')
    row.is_active = !row.is_active
  }
}

const handleSortOrderChange = async (row: DictionaryItem) => {
  try {
    await dictionaryItemApi.partialUpdate(row.id, { sort_order: row.sort_order })
  } catch (error) {
    ElMessage.error('更新排序失败')
  }
}

const handleBatchSort = async () => {
  try {
    await ElMessageBox.confirm('确定要按当前排序号重新排列所有字典项吗？', '确认', {
      type: 'warning'
    })

    loading.value = true
    for (let i = 0; i < tableData.value.length; i++) {
      const item = tableData.value[i]
      item.sort_order = i
      await dictionaryItemApi.partialUpdate(item.id, { sort_order: i })
    }

    await fetchData()
    ElMessage.success('批量排序成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量排序失败')
    }
  } finally {
    loading.value = false
  }
}

const handleDelete = async (row: DictionaryItem) => {
  try {
    await ElMessageBox.confirm(
      `确定删除字典项"${row.name}"吗？`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )

    await dictionaryItemApi.delete(row.id)
    ElMessage.success('删除成功')
    await fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleClose = () => {
  emit('update:visible', false)
}

watch(() => props.visible, (val) => {
  if (val) {
    fetchData()
  }
})
</script>

<style scoped>
.toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}

.item-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.item-icon {
  flex-shrink: 0;
}

:deep(.row-disabled) {
  opacity: 0.6;
}

:deep(.el-input-number) {
  width: 100px;
}
</style>
