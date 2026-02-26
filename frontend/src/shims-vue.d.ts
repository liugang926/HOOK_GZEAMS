/* eslint-disable */
declare module '*.vue' {
    import type { DefineComponent } from 'vue'
    const component: DefineComponent<{}, {}, any>
    export default component
}

declare module 'vue-router'
declare module 'element-plus'
declare module '@element-plus/icons-vue'
declare module 'element-plus/dist/locale/zh-cn.mjs'
declare module 'element-plus/dist/locale/en.mjs'
