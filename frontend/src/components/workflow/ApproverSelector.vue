<template>
  <div class="approver-selector">
    <el-tabs
      v-model="activeTab"
      type="card"
      size="small"
    >
      <el-tab-pane
        :label="t('workflow.approverSelector.specifiedMember')"
        name="user"
      >
        <UserSelector
          v-model="approvers"
          :multiple="true"
        />
      </el-tab-pane>

      <el-tab-pane
        :label="t('workflow.approverSelector.specifiedRole')"
        name="role"
      >
        <RoleSelector v-model="approvers" />
      </el-tab-pane>

      <el-tab-pane
        :label="t('workflow.approverSelector.initiatorLeader')"
        name="leader"
      >
        <div class="leader-config">
          <el-radio-group v-model="leaderConfig.type">
            <el-radio value="direct">
              {{ t('workflow.approverSelector.directLeader') }}
            </el-radio>
            <el-radio value="department">
              {{ t('workflow.approverSelector.departmentManager') }}
            </el-radio>
            <el-radio value="top">
              {{ t('workflow.approverSelector.nthLevel') }}
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
          >{{ t('common.units.level') }}</span>
        </div>
      </el-tab-pane>

      <el-tab-pane
        :label="t('workflow.approverSelector.dynamic')"
        name="dynamic"
      >
        <el-form size="small">
          <el-form-item :label="t('workflow.approverSelector.sourceField')">
            <el-select v-model="dynamicConfig.field">
              <el-option
                :label="t('workflow.fields.applicant')"
                value="applicant"
              />
              <el-option
                :label="t('workflow.fields.department')"
                value="department"
              />
              <el-option
                :label="t('workflow.fields.pickupDepartment')"
                value="pickup_department"
              />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('workflow.approverSelector.relationship')">
            <el-select v-model="dynamicConfig.relation">
              <el-option
                :label="t('workflow.approverSelector.directLeaderOf')"
                value="leader"
              />
              <el-option
                :label="t('workflow.approverSelector.departmentManagerOf')"
                value="manager"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane
        :label="t('workflow.approverSelector.selfSelect')"
        name="self_select"
      >
        <el-form size="small">
          <el-form-item :label="t('workflow.approverSelector.selectableRange')">
            <el-radio-group v-model="selfSelectConfig.range">
              <el-radio value="all">
                {{ t('workflow.approverSelector.allMembers') }}
              </el-radio>
              <el-radio value="department">
                {{ t('workflow.approverSelector.currentDepartment') }}
              </el-radio>
              <el-radio value="custom">
                {{ t('workflow.approverSelector.custom') }}
              </el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item :label="t('workflow.approverSelector.selectCount')">
            <el-input-number
              v-model="selfSelectConfig.count"
              :min="1"
              :max="10"
              size="small"
            />
            <span style="margin-left: 5px">{{ t('common.units.people') }}</span>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import UserSelector from '@/components/common/UserSelector.vue'
import RoleSelector from '@/components/common/RoleSelector.vue'

const { t } = useI18n()

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
