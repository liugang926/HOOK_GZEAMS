# GZEAMS 前端架构与 UI 一致性进阶 PRD (UI架构师全局演进版)

## 1. 文档信息
- 文档版本: `v2.0`
- 日期: `2026-03-05`
- 适用范围: `GZEAMS 前端系统 (Vue3 + Element Plus + Pinia + i18n)`
- 核心目标: 在 v1 交互体验的基础上，以**高级 UI 系统架构师**的视角，补充企业级 SaaS 必须具备的**前端韧性 (Resilience)**、**状态与缓存管控 (State & Caching)**、**无障碍访问 (a11y)**、**多租户白标主题 (Theming)** 与 **深度配置纠错 (Undo/Redo)** 的硬核技术规范，形成一张真正无死角的终极前端演进蓝图。

---

## 2. 演进背景与终极目标 (The Ultimate Goal)
随着 GZEAMS 从企业内用系统向商业化大型 SaaS 迈进，仅拥有好用的交互是不够的。当实施人员配出一个包含 200 个字段、5 个独立 Tab 和巨量下拉字典的复合资产页面时，我们需要系统：
1. **绝不崩溃 (Never Crash)**：一个配置错误的子表组件不能拉垮整个页面的渲染。
2. **极小化网络冗余 (Zero-Redundant Network)**：频繁访问的大宗系统级元数据（字典、结构）必须实施纯前端拦截与缓存复用。
3. **兼容各种端态与使用习惯 (Adaptability)**：支持跨国分公司文化设定，支持键盘盲打高频录入业务，支持 SaaS 大客户贴牌 (Whitelabeling)。

本 PRD 是指导前端基建组与业务研发团队未来 6 个月的最高纲领。

---

## 3. 核心架构规划 (Core UI Architecture & Topology)

### 3.1 极速微交互与无障碍连贯性 (Micro-Interactions & A11y)
**架构价值**：让系统具有肌肉记忆，不仅好看，而且在企业高频操作区“极度顺手”。

- **悬浮名片与内联操作 (Hover Popover & Inline Edit)**：
  - 提炼 `FieldDisplay.vue` 全局引用卡片，鼠标指针到达资产归属人时弹射 Quick Actions。
  - 在资产盘点类密集表格区间开启双击微型状态输入框，阻断多开浏览器 Tab 页。
- **关联视图侧滑抽屉 (Drawer / Slider)**：
  - 所有新增/编辑次级单据（如新增维保申请）强制调用 `el-drawer`，绝对保留底部 Record 详情页上下文深度。
- **全键盘无障碍导航矩阵 (Keyboard A11y & Focus Management) 🛡️ [新增]**：
  - 针对高频表单录入与流水线式的资产核验节点，全面支持按键遍历 (`Tab` Index 对齐)。
  - 当弹出 Dialog 或 Drawer 时，系统必须执行严格的**焦点圈定 (Focus Trap)**。
  - 核心操作必须绑定快捷键闭环（如 `Cmd/Ctrl + S` 保存，`Esc` 关闭并复原侧栏，`Cmd/Ctrl + F` 唤出表格过滤锚点）。

### 3.2 渲染管线、性能压榨与状态缓存 (Render Pipeline & State)
**架构价值**：突破 DOM 规模瓶颈，用智巧的数据层调度避免暴力渲染。

- **骨架屏与布局零偏移 (Stencils & Local Zero CLS)**：
  - 废弃全局 Spinner，核心页面首屏请求未到达前，严格按照元数据的 2 列 / 3 列表单结构使用 `el-skeleton` 画出 1:1 的占位斑马纹，确保渲染过程中的累积布局偏移（CLS）等于 0。
- **虚拟渲染与深度惰性 (Virtual Scrolling & Deep Lazy)**：
  - `<el-tabs>` 下的从属列表、评论与文件附件强制启用懒加载；处理千行以上的表单配置画布实装虚拟滚动树。
- **前端 SWR (Stale-While-Revalidate) 静态数据缓存层 🛡️ [新增]**：
  - 全局重构对数据字典 (Dictionary Options)、企业组织架构树、对象 Schema 定义等静态低频变更数据的抓取调用。
  - 封装前端请求级缓存（基于 Pinia + Cache Wrapper）：当页面组件高频销毁-重建时不再重新 Fetch，除非收到 WebSocket 脏数据失效信号，或定时自动静默刷新 (Background Revalidate)。彻底削平并发毛刺。

### 3.3 全局多态组件、一致性与韧性 (Polymorphism & Resilience)
**架构价值**：将 100 种业务页面抽象为 1 种元数据引擎渲染页面，并且保证引擎自身坚不可摧。

- **顶级渲染门面 (The `DynamicField` Facade)**：
  - 无论是哪类单据，属性读写必须调用顶层 `<DynamicField>` 抽象组件。
- **三大标准蓝图强制化 (Strict Page Archetypes)**：
  - **Record Detail** (含 Highlight Panel + 双栏 Tabs 与 Timeline) / **List View** (快动作树状受控宽表) / **Setup Designer** (三段式物料大画布)。
- **微组件错误边界 (Granular Error Boundaries) 🛡️ [新增]**：
  - 当某一个自研业务组件（例如一个高图表数据组件，或解析异常的二维码）在渲染树中抛出 JS 异常时，使用 Vue3 全局 `onErrorCaptured` 并封装 `<ErrorBoundary>`。
  - 异常必须被拦截在该板块内部，呈现一个带有 "Component Failed to Load / 组件解析失败" 的红色小外壳，**绝对禁止**拖垮乃至白屏掉整个父级 Vue 应用实例。

### 3.4 SaaS 白标主题与国际化上下文 (Theming & Globalization) 🌐
**架构价值**：满足大型买单企业 (B端客户) 的集团视觉占有欲以及跨国管理水准。

- **动态多租户白标架构 (Multi-Tenant Whitelabeling Theme) 🛡️ [新增]**：
  - 全面实行 CSS Design Tokens 架构。将 Element Plus / 系统定制变量按三级划分 (基础变量 `blue-500` -> 组件变量 `button-bg` -> 语义变量 `header-active`)。
  - 设计 Theme Injector：允许系统管理员在后端配置公司的主题品牌色 (`#FF6B00`)、圆角系数（`0px - 8px`）。前端基于一套 HSL 算法或 Chroma.js 运行时计算并注入 `:root`，所有 `<DynamicField>` 与全局 UI 样式瞬间应用并过渡为客户端专属色。支持动态暗黑模式反演 (Dark Mode Runtime Calculation)。
- **沉浸式翻译配置台 (Translation Workbench)**：
  - LayoutDesigner (布局设计器) 顶部嵌入“翻译模式”。边画画布边翻译 Label 的 `i18n_key` 值。
- **地区上下文感知引擎 (Locale Context Awareness) 🛡️ [新增]**：
  - i18n 引擎下沉至数据格式器内（Formatters）。
  - 时区、货币符、数字千分位不再跟随系统单一配置，而是读取登录用户的 Profile Preference Context。同样的 `1000.50`，在欧洲区账户渲染为 `1.000,50`，美国户渲染为 `$1,000.50`，跨区协同实现真正“本地化”。

### 3.5 布局设计器的大杀器进化 (Layout Designer Ergo & State) 🛠️
**架构价值**：让实施人员感受到构建巨型复杂表单不仅安全，而且具备心智上的游戏般愉悦体验。

- **绝对同构引擎 (100% WYSIWYG)**：
  - 画布直接代理运行态 Dynamic 真实组件树。
- **拖拽微动效与保护域 (Drop Ergonomics)**：
  - 新字段拖入时的位置排挤拉伸过渡动画 + 不允许塞入区域的红色高亮弹回拒绝态（Snap-back）。多端自适应实时预览切换仪。
- **不可变状态快照与撤销栈 (Immutable State Snapshots & Undo/Redo) 🛡️ [新增]**：
  - 在设计器内引入历史动作栈 (Action History Stack)，通过 Lodash CloneDeep 或类 Immutable.js 机制。
  - 提供丝滑且无穷（建议最高 50 步）的 `Ctrl + Z` 撤回功能。
  - **防崩溃云端/本地草稿箱自动封存**：即时监听页面变更，序列化脏状态写入 IndexedDB / LocalStorage。一旦断电关机，实施人员重开系统时，自动跳出：“发现一份未保存的资产报修配置布局草稿，是否恢复？”的挽救弹窗。

---

## 4. UI 架构治理准则 (Architecture Governance)

1. **骨架屏绝对法典 (Strict Skeleton Law)**：如果页面加载必须阻断用户超过 300ms，必须呈现 1:1 边界的骨架块模型。凡滥用 Spinner 贴全屏蒙层者代码审查不予通过。
2. **多态组件逃逸一票否决 (Zero-Tolerance Ad-hoc)**：但凡数据对象的呈现录入绕过底层抽象驱动层，去页面自己实例硬写 `el-input` 并绑定 `v-model:form.xxx`，视为背离元数据驱动架构，此 PR 免谈。
3. **顶层异常黏性指引 (Sticky Top-Level Validation)**：复杂子表和跨 Tab 表单的必填项出错，不允许只在视野外的输入框下方飘红。系统必须在页面天顶强制挂载 Sticky Banner 汇总出错矩阵锚点。

---

## 5. 里程碑与排期建议 (Rollovers)

| 阶段 | 核心任务矩阵 | 预估研发难度 |
|---|---|---|
| **Phase 1: 底座涅槃** | - `<DynamicField>` 大一统门面收敛<br>- 多语言 Translation Workbench 联调<br>- Design Token 全局覆盖与 SaaS 主题算法引擎打桩 | 🟡 中偏高 (核心代码换血) |
| **Phase 2: 极致柔性验证** | - `<ErrorBoundary>` 组件崩阻断注入<br>- V-List 虚拟滚动实装<br>- 前端 Pinia 骨架级数据缓存 SWR 防抖防瀑布机制 | 🟡 中 (考验内存泄露控制) |
| **Phase 3: 上帝视角搭建** | - Layout Designer 交互升阶（排挤、拒绝弹回态）<br>- Undo/Redo 时间机器引入与 IndexedDB 本地自动保存 | 🔴 极高 (复杂交互与栈控制算法) |
| **Phase 4: 暗光与无障碍** | - 键盘无障碍焦点隔离 (a11y Trapping)<br>- User Profile 级别的 Context 格式器适配 | � 低 (纯调优收尾) |

---

## 6. 核心架构验收 SLA
1. **统一性 SLA**：代码库全扫描，`el-input`, `el-select` 等原始组件 100% 被包裹至受控系统门面之内。
2. **韧性 SLA**：强制在运行时给某随机资产列表的数据块植入崩溃 JS (`throw new Error()`)，该页面的顶部导览、侧边栏不挂，仅对应子区块显式抛红。
3. **配置性 SLA**：管理员执行连续 30 次的高频拖拽动作拆烂布局后按住 `Ctrl+Z` 30 秒内丝滑完美还原最初面貌，内存曲线无暴涨。

***
*系统架构修订于 2026-03-05*
