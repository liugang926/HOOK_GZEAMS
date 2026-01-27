<!--
  DeptPicker Component

  A department selection component with:
  - Tree structure display
  - Searchable departments
  - Multiple selection support
  - Organization context filtering

  Usage:
  <DeptPicker
    v-model="selectedDept"
    :multiple="false"
    :check-strictly="false"
    placeholder="请选择部门"
    @change="handleDeptChange"
  />
-->

<script setup lang="ts">
/**
 * DeptPicker Component
 *
 * A specialized picker component for selecting departments.
 * Supports tree view, search, and multiple selection.
 */

import { ref, computed, watch } from 'vue'
import { deptApi, orgApi } from '@/api/organizations'
import type { TreeNode } from '@/types/common'

// ============================================================================
// Types
// ============================================================================

interface DeptNode extends TreeNode {
  /** Department name */
  name: string
  /** Department code */
  code?: string
  /** Manager ID */
  managerId?: string
  /** Parent department ID */
  parentId?: string
  /** Organization ID */
  organizationId?: string
  /** Has children */
  hasChildren?: boolean
}

interface Props {
  /** Selected department(s) */
  modelValue?: string | string[]
  /** Multiple selection */
  multiple?: boolean
  /** Show checkboxes for multiple selection */
  showCheckbox?: boolean
  /** Check child nodes independently (no parent-child relationship) */
  checkStrictly?: boolean
  /** Disabled state */
  disabled?: boolean
  /** Clearable */
  clearable?: boolean
  /** Placeholder text */
  placeholder?: string
  /** Filter by organization */
  organizationId?: string
  /** Only leaf nodes selectable */
  onlyLeaf?: boolean
  /** Show user count */
  showUserCount?: boolean
  /** Size */
  size?: 'large' | 'default' | 'small'
  /** Panel width */
  panelWidth?: number
  /** Dropdown height */
  dropdownHeight?: number
}

interface Emits {
  (e: 'update:modelValue', value: string | string[] | undefined): void
  (e: 'change', value: any, node: any): void
}

// ============================================================================
// Props & Emits
// ============================================================================

const props = withDefaults(defineProps<Props>(), {
  multiple: false,
  showCheckbox: false,
  checkStrictly: false,
  disabled: false,
  clearable: true,
  placeholder: '请选择部门',
  onlyLeaf: false,
  showUserCount: false,
  size: 'default',
  panelWidth: 280,
  dropdownHeight: 300
})

const emit = defineEmits<Emits>()

// ============================================================================
// State
// ============================================================================`

const loading = ref(false)
const treeData = ref<DeptNode[]>([])
const treeRef = ref()
const searchKeyword = ref('')

// ============================================================================
// Computed
// ============================================================================

/** Tree node key */
const nodeKey = computed(() => 'id')

/** Default checked keys */
const defaultCheckedKeys = computed(() => {
  if (!props.multiple) return []
  if (Array.isArray(props.modelValue)) {
    return props.modelValue
  }
  return props.modelValue ? [props.modelValue] : []
})

/** Current selected key */
const currentKey = computed(() => {
  if (props.multiple) return undefined
  return props.modelValue as string
})

/** Filtered tree data */
const filteredTreeData = computed(() => {
  if (!searchKeyword.value) return treeData.value

  const filterTree = (nodes: DeptNode[]): DeptNode[] => {
    return nodes.reduce((result: DeptNode[], node) => {
      const matches = node.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
      const filteredChildren = node.children ? filterTree(node.children) : []

      if (matches || filteredChildren.length > 0) {
        result.push({
          ...node,
          children: filteredChildren.length > 0 ? filteredChildren : node.children
        })
      }

      return result
    }, [])
  }

  return filterTree(treeData.value)
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Convert API response to tree nodes
 */
const toTreeNodes = (depts: any[], parentId: string | null = null): DeptNode[] => {
  return depts
    .filter(dept => dept.parentId === parentId)
    .map(dept => ({
      id: dept.id,
      label: dept.name,
      name: dept.name,
      code: dept.code,
      parentId: dept.parentId,
      organizationId: dept.organizationId,
      managerId: dept.managerId,
      hasChildren: dept.hasChildren,
      children: toTreeNodes(depts, dept.id),
      userCount: dept.userCount || 0
    }))
}

/**
 * Load department tree
 */
const loadDepartments = async () => {
  loading.value = true
  try {
    const response = await deptApi.tree()
    const depts = Array.isArray(response) ? response : []

    // Filter by organization if specified
    const filteredDepts = props.organizationId
      ? depts.filter((d: any) => d.organizationId === props.organizationId)
      : depts

    treeData.value = toTreeNodes(filteredDepts)
  } catch (error) {
    treeData.value = []
  } finally {
    loading.value = false
  }
}

/**
 * Handle node click
 */
const handleNodeClick = (data: DeptNode) => {
  if (props.onlyLeaf && data.children && data.children.length > 0) {
    return
  }

  if (!props.multiple) {
    emit('update:modelValue', data.id)
    emit('change', data.id, data)
  }
}

/**
 * Handle check change
 */
const handleCheckChange = () => {
  if (!props.multiple || !treeRef.value) return

  const checkedKeys = treeRef.value.getCheckedKeys()
  const halfCheckedKeys = treeRef.value.getHalfCheckedKeys()

  // Include half-checked keys if checkStrictly is false
  const keys = props.checkStrictly
    ? checkedKeys
    : [...checkedKeys, ...halfCheckedKeys]

  emit('update:modelValue', keys)
  emit('change', keys, null)
}

/**
 * Handle clear
 */
const handleClear = () => {
  emit('update:modelValue', props.multiple ? [] : undefined)
  emit('change', props.multiple ? [] : undefined, null)
}

/**
 * Filter node method
 */
const filterNode = (value: string, data: DeptNode) => {
  if (!value) return true
  return data.name.toLowerCase().includes(value.toLowerCase())
}

/**
 * Get selected node
 */
const getSelectedNode = (): DeptNode | null => {
  if (!currentKey.value) return null

  const findNode = (nodes: DeptNode[], id: string): DeptNode | null => {
    for (const node of nodes) {
      if (node.id === id) return node
      if (node.children) {
        const found = findNode(node.children, id)
        if (found) return found
      }
    }
    return null
  }

  return findNode(treeData.value, currentKey.value)
}

/**
 * Get selected nodes
 */
const getSelectedNodes = (): DeptNode[] => {
  if (!props.multiple) {
    const node = getSelectedNode()
    return node ? [node] : []
  }

  const keys = Array.isArray(props.modelValue) ? props.modelValue : []
  const nodes: DeptNode[] = []

  const findNodes = (treeNodes: DeptNode[]) => {
    for (const node of treeNodes) {
      if (keys.includes(node.id)) {
        nodes.push(node)
      }
      if (node.children) {
        findNodes(node.children)
      }
    }
  }

  findNodes(treeData.value)
  return nodes
}

// ============================================================================
// Watch
// ============================================================================

// Reload when organization changes
watch(() => props.organizationId, () => {
  loadDepartments()
})

// Reload tree data
watch(searchKeyword, () => {
  treeRef.value?.filter(searchKeyword.value)
})

// ============================================================================
// Lifecycle
// ============================================================================

loadDepartments()

// ============================================================================
// Expose
// ============================================================================

defineExpose({
  loadDepartments,
  getSelectedNode,
  getSelectedNodes,
  treeRef
})
</script>

<template>
  <div class="dept-picker">
    <el-tree-select
      :model-value="modelValue"
      :data="treeData"
      :props="{
        label: 'name',
        children: 'children',
        disabled: (data: DeptNode) => onlyLeaf && data.children?.length > 0
      }"
      :node-key="nodeKey"
      :multiple="multiple"
      :show-checkbox="showCheckbox || multiple"
      :check-strictly="checkStrictly"
      :disabled="disabled"
      :clearable="clearable"
      :placeholder="placeholder"
      :filterable="true"
      :filter-node-method="filterNode"
      :size="size"
      :loading="loading"
      :render-after-expand="true"
      :default-checked-keys="defaultCheckedKeys"
      class="dept-tree-select"
      @update:model-value="handleChange"
      @node-click="handleNodeClick"
      @check-change="handleCheckChange"
      @clear="handleClear"
    >
      <template #default="{ node, data }">
        <div class="tree-node-content">
          <el-icon
            v-if="data.children?.length"
            class="node-icon"
          >
            <Folder />
          </el-icon>
          <el-icon
            v-else
            class="node-icon"
          >
            <Document />
          </el-icon>
          <span class="node-label">{{ node.label }}</span>
          <span
            v-if="showUserCount && data.userCount"
            class="node-count"
          >
            ({{ data.userCount }})
          </span>
        </div>
      </template>
    </el-tree-select>
  </div>
</template>

<style scoped lang="scss">
.dept-picker {
  width: 100%;

  .dept-tree-select {
    width: 100%;
  }

  :deep(.el-tree-select__wrapper) {
    max-height: v-bind('dropdownHeight + "px"');
  }

  .tree-node-content {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    padding-right: 8px;

    .node-icon {
      font-size: 16px;
      color: #909399;
      flex-shrink: 0;
    }

    .node-label {
      flex: 1;
      font-size: 14px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .node-count {
      font-size: 12px;
      color: #909399;
      flex-shrink: 0;
    }
  }
}
</style>
