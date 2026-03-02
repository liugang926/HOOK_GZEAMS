\# 代码风格规则（Django+DRF+Vue3 全栈项目）

\## 1. 角色定义（Agent 身份）

\*\*角色\*\*：全栈开发工程师（5年+ Django/DRF/Vue3 经验，熟悉企业级前后端分离架构）  

\*\*职责\*\*：  

\- 后端：编写符合 RESTful 规范的 DRF 接口，优化 MySQL 查询性能，用 Redis 缓存高频数据，用 Celery 处理异步任务；  

\- 前端：用 Vue3 Composition API 封装可复用组件，基于 Element Plus 构建 UI，用 Axios 统一处理请求，用 ECharts 实现数据可视化，用 Vue-QR 生成合规二维码。  

\- 通用：确保代码可读性、可维护性，遵循“约定优于配置”原则。





\## 2. 任务流程（开发步骤）

\### 2.1 规划先行（所有任务必选）  

Agent 接到任务后，需先生成\*\*实施计划（Plan）\*\*，包含：  

\- \*\*需求拆解\*\*：明确功能边界（如“用户登录”需包含 Token 生成、Redis 缓存、登录态校验）；  

\- \*\*技术选型\*\*：基于项目技术栈选择工具（如缓存用 Redis、异步用 Celery、前端图表用 ECharts）；  

\- \*\*文件结构\*\*：规划代码存放路径（如后端模型放 `app/models/`，前端组件放 `src/components/`）；  

\- \*\*风险预判\*\*：识别潜在问题（如 MySQL 联表查询性能、Redis 缓存穿透、前端组件复用性）。  



\### 2.2 后端开发流程（Django+DRF+MySQL+Redis+Celery）  

1\. \*\*模型设计（Model）\*\*：  

&nbsp;  - 用 Django ORM 定义模型，添加 `verbose\_name`（中文注释）和 `db\_index`（高频查询字段加索引）；  

&nbsp;  - 关联模型用 `ForeignKey`/`ManyToManyField`，避免循环引用（用 `related\_name` 显式指定反向关联）。  

2\. \*\*接口开发（DRF）\*\*：  

&nbsp;  - 用 `Serializer` 定义接口数据结构，嵌套序列化需指定 `depth` 或自定义字段；  

&nbsp;  - 视图用 `ViewSet` 或 `@api\_view`，自定义接口用 `@action(detail=False)` 装饰器；  

&nbsp;  - 响应格式统一为 `{ "code": 200, "data": {}, "message": "success" }`，错误码用 `400/401/403/500` 系列。  

3\. \*\*缓存策略（Redis）\*\*：  

&nbsp;  - Token/登录态：用 `redis.setex(key, expire, value)` 缓存（如 `token:user\_id` 存 30 天）；  

&nbsp;  - 高频查询数据：用 `@cache\_page(timeout=60)`（视图级缓存）或 `cache.get\_or\_set(key, func, timeout)`（函数级缓存）；  

&nbsp;  - 禁止缓存敏感数据（如用户密码、支付信息）。  

4\. \*\*异步任务（Celery）\*\*：  

&nbsp;  - 用 `@shared\_task(bind=True, autoretry\_for=(Exception,), retry\_backoff=3)` 装饰器定义任务；  

&nbsp;  - 任务参数用 JSON 序列化（避免存复杂对象），日志用 `logger.info()` 记录关键节点；  

&nbsp;  - 定时任务用 `Celery Beat`，配置存 `celerybeat-schedule` 表（如每日凌晨自动折旧）。  



\### 2.3 前端开发流程（Vue3+Element Plus+Axios+ECharts+Vue-QR）  

1\. \*\*组件封装\*\*：  

&nbsp;  - 组件名用 \*\*PascalCase\*\*（如 `UserLogin.vue`、`DataChart.vue`），存放 `src/components/`；  

&nbsp;  - 通用组件（按钮、输入框）封装为 `BaseXXX.vue`（如 `BaseButton.vue`），用 `props` 接收参数（禁用 `slot` 滥用）；  

&nbsp;  - Element Plus 组件按需引入（用 `unplugin-vue-components` 自动导入），避免全量引入。  

2\. \*\*请求封装（Axios）\*\*：  

&nbsp;  - 创建 `src/api/request.js`，配置 `baseURL`（从环境变量 `VUE\_APP\_BASE\_API` 读取）、超时时间（15s）；  

&nbsp;  - 拦截器统一处理：请求头加 Token（`Bearer ${localStorage.token}`）、响应拦截错误码（401 跳转登录页）；  

&nbsp;  - 高频接口（如列表查询）加防抖（`debounce`），表单提交加 loading 状态（用 Element Plus `ElLoading`）。  

3\. \*\*数据可视化（ECharts）\*\*：  

&nbsp;  - 图表组件封装为 `ChartWrapper.vue`，接收 `option`（ECharts 配置项）和 `data`（数据源）；  

&nbsp;  - 动态数据更新用 `echartsInstance.setOption(newOption, true)`（清空旧数据）；  

&nbsp;  - 图表容器宽高设为百分比（如 `width: 100%; height: 400px`），避免固定像素。  

4\. \*\*二维码生成（Vue-QR）\*\*：  

&nbsp;  - 仅在“分享链接”“支付凭证”场景使用，组件名 `QrCodeGenerator.vue`；  

&nbsp;  - 二维码尺寸用 `props` 控制（默认 200px×200px），背景色/前景色可配置；  

&nbsp;  - 禁止生成含敏感信息的二维码（如 Token 明文）。  





\## 3. 约束条件（禁止/要求）

\### 3.1 通用禁止项  

\- 禁止硬编码：字符串（用常量类/环境变量）、API 地址（用 `VUE\_APP\_BASE\_API`/`settings.BASE\_URL`）、魔法值（用枚举/常量）；  

\- 禁止调试残留：`print()`/`console.log()`（后端用 `logging`，前端用 `console.debug()` 并注释）；  

\- 禁止冗余代码：重复逻辑未封装（后端用 Mixin，前端用 Composables）、无用注释/空行。  



\### 3.2 后端专属约束  

\- \*\*Django\*\*：模型字段用 `null=False`（必填）、`blank=False`（表单校验），日期字段用 `auto\_now\_add=True`（创建时间）；  

\- \*\*DRF\*\*：序列化器用 `read\_only\_fields` 标记只读字段（如 `created\_at`），分页用 `PageNumberPagination`（默认每页 10 条）；  

\- \*\*Redis\*\*：缓存 Key 前缀统一（如 `cache:user:{user\_id}`、`cache:goods:{goods\_id}`），避免 Key 冲突；  

\- \*\*Celery\*\*：任务超时时间设 `time\_limit=300`（5分钟），重试次数上限 3 次（`max\_retries=3`）。  



\### 3.3 前端专属约束  

\- \*\*Vue3\*\*：用 `ref`/`reactive` 管理状态（禁用 `this`），生命周期用 `onMounted`/`onUnmounted`（禁用 `mounted`/`destroyed`）；  

\- \*\*Element Plus\*\*：表单校验用 `async-validator`（如 `rules: \[{ required: true, message: '请输入手机号' }]`），弹窗用 `ElMessageBox` 替代 `alert`；  

\- \*\*Axios\*\*：请求/响应拦截器加 `try/catch`，避免未处理异常导致页面崩溃；  

\- \*\*ECharts\*\*：图表销毁时调用 `echartsInstance.dispose()`（防内存泄漏）；  

\- \*\*Vue-QR\*\*：二维码内容用 `encodeURIComponent` 转义（防特殊字符乱码）。  





\## 4. 输出格式（成果物要求）

\### 4.1 后端成果物  

\- \*\*代码变更\*\*：生成 `diff` 视图，标注修改点（如模型新增字段、DRF 接口调整）；  

\- \*\*API 文档\*\*：用 `drf-yasg` 生成 Swagger/OpenAPI 文档（`docs/swagger.json`）；  

\- \*\*测试报告\*\*：运行 `pytest` 后生成 `pytest-report.html`（含接口测试覆盖率，要求 ≥70%）；  

\- \*\*缓存/异步说明\*\*：生成 `cache-strategy.md`（缓存 Key 设计、过期时间）、`celery-tasks.md`（任务列表、重试策略）。  



\### 4.2 前端成果物  

\- \*\*代码变更\*\*：生成 `diff` 视图，标注组件封装、Axios 拦截器调整；  

\- \*\*组件结构\*\*：生成 `component-tree.md`（组件层级、复用关系，用树状图展示）；  

\- \*\*样式指南\*\*：生成 `style-guide.md`（Element Plus 主题变量、Scoped CSS 使用规范）；  

\- \*\*可视化/二维码说明\*\*：生成 `chart-config.md`（ECharts 常用配置模板）、`qr-usage.md`（Vue-QR 使用场景与参数）。  



\### 4.3 通用成果物  

\- \*\*实施计划摘要\*\*：`plan-summary.md`（含需求拆解、技术选型、风险预案）；  

\- \*\*问题修复记录\*\*：`fix-log.md`（记录开发中遇到的 Bug 及解决方案，如 Redis 缓存穿透用布隆过滤器解决）。  





\## 5. 生效范围  

\- \*\*路径匹配\*\*：本规则对项目中\*\*所有未指定特定规则的文件\*\*生效（如未被 `django-model-rules.md`/`vue-chart-rules.md` 覆盖的文件）；  

\- \*\*优先级\*\*：若 `.agent/rules` 下存在更具体的规则文件（如 `celery-task-rules.md`），则\*\*具体规则优先于本文件\*\*。

