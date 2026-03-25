import { computed, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessageBox } from 'element-plus'
import { camelToSnake, snakeToCamel } from '@/utils/case'

interface AuditInfoLike {
  createdBy?: string
  createdAt?: string | Date
  updatedBy?: string
  updatedAt?: string | Date
}

interface ExtraActionLike {
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | string
  icon?: string
  action: () => void | Promise<void>
}

interface DetailActionProps {
  auditInfo?: AuditInfoLike | null
  editMode: boolean
  showEdit: boolean
  showDelete: boolean
  editText?: string
  deleteText?: string
  deleteConfirmMessage?: string
  formData: Record<string, any>
  extraActions: ExtraActionLike[]
}

interface UseBaseDetailPageActionsOptions {
  props: DetailActionProps
  emit: {
    (e: 'edit'): void
    (e: 'delete'): void
    (e: 'back'): void
    (e: 'save', data: Record<string, any>): void
    (e: 'cancel'): void
    (e: 'update:formData', data: Record<string, any>): void
  }
  formRef: Ref<any>
}

export function useBaseDetailPageActions(options: UseBaseDetailPageActionsOptions) {
  const { props, emit, formRef } = options
  const { t } = useI18n()

  const hasAuditInfo = computed(() => {
    return !!(props.auditInfo && (
      props.auditInfo.createdBy ||
      props.auditInfo.createdAt ||
      props.auditInfo.updatedBy ||
      props.auditInfo.updatedAt
    ))
  })

  const handleDelete = async () => {
    try {
      await ElMessageBox.confirm(
        props.deleteConfirmMessage || t('common.messages.confirmDelete', { count: 1 }),
        t('common.actions.confirm'),
        {
          type: 'warning',
          confirmButtonText: t('common.actions.confirm'),
          cancelButtonText: t('common.actions.cancel')
        }
      )
      emit('delete')
    } catch {
      // user cancelled
    }
  }

  const availableActions = computed(() => {
    const actions: Array<{ label: string; type?: string; icon?: string; action: () => void; disabled?: boolean }> = []

    if (props.editMode) {
      actions.push({ label: t('common.actions.cancel'), action: () => emit('cancel') })
      actions.push({ label: t('common.actions.save'), type: 'primary', action: () => emit('save', props.formData) })
      return actions
    }

    if (props.showEdit) {
      actions.push({ label: props.editText || t('common.actions.edit'), type: 'primary', action: () => emit('edit') })
    }

    props.extraActions.forEach((action) => {
      actions.push(action)
    })

    if (props.showDelete) {
      actions.push({
        label: props.deleteText || t('common.actions.delete'),
        type: 'danger',
        action: handleDelete
      })
    }

    return actions
  })

  const handleBack = () => {
    emit('back')
  }

  const validateForm = async () => {
    if (!formRef.value) return true
    try {
      const valid = await formRef.value.validate()
      return valid
    } catch {
      return false
    }
  }

  const updateFormData = (prop: string, value: any) => {
    const newData = { ...props.formData }
    newData[prop] = value

    const camelKey = snakeToCamel(prop)
    if (camelKey !== prop && (Object.prototype.hasOwnProperty.call(newData, camelKey) || prop.includes('_'))) {
      newData[camelKey] = value
    }

    const snakeKey = camelToSnake(prop)
    if (snakeKey !== prop && (Object.prototype.hasOwnProperty.call(newData, snakeKey) || /[A-Z]/.test(prop))) {
      newData[snakeKey] = value
    }

    emit('update:formData', newData)
  }

  return {
    hasAuditInfo,
    availableActions,
    handleDelete,
    handleBack,
    validateForm,
    updateFormData
  }
}
