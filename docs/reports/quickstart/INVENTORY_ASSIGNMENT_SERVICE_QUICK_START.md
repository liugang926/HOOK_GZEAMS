# Inventory Assignment Service - Quick Start Guide

## 概述
`InventoryAssignmentService` 提供了完整的盘点分配功能，支持多种分配模式和策略。

## 核心服务类

### 1. InventoryAssignmentService (继承 BaseCRUDService)
**用途**: 管理盘点任务的分配
**初始化**:
```python
from apps.inventory.services.assignment_service import InventoryAssignmentService
from apps.inventory.models import InventoryTask

task = InventoryTask.objects.get(id=task_id)
service = InventoryAssignmentService(task)
```

### 2. InventoryExecutorService
**用途**: 执行人管理自己的盘点任务
**初始化**:
```python
from apps.inventory.services.assignment_service import InventoryExecutorService
from apps.accounts.models import User

executor = User.objects.get(id=user_id)
service = InventoryExecutorService(executor)
```

### 3. InventoryViewPermissionService
**用途**: 管理盘点任务的查看权限
**初始化**:
```python
from apps.inventory.services.assignment_service import InventoryViewPermissionService
from apps.inventory.models import InventoryTask

task = InventoryTask.objects.get(id=task_id)
service = InventoryViewPermissionService(task)
```

---

## 核心方法使用示例

### 1. 手动创建盘点分配
```python
assignment_data = [
    {
        "executor_id": 1,
        "mode": "region",
        "scope_config": {"location_ids": [1, 2, 3]},
        "instruction": "请盘点A区资产"
    },
    {
        "executor_id": 2,
        "mode": "category",
        "scope_config": {"category_ids": [4, 5]},
        "instruction": "请盘点电子设备"
    }
]

assignments = service.create_assignments(
    assignment_data=assignment_data,
    clear_existing=True  # 是否清除现有分配
)
```

### 2. 按模板自动分配
```python
from apps.inventory.models import InventoryAssignmentTemplate

template = InventoryAssignmentTemplate.objects.get(id=template_id)
assignments = service.auto_assign_by_template(template)
```

### 3. 按规则自动分配
```python
# 自动使用组织的激活规则（按优先级排序）
assignments = service.auto_assign_by_rules()
```

### 4. 按保管人分配（自行盘点模式）
```python
# 为每个资产的保管人创建分配任务
assignments = service.assign_by_custodian()
```

### 5. 随机盲分配
```python
from apps.accounts.models import User

executors = list(User.objects.filter(department_id=1))

# 方式1: 均匀分配
assignments = service.assign_random(executors=executors)

# 方式2: 每人指定数量
assignments = service.assign_random(
    executors=executors,
    per_executor=50  # 每人分配50个资产
)
```

---

## 分配模式说明

### 支持的分配模式 (mode)
| 模式 | 说明 | scope_config 示例 |
|------|------|-------------------|
| `region` | 按区域分配 | `{"location_ids": [1, 2, 3]}` |
| `category` | 按分类分配 | `{"category_ids": [4, 5]}` |
| `custodian` | 按保管人分配 | `{"custodian_ids": [1, 2, 3]}` |
| `manual` | 手动指定资产 | `{"asset_codes": ["ASSET001", "ASSET002"]}` |
| `random` | 随机盲分配 | `{}` |

### 执行人解析类型 (executor_type)
| 类型 | 说明 | executor_value |
|------|------|----------------|
| `user` | 指定用户 | 用户ID |
| `department` | 部门负责人 | 部门ID |
| `role` | 角色用户 | 角色名称 |

---

## InventoryExecutorService 方法

### 获取我的分配任务
```python
# 获取所有分配
assignments = executor_service.get_my_assignments()

# 按状态过滤
assignments = executor_service.get_my_assignments(status='pending')
assignments = executor_service.get_my_assignments(status='in_progress')
assignments = executor_service.get_my_assignments(status='completed')
assignments = executor_service.get_my_assignments(status='overdue')
```

### 获取我的待盘点资产
```python
from apps.inventory.models import InventoryAssignment

assignment = InventoryAssignment.objects.get(id=assignment_id)
pending_assets = executor_service.get_my_pending_assets(assignment)

# 返回格式:
# [
#     {
#         "snapshot_id": 123,
#         "asset_id": 456,
#         "asset_code": "ASSET001",
#         "asset_name": "笔记本电脑",
#         "expected_location": "A区",
#         "expected_custodian": "张三",
#         "expected_status": "在用"
#     },
#     ...
# ]
```

### 获取今日任务统计
```python
today_stats = executor_service.get_my_today_tasks()

# 返回格式:
# {
#     "total_count": 3,          # 今日分配总数
#     "total_assets": 150,       # 总资产数
#     "completed_assets": 45,    # 已完成资产数
#     "assignments": [...]       # 分配详情列表
# }
```

### 开始/完成任务
```python
# 开始任务
executor_service.start_assignment(assignment)

# 完成任务
executor_service.complete_assignment(assignment)
```

---

## InventoryViewPermissionService 方法

### 更新查看配置
```python
config_data = {
    "allow_department_leader": True,
    "department_leader_scope": "department_assets",
    "allow_asset_admin": False,
    "remark": "仅允许部门负责人查看本部门资产"
}

config = permission_service.update_config(config_data)
```

### 添加查看人
```python
viewer_ids = ["user-uuid-1", "user-uuid-2"]

# 允许查看所有分配
viewers = permission_service.add_viewers(
    viewer_ids=viewer_ids,
    scope='all',
    source='manual'
)

# 允许查看特定部门的分配
viewers = permission_service.add_viewers(
    viewer_ids=viewer_ids,
    scope='department',
    scope_config={'department_id': 1},
    source='manual'
)

# 允许查看特定分配
viewers = permission_service.add_viewers(
    viewer_ids=viewer_ids,
    scope='assignment',
    scope_config={'assignment_ids': ['assign-uuid-1', 'assign-uuid-2']},
    source='manual'
)
```

### 移除查看人
```python
viewer_ids = ["user-uuid-1", "user-uuid-2"]
permission_service.remove_viewers(viewer_ids)
```

### 检查查看权限
```python
from apps.accounts.models import User

user = User.objects.get(id=user_id)

# 检查是否可以查看任务
can_view = permission_service.can_view_task(user)

# 获取可查看的分配
viewable_assignments = permission_service.get_viewable_assignments(user)
```

### 记录查看日志
```python
# 记录查看访问
permission_service.log_view(
    user=user,
    view_method='web',  # web/mobile/export
    request=request     # 可选，用于记录IP和User-Agent
)
```

---

## 权限说明

### 自动权限规则
1. **任务创建者**: 自动拥有所有分配的查看权限
2. **分配执行人**: 自动拥有自己分配的查看权限
3. **部门负责人**: 当 `allow_department_leader=True` 时，部门负责人可查看本部门相关的分配
4. **资产管理员**: 当 `allow_asset_admin=True` 时，拥有 `asset_admin` 角色的用户可查看所有分配

### 查看权限范围 (scope)
| 范围 | 说明 |
|------|------|
| `all` | 可查看所有分配 |
| `department` | 可查看特定部门的分配 |
| `assignment` | 可查看指定的分配列表 |

---

## 常见使用场景

### 场景1: 创建季度盘点任务并分配
```python
from apps.inventory.services.inventory_service import InventoryTaskService
from apps.inventory.services.assignment_service import InventoryAssignmentService

# 1. 创建盘点任务
task_service = InventoryTaskService()
task = task_service.create_task({
    "task_name": "2024年第一季度盘点",
    "task_type": "quarterly",
    "start_date": "2024-03-01",
    "end_date": "2024-03-31",
    "organization_id": org_id
})

# 2. 生成资产快照
task_service.generate_snapshots(task.id)

# 3. 按部门自动分配
assignment_service = InventoryAssignmentService(task)
assignments = assignment_service.auto_assign_by_rules()
```

### 场景2: 自行盘点模式
```python
# 每个员工盘点自己名下的资产
assignment_service = InventoryAssignmentService(task)
assignments = assignment_service.assign_by_custodian()
```

### 场景3: 抽检盘点（随机分配）
```python
from apps.accounts.models import User

# 获取盘点组成员
auditors = list(User.objects.filter(department_id=audit_dept_id))

# 随机分配，每人30个资产
assignment_service = InventoryAssignmentService(task)
assignments = assignment_service.assign_random(
    executors=auditors,
    per_executor=30
)
```

### 场景4: 为外部审计人员配置查看权限
```python
from apps.inventory.services.assignment_service import InventoryViewPermissionService

permission_service = InventoryViewPermissionService(task)

# 配置允许部门负责人查看
config = permission_service.update_config({
    "allow_department_leader": True,
    "department_leader_scope": "department_assets",
    "allow_asset_admin": False
})

# 添加外部审计人员为查看人
auditor_ids = ["auditor-uuid-1", "auditor-uuid-2"]
permission_service.add_viewers(
    viewer_ids=auditor_ids,
    scope='all',
    source='manual'
)
```

---

## 错误处理

### 常见异常
| 异常 | 原因 | 解决方案 |
|------|------|---------|
| `InventoryTask.DoesNotExist` | 任务不存在 | 检查任务ID是否正确 |
| `User.DoesNotExist` | 执行人不存在 | 检查执行人ID是否正确 |
| `ValidationError` | 分配数据验证失败 | 检查 `mode` 和 `scope_config` 是否匹配 |

### 事务处理
所有写入操作都使用 `@transaction.atomic` 装饰器，确保数据一致性：
- 如果操作失败，所有更改会自动回滚
- 无需手动处理事务回滚

---

## 性能建议

### 批量操作
```python
# 推荐: 批量创建分配
assignment_data = [...]  # 准备所有分配数据
assignments = service.create_assignments(assignment_data)

# 避免: 循环单个创建
for data in assignment_data:
    service.create_assignments([data])  # 效率低
```

### 查询优化
```python
# 推荐: 使用 select_related 减少查询次数
snapshots = task.snapshots.select_related('asset').all()

# 推荐: 使用 prefetch_related 优化多对多查询
assignments = task.assignments.prefetch_related('task__snapshots').all()
```

---

## 相关文档
- **完整实施报告**: `docs/reports/implementation/INVENTORY_ASSIGNMENT_SERVICE_IMPLEMENTATION_REPORT.md`
- **后端PRD**: `docs/plans/phase4_4_inventory_assignment/backend.md`
- **模型定义**: `backend/apps/inventory/models/assignment.py`
- **API文档**: `docs/api/inventory/assignment.md`

---

**文档版本**: v1.0
**最后更新**: 2026-01-16
**作者**: Claude (Sonnet 4.5)
