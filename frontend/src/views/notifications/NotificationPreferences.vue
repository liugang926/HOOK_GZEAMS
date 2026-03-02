<template>
  <div class="notification-preferences">
    <el-card class="preferences-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2 class="title">
              {{ t('notifications.preferences.title') }}
            </h2>
            <p class="subtitle">
              {{ t('notifications.preferences.subtitle') }}
            </p>
          </div>
          <div class="header-actions">
            <el-button @click="goToCenter">
              {{ t('notifications.actions.backToCenter') }}
            </el-button>
            <el-button
              type="primary"
              :loading="saving"
              @click="savePreferences"
            >
              {{ t('common.actions.save') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane
          :label="t('notifications.preferences.tabs.my')"
          name="my"
        >
          <el-form
            ref="formRef"
            :model="formModel"
            label-width="180px"
            class="preference-form"
          >
            <el-form-item :label="t('notifications.preferences.fields.enableInbox')">
              <el-switch v-model="formModel.enableInbox" />
            </el-form-item>
            <el-form-item :label="t('notifications.preferences.fields.enableEmail')">
              <el-switch v-model="formModel.enableEmail" />
            </el-form-item>
            <el-form-item :label="t('notifications.preferences.fields.enableSms')">
              <el-switch v-model="formModel.enableSms" />
            </el-form-item>
            <el-form-item :label="t('notifications.preferences.fields.enableWework')">
              <el-switch v-model="formModel.enableWework" />
            </el-form-item>
            <el-form-item :label="t('notifications.preferences.fields.enableDingtalk')">
              <el-switch v-model="formModel.enableDingtalk" />
            </el-form-item>
            <el-form-item :label="t('notifications.preferences.fields.quietHoursEnabled')">
              <el-switch v-model="formModel.quietHoursEnabled" />
            </el-form-item>
            <el-form-item :label="t('notifications.preferences.fields.quietHoursStart')">
              <el-time-picker
                v-model="formModel.quietHoursStart"
                value-format="HH:mm:ss"
                format="HH:mm"
                :placeholder="t('notifications.preferences.placeholders.time')"
                style="width: 220px"
                :disabled="!formModel.quietHoursEnabled"
              />
            </el-form-item>
            <el-form-item :label="t('notifications.preferences.fields.quietHoursEnd')">
              <el-time-picker
                v-model="formModel.quietHoursEnd"
                value-format="HH:mm:ss"
                format="HH:mm"
                :placeholder="t('notifications.preferences.placeholders.time')"
                style="width: 220px"
                :disabled="!formModel.quietHoursEnabled"
              />
            </el-form-item>
            <el-form-item :label="t('notifications.preferences.fields.emailAddress')">
              <el-input
                v-model="formModel.emailAddress"
                :placeholder="t('notifications.preferences.placeholders.email')"
                style="max-width: 360px"
              />
            </el-form-item>
            <el-form-item :label="t('notifications.preferences.fields.phoneNumber')">
              <el-input
                v-model="formModel.phoneNumber"
                :placeholder="t('notifications.preferences.placeholders.phone')"
                style="max-width: 260px"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane
          v-if="isAdmin"
          :label="t('notifications.preferences.tabs.channels')"
          name="channels"
        >
          <el-table
            v-loading="channelsLoading"
            :data="channelRows"
            row-key="id"
          >
            <el-table-column
              prop="channelType"
              :label="t('notifications.columns.channel')"
              min-width="140"
            />
            <el-table-column
              prop="channelName"
              :label="t('notifications.columns.channelName')"
              min-width="180"
            />
            <el-table-column
              prop="priority"
              :label="t('notifications.columns.priority')"
              width="90"
            />
            <el-table-column
              prop="status"
              :label="t('notifications.columns.status')"
              width="120"
            />
            <el-table-column
              :label="t('notifications.columns.enabled')"
              width="120"
            >
              <template #default="{ row }">
                <el-switch
                  :model-value="Boolean(row.isEnabled ?? row.is_enabled)"
                  @change="(value: any) => handleToggleChannel(row, value)"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane
          v-if="isAdmin"
          :label="t('notifications.preferences.tabs.templates')"
          name="templates"
        >
          <el-table
            v-loading="templatesLoading"
            :data="templateRows"
            row-key="id"
          >
            <el-table-column
              prop="templateCode"
              :label="t('notifications.columns.templateCode')"
              min-width="180"
            />
            <el-table-column
              prop="templateName"
              :label="t('notifications.columns.templateName')"
              min-width="220"
            />
            <el-table-column
              prop="templateType"
              :label="t('notifications.columns.type')"
              min-width="160"
            />
            <el-table-column
              prop="channel"
              :label="t('notifications.columns.channel')"
              width="120"
            />
            <el-table-column
              prop="language"
              :label="t('notifications.columns.language')"
              width="110"
            />
            <el-table-column
              prop="version"
              :label="t('notifications.columns.version')"
              width="100"
            />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  notificationChannelApi,
  notificationConfigApi,
  notificationTemplateApi
} from '@/api/notifications'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const { t } = useI18n()
const userStore = useUserStore()

const activeTab = ref('my')
const formRef = ref()
const configId = ref<string>('')
const saving = ref(false)

const channelsLoading = ref(false)
const channelRows = ref<any[]>([])
const templatesLoading = ref(false)
const templateRows = ref<any[]>([])

const formModel = reactive({
  enableInbox: true,
  enableEmail: true,
  enableSms: false,
  enableWework: true,
  enableDingtalk: false,
  quietHoursEnabled: false,
  quietHoursStart: '',
  quietHoursEnd: '',
  emailAddress: '',
  phoneNumber: ''
})

const isAdmin = computed(() => {
  const userInfo = userStore.userInfo || {}
  const roleCodes = Array.isArray(userStore.roles) ? userStore.roles.map((r: any) => String(r).toLowerCase()) : []
  return Boolean(
    userInfo.isStaff ||
    userInfo.is_staff ||
    userInfo.isSuperuser ||
    userInfo.is_superuser ||
    roleCodes.includes('admin') ||
    roleCodes.includes('superadmin')
  )
})

const asRecord = (value: any): Record<string, any> => {
  return value && typeof value === 'object' ? value : {}
}

const unwrapPayload = (payload: any): any => {
  const root = asRecord(payload)
  if ('data' in root && root.data !== undefined) return root.data
  return payload
}

const parseList = (payload: any): any[] => {
  const data = unwrapPayload(payload)
  if (Array.isArray(data)) return data
  const record = asRecord(data)
  return Array.isArray(record.results) ? record.results : []
}

const hydrateForm = (raw: any) => {
  const item = asRecord(raw)
  configId.value = String(item.id || '')
  formModel.enableInbox = Boolean(item.enableInbox ?? item.enable_inbox ?? true)
  formModel.enableEmail = Boolean(item.enableEmail ?? item.enable_email ?? true)
  formModel.enableSms = Boolean(item.enableSms ?? item.enable_sms ?? false)
  formModel.enableWework = Boolean(item.enableWework ?? item.enable_wework ?? true)
  formModel.enableDingtalk = Boolean(item.enableDingtalk ?? item.enable_dingtalk ?? false)
  formModel.quietHoursEnabled = Boolean(item.quietHoursEnabled ?? item.quiet_hours_enabled ?? false)
  formModel.quietHoursStart = String(item.quietHoursStart ?? item.quiet_hours_start ?? '')
  formModel.quietHoursEnd = String(item.quietHoursEnd ?? item.quiet_hours_end ?? '')
  formModel.emailAddress = String(item.emailAddress ?? item.email_address ?? '')
  formModel.phoneNumber = String(item.phoneNumber ?? item.phone_number ?? '')
}

const loadMyConfig = async () => {
  try {
    const response = await notificationConfigApi.myConfig()
    hydrateForm(unwrapPayload(response))
  } catch (error) {
    const fallback = await notificationConfigApi.list({ page: 1, page_size: 1 })
    const first = parseList(fallback)[0]
    if (first) hydrateForm(first)
    console.warn('my_config endpoint unavailable, fallback to list', error)
  }
}

const loadAdminData = async () => {
  if (!isAdmin.value) return

  channelsLoading.value = true
  templatesLoading.value = true
  try {
    const [channels, templates] = await Promise.all([
      notificationChannelApi.list({ page: 1, page_size: 200, ordering: '-priority' }),
      notificationTemplateApi.list({ page: 1, page_size: 200, ordering: '-created_at' })
    ])
    channelRows.value = parseList(channels)
    templateRows.value = parseList(templates)
  } finally {
    channelsLoading.value = false
    templatesLoading.value = false
  }
}

const savePreferences = async () => {
  if (!configId.value) {
    ElMessage.warning(t('common.messages.operationFailed'))
    return
  }
  saving.value = true
  try {
    await notificationConfigApi.update(configId.value, {
      enable_inbox: formModel.enableInbox,
      enable_email: formModel.enableEmail,
      enable_sms: formModel.enableSms,
      enable_wework: formModel.enableWework,
      enable_dingtalk: formModel.enableDingtalk,
      quiet_hours_enabled: formModel.quietHoursEnabled,
      quiet_hours_start: formModel.quietHoursStart || null,
      quiet_hours_end: formModel.quietHoursEnd || null,
      email_address: formModel.emailAddress,
      phone_number: formModel.phoneNumber
    })
    ElMessage.success(t('notifications.messages.preferenceSaved'))
  } finally {
    saving.value = false
  }
}

const handleToggleChannel = async (row: any, value: boolean) => {
  const id = row?.id
  if (!id) return
  try {
    await notificationChannelApi.update(String(id), { is_enabled: value })
    row.isEnabled = value
    row.is_enabled = value
    ElMessage.success(t('notifications.messages.channelUpdated'))
  } catch (error) {
    row.isEnabled = !value
    row.is_enabled = !value
    console.error('Failed to update channel status', error)
  }
}

const goToCenter = () => {
  router.push('/notifications/center')
}

onMounted(async () => {
  await loadMyConfig()
  await loadAdminData()
})
</script>

<style scoped lang="scss">
.notification-preferences {
  min-height: 100%;
}

.preferences-card {
  border-radius: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.subtitle {
  margin: 6px 0 0;
  color: #909399;
  font-size: 13px;
}

.header-actions {
  display: inline-flex;
  gap: 8px;
}

.preference-form {
  max-width: 760px;
  padding-top: 6px;
}

@media (max-width: 900px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
