\# 前端开发规则（Gemini 3 Pro）

\## 1. 路径匹配

\*\*适用路径\*\*：

\- `src/frontend/\*\*/\*`  # 前端主目录

\- `\*\*/\*.vue`           # Vue组件

\- `\*\*/\*.jsx`           # React组件

\- `\*\*/\*.tsx`           # TypeScript组件



\## 2. 模型绑定

\*\*强制模型\*\*：`Gemini 3 Pro (High)`



\## 3. 约束条件

\- \*\*组件规范\*\*：

&nbsp; - 必须使用`<script setup lang="ts">`语法（Vue3）

&nbsp; - 状态管理用`Pinia`替代`Vuex`

\- \*\*UI规范\*\*：

&nbsp; - 按钮点击必须添加防抖（`debounce`）

&nbsp; - 表单验证用`async-validator`（Element Plus内置）

\- \*\*代码生成\*\*：

&nbsp; - 生成ECharts配置时，必须包含`tooltip`和`legend`配置项

&nbsp; - 二维码生成组件需支持`background`和`foreground`颜色配置



\## 4. 输出要求

\- 代码变更需生成`diff`视图

\- 任务完成后在docs/report目录下生成`frontend-report.md`，包含：

&nbsp; - 组件依赖关系图

&nbsp; - 样式覆盖率统计

