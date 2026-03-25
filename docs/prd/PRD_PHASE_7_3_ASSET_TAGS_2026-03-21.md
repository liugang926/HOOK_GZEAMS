# GZEAMS Phase 7.3: 资产标签系统 PRD

## 文档信息

| 项目 | 说明 |
|------|------|
| PRD 版本 | v3.0 |
| 创建日期 | 2026-03-21 |
| 基于分析 | Codex 架构师深度分析报告 (2026-03-21) |
| 目标阶段 | Phase 7.3 |
| 优先级 | P1 |

---

## 1. 项目现状总结

### 1.1 基于代码分析的完成度

通过 Codex CLI 深度扫描，GZEAMS 项目已从"纯低代码引擎"演进为"**混合动态架构**"：

| 层级 | 完成度 | 关键指标 |
|------|--------|----------|
| **公共模型抽象** | **85%** | BaseModel 继承率 97.7%，Service 层覆盖率 58.7% |
| **动态对象引擎** | **90%** | ObjectRouterViewSet + runtime 完整闭环 |
| **前端动态页面** | **78%** | DynamicListPage、BaseFormPage、DocumentWorkbench 可用 |
| **整体完成度** | **82%** | 相对上次评估提升 4 个百分点 |

### 1.2 核心架构事实

**后端架构**：
- 统一入口：`ObjectRouterViewSet` 通过 `/api/objects/{code}/` 动态路由
- 元数据驱动：`BusinessObject`、`FieldDefinition`、`PageLayout` 支持完全元数据化
- 混合模式：67 个硬编码对象通过 `object_catalog` 映射，动态对象支持 24 种字段类型
- 公共抽象：`BaseModel` 多租户隔离、`BaseCRUDService` 批量操作、`BaseModelViewSetWithBatch` 统一响应

**前端架构**：
- 统一页面：`DynamicListPage`、`DynamicFormPage`、`DynamicDetailPage`
- 工作区组件：`BaseFormPage` 表单骨架、`DocumentWorkbench` 面板集成
- 字段引擎：24 种字段类型完全支持，具备 capability matrix
- API 层：44.7% 接口使用统一对象路由，55.3% 保留专用 API

### 1.3 代码 vs 原计划偏差

**重要架构决策变化**：
- 原计划：纯元数据驱动，所有对象走 `MetadataDrivenViewSet`
- 实际实现：`ObjectRouterViewSet` 统一入口 + 运行时元数据组装
- 原计划：独立 `/api/tags/` 路由
- 实际实现：复用现有统一对象路由架构

**已有资产标签基础**：
- ✅ 系统已存在通用 `Tag` 模型（继承 `BaseModel`，包含 name、color、description 字段）
- ⚠️ 但缺少对应的 Serializer、ViewSet、ObjectRegistry 映射
- ⚠️ 前端无标签展示和管理页面

---

## 2. 功能需求

### 2.1 P0 - 核心功能（必须实现）

#### 2.1.1 标签组管理

| 功能 | 说明 | 技术实现 |
|------|------|----------|
| 创建标签组 | 定义标签组名称、编码、颜色、图标、排序 | 新建 `TagGroup` 模型，继承 `BaseModel`，使用 `GlobalMetadataManager` |
| 标签组排序 | 支持拖拽排序 | `sort_order` 字段 + 前端排序 API |
| 系统标签组 | 预置"状态"、"部门"、"风险"等系统标签组 | `is_system` 布尔字段，自动初始化预置数据 |

**数据模型**：
```python
class TagGroup(BaseModel):
    # 使用 GlobalMetadataManager - 标签组定义为系统级共享数据
    objects = GlobalMetadataManager()
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default='#409eff')
    icon = models.CharField(max_length=50, blank=True)
    sort_order = models.IntegerField(default=0)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
```

#### 2.1.2 标签管理

| 功能 | 说明 | 技术实现 |
|------|------|----------|
| 创建标签 | 属于某个标签组，定义名称、颜色、描述 | 新建 `AssetTag` 模型，继承 `BaseModel` |
| 标签排序 | 在组内排序 | `sort_order` 字段 |
| 标签激活/停用 | 支持停用不常用的标签 | `is_active` 字段，过滤停用标签 |

**数据模型**：
```python
class AssetTag(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    group = models.ForeignKey(TagGroup, on_delete=models.CASCADE)
    color = models.CharField(max_length=20, default='#409eff')
    icon = models.CharField(max_length=50, blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['group', 'code']
```

#### 2.1.3 资产标签关联

| 功能 | 说明 | 技术实现 |
|------|------|----------|
| 打标签 | 为资产添加一个或多个标签 | 新建 `AssetTagRelation` 模型，继承 `BaseModel` |
| 移除标签 | 从资产移除标签 | 软删除 `AssetTagRelation` 记录 |
| 批量打标签 | 批量为选中资产添加标签 | 继承 `BaseModelViewSetWithBatch` 的批量操作 |
| 标签展示 | 在资产列表和详情页显示标签 | 动态页面集成标签组件 |

**数据模型**：
```python
class AssetTagRelation(BaseModel):
    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE)
    tag = models.ForeignKey(AssetTag, on_delete=models.CASCADE)
    tagged_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL)
    tagged_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['asset', 'tag']
```

#### 2.1.4 对象路由集成

| 功能 | 说明 | 技术实现 |
|------|------|----------|
| 统一 API 入口 | 通过 `/api/objects/AssetTag/` 访问标签功能 | 在 `object_catalog.py` 注册 `AssetTag` 对象 |
| 动态页面支持 | 使用 `DynamicListPage` 和 `DynamicDetailPage` | 配置 `BusinessObject` 和 `PageLayout` |
| 标签字段支持 | 在资产对象添加标签类型字段 | 扩展 `FieldDefinition` 支持标签字段 |

### 2.2 P1 - 增强功能

#### 2.2.1 标签筛选器

| 功能 | 说明 | 技术实现 |
|------|------|----------|
| 单标签筛选 | 点击标签快速筛选资产 | 继承 `BaseModelFilter`，按标签过滤 |
| 多标签组合 | 支持 AND/OR 组合筛选 | 前端组合查询，后端复杂过滤 |
| 标签组筛选 | 按标签组快速定位 | 按标签组 + 标签二级筛选 |
| 保存筛选 | 保存常用筛选条件 | 用户偏好设置 + 筛选条件持久化 |

#### 2.2.2 标签统计

| 功能 | 说明 | 技术实现 |
|------|------|----------|
| 标签计数 | 显示每个标签下的资产数量 | 聚合查询 + 前端图表展示 |
| 价值统计 | 按标签汇总资产原值和净值 | 关联资产数据 + 聚合计算 |
| 可视化图表 | 标签分布饼图、柱状图 | 使用 ECharts 或类似库 |

#### 2.2.3 标签选择器组件

| 功能 | 说明 | 技术实现 |
|------|------|----------|
| 下拉选择 | 支持搜索和快速选择 | 基于 `DynamicFormPage` 的字段组件 |
| 颜色预览 | 显示标签颜色 | 前端组件渲染颜色预览 |
| 分组展示 | 按标签组分类显示 | 树形结构 + 分层选择 |
| 最近使用 | 记录最近使用的标签 | 用户偏好设置 + 缓存机制 |

### 2.3 P2 - 自动化功能

#### 2.3.1 自动标签规则

| 功能 | 说明 | 技术实现 |
|------|------|----------|
| 条件规则 | 满足条件自动打标签 | 新建 `TagAutoRule` 模型，集成规则引擎 |
| 触发时机 | 创建/更新资产时触发 | 信号监听 + 后台任务 |
| 规则优先级 | 支持规则排序和冲突处理 | `priority` 字段 + 执行顺序控制 |

**数据模型**：
```python
class TagAutoRule(BaseModel):
    name = models.CharField(max_length=100)
    tag = models.ForeignKey(AssetTag, on_delete=models.CASCADE)
    conditions = models.JSONField()  # 条件表达式
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    # 规则执行日志
    executions = models.JSONField(default=list)
```

---

## 3. 技术实现方案

### 3.1 架构适配要求

基于当前 GZEAMS 混合动态架构，标签系统必须遵循以下规范：

| 要求 | 说明 |
|------|------|
| **统一对象路由** | 使用 `/api/objects/AssetTag/` 而非独立 `/api/tags/` |
| **BaseModel 继承** | 所有模型继承 `apps.common.models.BaseModel` |
| **多租户隔离** | 通过 `organization` 字段自动隔离（标签可能为系统级） |
| **动态对象注册** | 在 `object_catalog.py` 注册标签相关对象 |
| **元数据驱动** | 通过 `BusinessObject` 配置字段和布局 |
| **GlobalMetadataManager** | 标签组、标签定义为系统级共享数据 |

### 3.2 后端实现

```
backend/apps/
├── tags/                           # 新标签模块
│   ├── __init__.py
│   ├── models.py                  # TagGroup, AssetTag, AssetTagRelation, TagAutoRule
│   ├── serializers/
│   │   ├── __init__.py
│   │   ├── tag_group.py
│   │   ├── asset_tag.py
│   │   └── tag_relation.py
│   ├── viewsets/
│   │   ├── __init__.py
│   │   ├── tag_group.py
│   │   └── asset_tag.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tag_service.py         # 标签业务逻辑
│   │   └── auto_rule_service.py   # 自动规则执行
│   ├── filters/
│   │   └── tag_filter.py
│   └── migrations/
└── system/
    ├── object_catalog.py           # 注册 AssetTag 对象
    └── urls.py                    # 配置路由
```

### 3.3 前端实现

```
frontend/src/
├── views/tags/
│   ├── TagGroupList.vue          # 标签组列表
│   ├── TagList.vue               # 标签列表
│   └── TagStatistics.vue         # 标签统计
├── components/tags/
│   ├── TagSelector.vue           # 标签选择器
│   ├── TagFilter.vue             # 标签筛选器
│   ├── TagBadge.vue              # 标签徽章
│   ├── TagCard.vue               # 标签卡片
│   └── BatchTagDialog.vue        # 批量打标签对话框
├── api/tags/
│   ├── tagGroup.ts
│   └── assetTag.ts
└── composables/
    └── useAssetTags.ts           # 标签相关逻辑
```

### 3.4 API 设计

遵循 GZEAMS 统一对象 API 规范：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/objects/TagGroup/` | GET/POST | 标签组列表/创建 |
| `/api/objects/TagGroup/{id}/` | GET/PUT/DELETE | 标签组详情/更新/删除 |
| `/api/objects/AssetTag/` | GET/POST | 标签列表/创建 |
| `/api/objects/AssetTag/{id}/` | GET/PUT/DELETE | 标签详情/更新/删除 |
| `/api/objects/Asset/{id}/tags/` | GET/POST/DELETE | 资产标签关联 |
| `/api/objects/Asset/batch-tag/` | POST | 批量打标签 |

---

## 4. 验收标准

### 4.1 功能验收

| 功能 | 验收标准 | 通过条件 |
|------|----------|----------|
| **标签组管理** | ✅ 可创建、编辑、删除、排序标签组 | CRUD 操作正常，排序生效 |
| **标签管理** | ✅ 可创建、编辑、删除、排序标签 | CRUD 操作正常，组内排序生效 |
| **资产打标签** | ✅ 可为单个/批量资产添加/移除标签 | 关联正常，批量操作性能达标 |
| **标签筛选** | ✅ 可按单个/多个标签筛选资产 | 筛选结果准确，响应时间 < 500ms |
| **标签统计** | ✅ 可查看各标签资产数量和价值统计 | 统计数据准确，图表正常显示 |
| **自动规则** | ✅ 配置规则后新资产自动打标签 | 规则执行成功率 > 95% |

### 4.2 技术验收

| 项目 | 验收标准 | 通过条件 |
|------|----------|----------|
| **单元测试** | 后端测试覆盖率 ≥ 80% | 新增测试文件覆盖率达标 |
| **前端测试** | 组件测试通过，无 TS 错误 | Jest/Vitest 测试通过，TypeScript 严格模式通过 |
| **API 文档** | Swagger 文档完整 | 新增接口自动生成文档 |
| **性能** | 标签筛选响应时间 < 500ms | 100 并发测试平均响应时间达标 |
| **兼容性** | 不影响现有资产模块功能 | 回归测试通过，现有功能无回归 |
| **架构遵循** | 使用统一对象路由 | 所有接口通过 `/api/objects/` 访问 |

### 4.3 用户体验验收

| 场景 | 验收标准 |
|------|----------|
| **标签展示** | 资产列表/详情页标签显示美观，点击可筛选 |
| **批量操作** | 支持多选资产批量打标签，操作反馈及时 |
| **搜索功能** | 标签选择器支持搜索和快速定位 |
| **响应式设计** | 在不同屏幕尺寸下正常显示和操作 |

---

## 5. 实施计划

### 5.1 里程碑

| 里程碑 | 内容 | 预计时间 | 依赖 |
|--------|------|----------|------|
| **M1: 数据模型** | TagGroup, AssetTag, AssetTagRelation, TagAutoRule 模型 + API | 2 天 | 无 |
| **M2: 前端组件** | 标签选择器、标签管理页面、标签统计 | 3 天 | M1 |
| **M3: 资产集成** | 资产列表/详情页标签展示和操作 | 2 天 | M1, M2 |
| **M4: 筛选统计** | 标签筛选器和统计图表 | 2 天 | M2 |
| **M5: 自动规则** | 自动标签规则引擎 | 2 天 | M1 |
| **M6: 测试优化** | 单元测试、性能优化、文档 | 2 天 | M1-M5 |

**总计：约 13 个工作日**

### 5.2 依赖关系

```
M1 (数据模型)
  ↓
M2 (前端组件) ←→ M3 (资产集成)
  ↓
M4 (筛选统计)
  ↓
M5 (自动规则)
  ↓
M6 (测试优化)
```

### 5.3 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 标签数量爆炸 | 筛选性能下降 | 限制单资产标签数，建立索引，分页加载 |
| 规则冲突 | 自动标签混乱 | 规则优先级 + 冲突日志 + 人工干预 |
| 用户接受度 | 功能闲置 | 提供预置标签组，降低使用门槛 |
| 性能问题 | 标签关联查询慢 | 数据库索引优化，缓存机制 |

---

## 6. 附录

### 6.1 预置标签组

| 标签组 | 标签示例 | 用途 |
|--------|----------|------|
| **状态** | 待维修、已折旧完、正常使用、闲置 | 资产状态管理 |
| **部门** | IT部、行政部、财务部、销售部 | 按部门分组管理 |
| **风险** | 高价值、易丢失、需保险、已投保 | 风险管控 |
| **项目** | 项目A专用、项目B专用、共享 | 项目归属管理 |

### 6.2 技术债务

| 优先级 | 问题 | 影响范围 | 计划修复时间 |
|--------|------|----------|--------------|
| P0 | `fieldRegistry.spec.ts` 测试回归 | sub_table 归一化 | M6 |
| P0 | TypeScript 严格模式 18+ 错误 | 前端可维护性 | M6 |
| P1 | Service 层 BaseCRUDService 覆盖率 58.7% | 代码风格不统一 | Q2 2026 |
| P1 | 仓库卫生（.bak 文件） | 影响交付质量 | M6 |

### 6.3 参考文档

- `docs/prd/PRD_PHASE_7_3_ASSET_TAGS_2026-03-21.md` - 本文档
- `docs/prd/prd-business-workspace-convergence-phase1-2026-03-20.md` - 业务工作区收敛
- `docs/plans/system/object_catalog.py` - 对象目录规范
- `backend/apps/common/models.py` - BaseModel 定义

---

## 7. 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2025-01-20 | 初始版本 | 架构师 |
| v2.0 | 2026-03-21 | 基于首次分析更新 | Codex |
| v3.0 | 2026-03-21 | 基于深度代码分析更新，适配混合动态架构 | Codex |

---

**审批状态**: 待审核  
**下次评审**: 2026-03-28  
**负责人**: 产品经理 + 技术架构师