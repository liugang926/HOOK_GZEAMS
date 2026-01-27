import { computed } from 'vue'

export function useFieldPermissions(fieldPermissions = {}, fieldDefinitions = []) {

    // 获取字段权限: 'editable' | 'read_only' | 'hidden'
    const getFieldPermission = (field) => {
        // 优先使用外部传入的权限覆盖 (例如来自工作流)
        if (fieldPermissions.value && fieldPermissions.value[field.code]) {
            return fieldPermissions.value[field.code]
        }

        // 系统字段强制只读 (除特殊情况)
        if (field.is_system && !field.is_editable) return 'read_only'

        // 字段定义中的只读属性
        if (field.is_readonly) return 'read_only'

        return 'editable'
    }

    const isFieldReadonly = (field) => getFieldPermission(field) === 'read_only'

    const isFieldVisible = (field) => getFieldPermission(field) !== 'hidden'

    return {
        getFieldPermission,
        isFieldReadonly,
        isFieldVisible
    }
}
