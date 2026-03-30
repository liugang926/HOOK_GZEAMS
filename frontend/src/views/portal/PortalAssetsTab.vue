<template>
  <el-tab-pane
    :label="$t('portal.tabs.myAssets')"
    name="assets"
  >
    <div class="tab-toolbar">
      <el-input
        v-model="searchModel"
        :placeholder="$t('portal.assets.searchPlaceholder')"
        clearable
        style="width:240px"
        @input="emit('refresh')"
      />
      <el-select
        v-model="statusFilterModel"
        :placeholder="$t('portal.assets.allStatus')"
        clearable
        style="width:140px"
        @change="emit('refresh')"
      >
        <el-option
          v-for="status in statuses"
          :key="status.value"
          :label="status.label"
          :value="status.value"
        />
      </el-select>
    </div>

    <el-table
      v-loading="loading"
      :data="assets"
      border
      stripe
      @row-click="emit('view', $event)"
    >
      <el-table-column
        :label="$t('portal.assets.cols.code')"
        width="130"
      >
        <template #default="{ row }">
          {{ row.assetCode || row.code || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('portal.assets.cols.name')"
        min-width="160"
      >
        <template #default="{ row }">
          {{ row.name || row.assetName || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('portal.assets.cols.category')"
        prop="categoryDisplay"
        width="130"
      />
      <el-table-column
        :label="$t('portal.assets.cols.status')"
        prop="statusDisplay"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            :type="getPortalAssetStatusTagType(row.status)"
            size="small"
          >
            {{ row.statusDisplay || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('portal.assets.cols.location')"
        prop="locationDisplay"
        width="140"
      />
      <el-table-column
        :label="$t('portal.assets.cols.value')"
        prop="currentValue"
        width="120"
      >
        <template #default="{ row }">
          {{ formatPortalAssetValue(row.currentValue, t) }}
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('portal.assets.cols.actions')"
        width="120"
      >
        <template #default="{ row }">
          <el-button
            size="small"
            @click.stop="emit('view', row)"
          >
            {{ $t('common.actions.view') }}
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

import type { PortalAssetRecord, PortalStatusOption } from '@/types/portal'
import {
  formatPortalAssetValue,
  getPortalAssetStatusTagType,
} from './portalAssetModel'

const props = defineProps<{
  assets: PortalAssetRecord[]
  currentPage: number
  loading: boolean
  pageSize: number
  search: string
  statusFilter: string
  statuses: PortalStatusOption[]
  total: number
}>()

const emit = defineEmits<{
  'update:currentPage': [value: number]
  'update:pageSize': [value: number]
  'update:search': [value: string]
  'update:statusFilter': [value: string]
  refresh: []
  view: [row: PortalAssetRecord]
}>()

const { t } = useI18n()

const searchModel = computed({
  get: () => props.search,
  set: (value: string) => emit('update:search', value),
})

const statusFilterModel = computed({
  get: () => props.statusFilter,
  set: (value: string) => emit('update:statusFilter', value),
})
</script>

<style scoped>
.tab-toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.mt-16 { margin-top: 16px; }

:deep(.el-table__row) { cursor: pointer; }
</style>
