<!--
  OrganizationTree.vue

  Left-sidebar tree of departments/organizations + right-side detail panel.
  - Tree is built from deptApi.tree() (hierarchical structure)
  - Selecting a node loads the department details and member list
  - Add / Edit / Delete department operations
  - Uses sortablejs for drag-to-reorder (visual reorder only)

  layout: [tree panel 280px] | [detail panel flex]
-->
<template>
  <div class="org-tree-page">
    <!-- ── Left: Tree Panel ──────────────────────────────────── -->
    <div class="tree-panel">
      <div class="tree-header">
        <span class="tree-title">{{ $t('org.tree.title') }}</span>
        <el-button
          :icon="Plus"
          type="primary"
          size="small"
          @click="addNode(null)"
        >
          {{ $t('org.tree.addRoot') }}
        </el-button>
      </div>

      <el-input
        v-model="treeSearch"
        :placeholder="$t('org.tree.searchPlaceholder')"
        clearable
        class="tree-search"
        :prefix-icon="Search"
      />

      <div
        v-loading="loadingTree"
        class="tree-scroll"
      >
        <el-tree
          ref="treeRef"
          :data="filteredTree"
          :props="treeProps"
          :expand-on-click-node="false"
          :filter-node-method="filterNode"
          default-expand-all
          highlight-current
          node-key="id"
          @node-click="handleNodeClick"
        >
          <template #default="{ data }">
            <div class="tree-node">
              <el-icon class="node-icon">
                <OfficeBuilding />
              </el-icon>
              <span class="node-label">{{ data.name }}</span>
              <span
                v-if="data.memberCount !== undefined"
                class="node-count"
              >
                ({{ data.memberCount }})
              </span>
              <div class="node-actions">
                <el-icon
                  class="action-icon"
                  @click.stop="addNode(data)"
                >
                  <Plus />
                </el-icon>
                <el-icon
                  class="action-icon"
                  @click.stop="editNode(data)"
                >
                  <Edit />
                </el-icon>
                <el-icon
                  class="action-icon danger"
                  @click.stop="deleteNode(data)"
                >
                  <Delete />
                </el-icon>
              </div>
            </div>
          </template>
        </el-tree>
      </div>
    </div>

    <!-- ── Right: Detail Panel ───────────────────────────────── -->
    <div class="detail-panel">
      <div
        v-if="!selectedNode"
        class="empty-state"
      >
        <el-empty :description="$t('org.tree.selectPrompt')" />
      </div>

      <div v-else>
        <!-- Dept info header -->
        <div class="detail-header">
          <div class="detail-title-row">
            <h3 class="detail-title">
              {{ selectedNode.name }}
            </h3>
            <div class="detail-actions">
              <el-button
                size="small"
                :icon="Edit"
                @click="editNode(selectedNode)"
              >
                {{ $t('common.actions.edit') }}
              </el-button>
              <el-button
                size="small"
                type="primary"
                :icon="Plus"
                @click="addNode(selectedNode)"
              >
                {{ $t('org.tree.addChild') }}
              </el-button>
            </div>
          </div>
          <el-descriptions
            :column="2"
            border
            size="small"
            class="mt-12"
          >
            <el-descriptions-item :label="$t('org.cols.code')">
              {{ selectedNode.code || '-' }}
            </el-descriptions-item>
            <el-descriptions-item :label="$t('org.cols.parent')">
              {{ selectedNode.parentName || $t('org.tree.rootNode') }}
            </el-descriptions-item>
            <el-descriptions-item
              :label="$t('org.cols.description')"
              :span="2"
            >
              {{ selectedNode.description || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- Members table -->
        <div class="members-section">
          <div class="section-title">
            <span>{{ $t('org.members.title') }}</span>
            <el-tag
              size="small"
              type="info"
            >
              {{ members.length }}
            </el-tag>
          </div>

          <el-table
            v-loading="loadingMembers"
            :data="members"
            border
            size="small"
          >
            <el-table-column
              :label="$t('org.members.cols.name')"
              prop="fullName"
            />
            <el-table-column
              :label="$t('org.members.cols.username')"
              prop="username"
            />
            <el-table-column
              :label="$t('org.members.cols.email')"
              prop="email"
            />
            <el-table-column
              :label="$t('org.members.cols.title')"
              prop="title"
            />
            <el-table-column
              :label="$t('org.members.cols.status')"
              prop="isActive"
              width="80"
            >
              <template #default="{ row }">
                <el-tag
                  :type="row.isActive ? 'success' : 'info'"
                  size="small"
                >
                  {{ row.isActive ? $t('common.status.active') : $t('common.status.inactive') }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- ── Node Create/Edit Dialog ───────────────────────────── -->
    <el-dialog
      v-model="nodeDialog"
      :title="editingNode ? $t('org.dialog.editTitle') : $t('org.dialog.createTitle')"
      width="460px"
      destroy-on-close
    >
      <el-form
        ref="nodeFormRef"
        :model="nodeForm"
        :rules="nodeRules"
        label-width="90px"
      >
        <el-form-item
          :label="$t('org.cols.name')"
          prop="name"
        >
          <el-input v-model="nodeForm.name" />
        </el-form-item>
        <el-form-item
          :label="$t('org.cols.code')"
          prop="code"
        >
          <el-input v-model="nodeForm.code" />
        </el-form-item>
        <el-form-item :label="$t('org.cols.parent')">
          <el-input
            :value="nodeForm.parentName || $t('org.tree.rootNode')"
            disabled
          />
        </el-form-item>
        <el-form-item :label="$t('org.cols.description')">
          <el-input
            v-model="nodeForm.description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="nodeDialog = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="savingNode"
          @click="saveNode"
        >
          {{ $t('common.actions.save') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Plus, Edit, Delete, Search, OfficeBuilding } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { deptApi } from '@/api/organizations'

const { t } = useI18n()

// ── Tree ────────────────────────────────────────────────────────
const loadingTree = ref(false)
const treeData = ref<any[]>([])
const treeSearch = ref('')
const treeRef = ref()
const treeProps = { label: 'name', children: 'children' }

const filteredTree = computed(() => treeData.value)

const filterNode = (value: string, data: any) =>
  !value || data.name?.toLowerCase().includes(value.toLowerCase())

watch(treeSearch, v => treeRef.value?.filter(v))

const loadTree = async () => {
  loadingTree.value = true
  try {
    const res: any = await deptApi.tree()
    treeData.value = Array.isArray(res) ? res : (res?.results ?? [])
  } finally {
    loadingTree.value = false
  }
}

// ── Node Selection ──────────────────────────────────────────────
const selectedNode = ref<any>(null)
const loadingMembers = ref(false)
const members = ref<any[]>([])

const handleNodeClick = async (data: any) => {
  selectedNode.value = data
  loadingMembers.value = true
  members.value = []
  try {
    const res: any = await deptApi.getMembers(data.id)
    members.value = Array.isArray(res) ? res : (res?.results ?? [])
  } finally {
    loadingMembers.value = false
  }
}

// ── Node CRUD ───────────────────────────────────────────────────
const nodeDialog = ref(false)
const savingNode = ref(false)
const editingNode = ref<any>(null)
const nodeFormRef = ref()
const nodeForm = reactive({ name: '', code: '', parentId: '', parentName: '', description: '' })
const nodeRules = {
  name: [{ required: true, message: t('common.validation.required') }],
  code: [{ required: true, message: t('common.validation.required') }]
}

const addNode = (parent: any) => {
  editingNode.value = null
  Object.assign(nodeForm, { name: '', code: '', description: '', parentId: parent?.id || '', parentName: parent?.name || '' })
  nodeDialog.value = true
}

const editNode = (data: any) => {
  editingNode.value = data
  Object.assign(nodeForm, {
    name: data.name,
    code: data.code || '',
    description: data.description || '',
    parentId: data.parentId || '',
    parentName: data.parentName || ''
  })
  nodeDialog.value = true
}

const saveNode = async () => {
  await nodeFormRef.value?.validate()
  savingNode.value = true
  try {
    const payload = { name: nodeForm.name, code: nodeForm.code, parentId: nodeForm.parentId || undefined, description: nodeForm.description }
    if (editingNode.value) {
      await deptApi.update(editingNode.value.id, payload)
    } else {
      await deptApi.create({ ...payload, name: nodeForm.name, code: nodeForm.code })
    }
    ElMessage.success(t('common.messages.saveSuccess'))
    nodeDialog.value = false
    await loadTree()
  } finally {
    savingNode.value = false
  }
}

const deleteNode = async (data: any) => {
  await ElMessageBox.confirm(t('common.messages.deleteConfirm'), t('common.messages.warning'), { type: 'warning' })
  await deptApi.delete(data.id)
  ElMessage.success(t('common.messages.deleteSuccess'))
  if (selectedNode.value?.id === data.id) selectedNode.value = null
  await loadTree()
}

onMounted(loadTree)
</script>

<style scoped>
.org-tree-page {
  display: flex;
  height: calc(100vh - 112px);
  gap: 0;
  background: #f5f7fa;
}

/* ── Tree panel ── */
.tree-panel {
  width: 280px;
  min-width: 240px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 12px 8px;
}
.tree-title { font-weight: 600; font-size: 14px; }
.tree-search { padding: 4px 12px 8px; }
.tree-scroll { flex: 1; overflow-y: auto; padding: 4px 4px; }

/* Tree node */
.tree-node {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  position: relative;
}
.node-icon { color: #909399; font-size: 14px; }
.node-label { flex: 1; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-count { font-size: 11px; color: #c0c4cc; }
.node-actions {
  display: none;
  gap: 4px;
  align-items: center;
}
.tree-node:hover .node-actions { display: flex; }
.action-icon { font-size: 13px; cursor: pointer; color: #909399; }
.action-icon:hover { color: #409eff; }
.action-icon.danger:hover { color: #f56c6c; }

/* ── Detail panel ── */
.detail-panel { flex: 1; overflow-y: auto; padding: 20px; background: #fff; }
.empty-state { display: flex; align-items: center; justify-content: center; height: 100%; }
.detail-header { margin-bottom: 20px; }
.detail-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.detail-title { margin: 0; font-size: 18px; font-weight: 600; }
.detail-actions { display: flex; gap: 8px; }
.mt-12 { margin-top: 12px; }

.members-section { margin-top: 24px; }
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}
</style>
