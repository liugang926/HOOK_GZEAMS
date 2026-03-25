import { defineComponent } from 'vue'

export const loadingDirectiveStubs = {
  loading: () => undefined,
}

export const createObjectAvatarStub = () => defineComponent({
  template: '<div class="object-avatar-stub" />',
})

export const createElementResultStub = () => defineComponent({
  props: ['title', 'subTitle'],
  template: '<div class="el-result-stub"><div>{{ title }}</div><div>{{ subTitle }}</div><slot /><slot name="extra" /></div>',
})

export const createPlainButtonStub = () => defineComponent({
  template: '<button><slot /></button>',
})

export const createClickableButtonStub = () => defineComponent({
  emits: ['click'],
  template: '<button @click="$emit(\'click\', $event)"><slot /></button>',
})

export const createPlainCardStub = () => defineComponent({
  template: '<div><slot /><slot name="header" /></div>',
})

export const createPlainStepsStub = () => defineComponent({
  template: '<div><slot /></div>',
})

export const createDynamicListGlobalOptions = (clickableButtons = false) => ({
  directives: loadingDirectiveStubs,
  stubs: {
    ContextDrawer: defineComponent({ template: '<div class="drawer-stub" />' }),
    FieldRenderer: defineComponent({ template: '<div class="field-stub" />' }),
    ObjectAvatar: createObjectAvatarStub(),
    ExportButton: defineComponent({ template: '<div class="export-button-stub" />' }),
    ImportButton: defineComponent({ template: '<div class="import-button-stub" />' }),
    ExportFieldSelector: defineComponent({ template: '<div class="export-selector-stub" />' }),
    ImportConfigDialog: defineComponent({ template: '<div class="import-config-stub" />' }),
    'el-alert': defineComponent({ template: '<div />' }),
    'el-input': defineComponent({ template: '<input />' }),
    'el-option': defineComponent({ template: '<option />' }),
    'el-result': createElementResultStub(),
    'el-select': defineComponent({ template: '<select><slot /></select>' }),
    'el-skeleton': defineComponent({ template: '<div />' }),
    'el-button': clickableButtons ? createClickableButtonStub() : createPlainButtonStub(),
    'el-tag': defineComponent({ template: '<span><slot /></span>' }),
  },
})

export const createDynamicFormGlobalOptions = (dynamicFormStub: ReturnType<typeof defineComponent>) => ({
  directives: loadingDirectiveStubs,
  stubs: {
    DynamicForm: dynamicFormStub,
    ObjectAvatar: createObjectAvatarStub(),
    'el-result': createElementResultStub(),
    'el-button': createClickableButtonStub(),
  },
})

export const createDynamicDetailGlobalOptions = () => ({
  directives: loadingDirectiveStubs,
  stubs: {
    ObjectAvatar: createObjectAvatarStub(),
    'el-card': createPlainCardStub(),
    'el-result': createElementResultStub(),
    'el-button': createPlainButtonStub(),
    'el-step': defineComponent({ template: '<div />' }),
    'el-steps': createPlainStepsStub(),
  },
})
