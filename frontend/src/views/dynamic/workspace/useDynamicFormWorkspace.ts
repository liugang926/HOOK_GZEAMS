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
  const isAssetProject = computed(() => objectCode.value === 'AssetProject')

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

    if (isAssetProject.value) {
      return isEdit.value
        ? (isZhLocale.value
          ? '更新项目范围、预算与负责人信息。保存后可继续在项目详情页处理资产分配和成员协同。'
          : 'Update the project scope, budget, and ownership details. After save, continue with asset allocation and member coordination from the project detail workspace.')
        : (isZhLocale.value
          ? '完成项目立项信息后保存，系统会生成项目编号，并在详情页承接资产与成员协同。'
          : 'Complete the project setup details and save to generate the project code, then continue with assets and members from the detail workspace.')
    }

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
    if (isAssetProject.value) {
      return isEdit.value
        ? (isZhLocale.value ? '编辑项目工作区' : 'Edit project workspace')
        : (isZhLocale.value ? '创建项目工作区' : 'Create project workspace')
    }
    return isEdit.value
      ? (isZhLocale.value ? '编辑对象信息' : 'Edit object information')
      : (isZhLocale.value ? '填写对象信息' : 'Complete object information')
  })

  const formPanelDescription = computed(() => {
    if (isAssetProject.value) {
      return isEdit.value
        ? (isZhLocale.value
          ? '优先校准项目负责人、时间与预算字段，保存后详情页会同步展示最新资产和成员上下文。'
          : 'Update owner, schedule, and budget first. The detail workspace will immediately reflect the latest asset and member context after save.')
        : (isZhLocale.value
          ? '先完成项目主数据录入。项目创建成功后，可在详情页继续分配资产和维护成员。'
          : 'Start with the core project master data. After creation, continue with asset allocation and member maintenance from the detail page.')
    }
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
    ...(isAssetProject.value
      ? [
        isZhLocale.value
          ? '项目创建后会自动生成项目编码，后续项目资产和成员明细都会以当前项目为上下文。'
          : 'A project code is generated automatically after creation, and the related asset/member flows use this project as their working context.',
        isZhLocale.value
          ? '建议在保存前确认项目经理、所属部门与计划时间，避免后续资产分配归属错误。'
          : 'Confirm the project manager, department, and schedule before saving to avoid downstream allocation errors.',
      ]
      : []),
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
    if (isAssetProject.value) {
      return isEdit.value
        ? (isZhLocale.value
          ? '确认项目信息无误后保存，详情页中的资产与成员面板会基于最新数据刷新。'
          : 'Save once the project details are confirmed. The asset and member panels on the detail page will refresh from the updated data.')
        : (isZhLocale.value
          ? '保存后进入统一项目工作区，继续处理项目资产和成员协同。'
          : 'Save to enter the unified project workspace and continue with project assets and member coordination.')
    }
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
