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
  template: '<button @click="$emit(\'click\')"><slot /></button>',
})

export const createPlainCardStub = () => defineComponent({
  template: '<div><slot /><slot name="header" /></div>',
})

export const createPlainStepsStub = () => defineComponent({
  template: '<div><slot /></div>',
})
