# GZEAMS 项目进展分析与下一步开发计划 PRD

## 1. 文档信息
- 文档版本: `v1.0`
- 日期: `2026-02-27`
- 适用范围: `GZEAMS 全栈（Django 后端 + Vue3 前端）`

---

## 2. 项目进展总览

### 2.1 整体架构完成度

| 层面 | 完成度 | 说明 |
|------|--------|------|
| **后端模型层** | ★★★★★ 95% | 20 个 Django App，模型定义完整，包含完善的字段、索引、约束 |
| **后端 API 层** | ★★★★☆ 80% | 19 个 `urls.py`，REST API 端点覆盖所有模块 |
| **后端 Service 层** | ★★★★☆ 75% | 12 个 service 有测试文件，核心业务逻辑已实现 |
| **前端基础架构** | ★★★★★ 90% | 元数据驱动动态路由、动态表单/列表/详情页完整 |
| **前端业务页面** | ★★★☆☆ 55% | 核心资产/耗材/盘点已有页面，大量后端模块无专属前端 |
| **前端组件库** | ★★★★☆ 80% | 87 个组件，designer/engine/workflow 等体系完善 |
| **测试覆盖** | ★★★☆☆ 50% | 后端有 pytest 覆盖，前端有 vitest + e2e，但覆盖面有限 |
| **CI/CD** | ★★★★☆ 75% | GitHub Actions 流水线已搭建，lint + test 自动执行 |

### 2.2 后端模块实现状态（20 个 Django App）

| 模块 | App 名称 | 模型行数 | 有 Service 测试 | 有 URL 路由 | 状态 |
|------|----------|----------|----------------|-------------|------|
| 认证账户 | `accounts` | ✅ | ✅ | ✅ | ✅ 完整 |
| 固定资产 | `assets` | ✅ | ✅ | ✅ | ✅ 完整 |
| 公共基类 | `common` | ✅ | ✅ | — | ✅ 完整 |
| 低值易耗 | `consumables` | ✅ | ✅ | ✅ | ✅ 完整 |
| 折旧计算 | `depreciation` | ✅ | — | ✅ | ⚠️ 缺服务测试 |
| 财务集成 | `finance` | ✅ | — | ✅ | ⚠️ 缺服务测试 |
| 保险管理 | `insurance` | 742 行 | — | ✅ | ⚠️ 缺服务测试 |
| 集成框架 | `integration` | ✅ | ✅ | ✅ | ✅ 完整 |
| 盘点管理 | `inventory` | ✅ | ✅ | ✅ | ✅ 完整 |
| IT 资产 | `it_assets` | ✅ | — | ✅ | ⚠️ 缺服务测试 |
| 租赁管理 | `leasing` | 642 行 | — | ✅ | ⚠️ 缺服务测试 |
| 生命周期 | `lifecycle` | 1179 行 | ✅ | ✅ | ✅ 完整 |
| 移动端 | `mobile` | 541 行 | ✅ | ✅ | ✅ 完整 |
| 通知系统 | `notifications` | 1254 行 | ✅ | ✅ | ✅ 完整 |
| 组织架构 | `organizations` | ✅ | — | ✅ | ⚠️ 缺服务测试 |
| 权限管理 | `permissions` | ✅ | — | ✅ | ⚠️ 缺服务测试 |
| 软件许可 | `software_licenses` | ✅ | — | ✅ | ⚠️ 缺服务测试 |
| 单点登录 | `sso` | 418 行 | ✅ | ✅ | ✅ 完整 |
| 系统管理 | `system` | ✅ | ✅ | ✅ | ✅ 完整 |
| 工作流 | `workflows` | ✅ | — | ✅ | ⚠️ 缺服务测试 |

### 2.3 前端模块实现状态

| 业务模块 | 有专属 Views | 有 API 模块 | 路由方式 | 状态 |
|----------|-------------|-------------|---------|------|
| 登录认证 | ✅ Login | ✅ `auth.ts` | 专属路由 | ✅ 完整 |
| 仪表盘 | ✅ Dashboard | — | 专属路由 | ✅ 完整 |
| 固定资产 | ✅ 4 页面 + operations(8) + settings(5) | ✅ `assets.ts` | 动态路由重定向 | ✅ 完整 |
| 低值易耗 | ✅ 3 页面 | ✅ `consumables.ts` | 动态路由重定向 | ✅ 完整 |
| 盘点管理 | ✅ 2 页面 (TaskList + TaskExecute) | ✅ `inventory.ts` | 混合路由 | ✅ 完整 |
| 财务集成 | ✅ 3 页面 (Voucher + Depreciation) | ✅ `finance.ts` | 专属路由 | ✅ 完整 |
| IT 资产 | ✅ 3 页面 + 3 组件 | ✅ `itAssets.ts` | 专属路由 | ✅ 完整 |
| 软件许可 | ✅ 5 页面 | ✅ `softwareLicenses.ts` | 专属路由 | ✅ 完整 |
| 工作流 | ✅ 3 页面 + admin 3 页面 | ✅ `workflow.ts` | 专属路由 | ✅ 完整 |
| 系统管理 | ✅ 13 页面 + 8 组件 | ✅ `system/` 11 文件 | 专属路由 | ✅ 完整 |
| 集成框架 | ✅ 1 页面 | ✅ `integration.ts` | 专属路由 | ⚠️ 基础 |
| 移动端 | ⚠️ 2 子目录（各1文件） | ✅ `mobile.ts` | — | ⚠️ 基础 |
| **通知系统** | ❌ 空目录 | ✅ `notifications.ts` | — | ❌ 未实现 |
| **保险管理** | ❌ 无 | ✅ `insurance.ts` | — | ❌ 未实现 |
| **租赁管理** | ❌ 无 | ✅ `leasing.ts` | — | ❌ 未实现 |
| **生命周期** | ❌ 无（采购/入库/维护/处置） | ✅ `lifecycle.ts` | — | ❌ 未实现 |
| **SSO 管理** | ❌ 无 | ✅ `sso.ts` | — | ❌ 未实现 |
| 权限管理 | ⚠️ 1 页面 (PermissionManagement) | ✅ `permissions.ts` | 专属路由 | ⚠️ 基础 |
| 组织架构 | ⚠️ 通过系统管理 DepartmentList | ✅ `organizations.ts` | 动态路由 | ⚠️ 基础 |

### 2.4 前端动态渲染引擎状态

前端已建立完善的**元数据驱动动态路由系统**：

- **统一路由**: `/objects/:code` 模式覆盖所有业务对象 (Asset, AssetPickup, AssetTransfer, AssetReturn, AssetLoan, AssetCategory, Supplier, Location, Consumable, ConsumableCategory, ConsumableStock, InventoryTask, Department, BusinessObject, FieldDefinition, PageLayout)
- **三大动态页面**: `DynamicListPage`, `DynamicFormPage`, `DynamicDetailPage`
- **布局引擎**: 44 个 engine 组件 + 13 个 designer 组件
- **字段类型**: 支持 15+ 字段类型渲染
- **正在重构**: 元数据渲染引擎统一契约 (M1 已完成, M2 进行中)

---

## 3. 前后端差异分析

### 3.1 关键差距总结

```
后端完成度 ████████████████████░ 95%
前端完成度 ███████████░░░░░░░░░░ 55%
                                    ▲ 差距 ~40%
```

### 3.2 按业务域分析差距

#### ❌ 完全缺失的前端模块

| 模块 | 后端模型 | 后端能力 | 前端缺失内容 |
|------|---------|---------|------------|
| **通知系统** | NotificationTemplate, Notification, NotificationLog, NotificationConfig | 模板渲染、多渠道推送、免打扰、重试 | 通知中心页面、偏好设置、模板管理、通知列表 |
| **保险管理** | InsuranceCompany, InsurancePolicy, InsuredAsset, PremiumPayment, InsuranceClaim, RenewalRecord | 保单管理、理赔、续保、保费追踪 | 保险公司管理、保单列表/详情、理赔流程、保费日历 |
| **租赁管理** | LeaseContract, LeaseItem, RentPayment, LeaseReturn, LeaseExtension | 合同管理、资产出租、租金管理、退租 | 合同列表/详情、租金日历、退租表单、续租流程 |
| **生命周期** | PurchaseRequest, PurchaseRequestItem, AssetReceipt, Maintenance, DisposalRequest, DisposalItem, AssetWarranty | 采购申请、到货验收、维修维护、报废处置、保修管理 | 采购申请列表/表单、验收页面、维修工单、报废流程、保修查询 |
| **SSO 管理** | WeWorkConfig, UserMapping, OAuthState, SyncLog | 企微配置、用户映射、同步日志 | SSO 配置页面、同步日志查看、用户映射管理 |

#### ⚠️ 仅有基础实现的前端模块

| 模块 | 现状 | 缺失内容 |
|------|------|---------|
| **权限管理** | 仅 1 个 PermissionManagement 页面 | 角色管理、字段级权限、行级数据权限、权限继承配置 |
| **集成框架** | 仅 1 个 IntegrationConfigList 页面 | 适配器管理、字段映射配置、同步日志、数据推送监控 |
| **移动端** | 仅扫码和资产 2 个子页面 | 设备管理、离线数据管理、同步冲突处理、移动审批 |
| **组织架构** | 仅通过 DepartmentList 和动态路由 | 组织树管理、多部门用户、部门主管配置、行政区划 |

---

## 4. 下一步开发计划

### 4.1 优先级原则

1. **业务价值优先**: 优先完成对日常业务操作影响最大的模块
2. **前端追赶后端**: 集中力量补齐前端空白，充分利用已有后端 API
3. **动态引擎优先**: 尽量通过元数据动态路由覆盖，减少硬编码页面
4. **渐进式交付**: 每个迭代交付可用功能，而非一次性完成

### 4.2 分阶段开发计划

---

#### 🔴 Sprint 1: 资产生命周期前端（高优先级 · 2 周）

**业务价值**: 采购→入库→维护→处置 是资产管理的核心链路，目前后端完整但无前端页面。

| 任务 | 页面 | 路由方式 | 依赖 |
|------|------|---------|------|
| 采购申请管理 | PurchaseRequestList + PurchaseRequestForm | 动态路由 `/objects/PurchaseRequest` | 业务对象注册 |
| 到货验收 | AssetReceiptList + AssetReceiptForm | 动态路由 `/objects/AssetReceipt` | 采购单关联 |
| 维修维护 | MaintenanceList + MaintenanceForm | 动态路由 `/objects/Maintenance` | — |
| 报废处置 | DisposalRequestList + DisposalRequestForm | 动态路由 `/objects/DisposalRequest` | 审批工作流 |
| 保修管理 | AssetWarrantyList + AssetWarrantyForm | 动态路由 `/objects/AssetWarranty` | — |

**技术要点**:
- 在 `BusinessObject` 中注册 PurchaseRequest/AssetReceipt/Maintenance/DisposalRequest/AssetWarranty
- 利用现有 `DynamicListPage` + `DynamicFormPage` + `DynamicDetailPage` 动态渲染
- 采购→验收→入库流程需要**跨对象操作按钮**（在详情页添加操作入口）
- 报废处置需关联工作流审批

**验收标准**:
- 采购申请可创建、编辑、提交审批
- 到货验收可关联采购单，执行质量检验
- 维修工单可创建并跟踪状态
- 报废可提交审批并自动更新资产状态

---

#### 🔴 Sprint 2: 通知中心前端（高优先级 · 1.5 周）

**业务价值**: 通知是所有业务流程的支撑基础，审批提醒、到期提醒、预警通知均依赖此模块。

| 任务 | 页面/组件 | 说明 |
|------|----------|------|
| 通知中心页面 | `views/notifications/NotificationCenter.vue` | 用户站内通知列表，支持已读/未读、批量操作 |
| 通知铃铛组件 | `components/common/NotificationBell.vue` | 顶部导航栏通知图标 + 未读数 + 下拉预览 |
| 通知偏好设置 | `views/notifications/NotificationSettings.vue` | 用户按类型/渠道配置通知开关、免打扰时段 |
| 通知模板管理 | `views/admin/NotificationTemplateList.vue` | 管理员管理通知模板（系统管理入口） |

**技术要点**:
- 利用 WebSocket 或轮询实现实时通知推送
- 通知铃铛组件集成到 `MainLayout.vue` 顶部导航
- 通知列表支持按类型/优先级/时间筛选
- 考虑未来对接企业微信消息推送

**验收标准**:
- 导航栏显示未读通知数
- 通知中心可查看、标记已读、批量操作
- 用户可配置通知偏好

---

#### 🟡 Sprint 3: 保险与租赁管理前端（中优先级 · 2 周）

**业务价值**: 高价值资产的保险和租赁是财务合规的重要环节。

##### 保险管理

| 任务 | 页面 | 路由方式 |
|------|------|---------|
| 保险公司管理 | InsuranceCompanyList | 动态路由 |
| 保单管理 | InsurancePolicyList + InsurancePolicyDetail | 动态路由 + 专属详情 |
| 投保资产关联 | InsuredAssetList（保单详情内嵌） | 子表组件 |
| 保费日历 | PremiumPaymentCalendar | 专属页面 |
| 理赔管理 | InsuranceClaimList + InsuranceClaimForm | 动态路由 |

##### 租赁管理

| 任务 | 页面 | 路由方式 |
|------|------|---------|
| 租赁合同管理 | LeaseContractList + LeaseContractForm | 动态路由 |
| 合同详情 | LeaseContractDetail（含租赁项、付款、退租） | 专属详情页 |
| 租金管理 | RentPaymentList（到期提醒） | 动态路由 |
| 退租流程 | LeaseReturnForm（含状况评估） | 专属表单 |

**技术要点**:
- 保单详情页需要**子表嵌入**（投保资产列表、保费记录、理赔记录）
- 租赁合同详情页需要**多 Tab 布局**（合同信息、租赁项、付款计划、退租记录）
- 保费/租金到期提醒对接通知系统
- 保险理赔需关联工作流审批

---

#### 🟡 Sprint 4: 权限管理增强 + SSO 管理（中优先级 · 1.5 周）

**业务价值**: 企业级部署必备功能，多角色权限和企业微信登录是客户刚需。

| 任务 | 页面 | 说明 |
|------|------|------|
| 角色管理 | `RoleList.vue` + `RoleForm.vue` | CRUD + 权限分配 |
| 字段级权限 | `FieldPermissionConfig.vue` | 按角色配置字段可见/只读/可编辑 |
| 数据权限 | `DataPermissionConfig.vue` | 行级数据过滤规则配置 |
| SSO 配置 | `SSOConfigPage.vue` | 企业微信/钉钉/飞书 SSO 参数配置 |
| 同步日志 | `SyncLogList.vue` | 查看组织同步状态与错误 |
| 用户映射 | `UserMappingList.vue` | 管理系统用户与三方平台用户映射 |

---

#### 🟢 Sprint 5: 集成框架增强 + 移动端增强（低优先级 · 2 周）

##### 集成框架增强

| 任务 | 说明 |
|------|------|
| 适配器管理 | M18/SAP 适配器列表、连接测试 |
| 字段映射配置 | 可视化字段映射编辑器 |
| 同步日志监控 | 推送记录、错误重试、统计面板 |

##### 移动端增强

| 任务 | 说明 |
|------|------|
| 设备注册管理 | 管理员查看已绑定设备 |
| 离线数据面板 | 查看/处理离线上传数据 |
| 同步冲突处理 | 冲突列表 + 手动解决界面 |

---

#### 🟢 Sprint 6: 组织架构增强 + 用户门户（低优先级 · 2 周）

| 任务 | 说明 |
|------|------|
| 组织树管理 | 可视化组织架构树，支持拖拽调整层级 |
| 多部门用户 | 用户部门归属管理，支持兼任 |
| 用户门户 - 我的资产 | 普通用户查看名下资产 |
| 用户门户 - 我的申请 | 查看提交的各类申请及进度 |
| 用户门户 - 我的待办 | 待审批、待盘点、待处理事项汇总 |

---

### 4.3 并行进行的技术改进

| 领域 | 任务 | 优先级 |
|------|------|--------|
| **渲染引擎** | 完成 M2-M5 元数据渲染引擎重构（属性契约统一、25 字段类型、设计器一致性） | 高 |
| **后端测试** | 补充 depreciation/finance/insurance/it_assets/leasing/organizations/permissions/software_licenses/workflows 的 service 测试 | 中 |
| **前端测试** | 补充 E2E 测试覆盖核心用户路径（资产 CRUD → 领用 → 盘点 → 报废） | 中 |
| **i18n** | 完善中英文翻译覆盖 | 低 |
| **代码清理** | 清理根目录临时文件（test scripts, screenshots, metadata json dumps） | 低 |

---

## 5. 技术方案建议

### 5.1 新模块接入策略

对于 Sprint 1-3 新增的前端页面，建议优先使用**动态路由**方式接入：

```
1. 后端: 在 BusinessObject 表注册新对象 (如 PurchaseRequest)
2. 后端: 在 FieldDefinition 表注册字段定义
3. 后端: 创建默认 PageLayout
4. 前端: 通过 /objects/PurchaseRequest 自动生效
5. 前端: 仅在需要特殊交互时（子表嵌入、跨对象操作）创建定制页面
```

### 5.2 子表/明细表组件标准化

保险保单详情、租赁合同详情、采购申请明细等场景都需要**父子关联表**显示。建议：

- 创建通用 `SubTablePanel.vue` 组件
- 支持配置：关联对象 code、外键字段、列显示、行内编辑
- 复用 engine 层已有渲染逻辑

### 5.3 操作按钮/状态流转标准化

资产生命周期涉及大量**状态流转**操作（提交→审批→完成/退回）。建议：

- 创建通用 `StatusActionBar.vue` 组件
- 后端提供 `/api/{object}/available-actions/` 接口返回当前可用操作
- 前端据此动态渲染操作按钮

---

## 6. 里程碑时间线

```
2026-03 ─────── Sprint 1: 资产生命周期前端 ───────────────── 🔴
     W1-W2      采购申请/到货验收/维修维护/报废处置/保修管理

2026-03~04 ──── Sprint 2: 通知中心前端 ──────────────────── 🔴
     W3-W4      通知中心/铃铛组件/偏好设置/模板管理

2026-04 ─────── Sprint 3: 保险与租赁管理前端 ────────────── 🟡
     W5-W6      保险公司/保单/理赔 + 租赁合同/租金/退租

2026-04~05 ──── Sprint 4: 权限管理增强 + SSO 管理 ─────── 🟡
     W7-W8      角色/字段级权限/数据权限 + SSO/同步/映射

2026-05 ─────── Sprint 5: 集成框架 + 移动端增强 ──────────── 🟢
     W9-W10     适配器/字段映射/日志 + 设备/离线/同步

2026-05~06 ──── Sprint 6: 组织架构 + 用户门户 ───────────── 🟢
     W11-W12    组织树/多部门用户 + 我的资产/申请/待办
```

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 动态路由无法覆盖复杂业务交互 | 部分模块需要定制页面，增加工作量 | 优先评估，仅复杂场景(子表、跨对象操作)才定制 |
| 后端 API 格式不统一 | 前端对接成本高 | 统一使用 `BaseModelViewSetWithBatch` + 响应拦截器 |
| 通知系统需要 WebSocket | 技术栈扩展 | 可先用轮询方案快速上线，后续升级 WebSocket |
| 保险/租赁业务流程复杂 | 前端交互设计难度大 | 参考标杆产品 NIIMBOT 设计，分步表单简化操作 |
| 渲染引擎重构并行进行 | 新页面可能受影响 | Sprint 1-2 结束前完成 M2，新页面直接基于新契约 |

---

## 8. 验收标准总览

- [ ] Sprint 1: 采购→验收→维护→报废全链路可操作
- [ ] Sprint 2: 导航栏显示通知数，通知中心可用
- [ ] Sprint 3: 保单/合同可创建并查看详情（含子表）
- [ ] Sprint 4: 角色可分配权限，SSO 可配置并登录
- [ ] Sprint 5: 集成配置可测试连接，移动设备可管理
- [ ] Sprint 6: 用户门户三个入口可用
- [ ] 全部新页面支持中英文切换
- [ ] 核心路径有 E2E 测试覆盖
