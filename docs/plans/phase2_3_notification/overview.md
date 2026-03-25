# Phase 2.3: 通知中心模块 - 总览

## 1. 功能概述与业务场景

### 1.1 功能概述

建立统一的通知中心，支持多渠道消息推送（企业微信、钉钉、飞书、邮件、短信、站内信），将系统各类通知统一管理、统一发送。核心特性包括：

- **多渠道适配**：支持6种主流通知渠道，可根据业务场景灵活配置
- **模板引擎**：支持动态变量替换的消息模板，简化通知内容维护
- **发送跟踪**：完整记录发送状态，支持失败重试机制
- **实时推送**：通过WebSocket实现站内信实时推送
- **统一服务层**：所有业务模块通过统一接口调用通知服务

### 1.2 业务场景

| 场景 | 渠道 | 优先级 | 说明 |
|------|------|--------|------|
| **审批通知** | 企微+站内信 | 高 | 待审批任务提醒，需要及时处理 |
| **系统公告** | 站内信 | 中 | 系统公告发布，全量用户可见 |
| **盘点提醒** | 企微+短信 | 高 | 盘点任务提醒，确保按时完成 |
| **异常预警** | 邮件+企微 | 紧急 | 资产异常预警，需要快速响应 |
| **定期报告** | 邮件 | 低 | 定期资产报告生成通知 |

### 1.3 核心目标

- **统一入口**：避免各业务模块重复建设通知功能
- **灵活配置**：支持按组织、按类型配置不同通知渠道
- **高可用性**：异步发送+失败重试，保证通知送达率
- **模板化管理**：支持消息模板统一管理和版本控制
- **发送可追溯**：完整记录发送日志，便于问题排查

---

## 2. 用户角色与权限

### 2.1 角色定义

| 角色 | 说明 | 主要权限 |
|------|------|----------|
| **系统管理员** | 负责通知渠道配置和维护 | - 配置所有通知渠道<br>- 管理消息模板<br>- 查看所有发送记录<br>- 查看通知统计 |
| **组织管理员** | 管理本组织通知配置 | - 配置本组织通知渠道<br>- 管理本组织消息模板<br>- 查看本组织发送记录 |
| **普通用户** | 通知接收者 | - 查看个人站内信<br>- 标记已读/删除<br>- 管理个人通知偏好 |

### 2.2 权限矩阵

| 操作 | 系统管理员 | 组织管理员 | 普通用户 |
|------|-----------|-----------|---------|
| 配置通知渠道 | ✅ 全部组织 | ✅ 本组织 | ❌ |
| 管理消息模板 | ✅ 全部 | ✅ 本组织 | ❌ |
| 发送通知 | ✅ | ✅ | ❌ |
| 查看发送记录 | ✅ 全部 | ✅ 本组织 | ❌ |
| 查看统计报表 | ✅ 全部 | ✅ 本组织 | ❌ |
| 查看个人站内信 | ✅ | ✅ | ✅ |
| 管理通知偏好 | ✅ | ✅ | ✅ 本人 |

---

## 3. 公共模型引用声明

### 3.1 引用公共基类

本模块所有数据模型均继承自 `apps.common.models.BaseModel`，自动获得以下能力：

- **多组织数据隔离**：内置 `organization` 字段，自动过滤组织数据
- **软删除机制**：内置 `is_deleted`、`deleted_at` 字段，物理删除禁用
- **审计字段**：内置 `created_at`、`updated_at`、`created_by` 字段，追踪数据变更
- **动态扩展**：内置 `custom_fields` (JSONB) 字段，支持低代码动态扩展

### 3.2 引用公共模型

| 模型名称 | 引用路径 | 用途 |
|----------|----------|------|
| **Organization** | `apps.organizations.models.Organization` | 组织多租户隔离 |
| **User** | `apps.accounts.models.User` | 系统用户，通知接收者 |
| **BaseModel** | `apps.common.models.BaseModel` | 所有模型的抽象基类 |

### 3.3 基类继承规范

```python
from apps.common.models import BaseModel
from apps.organizations.models import Organization
from apps.accounts.models import User

# 所有模型必须继承BaseModel
class NotificationChannel(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='notification_channels',
        verbose_name='所属组织'
    )

    # 自动继承字段：
    # - is_deleted: 布尔字段，软删除标记
    # - deleted_at: 时间字段，删除时间
    # - created_at: 时间字段，创建时间
    # - updated_at: 时间字段，更新时间
    # - created_by: 外键字段，创建人
    # - custom_fields: JSONB字段，动态扩展

    class Meta:
        db_table = 'notification_channel'
        verbose_name = '通知渠道'
        verbose_name_plural = verbose_name
        # 默认按组织过滤，自动应用多租户隔离
        indexes = [
            models.Index(fields=['organization', 'channel_type']),
            models.Index(fields=['organization', 'is_enabled']),
        ]
```

---

## 4. 功能架构

### 4.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    统一通知中心                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  业务调用层                           │    │
│  │  - 审批流程触发 (workflows)                          │    │
│  │  - 资产操作触发 (assets)                             │    │
│  │  - 盘点任务触发 (inventory)                          │    │
│  │  - 系统公告触发 (system)                             │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  通知服务层                           │    │
│  │  NotificationService                                │    │
│  │  - send()           直接发送通知                     │    │
│  │  - send_template()  模板发送通知                     │    │
│  │  - send_batch()     批量发送通知                     │    │
│  │  - get_templates()  获取消息模板                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  渠道适配器层                         │    │
│  │  NotificationChannelAdapter (抽象接口)               │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │    │
│  │  │WeWork  │ │DingTalk│ │ Feishu │ │ Email  │       │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │    │
│  │  ┌────────┐ ┌────────┐                            │    │
│  │  │  SMS   │ │ InApp  │                            │    │
│  │  └────────┘ └────────┘                            │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  数据存储层                           │    │
│  │  - NotificationMessage    通知消息                   │    │
│  │  - InAppMessage           站内信                     │    │
│  │  - NotificationLog        发送日志                   │    │
│  │  - NotificationTemplate   消息模板                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 数据流转

```
1. 业务触发
   │
   ├─> 审批流程创建 → 触发审批待处理通知
   ├─> 资产领用申请 → 触发审批通知
   ├─> 盘点任务分配 → 触发盘点提醒
   └─> 系统公告发布 → 触发广播通知
      │
      ▼
2. 调用通知服务
   NotificationService.send_template(
       template_code="asset_pickup_created",
       recipients=[user1, user2],
       channels=["wework", "inapp"],
       variables={...}
   )
      │
      ▼
3. 渲染消息模板
   {{applicant}} → "张三"
   {{department}} → "技术部"
   {{pickup_reason}} → "项目开发需要"
      │
      ▼
4. 选择可用渠道
   ├─> 查询 NotificationChannel (is_enabled=True)
   ├─> 按优先级排序
   └─> 过滤用户禁用渠道
      │
      ▼
5. 异步发送 (Celery)
   for channel in channels:
       adapter.send_message(message, recipients)
      │
      ▼
6. 记录发送结果
   ├─> 更新 NotificationMessage.status
   ├─> 记录 NotificationLog
   └─> 失败自动重试 (指数退避)
      │
      ▼
7. 实时推送 (WebSocket)
   └─> InApp消息通过WebSocket推送到前端
```

---

## 5. 渠道适配器

### 5.1 支持的渠道

| 渠道 | 标识 | 消息类型 | 适用场景 | 优先级 |
|------|------|----------|----------|--------|
| 企业微信 | wework | 文本卡片 | 审批通知、任务提醒 | 高 |
| 钉钉 | dingtalk | ActionCard | 审批通知 | 高 |
| 飞书 | feishu | 交互式卡片 | 审批通知 | 高 |
| 邮件 | email | HTML | 报表、正式通知 | 中 |
| 短信 | sms | 纯文本 | 紧急通知 | 紧急 |
| 站内信 | inapp | JSON | 系统通知、实时消息 | 低 |

### 5.2 适配器接口规范

```python
from abc import ABC, abstractmethod
from typing import Dict, List

class NotificationChannelAdapter(ABC):
    """通知渠道适配器抽象基类"""

    @abstractmethod
    def get_channel_type(self) -> str:
        """获取渠道类型标识"""
        pass

    @abstractmethod
    def get_channel_name(self) -> str:
        """获取渠道显示名称"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查渠道是否可用"""
        pass

    @abstractmethod
    def send_message(
        self,
        message: Dict,
        recipients: List[Dict]
    ) -> Dict:
        """
        发送消息

        Args:
            message: 消息内容
                {
                    "title": "消息标题",
                    "content": "消息内容",
                    "url": "跳转链接",
                    "button_text": "按钮文字",
                    "button_url": "按钮链接"
                }
            recipients: 接收人列表
                [
                    {"user_id": "1", "channel_id": "wework_user_id"},
                    {"user_id": "2", "channel_id": "wework_user_id"}
                ]

        Returns:
            发送结果
                {
                    "success": true,
                    "sent_count": 2,
                    "failed_count": 0,
                    "details": [
                        {"user_id": "1", "status": "sent", "external_id": "msg_001"},
                        {"user_id": "2", "status": "sent", "external_id": "msg_002"}
                    ]
                }
        """
        pass

    @abstractmethod
    def get_user_channel_id(self, system_user_id: str) -> str:
        """
        获取用户在第三方渠道的ID

        Args:
            system_user_id: 系统内用户ID

        Returns:
            第三方渠道用户ID (如企业微信userid)
        """
        pass
```

---

## 6. 通知模板

### 6.1 模板类型

| 业务分类 | 模板代码示例 | 说明 |
|----------|-------------|------|
| **审批通知** | asset_pickup_created | 资产领用待审批 |
| | asset_transfer_created | 资产调拨待审批 |
| | procurement_request_created | 采购申请待审批 |
| **资产通知** | asset_warning | 资产异常预警 |
| | asset_expired | 资产到期提醒 |
| **盘点通知** | inventory_assigned | 盘点任务分配 |
| | inventory_reminder | 盘点截止提醒 |
| | inventory_completed | 盘点完成通知 |
| **系统通知** | system_announcement | 系统公告 |
| | system_maintenance | 系统维护通知 |

### 6.2 模板变量语法

使用Jinja2模板语法，支持：

- **简单变量**：`{{applicant}}` - 替换为申请人姓名
- **对象属性**：`{{asset.code}}` - 替换为资产编码
- **条件渲染**：`{% if urgent %}紧急{% endif %}`
- **循环渲染**：`{% for item in items %}{{item.name}}{% endfor %}`

### 6.3 模板示例

```jinja2
标题: 待审批: {{pickup_type}}
申请人: {{applicant}}
部门: {{department}}
领用原因: {{pickup_reason}}
{% if pickup_items %}
资产清单:
{% for item in pickup_items %}
- {{item.asset_name}} ({{item.asset_code}})
{% endfor %}
{% endif %}
请及时处理。

点击链接查看详情: {{approval_link}}
```

---

## 7. 发送状态与重试

### 7.1 消息状态枚举

| 状态 | 说明 | 下一步操作 |
|------|------|-----------|
| pending | 待发送 | 加入Celery队列 |
| sending | 发送中 | 调用渠道适配器 |
| success | 发送成功 | 完成 |
| partial_success | 部分成功 | 重试失败接收人 |
| failed | 发送失败 | 加入重试队列 |
| retrying | 重试中 | 指数退避重试 |

### 7.2 日志状态枚举

| 状态 | 说明 |
|------|------|
| pending | 待发送 |
| sent | 已发送到第三方平台 |
| delivered | 已送达接收人 |
| read | 已读 (部分渠道支持) |
| failed | 发送失败 |

### 7.3 失败重试策略

- **自动重试**：网络错误、超时错误自动重试3次
- **指数退避**：重试间隔 1分钟 → 5分钟 → 30分钟
- **最大重试次数**：3次
- **死信队列**：超过重试次数进入死信队列，需要人工处理

```python
# Celery任务配置
@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 首次重试延迟60秒
    autoretry_for=(ConnectionError, TimeoutError)
)
def send_notification_task(self, message_id, channel_type):
    try:
        adapter = get_channel_adapter(channel_type)
        result = adapter.send_message(...)
        return result
    except Exception as exc:
        # 指数退避重试
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

---

## 8. 实时推送

### 8.1 WebSocket连接

```
wss://api.example.com/ws/notifications/?token=<jwt_token>
```

### 8.2 推送事件

| 事件名称 | 触发时机 | 数据格式 |
|---------|---------|----------|
| new_notification | 新站内信 | 完整消息对象 |
| notification.read | 消息已读 | {notification_id, unread_count} |
| notification.deleted | 消息删除 | {notification_id} |

### 8.3 浏览器通知

支持浏览器原生通知，需用户授权：

```javascript
// 请求通知权限
Notification.requestPermission().then(permission => {
    if (permission === 'granted') {
        // 显示通知
        new Notification('新消息', {
            body: '您有新的审批任务待处理',
            icon: '/logo.png',
            data: {url: '/approval/123'}
        })
    }
})
```

---

## 9. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 模型设计、服务层、渠道适配器 |
| [api.md](./api.md) | API接口定义 - 完整的RESTful API规范 |
| [frontend.md](./frontend.md) | 前端实现 - Vue3组件、状态管理、WebSocket |

---

## 10. 后续集成任务

1. **Phase 3.1**: 集成LogicFlow流程设计器，支持可视化审批流程配置
2. **Phase 3.2**: 实现工作流执行引擎，审批节点触发通知
3. **Phase 4.3**: 盘点任务分配时触发通知提醒
4. **Phase 5.4**: 报表生成完成后邮件通知

---

## 11. 核心技术要点

### 11.1 异步任务

所有通知发送操作必须通过Celery异步执行，避免阻塞主线程：

```python
# ✅ 正确：异步发送
from apps.notifications.tasks import send_notification_task

def create_asset_pickup(request):
    pickup = AssetPickup.objects.create(...)
    # 触发通知
    send_notification_task.delay(
        template_code='asset_pickup_created',
        recipients=[pickup.approver.id],
        business_type='asset_pickup',
        business_id=str(pickup.id)
    )

# ❌ 错误：同步发送
def create_asset_pickup(request):
    pickup = AssetPickup.objects.create(...)
    # 阻塞主线程！
    NotificationService.send(...)
```

### 11.2 多组织数据隔离

所有通知数据必须自动隔离到对应组织：

```python
# BaseModel自动应用组织过滤
class NotificationMessage(BaseModel):
    organization = ForeignKey(Organization, ...)

# 查询时自动过滤当前组织数据
messages = NotificationMessage.objects.all()
# 自动转换为：
# SELECT * FROM notification_message
# WHERE organization_id = <当前用户组织ID> AND is_deleted = False
```

### 11.3 错误处理

统一使用标准错误码，便于前端处理：

```python
from apps.common.responses import ErrorResponse

# 渠道未启用
return ErrorResponse(
    error_code='CHANNEL_NOT_ENABLED',
    message='企业微信渠道未启用',
    details={'channel': 'wework'}
)
```
