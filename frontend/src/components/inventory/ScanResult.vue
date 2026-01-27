<template>
  <div
    v-if="asset"
    class="scan-result"
  >
    <el-card>
      <template #header>
        <div class="card-header">
          <span>扫描结果</span>
          <el-tag :type="getStatusType(asset.status)">
            {{ getStatusLabel(asset.status) }}
          </el-tag>
        </div>
      </template>
      <el-descriptions
        :column="1"
        border
      >
        <el-descriptions-item label="资产编码">
          {{ asset.code }}
        </el-descriptions-item>
        <el-descriptions-item label="资产名称">
          {{ asset.name }}
        </el-descriptions-item>
        <el-descriptions-item label="位置">
          {{ asset.locationName }}
        </el-descriptions-item>
        <el-descriptions-item label="保管人">
          {{ asset.custodianName }}
        </el-descriptions-item>
      </el-descriptions>
      <div class="actions mt-4">
        <el-button
          type="primary"
          @click="handleConfirm"
        >
          确认盘点
        </el-button>
        <el-button @click="$emit('cancel')">
          取消
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
    asset: {
        type: Object,
        default: null
    }
})

const emit = defineEmits(['confirm', 'cancel'])

const handleConfirm = () => {
    emit('confirm', props.asset)
}

const getStatusType = (status: string) => {
  const map: any = { idle: 'success', in_use: 'warning', maintenance: 'danger' }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: any = { idle: '闲置', in_use: '使用中', maintenance: '维修中' }
  return map[status] || status
}
</script>

<style scoped>
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.mt-4 {
    margin-top: 15px;
}
.actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
}
</style>
