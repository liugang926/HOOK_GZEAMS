# Phase 3.2: 工作流执行引擎 - 总览

## 概述

实现工作流执行引擎，负责解析LogicFlow流程定义、分配任务、执行条件判断、管理流程状态流转。

---

## 1. 业务背景

### 1.1 核心功能

| 功能 | 说明 |
|------|------|
| **流程启动** | 根据流程定义创建实例 |
| **任务分配** | 根据节点配置分配审批人 |
| **任务处理** | 审批人通过/拒绝/退回 |
| **条件判断** | 根据业务数据判断分支 |
| **状态流转** | 自动流转到下一节点 |

### 1.2 流程状态

| 状态 | 说明 |
|------|------|
| draft | 草稿 |
| running | 运行中 |
| pending_approval | 待审批 |
| approved | 已通过 |
| rejected | 已拒绝 |
| cancelled | 已取消 |
| terminated | 已终止 |

---

## 2. 执行架构

```
┌─────────────────────────────────────────────────────────────┐
│                    工作流执行引擎                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  流程实例层                          │    │
│  │  WorkflowInstance                                   │    │
│  │  - definition: 流程定义                              │    │
│  │  - business_object: 业务对象                         │    │
│  │  - business_id: 业务数据ID                           │    │
│  │  - status: 流程状态                                  │    │
│  │  - current_node: 当前节点                            │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  任务管理层                          │    │
│  │  WorkflowTask                                        │    │
│  │  - instance: 流程实例                                │    │
│  │  - node: 节点定义                                    │    │
│  │  - assignee: 审批人                                  │    │
│  │  - status: 任务状态                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  执行引擎                            │    │
│  │  WorkflowEngine                                      │    │
│  │  - start_workflow()   启动流程                      │    │
│  │  - complete_task()    完成任务                      │    │
│  │  - evaluate_condition() 条件判断                    │    │
│  │  - get_next_nodes()   获取下一节点                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  审批记录                            │    │
│  │  WorkflowApproval                                   │    │
│  │  - task: 关联任务                                    │    │
│  │  - approver: 审批人                                  │    │
│  │  - action: 通过/拒绝/退回                            │    │
│  │  - comment: 审批意见                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型

### 3.1 WorkflowInstance（流程实例）

| 字段 | 说明 |
|------|------|
| definition | 关联流程定义 |
| business_object | 业务对象代码 |
| business_id | 业务数据ID |
| business_no | 业务单号 |
| status | 流程状态 |
| current_node_id | 当前节点ID |
| current_node_name | 当前节点名称 |
| initiator | 发起人 |

### 3.2 WorkflowTask（任务）

| 字段 | 说明 |
|------|------|
| instance | 关联流程实例 |
| node_id | 节点ID |
| node_name | 节点名称 |
| assignee | 审批人 |
| status | 任务状态 |
| due_date | 截止日期 |

### 3.3 任务状态

| 状态 | 说明 |
|------|------|
| pending | 待处理 |
| approved | 已通过 |
| rejected | 已拒绝 |
| returned | 已退回 |
| cancelled | 已取消 |

---

## 4. 执行流程

### 4.1 流程启动

```python
def start_workflow(definition_id, business_object, business_id, initiator):
    """启动工作流"""

    # 1. 获取流程定义
    definition = get_workflow_definition(definition_id)

    # 2. 创建流程实例
    instance = WorkflowInstance.objects.create(
        definition=definition,
        business_object=business_object,
        business_id=business_id,
        initiator=initiator,
        status='running'
    )

    # 3. 获取开始节点的下一节点
    start_node = get_start_node(definition)
    next_nodes = get_next_nodes(start_node)

    # 4. 创建任务
    for node in next_nodes:
        create_tasks(instance, node)

    return instance
```

### 4.2 任务完成

```python
def complete_task(task_id, approver, action, comment):
    """完成任务"""

    # 1. 获取任务
    task = get_task(task_id)

    # 2. 记录审批
    WorkflowApproval.objects.create(
        task=task,
        approver=approver,
        action=action,
        comment=comment
    )

    # 3. 更新任务状态
    task.status = 'approved' if action == 'approve' else 'rejected'
    task.save()

    # 4. 检查节点任务是否全部完成
    if is_node_completed(task.node_id):
        # 5. 获取下一节点
        next_nodes = get_next_nodes(task.node_id)

        if next_nodes:
            create_tasks(instance, next_nodes)
        else:
            # 流程结束
            instance.status = 'approved'
            instance.save()

    return task
```

---

## 5. 审批人配置

### 5.1 审批人类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 指定人 | 直接指定审批人 | user:123 |
| 部门负责人 | 部门负责人 | dept_leader |
| 发起人领导 | 发起人的上级领导 | initiator_leader |
| 角色 | 指定角色 | role:asset_manager |
| 动态选择 | 发起时选择 | dynamic |

### 5.2 审批方式

| 方式 | 说明 |
|------|------|
| 或签 | 任一人审批即可 |
| 会签 | 所有人都需审批 |
| 依次审批 | 按顺序依次审批 |

---

## 6. API接口

### 6.1 启动流程

```
POST /api/workflows/instances/start/
Request: {
    "definition_id": 1,
    "business_object": "asset_pickup",
    "business_id": 100
}
```

### 6.2 我的待办

```
GET /api/workflows/tasks/my/?status=pending
Response: {
    "results": [
        {
            "id": 1,
            "node_name": "部门审批",
            "business_no": "LY20240115001",
            "business_object": "asset_pickup"
        }
    ]
}
```

### 6.3 审批

```
POST /api/workflows/tasks/{id}/approve/
Request: {
    "action": "approve",  // approve / reject / return
    "comment": "同意"
}
```

---

## 7. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 执行引擎、任务管理 |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 审批组件 |
| [test.md](./test.md) | 测试计划 |

---

## 8. 后续任务

1. 实现流程实例创建
2. 实现任务分配逻辑
3. 实现审批处理
4. 实现条件判断
