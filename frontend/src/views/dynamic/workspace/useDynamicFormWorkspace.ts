import { computed, type ComputedRef, type Ref } from 'vue'
import type { ObjectMetadata } from '@/api/dynamic'
import type { ObjectWorkspaceChip, ObjectWorkspaceStat } from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'
import type { ObjectWorkspaceInfoRow } from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'

interface Params {
  isZhLocale: ComputedRef<boolean>
  isEdit: ComputedRef<boolean>
  canEdit: ComputedRef<boolean>
  objectCode: Ref<string>
  objectMetadata: Ref<ObjectMetadata | null>
  objectDisplayName: ComputedRef<string>
}

export const useDynamicFormWorkspace = ({
  isZhLocale,
  isEdit,
  canEdit,
  objectCode,
  objectMetadata,
  objectDisplayName,
}: Params) => {
  const moduleLabel = computed(() => {
    const raw = String(objectMetadata.value?.module || '').trim()
    return raw || objectCode.value
  })

  const modeLabel = computed(() => {
    return isEdit.value ? (isZhLocale.value ? '编辑' : 'Edit') : (isZhLocale.value ? '新建' : 'Create')
  })

  const readonlyLabel = computed(() => {
    return isZhLocale.value ? '只读访问' : 'Read only'
  })

  const pageTitle = computed(() => {
    return `${modeLabel.value} ${objectDisplayName.value}`
  })

  const pageDescription = computed(() => {
    const description = String(objectMetadata.value?.description || '').trim()
    if (description) return description

    if (isEdit.value) {
      return isZhLocale.value
        ? '调整表单内容并保存，修改会立即同步到当前对象记录。'
        : 'Update the form fields and save to apply changes to this record immediately.'
    }

    return isZhLocale.value
      ? '填写必要信息并保存，系统会按当前对象配置创建一条新记录。'
      : 'Complete the required information and save to create a new record with the current object configuration.'
  })

  const fieldCount = computed(() => {
    return Array.isArray(objectMetadata.value?.fields) ? objectMetadata.value?.fields.length || 0 : 0
  })

  const requiredFieldCount = computed(() => {
    return (objectMetadata.value?.fields || []).filter((field: any) => {
      return field?.required === true || field?.isRequired === true
    }).length
  })

  const fieldCountLabel = computed(() => {
    return isZhLocale.value ? '字段数' : 'Fields'
  })

  const requiredFieldCountLabel = computed(() => {
    return isZhLocale.value ? '必填字段' : 'Required'
  })

  const saveDestinationLabel = computed(() => {
    return isZhLocale.value ? '保存目标' : 'Target'
  })

  const formPanelTitle = computed(() => {
    return isEdit.value
      ? (isZhLocale.value ? '编辑对象信息' : 'Edit object information')
      : (isZhLocale.value ? '填写对象信息' : 'Complete object information')
  })

  const formPanelDescription = computed(() => {
    return isEdit.value
      ? (isZhLocale.value
        ? '建议优先处理关键信息和必填项，保存后将直接刷新到对象详情与列表。'
        : 'Focus on key and required fields first. Saved changes will immediately sync to the detail and list views.')
      : (isZhLocale.value
        ? '按当前对象布局完成录入。支持快捷键保存，系统会按字段权限自动处理只读项。'
        : 'Complete the form using the current object layout. Save shortcuts are supported and read-only fields stay protected automatically.')
  })

  const summaryLabel = computed(() => {
    return isZhLocale.value ? '对象摘要' : 'Object summary'
  })

  const objectCodeLabel = computed(() => {
    return isZhLocale.value ? '对象编码' : 'Object code'
  })

  const moduleNameLabel = computed(() => {
    return isZhLocale.value ? '所属模块' : 'Module'
  })

  const permissionLabel = computed(() => {
    return isZhLocale.value ? '当前权限' : 'Access'
  })

  const accessLabel = computed(() => {
    if (!canEdit.value) return readonlyLabel.value
    return isEdit.value
      ? (isZhLocale.value ? '可编辑' : 'Editable')
      : (isZhLocale.value ? '可创建' : 'Create enabled')
  })

  const tipsLabel = computed(() => {
    return isZhLocale.value ? '操作提示' : 'Tips'
  })

  const tips = computed<string[]>(() => [
    isZhLocale.value
      ? '先完成必填字段，保存失败时优先检查红色校验提示。'
      : 'Complete required fields first and use validation hints as the first checkpoint if saving fails.',
    isZhLocale.value
      ? '编辑模式下，保存会直接覆盖当前记录；取消会返回对象列表。'
      : 'In edit mode, save writes directly to the current record, while cancel returns to the list.',
    isZhLocale.value
      ? '如果当前账号只有查看权限，表单会自动切换为只读。'
      : 'The form automatically switches to read-only when the current account only has view permission.',
  ])

  const actionBarText = computed(() => {
    return isEdit.value
      ? (isZhLocale.value ? '确认修改无误后保存，系统会立即返回列表页。' : 'Save after confirming your changes. You will return to the list right away.')
      : (isZhLocale.value ? '完成录入后保存，系统将创建一条新的对象记录。' : 'Save after completion to create a new object record.')
  })

  const heroChips = computed<ObjectWorkspaceChip[]>(() => {
    const chips: ObjectWorkspaceChip[] = [
      { label: modeLabel.value, kind: 'primary' },
      { label: objectCode.value },
    ]
    if (!canEdit.value) {
      chips.push({ label: readonlyLabel.value, kind: 'muted' })
    }
    return chips
  })

  const heroStats = computed<ObjectWorkspaceStat[]>(() => ([
    { label: fieldCountLabel.value, value: fieldCount.value },
    { label: requiredFieldCountLabel.value, value: requiredFieldCount.value },
    { label: saveDestinationLabel.value, value: objectDisplayName.value },
  ]))

  const infoRows = computed<ObjectWorkspaceInfoRow[]>(() => ([
    { label: objectCodeLabel.value, value: objectCode.value },
    { label: moduleNameLabel.value, value: moduleLabel.value },
    { label: permissionLabel.value, value: accessLabel.value },
  ]))

  return {
    moduleLabel,
    modeLabel,
    pageTitle,
    pageDescription,
    formPanelTitle,
    formPanelDescription,
    summaryLabel,
    tipsLabel,
    heroChips,
    heroStats,
    infoRows,
    tips,
    actionBarText,
  }
}
