<template>
  <el-tab-pane name="requests">
    <template #label>
      <span>{{ $t('portal.tabs.myRequests') }}</span>
      <el-badge
        v-if="pendingCount > 0"
        :value="pendingCount"
        type="warning"
        class="tab-badge"
      />
    </template>

    <div class="tab-toolbar">
      <el-radio-group
        :model-value="requestType"
        @update:model-value="emit('update:requestType', $event)"
        @change="emit('refresh')"
      >
        <el-radio-button value="purchase">
          {{ $t('portal.requests.type.purchase') }}
        </el-radio-button>
        <el-radio-button value="maintenance">
          {{ $t('portal.requests.type.maintenance') }}
        </el-radio-button>
        <el-radio-button value="disposal">
          {{ $t('portal.requests.type.disposal') }}
        </el-radio-button>
      </el-radio-group>
      <el-select
        v-model="statusFilterModel"
        :placeholder="$t('portal.requests.allStatus')"
        clearable
        style="width:130px"
        @change="emit('refresh')"
      >
        <el-option
          v-for="status in statuses"
          :key="status.value"
          :label="status.label"
          :value="status.value"
        />
      </el-select>
      <el-button
        type="primary"
        :icon="Plus"
        @click="emit('create')"
      >
        {{ $t('portal.requests.new') }}
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="requests"
      border
      stripe
    >
      <el-table-column
        :label="$t('portal.requests.cols.code')"
        prop="code"
        width="140"
      />
      <el-table-column
        :label="$t('portal.requests.cols.title')"
        prop="title"
        min-width="160"
      />
      <el-table-column
        :label="$t('portal.requests.cols.status')"
        prop="statusDisplay"
        width="110"
      >
        <template #default="{ row }">
          <el-tag
            :type="getPortalRequestStatusTagType(row.status)"
            size="small"
          >
            {{ row.statusDisplay || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('portal.requests.cols.createdAt')"
        prop="createdAt"
        width="155"
      >
        <template #default="{ row }">
          {{ formatDate(row.createdAt) }}
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('portal.requests.cols.actions')"
        width="160"
      >
        <template #default="{ row }">
          <el-button
            size="small"
            @click="emit('view', row)"
          >
            {{ $t('common.actions.view') }}
          </el-button>
          <el-button
            v-if="canSubmit(row)"
            size="small"
            type="primary"
            @click="emit('submit', row)"
          >
            {{ $t('portal.requests.submit') }}
          </el-button>
          <el-button
            v-if="canCancel(row)"
            size="small"
            type="danger"
            @click="emit('cancel', row)"
          >
            {{ $t('portal.requests.cancel') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      class="mt-16"
      @update:current-page="emit('update:currentPage', $event)"
      @update:page-size="emit('update:pageSize', $event)"
      @current-change="emit('refresh')"
    />
  </el-tab-pane>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus } from '@element-plus/icons-vue'

import { formatDate } from '@/utils/dateFormat'

import {
  getPortalRequestStatusTagType,
  type PortalRequestType,
} from './portalRequestModel'

interface StatusOption {
  value: string
  label: string
}

const props = defineProps<{
  canCancel: (row: Record<string, any>) => boolean
  canSubmit: (row: Record<string, any>) => boolean
  currentPage: number
  loading: boolean
  pageSize: number
  pendingCount: number
  requestType: PortalRequestType
  requests: any[]
  statusFilter: string
  statuses: StatusOption[]
  total: number
}>()

const emit = defineEmits<{
  cancel: [row: Record<string, any>]
  create: []
  'update:currentPage': [value: number]
  'update:pageSize': [value: number]
  'update:requestType': [value: PortalRequestType]
  'update:statusFilter': [value: string]
  refresh: []
  submit: [row: Record<string, any>]
  view: [row: Record<string, any>]
}>()

useI18n()

const statusFilterModel = computed({
  get: () => props.statusFilter,
  set: (value: string) => emit('update:statusFilter', value),
})
</script>

<style scoped>
.tab-badge { margin-left: 4px; }
.tab-toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.mt-16 { margin-top: 16px; }
</style>
