<template>
  <div
    v-if="auditInfo"
    class="base-audit-info"
  >
    <el-collapse v-model="activeNames">
      <el-collapse-item name="audit">
        <template #title>
          <span class="audit-title">
            <el-icon><InfoFilled /></el-icon>
            Audit Information
          </span>
        </template>
        <div class="audit-content">
          <el-descriptions
            :column="2"
            border
            size="small"
          >
            <el-descriptions-item
              v-if="auditInfo.created_by"
              label="Created By"
            >
              <UserDisplay :user="auditInfo.created_by" />
            </el-descriptions-item>
            <el-descriptions-item
              v-if="auditInfo.created_at"
              label="Created At"
            >
              {{ formatDateTime(auditInfo.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item
              v-if="auditInfo.updated_by"
              label="Updated By"
            >
              <UserDisplay :user="auditInfo.updated_by" />
            </el-descriptions-item>
            <el-descriptions-item
              v-if="auditInfo.updated_at"
              label="Updated At"
            >
              {{ formatDateTime(auditInfo.updated_at) }}
            </el-descriptions-item>
            <el-descriptions-item
              v-if="auditInfo.deleted_by"
              label="Deleted By"
            >
              <UserDisplay :user="auditInfo.deleted_by" />
            </el-descriptions-item>
            <el-descriptions-item
              v-if="auditInfo.deleted_at"
              label="Deleted At"
            >
              {{ formatDateTime(auditInfo.deleted_at) }}
            </el-descriptions-item>
            <el-descriptions-item
              v-if="auditInfo.organization"
              label="Organization"
              :span="2"
            >
              {{ auditInfo.organization.name || auditInfo.organization }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
  <div
    v-else
    class="base-audit-info--empty"
  >
    <el-empty
      description="No audit information available"
      :image-size="60"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/dateFormat'

/**
 * User display types
 */
interface User {
  id: string
  username?: string
  email?: string
  first_name?: string
  last_name?: string
  full_name?: string
}

interface Organization {
  id: string
  name?: string
}

/**
 * Audit info types
 */
export interface AuditInfo {
  created_by?: User | string
  created_at?: string
  updated_by?: User | string
  updated_at?: string
  deleted_by?: User | string
  deleted_at?: string
  organization?: Organization | string
}

interface Props {
  data?: AuditInfo | null
  defaultExpanded?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  data: null,
  defaultExpanded: false
})

const activeNames = ref<string[]>(props.defaultExpanded ? ['audit'] : [])

const auditInfo = computed(() => {
  if (!props.data) return null

  // Check if any audit field has data
  const hasData = Object.values(props.data).some(
    v => v !== null && v !== undefined && v !== ''
  )

  return hasData ? props.data : null
})

// Simple user display component
const UserDisplay = {
  props: ['user'],
  template: `
    <span class="user-display">
      <el-tag size="small" type="info">
        {{ displayName }}
      </el-tag>
    </span>
  `,
  computed: {
    displayName() {
      const user = this.user
      if (typeof user === 'string') return user
      if (!user) return '-'
      return user.full_name ||
             user.username ||
             `${user.first_name || ''} ${user.last_name || ''}`.trim() ||
             user.email ||
             user.id
    }
  }
}
</script>

<script lang="ts">
export default {
  components: { UserDisplay }
}
</script>

<style scoped>
.base-audit-info {
  margin-top: 20px;
}

.audit-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.audit-content {
  padding: 10px 0;
}

.user-display {
  display: inline-flex;
  align-items: center;
}

.base-audit-info--empty {
  padding: 20px;
  text-align: center;
}

:deep(.el-collapse-item__header) {
  font-size: 14px;
}

:deep(.el-descriptions__label) {
  font-weight: 500;
}
</style>
