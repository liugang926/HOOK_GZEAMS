# Phase 3.1: LogicFlow可视化流程设计器 - 功能概述

## 1. 功能概述

### 1.1 核心价值
LogicFlow可视化流程设计器是GZEAMS工作流引擎的核心前端组件,为业务用户提供**低代码可视化工作流设计能力**。通过拖拽式交互,用户可以快速设计、配置和部署符合企业业务需求的审批流程,无需编写任何代码。

### 1.2 主要功能
- **可视化流程设计**: 基于LogicFlow库的拖拽式流程图设计器
- **多种节点类型**: 支持开始/结束/审批/条件/抄送/并行网关节点
- **属性配置面板**: 每个节点可配置审批人、条件表达式、字段权限等
- **流程校验**: 自动检测流程完整性(开始/结束节点、孤立节点、循环依赖)
- **流程模拟**: 支持模拟流程执行路径,验证配置正确性
- **版本管理**: 流程定义版本控制,支持查看历史版本和回滚
- **流程模板**: 提供常用流程模板,加速流程设计

### 1.3 业务场景
1. **资产领用审批**: 员工领用资产 → 部门审批 → 财务审批 → 资产发放
2. **资产调拨审批**: 发起调拨 → 部门审批 → 跨组织审批 → 完成调拨
3. **采购申请审批**: 采购申请 → 部门审批 → 条件判断(金额) → 财务/总经理审批
4. **盘点任务审批**: 盘点计划 → 财务审批 → 执行盘点 → 差异处理

---

## 2. 用户角色与权限

| 角色 | 职责 | 权限范围 |
|------|------|----------|
| **系统管理员** | 管理所有流程定义 | 全权限(查看/编辑/删除/发布所有流程) |
| **流程管理员** | 管理本组织流程定义 | 本组织流程全权限 |
| **流程设计师** | 设计和配置流程 | 本组织流程的查看/编辑/发布 |
| **流程查看者** | 查看流程定义和版本 | 只读权限 |
| **普通用户** | 发起和参与流程 | 无设计器权限,仅使用流程 |

### 权限矩阵

| 操作 | 系统管理员 | 流程管理员 | 流程设计师 | 流程查看者 | 普通用户 |
|------|-----------|-----------|-----------|-----------|---------|
| 创建流程定义 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 编辑流程定义 | ✅ | ✅(仅本组织) | ✅(仅本组织) | ❌ | ❌ |
| 删除流程定义 | ✅ | ✅(仅本组织) | ❌ | ❌ | ❌ |
| 发布流程 | ✅ | ✅(仅本组织) | ✅(仅本组织) | ❌ | ❌ |
| 查看流程列表 | ✅ | ✅(仅本组织) | ✅(仅本组织) | ✅(仅本组织) | ❌ |
| 查看流程详情 | ✅ | ✅(仅本组织) | ✅(仅本组织) | ✅(仅本组织) | ❌ |
| 查看版本历史 | ✅ | ✅(仅本组织) | ✅(仅本组织) | ✅(仅本组织) | ❌ |
| 回滚版本 | ✅ | ✅(仅本组织) | ❌ | ❌ | ❌ |

---

## 3. 公共模型引用声明

本模块严格遵循GZEAMS公共基础架构规范,所有组件均继承相应的公共基类:

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离(`organization` FK)、软删除(`is_deleted`+`deleted_at`)、审计字段(`created_at`+`updated_at`+`created_by`)、动态字段(`custom_fields` JSONB) |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段自动序列化、`custom_fields`处理、审计字段嵌套序列化 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除过滤、批量操作(`/batch-delete/`、`/batch-restore/`、`/batch-update/`) |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法、组织隔离、分页支持 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 公共字段过滤(时间范围、用户、组织) |

---

## 4. 数据模型设计

### 4.1 核心模型

#### WorkflowDefinition (流程定义)
```python
from apps.common.models import BaseModel

class WorkflowDefinition(BaseModel):
    """工作流定义模型"""
    # 自动继承字段: organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields

    # 基础字段
    code = models.CharField(max_length=50, unique=True)  # 流程编码
    name = models.CharField(max_length=200)  # 流程名称
    description = models.TextField(blank=True)  # 流程描述

    # 业务对象关联
    business_object = models.CharField(max_length=50)  # 关联业务对象: asset_pickup, asset_transfer等

    # 流程图数据(JSON格式,符合LogicFlow规范)
    graph_data = models.JSONField(default=dict)  # 流程图完整数据(包含nodes和edges)

    # 版本控制
    version = models.IntegerField(default=1)  # 版本号
    is_published = models.BooleanField(default=False)  # 是否已发布
    is_active = models.BooleanField(default=True)  # 是否启用

    # 表单字段权限配置
    form_permissions = models.JSONField(default=dict)  # 各节点的字段权限配置

    # 自动从BaseModel继承的功能
    # - organization: 组织隔离
    # - is_deleted + deleted_at: 软删除
    # - created_at + updated_at + created_by: 审计字段
    # - custom_fields: 动态扩展字段

    class Meta:
        db_table = 'workflow_definitions'
        verbose_name = '工作流定义'
        verbose_name_plural = '工作流定义'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} (v{self.version})'
```

### 4.2 数据字典

#### 流程状态 (is_published + is_active 组合)
| 状态 | is_published | is_active | 说明 |
|------|-------------|-----------|------|
| 草稿 | False | True | 编辑中,不可用于启动流程 |
| 已发布 | True | True | 可用于启动新流程实例 |
| 已停用 | True | False | 已发布但暂停使用 |
| 已归档 | False | False | 历史版本,不可编辑 |

#### 节点类型 (graph_data.nodes[].type)
| 类型代码 | 节点名称 | 说明 | 可配置属性 |
|---------|---------|------|------------|
| `start` | 开始节点 | 流程起点,每个流程有且仅有一个 | 无 |
| `end` | 结束节点 | 流程终点,可配置多种结束状态 | 结束状态: approved/rejected/cancelled |
| `approval` | 审批节点 | 需要人工审批的节点 | 审批人配置、审批类型、超时时间、字段权限 |
| `condition` | 条件节点 | 根据条件判断分支路径 | 条件表达式、默认分支 |
| `parallel` | 并行网关 | 并行执行多个分支 | 并行模式(AND/XOR) |
| `cc` | 抄送节点 | 仅通知,无需审批 | 抄送人列表、通知方式 |
| `notify` | 通知节点 | 发送系统通知 | 通知模板、接收人配置 |

#### 审批类型 (approveType)
| 类型 | 代码 | 说明 |
|------|------|------|
| 或签 | `or` | 任一审批人同意即可通过 |
| 会签 | `and` | 所有审批人都需同意 |
| 依次审批 | `sequence` | 按顺序依次审批 |

#### 审批人配置类型 (approver[].type)
| 类型 | 代码 | 配置示例 |
|------|------|---------|
| 指定成员 | `user` | `{"type": "user", "user_id": 123}` |
| 指定角色 | `role` | `{"type": "role", "role_id": 5}` |
| 发起人直属领导 | `leader` | `{"type": "leader", "leader_type": "direct"}` |
| 发起人部门领导 | `dept_leader` | `{"type": "dept_leader", "level": 1}` |
| 连续上级领导 | `continuous_leader` | `{"type": "continuous_leader", "max_level": 3}` |

#### 字段权限级别 (fieldPermissions)
| 级别 | 代码 | 说明 |
|------|------|------|
| 可编辑 | `editable` | 用户可以修改字段值 |
| 只读 | `read_only` | 用户只能查看,不可修改 |
| 隐藏 | `hidden` | 用户不可见 |

---

## 5. 核心业务流程

### 5.1 流程设计流程

```
┌─────────────┐
│  创建流程   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 拖拽添加节点 │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 连接节点连线 │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 配置节点属性 │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  校验流程   │
└──────┬──────┘
       │
       ▼
    ┌────┴────┐
    │  通过?   │
    └────┬────┘
         │ No    │ Yes
         ▼       ▼
  ┌──────────┐  ┌─────────────┐
  │ 修正错误 │  │  保存草稿   │
  └─────┬────┘  └──────┬──────┘
        └─────────────┘
                      │
                      ▼
              ┌─────────────┐
              │  发布流程   │
              └─────────────┘
```

### 5.2 节点配置流程

#### 审批节点配置
1. **基础信息**: 节点名称、节点描述
2. **审批人配置**:
   - 选择审批人类型(指定成员/角色/领导)
   - 配置具体审批人
   - 选择审批类型(或签/会签/依次)
3. **高级配置**:
   - 超时时间(小时)
   - 超时处理方式(自动通过/自动拒绝/提醒)
   - 字段权限(哪些字段可编辑/只读/隐藏)
4. **通知配置**:
   - 审批通知方式(站内信/邮件/企微)
   - 抄送人员列表

#### 条件节点配置
1. **分支配置**:
   - 添加多个分支
   - 为每个分支配置条件表达式
   - 设置默认分支(可选)
2. **条件表达式**:
   - 支持字段引用: `${amount}`, `${applicant.department.id}`
   - 支持操作符: `==`, `!=`, `>`, `>=`, `<`, `<=`, `in`, `not_in`, `contains`
   - 支持逻辑运算: `&&`, `||`
   - 示例: `${amount} > 10000 && ${applicant.department.id} == 5`

---

## 6. 技术实现要点

### 6.1 前端技术栈
- **LogicFlow**: 核心流程图绘制库
- **Vue 3**: 前端框架(Composition API)
- **Element Plus**: UI组件库
- **Pinia**: 状态管理

### 6.2 关键技术点

#### 流程图数据结构
```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "start",
      "x": 100,
      "y": 100,
      "text": "开始",
      "properties": {}
    },
    {
      "id": "node_2",
      "type": "approval",
      "x": 300,
      "y": 100,
      "text": "部门审批",
      "properties": {
        "approveType": "or",
        "approvers": [
          {"type": "user", "user_id": 123},
          {"type": "role", "role_id": 5}
        ],
        "timeout": 72,
        "timeoutAction": "remind",
        "fieldPermissions": {
          "amount": "read_only",
          "pickup_reason": "editable",
          "department": "hidden"
        }
      }
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "sourceNodeId": "node_1",
      "targetNodeId": "node_2",
      "type": "polyline",
      "properties": {}
    }
  ]
}
```

#### 流程校验规则
1. **必填节点检查**: 有且仅有一个开始节点、至少一个结束节点
2. **孤立节点检查**: 所有节点必须连通,无孤立节点
3. **循环依赖检查**: 不允许节点之间形成闭环
4. **审批人配置检查**: 所有审批节点必须配置审批人
5. **条件节点检查**: 条件节点必须有至少2个输出分支

#### 版本管理策略
- 每次发布流程时,自动创建新版本(`version += 1`)
- 旧版本数据保留,可查看和回滚
- 流程实例始终使用发布版本的快照数据

---

## 7. 与其他模块集成

### 7.1 依赖模块
- **apps.system**: BusinessObject(业务对象) - 流程定义关联业务对象
- **apps.organizations**: Organization(组织) - 组织隔离
- **apps.accounts**: User, Role - 审批人和角色配置

### 7.2 被依赖模块
- **apps.workflows**: WorkflowDefinition被工作流执行引擎引用

---

## 8. 非功能性需求

### 8.1 性能要求
- 流程设计器加载时间 < 2秒
- 节点拖拽延迟 < 100ms
- 流程校验响应时间 < 1秒
- 支持至少50个节点的大型流程图

### 8.2 兼容性要求
- 浏览器: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- 分辨率: 最低1366x768,推荐1920x1080

### 8.3 可用性要求
- 操作直观,无需求助文档即可完成基本流程设计
- 提供撤销/重做功能(最多20步)
- 支持快捷键操作(Ctrl+C/V/Z等)
- 提供操作提示和错误说明

---

## 9. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 流程定义模型与API |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - LogicFlow设计器组件 |
| [test.md](./test.md) | 测试计划 |

---

## 10. 后续任务

1. **Phase 3.2**: 工作流执行引擎 - 实现流程定义的运行时执行
2. **Phase 4.x**: 将工作流引擎集成到资产领用、调拨等业务场景

---

## 附录: 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| 流程定义 | Workflow Definition | 流程的结构化描述,包含节点、连线、属性等 |
| 流程实例 | Workflow Instance | 流程定义的一次运行实例 |
| 节点 | Node | 流程图中的基本单元,如审批节点、条件节点 |
| 边/连线 | Edge | 连接两个节点的有向线段 |
| 审批人 | Approver | 负责处理审批节点的用户或角色 |
| 或签 | OR Approval | 任一审批人同意即可通过 |
| 会签 | AND Approval | 所有审批人都需同意 |
| 字段权限 | Field Permission | 控制字段在不同审批节点的可见性和可编辑性 |
