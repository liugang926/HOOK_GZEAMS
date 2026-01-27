import { ref, reactive } from 'vue'
import { getFieldDefinitions, getPageLayout, getBusinessObject } from '@/api/system'
import { useValidation } from './useValidation'
import { ElMessage } from 'element-plus'

export function useDynamicForm(businessObject, layoutCode = 'form', initialLayoutConfig = null, initialFieldDefinitions = null) {
    const formRef = ref(null)
    const formData = reactive({})
    const formRules = reactive({})
    const fieldDefinitions = ref([])
    const layoutSections = ref([])
    const loading = ref(false)
    const businessObjectActions = ref([])

    // 加载元数据
    const loadMetadata = async () => {
        loading.value = true
        try {
            // If initial config is provided, use it (Preview Mode)
            if (initialLayoutConfig) {
                fieldDefinitions.value = initialFieldDefinitions || []
                layoutSections.value = parseLayoutConfig(initialLayoutConfig)
                initFormRules(fieldDefinitions.value)
                initFormData(fieldDefinitions.value)
                return
            }

            // Run in parallel for performance
            const [fieldsRes, layoutRes, objectRes] = await Promise.all([
                getFieldDefinitions(businessObject),
                getPageLayout(businessObject, layoutCode),
                getBusinessObject(businessObject)
            ])

            fieldDefinitions.value = fieldsRes.results || fieldsRes.data || []
            businessObjectActions.value = objectRes.data?.actions || objectRes.actions || []

            const layoutConfig = layoutRes.data?.layout_config || layoutRes.layout_config
            layoutSections.value = parseLayoutConfig(layoutConfig)

            initFormRules(fieldDefinitions.value)
            initFormData(fieldDefinitions.value)

        } catch (error) {
            console.error('加载元数据失败:', error)
            ElMessage.error('加载表单配置失败')
        } finally {
            loading.value = false
        }
    }

    // 解析布局配置
    const parseLayoutConfig = (config) => {
        if (!config || !config.sections) {
            // Default fallback layout if no config exists
            return [{
                id: 'default',
                title: '基本信息',
                fields: fieldDefinitions.value.map(f => f.code),
                visible: true
            }]
        }

        return config.sections.map(section => ({
            ...section,
            visible: section.visible !== false,
            collapsed: section.collapsed === true
        }))
    }

    // 初始化验证规则
    const { validateFieldCustom } = useValidation(formData, fieldDefinitions)

    const initFormRules = (fields) => {
        Object.keys(formRules).forEach(key => delete formRules[key])

        fields.forEach(field => {
            const rules = []

            if (field.is_required) {
                rules.push({
                    required: true,
                    message: `${field.name}不能为空`,
                    trigger: ['blur', 'change']
                })
            }

            if (field.regex_pattern) {
                rules.push({
                    pattern: new RegExp(field.regex_pattern),
                    message: '格式不正确',
                    trigger: 'blur'
                })
            }

            // Advanced Validation Rules (Phase 3)
            if (field.validation_rules && Array.isArray(field.validation_rules) && field.validation_rules.length > 0) {
                rules.push({
                    validator: (rule, value, callback) => {
                        const result = validateFieldCustom(field.code, value, field.validation_rules)
                        if (result === true) {
                            callback()
                        } else {
                            callback(new Error(result))
                        }
                    },
                    trigger: ['blur', 'change']
                })
            }

            if (rules.length > 0) {
                formRules[field.code] = rules
            }
        })
    }

    // 初始化表单数据
    const initFormData = (fields) => {
        fields.forEach(field => {
            // Only set if not already present (preserve passed-in values)
            if (!(field.code in formData)) {
                if (field.default_value !== undefined && field.default_value !== null && field.default_value !== '') {
                    formData[field.code] = parseDefaultValue(field.default_value)
                } else if (field.field_type === 'select' && field.multiple) {
                    formData[field.code] = []
                } else if (field.field_type === 'number' || field.field_type === 'currency') {
                    formData[field.code] = undefined // Better than 0 for placeholder visibility
                } else if (field.field_type === 'sub_table') {
                    formData[field.code] = []
                } else if (field.field_type === 'boolean') {
                    formData[field.code] = false
                } else {
                    formData[field.code] = ''
                }
            }
        })
    }

    // 解析默认值（支持变量）
    const parseDefaultValue = (value) => {
        if (typeof value !== 'string') return value

        const now = new Date()
        const today = now.toISOString().split('T')[0]

        // Simple variable replacement
        if (value.includes('{today}')) return value.replace('{today}', today)
        if (value.includes('{now}')) return value.replace('{now}', now.toISOString())

        return value
    }

    // 表单验证
    const validate = () => formRef.value?.validate()

    // 重置表单
    const resetFields = () => {
        formRef.value?.resetFields()
        // Reset to defaults
        initFormData(fieldDefinitions.value)
    }

    return {
        formRef,
        formData,
        formRules,
        fieldDefinitions,
        layoutSections,
        loading,
        businessObjectActions,
        loadMetadata,
        validate,
        resetFields
    }
}
