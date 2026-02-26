<template>
  <div class="location-list">
    <!-- Header -->
    <div class="page-header">
      <div class="header-title">
        <span class="title-text">{{ t('assets.location.manage') }}</span>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          {{ t('assets.location.create') }}
        </el-button>
      </div>
    </div>

    <!-- Content with tree and table -->
    <el-card shadow="never">
      <el-row :gutter="20">
        <!-- Tree -->
        <el-col :span="6">
          <div class="tree-container">
            <div class="tree-header">
              <span>{{ t('assets.location.tree') }}</span>
              <el-button
                link
                type="primary"
                @click="handleRefreshTree"
              >
                {{ t('common.actions.refresh') }}
              </el-button>
            </div>
            <el-tree
              ref="treeRef"
              v-loading="treeLoading"
              :data="treeData"
              :props="treeProps"
              node-key="id"
              highlight-current
              default-expand-all
              @node-click="handleNodeClick"
            >
              <template #default="{ node, data }">
                <span class="tree-node">
                  <span>{{ node.label }}</span>
                  <span
                    class="tree-node-actions"
                    @click.stop
                  >
                    <el-button
                      v-if="!data.isRoot"
                      link
                      type="primary"
                      size="small"
                      @click="handleEdit(data)"
                    >
                      {{ t('common.actions.edit') }}
                    </el-button>
                  </span>
                </span>
              </template>
            </el-tree>
          </div>
        </el-col>

        <!-- Table -->
        <el-col :span="18">
          <div class="table-container">
            <div class="table-header">
              <span>{{ currentLocation ? `${t('assets.location.current')}: ${currentLocation.name}` : t('assets.location.manage') }}</span>
              <el-button
                v-if="currentLocation"
                link
                type="primary"
                @click="handleCreateChild"
              >
                {{ t('assets.location.createChild') }}
              </el-button>
            </div>
            <el-table
              v-loading="tableLoading"
              :data="tableData"
              style="width: 100%"
              @row-click="handleRowClick"
            >
              <el-table-column
                prop="code"
                :label="t('assets.location.code')"
                width="150"
              />
              <el-table-column
                prop="name"
                :label="t('assets.location.name')"
                width="200"
              />
              <el-table-column
                prop="fullPath"
                :label="t('assets.location.fullPath')"
                min-width="250"
                show-overflow-tooltip
              />
              <el-table-column
                prop="description"
                :label="t('assets.location.description')"
                min-width="200"
                show-overflow-tooltip
              />
              <el-table-column
                :label="t('common.labels.status')"
                width="80"
                align="center"
              >
                <template #default="{ row }">
                  <el-tag :type="row.isActive ? 'success' : 'danger'">
                    {{ row.isActive ? t('common.status.enabled') : t('common.status.inactive') }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column
                :label="t('common.table.operations')"
                width="180"
                fixed="right"
              >
                <template #default="{ row }">
                  <div @click.stop>
                    <el-button
                      link
                      type="primary"
                      @click="handleView(row)"
                    >
                      {{ t('common.actions.view') }}
                    </el-button>
                    <el-button
                      link
                      type="primary"
                      @click="handleEdit(row)"
                    >
                      {{ t('common.actions.edit') }}
                    </el-button>
                    <el-button
                      link
                      type="danger"
                      @click="handleDelete(row)"
                    >
                      {{ t('common.actions.delete') }}
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <!-- Pagination -->
            <div class="pagination-footer">
              <el-pagination
                v-model:current-page="pagination.page"
                v-model:page-size="pagination.page_size"
                :total="pagination.total"
                :page-sizes="[10, 20, 50, 100]"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="fetchTableData"
                @current-change="fetchTableData"
              />
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { getLocationList, getLocationTree, deleteLocation } from '@/api/assets/locations'

const { t } = useI18n()

const router = useRouter()
const treeRef = ref()
const treeLoading = ref(false)
const tableLoading = ref(false)
const treeData = ref([])
const tableData = ref([])
const currentLocation = ref<any>(null)

const treeProps = {
  children: 'children',
  label: 'name',
  value: 'id'
}

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const fetchTreeData = async () => {
  treeLoading.value = true
  try {
    const res = await getLocationTree()
    treeData.value = res || []
  } finally {
    treeLoading.value = false
  }
}

const fetchTableData = async () => {
  tableLoading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (currentLocation.value) {
      params.parent = currentLocation.value.id
    }
    const res = await getLocationList(params)
    tableData.value = res.results || res.items || []
    pagination.total = res.count || res.total || 0
  } finally {
    tableLoading.value = false
  }
}

const handleRefreshTree = () => {
  fetchTreeData()
}

const handleNodeClick = (data: any) => {
  currentLocation.value = data
  pagination.page = 1
  fetchTableData()
}

const handleCreate = () => {
  router.push('/assets/settings/locations/create')
}

const handleCreateChild = () => {
  if (currentLocation.value) {
    router.push(`/assets/settings/locations/create?parent=${currentLocation.value.id}`)
  }
}

const handleView = (row: any) => {
  router.push(`/assets/settings/locations/${row.id}`)
}

const handleEdit = (row: any) => {
  router.push(`/assets/settings/locations/${row.id}/edit`)
}

const handleRowClick = (row: any) => {
  handleView(row)
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`${t('common.dialog.confirmDeleteMessage').replace('{count}', `"${row.name}"`)}`, t('common.dialog.confirmTitle'), { type: 'warning' })
    await deleteLocation(row.id)
    ElMessage.success(t('common.messages.deleteSuccess'))
    fetchTreeData()
    fetchTableData()
  } catch {
    // cancelled
  }
}

onMounted(() => {
  fetchTreeData()
  fetchTableData()
})
</script>

<style scoped>
.location-list {
    padding: 20px;
}
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.title-text {
    font-size: 20px;
    font-weight: 500;
}
.tree-container {
    border-right: 1px solid #ebeef5;
    padding-right: 20px;
    min-height: 400px;
}
.tree-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    font-weight: 500;
}
.tree-node {
    flex: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
}
.tree-node:hover .tree-node-actions {
    opacity: 1;
}
.tree-node-actions {
    opacity: 0;
    transition: opacity 0.2s;
}
.table-container {
    padding-left: 10px;
}
.table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    font-weight: 500;
}
.pagination-footer {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
}
</style>
