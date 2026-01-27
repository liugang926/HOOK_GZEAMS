<template>
  <div class="approver-selector">
    <el-tabs
      v-model="activeTab"
      type="card"
      size="small"
    >
      <el-tab-pane
        label="指定成员"
        name="user"
      >
        <UserSelector
          v-model="approvers"
          :multiple="true"
        />
      </el-tab-pane>

      <el-tab-pane
        label="指定角色"
        name="role"
      >
        <RoleSelector v-model="approvers" />
      </el-tab-pane>

      <el-tab-pane
        label="发起人领导"
        name="leader"
      >
        <div class="leader-config">
          <el-radio-group v-model="leaderConfig.type">
            <el-radio value="direct">
              直属领导
            </el-radio>
            <el-radio value="department">
              部门负责人
            </el-radio>
            <el-radio value="top">
              第N上级
            </el-radio>
          </el-radio-group>

          <el-input-number
            v-if="leaderConfig.type === 'top'"
            v-model="leaderConfig.level"
            :min="1"
            :max="5"
            size="small"
            style="margin-left: 10px"
          />
          <span
            v-if="leaderConfig.type === 'top'"
            style="margin-left: 5px"
          >级</span>
        </div>
      </el-tab-pane>

      <el-tab-pane
        label="动态选择"
        name="dynamic"
      >
        <el-form size="small">
          <el-form-item label="来源字段">
            <el-select v-model="dynamicConfig.field">
              <el-option
                label="申请人"
                value="applicant"
              />
              <el-option
                label="部门"
                value="department"
              />
              <el-option
                label="领用部门"
                value="pickup_department"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="关系">
            <el-select v-model="dynamicConfig.relation">
              <el-option
                label="的直属领导"
                value="leader"
              />
              <el-option
                label="的部门负责人"
                value="manager"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane
        label="自选"
        name="self_select"
      >
        <el-form size="small">
          <el-form-item label="可选范围">
            <el-radio-group v-model="selfSelectConfig.range">
              <el-radio value="all">
                全员
              </el-radio>
              <el-radio value="department">
                本部门
              </el-radio>
              <el-radio value="custom">
                自定义
              </el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="选择人数">
            <el-input-number
              v-model="selfSelectConfig.count"
              :min="1"
              :max="10"
              size="small"
            />
            <span style="margin-left: 5px">人</span>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import UserSelector from '@/components/common/UserSelector.vue'
import RoleSelector from '@/components/common/RoleSelector.vue'

interface Props {
  modelValue: any[]
}

interface Emits {
  (e: 'update:modelValue', value: any[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const activeTab = ref('user')

const approvers = computed({
  get: () => props.modelValue || [],
  set: (val) => emit('update:modelValue', val)
})

const leaderConfig = ref({
  type: 'direct',
  level: 1
})

const dynamicConfig = ref({
  field: 'applicant',
  relation: 'leader'
})

const selfSelectConfig = ref({
  range: 'department',
  count: 1
})
</script>

<style scoped>
.approver-selector {
  padding: 10px 0;
}

.leader-config {
  display: flex;
  align-items: center;
}
</style>
