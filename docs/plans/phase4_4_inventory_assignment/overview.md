# Phase 4.4: 盘点任务分配与执行 - 总览

## 概述

在盘点模型基础上，封装盘点分配机制，支持多种盘点模式的统一调度，区分管理端（任务分配与追踪）和用户端（任务执行与反馈）。

---

## 1. 业务背景

### 1.1 分配需求

| 需求 | 说明 |
|------|------|
| **任务拆分** | 将大盘点任务拆分为可执行的子任务 |
| **人员分配** | 指定盘点执行人 |
| **进度跟踪** | 实时跟踪各执行人进度 |
| **结果汇总** | 汇总所有执行结果 |

### 1.2 分配模式

- **区域分配**：按物理区域分配
- **分类分配**：按资产分类分配
- **人员分配**：按保管人分配
- **自定义分配**：手动选择资产分配

---

## 2. 功能架构

```
┌─────────────────────────────────────────────────────────────┐
│                    盘点任务分配系统                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   InventoryTask (盘点任务)            │    │
│  │  - inventory_type: 盘点类型                          │    │
│  │  - department: 部门                                  │    │
│  │  - category: 分类                                    │    │
│  │  - location: 位置范围                                │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 InventoryAssignment (盘点分配)        │    │
│  │  - task: 盘点任务                                    │    │
│  │  - executor: 执行人                                  │    │
│  │  - assets: 分配的资产列表                            │    │
│  │  - status: 执行状态                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│           ┌───────────────┼───────────────┐                 │
│           ▼               ▼               ▼                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  区域分配   │  │  分类分配   │  │  人员分配   │       │
│  │  模式       │  │  模式       │  │  模式       │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    用户端                             │    │
│  │  - 我的盘点任务                                      │    │
│  │  - 执行盘点                                          │    │
│  │  - 提交结果                                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型

### 3.1 InventoryAssignment（盘点分配）

| 字段 | 说明 |
|------|------|
| task | 盘点任务 |
| executor | 执行人 |
| assign_mode | 分配模式 |
| asset_count | 分配资产数量 |
| scanned_count | 已扫描数量 |
| status | 执行状态 |
| start_time | 开始时间 |
| complete_time | 完成时间 |

### 3.2 执行状态

| 状态 | 说明 |
|------|------|
| pending | 待执行 |
| in_progress | 执行中 |
| submitted | 已提交 |
| completed | 已完成 |

---

## 4. 公共模型引用

本模块所有组件均遵循 GZEAMS 公共基类规范，继承相应的基类以获得标准功能。

### 4.1 基类引用表

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离（org字段）、软删除（is_deleted+deleted_at）、审计字段（created_at+updated_at+created_by）、动态字段（custom_fields JSONB） |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields自动处理、created_by用户信息嵌入 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除过滤、审计字段自动设置、批量操作（/batch-delete/、/batch-restore/、/batch-update/） |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法、组织隔离、复杂查询、分页支持 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤（时间范围、用户、组织） |

### 4.2 核心模型继承关系

```python
# 盘点分配模型
class InventoryAssignment(BaseModel):
    """盘点任务分配记录"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    task = models.ForeignKey('inventory.InventoryTask', ...)
    executor = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    mode = models.CharField(...)  # region/category/custodian/random/manual
    scope_config = models.JSONField(...)  # 分配范围配置
    assigned_snapshot_ids = models.JSONField(...)  # 分配的快照ID列表
    total_assigned = models.IntegerField(default=0)
    completed_count = models.IntegerField(default=0)
    status = models.CharField(...)  # pending/in_progress/completed/overdue
    start_time = models.DateTimeField(null=True, blank=True)
    complete_time = models.DateTimeField(null=True, blank=True)
    completion_rate = models.FloatField(default=0.0)

# 分配模板模型
class InventoryAssignmentTemplate(BaseModel):
    """盘点分配模板（可复用的分配规则）"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    template_name = models.CharField(max_length=200)
    assign_mode = models.CharField(...)
    scope_config = models.JSONField(...)
    is_active = models.BooleanField(default=True)

# 分配规则模型
class InventoryAssignmentRule(BaseModel):
    """自动分配规则（基于条件自动触发分配）"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    rule_name = models.CharField(max_length=200)
    trigger_conditions = models.JSONField(...)
    assign_template = models.ForeignKey('InventoryAssignmentTemplate', ...)
    priority = models.IntegerField(default=0)
```

### 4.3 序列化器继承关系

```python
class InventoryAssignmentSerializer(BaseModelSerializer):
    """盘点分配序列化器"""
    class Meta(BaseModelSerializer.Meta):
        model = InventoryAssignment
        fields = BaseModelSerializer.Meta.fields + [
            'task', 'executor', 'mode', 'scope_config',
            'assigned_snapshot_ids', 'total_assigned', 'completed_count',
            'status', 'start_time', 'complete_time', 'completion_rate'
        ]
```

### 4.4 服务层继承关系

```python
class InventoryAssignmentService(BaseCRUDService):
    """盘点分配服务"""
    def __init__(self):
        super().__init__(InventoryAssignment)
        # 自动获得：create(), update(), delete(), restore(), get(), query(), paginate()
```

---

## 5. 分配模式

### 5.1 区域分配模式

按物理位置区域分配：

```python
def assign_by_location(task, locations, executors):
    """按位置分配"""

    for location, executor in zip(locations, executors):
        assets = Asset.objects.filter(location=location)

        InventoryAssignment.objects.create(
            task=task,
            executor=executor,
            assign_mode='location',
            location=location,
            asset_count=assets.count()
        )
```

### 4.2 分类分配模式

按资产分类分配：

```python
def assign_by_category(task, categories, executors):
    """按分类分配"""

    for category, executor in zip(categories, executors):
        assets = Asset.objects.filter(category=category)

        InventoryAssignment.objects.create(
            task=task,
            executor=executor,
            assign_mode='category',
            category=category,
            asset_count=assets.count()
        )
```

### 4.3 人员分配模式

按资产保管人分配：

```python
def assign_by_custodian(task, custodians):
    """按保管人分配（自我盘点）"""

    for custodian in custodians:
        assets = Asset.objects.filter(custodian=custodian)

        InventoryAssignment.objects.create(
            task=task,
            executor=custodian,
            assign_mode='custodian',
            asset_count=assets.count()
        )
```

---

## 6. 管理端功能

### 6.1 任务分配

- 选择盘点任务
- 选择分配模式
- 选择执行人员
- 预览分配结果
- 确认分配

### 6.2 进度跟踪

```
┌─────────────────────────────────────────────────────────┐
│  盘点任务: 2024年1月全面盘点                              │
├─────────────────────────────────────────────────────────┤
│  总进度: ████████░░ 80% (400/500)                        │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 执行人    │ 分配数 │ 已盘点 │ 进度   │ 状态      │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ 张三      │ 100    │ 100    │ 100%   │ 已完成    │    │
│  │ 李四      │ 100    │ 80     │ 80%    │ 进行中    │    │
│  │ 王五      │ 100    │ 95     │ 95%    │ 进行中    │    │
│  │ 赵六      │ 100    │ 75     │ 75%    │ 进行中    │
│  │ 钱七      │ 100    │ 50     │ 50%    │ 进行中    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 6.3 结果汇总

- 汇总各执行人结果
- 生成汇总报告
- 标记异常情况

---

## 7. 用户端功能

### 7.1 我的盘点任务

```
GET /api/inventory/my-assignments/
Response: {
    "results": [
        {
            "task_name": "2024年1月全面盘点",
            "asset_count": 100,
            "scanned_count": 80,
            "progress": "80%",
            "status": "in_progress"
        }
    ]
}
```

### 7.2 执行盘点

- 查看分配资产列表
- 扫码/手动盘点
- 实时显示进度
- 提交盘点结果

### 7.3 提交结果

```
POST /api/inventory/assignments/{id}/submit/
Request: {
    "comment": "盘点完成，无异常"
}
```

---

## 8. API接口

### 8.1 创建分配

```
POST /api/inventory/tasks/{id}/assign/
Request: {
    "assign_mode": "location",
    "assignments": [
        {"executor_id": 1, "location": "A区"},
        {"executor_id": 2, "location": "B区"}
    ]
}
```

### 8.2 查询分配

```
GET /api/inventory/tasks/{id}/assignments/
Response: {
    "results": [
        {
            "executor_name": "张三",
            "asset_count": 100,
            "scanned_count": 50,
            "progress": "50%"
        }
    ]
}
```

### 8.3 执行人任务列表

```
GET /api/inventory/my-assignments/
```

---

## 9. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 分配模型、分配服务 |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 管理端/用户端界面 |
| [test.md](./test.md) | 测试计划 |

---

## 10. 后续任务

1. 实现盘点分配模型
2. 实现多种分配模式
3. 实现进度跟踪
4. 实现用户端执行界面
