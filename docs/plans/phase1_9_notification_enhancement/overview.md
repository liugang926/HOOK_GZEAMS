# Phase 1.9: 统一通知机制 - 总览

## 概述

本模块建立统一的通知服务框架，整合系统内各类通知（审批通知、系统消息、预警提醒等），支持多渠道推送（站内信、邮件、短信、企业微信、钉钉），实现通知模板化管理、发送失败重试、发送状态追踪等功能。

---

## 1. 业务背景

### 1.1 当前痛点

| 痛点 | 说明 | 影响 |
|------|------|------|
| **渠道分散** | 各模块独立实现通知，代码重复 | 维护成本高 |
| **无模板管理** | 通知内容硬编码，修改困难 | 运营不灵活 |
| **失败无重试** | 发送失败后无法自动重试 | 通知丢失 |
| **状态不可见** | 无法追踪通知发送状态 | 问题排查难 |
| **无统一接入** | 新增通知类型需要重复开发 | 效率低 |

### 1.2 业务目标

- **统一接入**: 提供统一的通知发送API
- **模板管理**: 支持可视化配置通知模板
- **多渠道推送**: 站内信/邮件/短信/企微/钉钉
- **失败重试**: 自动重试机制，支持退避策略
- **状态追踪**: 完整的发送状态和日志

---

## 2. 功能架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         统一通知服务                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    接入层 (API Layer)                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │   │
│  │  │  同步API     │  │  异步API    │  │  批量API    │             │   │
│  │  │  send()     │  │  send_async│  │  send_batch │             │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    核心层 (Core Layer)                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │   │
│  │  │  模板引擎    │  │  渠道路由    │  │  重试调度    │             │   │
│  │  │  Template   │  │  Router     │  │  Retry      │             │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                ↓                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    渠道层 (Channel Layer)                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ 站内信   │  │  邮件    │  │  短信    │  │  IM推送  │       │   │
│  │  │ Inbox    │  │  Email   │  │  SMS     │  │  WeWork  │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 用户角色与权限

| 角色 | 权限说明 | 主要操作 |
|------|---------|---------|
| **普通员工** | 查看通知、标记已读/未读、设置通知偏好 | 查看我的通知、标记已读、设置通知渠道 |
| **部门主管** | 查看部门通知、批量审批通知 | 查看部门统计、批量标记已读 |
| **系统管理员** | 全部权限，包括通知配置、模板管理、系统监控 | 管理通知模板、查看发送统计、配置渠道 |
| **财务管理员** | 查看财务相关通知 | 查看财务通知、配置财务通知偏好 |

## 4. 公共模型引用声明

本模块严格遵循GZEAMS公共基类架构规范，所有后端组件均继承相应的公共基类：

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离（org字段）、软删除（is_deleted+deleted_at）、审计字段（created_at+updated_at+created_by）、动态扩展（custom_fields JSONField） |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 自动序列化公共字段、custom_fields处理 |
| Serializer (带审计) | BaseModelWithAuditSerializer | apps.common.serializers.base.BaseModelWithAuditSerializer | 包含updated_by和deleted_by的完整审计信息 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除过滤、自动设置审计字段、批量操作、已删除记录查询 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤、时间范围查询 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法、自动组织隔离、软删除处理、批量操作支持 |

**核心模型继承关系**：

```python
# 所有通知模型继承BaseModel
from apps.common.models import BaseModel

class NotificationTemplate(BaseModel):
    """通知模板 - 自动获得组织隔离、软删除、审计、自定义字段"""
    template_code = models.CharField(max_length=50, unique=True)
    # ...

class Notification(BaseModel):
    """通知记录 - 自动获得组织隔离、软删除、审计、自定义字段"""
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # ...

class NotificationLog(BaseModel):
    """通知日志 - 自动获得组织隔离、软删除、审计、自定义字段"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    # ...

class NotificationConfig(BaseModel):
    """通知配置 - 自动获得组织隔离、软删除、审计、自定义字段"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # ...
```

## 5. 功能范围

### 3.1 通知模板管理

| 功能 | 说明 |
|------|------|
| 模板创建 | 支持富文本编辑、变量插入 |
| 模板分类 | 按业务模块、通知类型分类 |
| 模板预览 | 实时预览模板渲染效果 |
| 模板版本 | 支持模板版本管理和回滚 |
| 多语言 | 支持中英文等多语言模板 |

### 3.2 渠道管理

| 渠道 | 支持情况 | 说明 |
|------|----------|------|
| 站内信 | 支持 | 系统内消息中心 |
| 邮件 | 支持 | SMTP/发送服务 |
| 短信 | 支持 | 阿里云/腾讯云短信 |
| 企业微信 | 支持 | 应用消息推送 |
| 钉钉 | 支持 | 机器人消息 |
| 飞书 | 支持 | 开放平台消息 |

### 3.3 失败重试机制

| 策略 | 说明 |
|------|------|
| 指数退避 | 重试间隔按指数增长 |
| 最大重试次数 | 默认3次，可配置 |
| 死信队列 | 超过最大重试次数后进入死信队列 |
| 人工处理 | 支持手动重新发送 |

### 3.4 通知追踪

| 功能 | 说明 |
|------|------|
| 发送状态 | 待发送/发送中/成功/失败 |
| 送达回执 | 邮件打开、短信送达状态 |
| 阅读状态 | 站内信已读/未读 |
| 发送日志 | 完整的发送和重试日志 |

---

## 4. 通知类型定义

### 4.1 系统通知类型

| 类型代码 | 名称 | 默认渠道 | 模板 |
|----------|------|----------|------|
| workflow_approval | 审批通知 | 站内信+企微 | WORKFLOW_APPROVAL |
| workflow_approved | 审批完成 | 站内信+邮件 | WORKFLOW_APPROVED |
| workflow_rejected | 审批拒绝 | 站内信+邮件 | WORKFLOW_REJECTED |
| inventory_assigned | 盘点任务分配 | 站内信+短信 | INVENTORY_ASSIGNED |
| inventory_reminder | 盘点提醒 | 站内信+企微 | INVENTORY_REMINDER |
| asset_warning | 资产预警 | 站内信+邮件 | ASSET_WARNING |
| system_announcement | 系统公告 | 站内信 | SYSTEM_ANNOUNCEMENT |
| report_generated | 报表生成完成 | 站内信+邮件 | REPORT_GENERATED |

### 4.2 通知优先级

| 级别 | 代码 | 说明 | 重试策略 |
|------|------|------|----------|
| 紧急 | urgent | 需立即处理 | 立即重试，最多5次 |
| 重要 | high | 重要但不紧急 | 1分钟后重试 |
| 普通 | normal | 常规通知 | 5分钟后重试 |
| 低 | low | 非重要通知 | 不重试 |

---

## 5. 模板引擎设计

### 5.1 模板语法

采用 Jinja2 风格的模板语法：

```
标题: {{ title }}

尊敬的 {{ recipient_name }}：

您有 {{ count }} 条待处理的审批任务：

{% for task in tasks %}
- {{ task.title }} ({{ task.workflow_name }})
{% endfor %}

请及时处理。

点击链接查看详情: {{ link }}
```

### 5.2 内置变量

| 变量 | 说明 |
|------|------|
| recipient_name | 接收人姓名 |
| recipient_email | 接收人邮箱 |
| sender_name | 发送人姓名 |
| current_date | 当前日期 |
| current_time | 当前时间 |
| system_name | 系统名称 |
| link | 链接地址 |

### 5.3 自定义函数

| 函数 | 说明 | 示例 |
|------|------|------|
| format_date | 格式化日期 | {{ task.created_at\|format_date }} |
| format_money | 格式化金额 | {{ amount\|format_money }} |
| truncate | 截断文本 | {{ content\|truncate(50) }} |

---

## 6. 渠道适配器设计

### 6.1 适配器接口

```python
class NotificationChannel(ABC):
    """通知渠道适配器基类"""

    @abstractmethod
    def send(self, message: NotificationMessage) -> SendResult:
        """发送通知"""
        pass

    @abstractmethod
    def get_template_type(self) -> str:
        """获取支持的模板类型"""
        pass

    @abstractmethod
    def supports_retry(self) -> bool:
        """是否支持重试"""
        pass
```

### 6.2 渠道适配器实现

| 渠道 | 适配器类 | 模板类型 |
|------|----------|----------|
| 站内信 | InboxChannel | JSON |
| 邮件 | EmailChannel | HTML |
| 短信 | SMSChannel | 纯文本 |
| 企业微信 | WeWorkChannel | Markdown |
| 钉钉 | DingTalkChannel | Markdown |

---

## 7. 数据模型关系

```
NotificationTemplate (通知模板)
    ├── template_code (模板代码)
    ├── template_name (模板名称)
    ├── channel (渠道类型)
    ├── subject_template (标题模板)
    ├── content_template (内容模板)
    ├── variables (JSON) # 模板变量定义
    ├── is_active (是否启用)
    └── version (版本号)

Notification (通知)
    ├── recipient → User
    ├── template → NotificationTemplate
    ├── type (通知类型)
    ├── priority (优先级)
    ├── channel (发送渠道)
    ├── status (发送状态)
    ├── subject (通知标题)
    ├── content (通知内容)
    ├── variables (JSON) # 模板变量值
    ├── sent_at (发送时间)
    ├── read_at (阅读时间)
    └── retry_count (重试次数)

NotificationLog (通知日志)
    ├── notification → Notification
    ├── channel (渠道)
    ├── status (状态)
    ├── response (JSON) # 渠道响应
    ├── error_message (错误信息)
    ├── retry_count (重试次数)
    └── created_at (创建时间)

NotificationConfig (通知配置)
    ├── user → User
    ├── type (通知类型)
    ├── channel_enabled (JSON) # 渠道开关
    ├── quiet_hours (JSON) # 免打扰时段
    └── is_enabled (是否启用)
```

---

## 8. 重试策略设计

### 8.1 重试策略配置

```python
RETRY_STRATEGIES = {
    'urgent': {
        'max_retries': 5,
        'backoff': 'immediate',  # 立即重试
        'retry_on': ['timeout', 'server_error']
    },
    'high': {
        'max_retries': 3,
        'backoff': 'exponential',
        'initial_delay': 60,  # 1分钟
        'max_delay': 600  # 最大10分钟
    },
    'normal': {
        'max_retries': 3,
        'backoff': 'exponential',
        'initial_delay': 300,  # 5分钟
        'max_delay': 3600  # 最大1小时
    },
    'low': {
        'max_retries': 0,  # 不重试
        'backoff': 'none'
    }
}
```

### 8.2 退避算法

| 算法 | 说明 | 延迟计算 |
|------|------|----------|
| fixed | 固定延迟 | delay |
| linear | 线性增长 | delay * retry_count |
| exponential | 指数增长 | delay * (2 ^ retry_count) |

---

## 9. 与其他模块的集成

| 集成点 | 关联模块 | 集成方式 |
|--------|---------|---------|
| 审批通知 | workflows | 流程节点事件触发 |
| 盘点通知 | inventory | 任务分配/提醒 |
| 预警通知 | assets | 资产异常触发 |
| 消息中心 | frontend | 站内信展示 |
| 移动推送 | mobile | 移动端通知 |

---

## 10. API示例

### 10.1 发送通知

```python
from notifications.services import NotificationService

# 简单发送
NotificationService.send(
    recipient=user,
    type='workflow_approval',
    variables={
        'task_title': '资产采购申请',
        'workflow_name': '采购流程',
        'link': 'https://...'
    }
)

# 批量发送
NotificationService.send_batch(
    recipients=[user1, user2, user3],
    type='inventory_assigned',
    variables={'task_no': 'PD2024001'}
)

# 指定渠道
NotificationService.send(
    recipient=user,
    type='urgent_alert',
    channels=['email', 'sms', 'wework'],
    variables={'message': '紧急通知'}
)
```

---

## 11. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 模型、渠道适配器、重试机制 |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 消息中心、通知设置 |
| [test.md](./test.md) | 测试计划 |

---

## 12. 后续任务

1. 实现通知模板引擎
2. 实现各渠道适配器
3. 实现重试调度器
4. 实现发送状态追踪
5. 集成到各业务模块
6. 前端消息中心开发
7. 通知配置页面开发
8. 单元测试和集成测试
