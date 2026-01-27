<template>
  <div class="category-tree-container">
    <div class="tree-toolbar">
      <el-input
        v-model="filterText"
        placeholder="搜索分类"
        prefix-icon="Search"
        clearable
      />
      <el-button-group
        class="mt-2"
        style="display: flex; margin-top: 10px;"
      >
        <el-button
          type="primary"
          :icon="Plus"
          style="flex: 1"
          @click="$emit('add-root')"
        >
          新增根分类
        </el-button>
        <el-button
          :icon="Refresh"
          @click="fetchTree"
        />
      </el-button-group>
    </div>

    <div
      v-loading="loading"
      class="tree-content"
    >
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="defaultProps"
        :filter-node-method="filterNode"
        node-key="id"
        highlight-current
        default-expand-all
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <span class="custom-tree-node">
            <span>{{ node.label }} <small style="color: #999">({{ data.code }})</small></span>
            <span
              v-if="node.id === currentNodeId"
              class="node-actions"
            >
              <el-button
                link
                type="primary"
                :icon="Plus"
                @click.stop="$emit('add-child', data)"
              >新增子级</el-button>
              <el-button
                link
                type="danger"
                :icon="Delete"
                @click.stop="handleDelete(data)"
              >删除</el-button>
            </span>
          </span>
        </template>
      </el-tree>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Search, Plus, Refresh, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryApi } from '@/api/assets'

const emit = defineEmits(['select', 'add-root', 'add-child', 'delete'])

const loading = ref(false)
const filterText = ref('')
const treeRef = ref()
const treeData = ref([])
const currentNodeId = ref<string | null>(null)

const defaultProps = {
  children: 'children',
  label: 'name'
}

watch(filterText, (val) => {
  treeRef.value?.filter(val)
})

const filterNode = (value: string, data: any) => {
  if (!value) return true
  return data.name.includes(value) || data.code.includes(value)
}

const fetchTree = async () => {
  loading.value = true
  try {
    const data = await categoryApi.tree()
    treeData.value = data
  } catch (error) {
    console.error(error)
    ElMessage.error('加载分类树失败')
  } finally {
    loading.value = false
  }
}

const handleNodeClick = (data: any) => {
  currentNodeId.value = data.id
  emit('select', data)
}

const handleDelete = (data: any) => {
  if (data.children && data.children.length > 0) {
    ElMessage.warning('请先删除子分类')
    return
  }
  
  ElMessageBox.confirm(`确定要删除分类 "${data.name}" 吗？`, '提示', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  }).then(async () => {
    try {
      await categoryApi.delete(data.id)
      ElMessage.success('删除成功')
      emit('delete', data)
      fetchTree() // Refresh tree
    } catch (error: any) {
      ElMessage.error(error.message || '删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchTree()
})

defineExpose({
  fetchTree
})
</script>

<style scoped lang="scss">
.category-tree-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-right: 1px solid #ebeef5;
}

.tree-toolbar {
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;

  .node-actions {
    display: none;
  }

  &:hover .node-actions {
    display: inline-block;
  }
}
</style>
