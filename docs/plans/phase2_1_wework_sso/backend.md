# Phase 2.1: 企业微信SSO登录 - 后端实现

## 概述

本文档描述企业微信SSO登录功能的后端实现。所有代码示例均已更新为使用公共基类，以保持代码一致性和可维护性。

### 核心依赖

- **BaseModelSerializer**: 所有序列化器继承此类，自动获得公共字段序列化
- **BaseModelViewSetWithBatch**: 所有 ViewSet 继承此类，自动获得组织隔离、软删除、批量操作
- **BaseCRUDService**: 所有 Service 类继承此类，自动获得标准 CRUD 方法
- **BaseModelFilter**: 所有过滤器继承此类，自动获得公共字段过滤能力

---

## 公共模型引用声明

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |

---

## 错误处理机制

### 异常类型
- NetworkException: 网络异常
- APIException: API调用异常
- ValidationException: 数据验证异常

### 重试策略
- 指数退避重试: 60s -> 120s -> 240s -> 480s
- 最大重试次数: 3次
- 失败告警: 记录IntegrationLog并发送通知

### 错误日志
所有错误记录到IntegrationLog模型，包含：
- request_url: 请求地址
- request_body: 请求体
- response_body: 响应体
- status_code: 状态码
- error_message: 错误信息

---

### 更新内容

1. **序列化器**: 使用 `BaseModelSerializer` 替代 `serializers.ModelSerializer`
2. **ViewSet**: 使用 `BaseModelViewSetWithBatch` 替代函数视图，获得完整 CRUD 和批量操作
3. **Service**: 使用 `BaseCRUDService` 作为基类，提供统一的 CRUD 接口
4. **过滤器**: 使用 `BaseModelFilter` 作为基类，继承公共字段过滤

---

## 模型定义

### 1. 企业微信配置模型

#### WeWorkConfig (企业微信配置表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| organization | FK | OneToOne | 所属组织 |
| corp_id | string | max_length=100 | 企业ID |
| corp_name | string | max_length=200 | 企业名称 |
| agent_id | integer | - | 应用ID |
| agent_secret | string | max_length=200 | 应用Secret |
| sync_department | boolean | default=True | 同步部门 |
| sync_user | boolean | default=True | 同步用户 |
| auto_create_user | boolean | default=True | 自动创建用户 |
| default_role_id | integer | nullable | 默认角色 |
| redirect_uri | URL | blank | 回调地址 |
| is_enabled | boolean | default=True | 是否启用 |

*注: 继承 BaseModel 自动获得 organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields*

#### UserMapping (用户平台映射表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| system_user | FK | cascade | 系统用户 |
| platform | string | max_length=20 | 平台类型 (wework/dingtalk/feishu) |
| platform_userid | string | max_length=100 | 平台用户ID |
| platform_unionid | string | max_length=100, blank | 平台UnionID |
| platform_name | string | max_length=200, blank | 平台名称 |
| extra_data | JSON | default=dict | 额外数据 |

*唯一约束: (platform, platform_userid)*

#### OAuthState (OAuth状态表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| state | string | max_length=100, unique | 状态码 |
| platform | string | max_length=20 | 平台 |
| session_data | JSON | default=dict | 会话信息 |
| expires_at | datetime | - | 过期时间 |

*方法: is_valid(), consume()*

---

## 适配器实现

### 1. 企业微信适配器

```python
# apps/sso/adapters/wework_adapter.py

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from django.core.cache import cache
from apps.sso.models import WeWorkConfig


class WeWorkAdapter:
    """企业微信适配器"""

    API_BASE = "https://qyapi.weixin.qq.com/cgi-bin"
    OAUTH_BASE = "https://open.weixin.qq.com/connect/oauth2"
    QR_CONNECT_BASE = "https://open.work.weixin.qq.com/wwopen/sso/qrConnect"

    def __init__(self, config: WeWorkConfig):
        self.config = config
        self.corp_id = config.corp_id
        self.agent_id = config.agent_id
        self.agent_secret = config.agent_secret

    def get_access_token(self) -> str:
        """获取access_token（带缓存）"""
        cache_key = f"wework:access_token:{self.corp_id}:{self.agent_id}"
        token = cache.get(cache_key)

        if token:
            return token

        # 从企业微信获取
        url = f"{self.API_BASE}/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.agent_secret
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"获取access_token失败: {data['errmsg']}")

        token = data['access_token']
        # 缓存token，提前5分钟过期
        expires_in = data.get('expires_in', 7200) - 300
        cache.set(cache_key, token, expires_in)

        return token

    def get_jsapi_ticket(self) -> str:
        """获取jsapi_ticket（用于前端JSAPI）"""
        cache_key = f"wework:jsapi_ticket:{self.corp_id}:{self.agent_id}"
        ticket = cache.get(cache_key)

        if ticket:
            return ticket

        access_token = self.get_access_token()
        url = f"{self.API_BASE}/get_jsapi_ticket"
        params = {"access_token": access_token}

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"获取jsapi_ticket失败: {data['errmsg']}")

        ticket = data['ticket']
        expires_in = data.get('expires_in', 7200) - 300
        cache.set(cache_key, ticket, expires_in)

        return ticket

    def get_oauth_url(self, redirect_uri: str, state: str = '', scope: str = 'snsapi_base') -> str:
        """
        获取OAuth授权URL（用于网页内跳转授权）

        Args:
            redirect_uri: 授权后重定向的回调地址
            state: 防CSRF攻击的状态码
            scope: 授权作用域
                - snsapi_base: 静默授权，可获取成员userid
                - snsapi_userinfo: 静默授权，可获取成员详细信息
                - snsapi_privateinfo: 手动授权，可获取成员详细信息及敏感信息
        """
        from urllib.parse import quote

        params = {
            "appid": self.corp_id,
            "redirect_uri": quote(redirect_uri),
            "response_type": "code",
            "scope": scope,
            "agentid": self.agent_id,
            "state": state
        }

        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.OAUTH_BASE}/authorize?{param_str}#wechat_redirect"

    def get_qr_connect_url(self, redirect_uri: str, state: str = '', size: str = '') -> str:
        """
        获取扫码登录URL（用于PC端扫码登录）

        Args:
            redirect_uri: 授权后重定向的回调地址
            state: 防CSRF攻击的状态码
            size: 二维码尺寸 (430, 560)
        """
        from urllib.parse import quote

        params = {
            "appid": self.corp_id,
            "agentid": self.agent_id,
            "redirect_uri": quote(redirect_uri),
            "state": state,
            "usertype": "member"
        }

        if size:
            params["size"] = size

        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.QR_CONNECT_BASE}?{param_str}"

    def get_user_info_by_code(self, code: str) -> Dict:
        """
        通过授权码获取用户信息

        Args:
            code: OAuth授权码

        Returns:
            用户信息字典
        """
        # 1. 获取用户userid
        access_token = self.get_access_token()
        url = f"{self.API_BASE}/auth/getuserinfo"
        params = {
            "access_token": access_token,
            "code": code
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"获取用户userid失败: {data['errmsg']}")

        user_id = data['userid']

        # 2. 获取用户详细信息
        return self.get_user_detail(user_id)

    def get_user_detail(self, user_id: str) -> Dict:
        """
        获取用户详细信息

        Args:
            user_id: 企业微信userid

        Returns:
            用户详细信息字典
        """
        access_token = self.get_access_token()
        url = f"{self.API_BASE}/user/get"
        params = {
            "access_token": access_token,
            "userid": user_id
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"获取用户详情失败: {data['errmsg']}")

        return {
            'userid': data['userid'],
            'name': data['name'],
            'english_name': data.get('english_name', ''),
            'department': data.get('department', []),
            'order_in_depts': data.get('order_in_depts', []),
            'position': data.get('position', ''),
            'mobile': data.get('mobile', ''),
            'gender': data.get('gender', ''),
            'email': data.get('email', ''),
            'avatar': data.get('avatar', ''),
            'status': data.get('status', 1),
            'is_leader': data.get('isleader', 0),
            'direct_leader': data.get('direct_leader', []),
            'main_department': data.get('main_department', 0),
        }

    def get_department_list(self) -> List[Dict]:
        """获取部门列表"""
        access_token = self.get_access_token()
        url = f"{self.API_BASE}/department/list"
        params = {"access_token": access_token}

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"获取部门列表失败: {data['errmsg']}")

        return data.get('department', [])

    def get_user_list(self, department_id: int = None, fetch_child: bool = False) -> List[Dict]:
        """
        获取部门成员列表

        Args:
            department_id: 部门ID，为空则获取全部
            fetch_child: 是否递归获取子部门成员
        """
        access_token = self.get_access_token()
        url = f"{self.API_BASE}/user/list"
        params = {
            "access_token": access_token,
            "department_id": department_id,
            "fetch_child": 1 if fetch_child else 0
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"获取用户列表失败: {data['errmsg']}")

        return data.get('userlist', [])

    def send_message(self, user_id: str, content: str, msg_type: str = 'text') -> Dict:
        """
        发送应用消息

        Args:
            user_id: 接收人userid
            content: 消息内容
            msg_type: 消息类型 (text/image/file等)
        """
        access_token = self.get_access_token()
        url = f"{self.API_BASE}/message/send"
        params = {"access_token": access_token}

        if msg_type == 'text':
            data = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {
                    "content": content
                },
                "safe": 0
            }
        elif msg_type == 'textcard':
            data = {
                "touser": user_id,
                "msgtype": "textcard",
                "agentid": self.agent_id,
                "textcard": content
            }
        elif msg_type == 'news':
            data = {
                "touser": user_id,
                "msgtype": "news",
                "agentid": self.agent_id,
                "news": content
            }
        else:
            raise ValueError(f"不支持的消息类型: {msg_type}")

        response = requests.post(url, params=params, json=data, timeout=10)
        result = response.json()

        if result['errcode'] != 0:
            raise Exception(f"发送消息失败: {result['errmsg']}")

        return result
```

---

## 序列化器实现

### 1. 企业微信配置序列化器

```python
# apps/sso/serializers/wework_serializer.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.sso.models import WeWorkConfig, UserMapping, OAuthState


class WeWorkConfigSerializer(BaseModelSerializer):
    """企业微信配置序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = WeWorkConfig
        fields = BaseModelSerializer.Meta.fields + [
            'corp_id', 'corp_name', 'agent_id', 'agent_secret',
            'sync_department', 'sync_user', 'auto_create_user',
            'default_role_id', 'redirect_uri', 'is_enabled'
        ]
        extra_kwargs = {
            'agent_secret': {'write_only': True}
        }


class WeWorkConfigDetailSerializer(BaseModelWithAuditSerializer):
    """企业微信配置详情序列化器（包含完整审计信息）"""

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = WeWorkConfig
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'corp_id', 'corp_name', 'agent_id', 'agent_secret',
            'sync_department', 'sync_user', 'auto_create_user',
            'default_role_id', 'redirect_uri', 'is_enabled'
        ]
        extra_kwargs = {
            'agent_secret': {'write_only': True}
        }


class UserMappingSerializer(BaseModelSerializer):
    """用户平台映射序列化器"""

    system_user_info = serializers.SerializerMethodField()
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = UserMapping
        fields = BaseModelSerializer.Meta.fields + [
            'platform', 'platform_userid', 'platform_unionid',
            'platform_name', 'extra_data', 'system_user_info',
            'platform_display'
        ]

    def get_system_user_info(self, obj):
        """获取系统用户信息"""
        if obj.system_user:
            return {
                'id': str(obj.system_user.id),
                'username': obj.system_user.username,
                'real_name': obj.system_user.real_name,
                'email': obj.system_user.email,
                'mobile': obj.system_user.mobile
            }
        return None


class OAuthStateSerializer(BaseModelSerializer):
    """OAuth状态序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = OAuthState
        fields = [
            'id', 'state', 'platform', 'session_data',
            'expires_at', 'created_at'
        ]
```

---

## 服务层实现

### 1. SSO服务

```python
# apps/sso/services/sso_service.py

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.utils import timezone
from apps.common.services.base_crud import BaseCRUDService
from apps.sso.models import WeWorkConfig, UserMapping, OAuthState
from apps.accounts.models import User
from apps.accounts.auth import generate_jwt_token


class SSOService:
    """SSO服务基类"""

    @staticmethod
    def generate_state() -> str:
        """生成随机state码"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_oauth_state(platform: str, session_data: dict = None) -> str:
        """创建并存储OAuth状态"""
        state = SSOService.generate_state()
        expires_at = timezone.now() + timedelta(minutes=10)

        OAuthState.objects.create(
            state=state,
            platform=platform,
            session_data=session_data or {},
            expires_at=expires_at
        )

        return state

    @staticmethod
    def validate_and_consume_state(state: str, platform: str) -> dict:
        """验证并消费OAuth状态"""
        return OAuthState.consume(state, platform) or {}


class WeWorkConfigService(BaseCRUDService):
    """企业微信配置服务 - 继承 BaseCRUDService"""

    def __init__(self):
        super().__init__(WeWorkConfig)

    def get_enabled_config(self, organization_id: int = None) -> WeWorkConfig:
        """获取启用的企业微信配置"""
        from apps.organizations.middleware import get_current_organization

        org_id = organization_id or get_current_organization()
        if not org_id:
            raise ValueError("无法确定组织")

        try:
            return self.model_class.objects.get(
                organization_id=org_id,
                is_enabled=True
            )
        except WeWorkConfig.DoesNotExist:
            raise ValueError("企业微信未配置或未启用")

    def get_config_by_corp_id(self, corp_id: str) -> Optional[WeWorkConfig]:
        """根据企业ID获取配置"""
        try:
            return self.model_class.objects.get(corp_id=corp_id)
        except WeWorkConfig.DoesNotExist:
            return None


class UserMappingService(BaseCRUDService):
    """用户映射服务 - 继承 BaseCRUDService"""

    def __init__(self):
        super().__init__(UserMapping)

    def get_by_platform_userid(self, platform: str, platform_userid: str) -> Optional[UserMapping]:
        """根据平台用户ID获取映射"""
        try:
            return self.model_class.objects.get(
                platform=platform,
                platform_userid=platform_userid
            )
        except UserMapping.DoesNotExist:
            return None

    def get_user_mappings(self, user_id: str) -> Dict[str, UserMapping]:
        """获取用户的所有平台映射"""
        mappings = self.model_class.objects.filter(system_user_id=user_id)
        return {m.platform: m for m in mappings}

    def create_or_update_mapping(
        self,
        user: User,
        platform: str,
        platform_userid: str,
        platform_name: str = None,
        platform_unionid: str = None,
        extra_data: dict = None
    ) -> UserMapping:
        """创建或更新用户映射"""
        mapping, created = self.model_class.objects.update_or_create(
            system_user=user,
            platform=platform,
            defaults={
                'platform_userid': platform_userid,
                'platform_unionid': platform_unionid or '',
                'platform_name': platform_name or '',
                'extra_data': extra_data or {}
            }
        )
        return mapping


class WeWorkSSOService(SSOService):
    """企业微信SSO服务"""

    def __init__(self):
        self.config_service = WeWorkConfigService()
        self.mapping_service = UserMappingService()

    def get_config(self, organization_id: int = None) -> WeWorkConfig:
        """获取企业微信配置"""
        return self.config_service.get_enabled_config(organization_id)

    def get_auth_url(self, redirect_uri: str, organization_id: int = None) -> str:
        """获取授权URL"""
        config = self.get_config(organization_id)
        state = self.create_oauth_state('wework')

        from apps.sso.adapters.wework_adapter import WeWorkAdapter
        adapter = WeWorkAdapter(config)
        return adapter.get_oauth_url(redirect_uri, state)

    def get_qr_connect_url(self, redirect_uri: str, organization_id: int = None) -> str:
        """获取扫码登录URL"""
        config = self.get_config(organization_id)
        state = self.create_oauth_state('wework')

        from apps.sso.adapters.wework_adapter import WeWorkAdapter
        adapter = WeWorkAdapter(config)
        return adapter.get_qr_connect_url(redirect_uri, state)

    def handle_callback(self, code: str, state: str) -> dict:
        """
        处理OAuth回调

        Returns:
            包含token和用户信息的字典
        """
        # 验证state
        session_data = self.validate_and_consume_state(state, 'wework')
        if session_data is None:
            raise ValueError("无效的state参数")

        # 获取配置
        config = self.get_config()

        # 获取企业微信用户信息
        from apps.sso.adapters.wework_adapter import WeWorkAdapter
        adapter = WeWorkAdapter(config)
        user_info = adapter.get_user_info_by_code(code)

        # 查找或创建系统用户
        user = self.get_or_create_user(user_info, config)

        # 生成JWT token
        token = generate_jwt_token(user)

        return {
            'token': token,
            'user': {
                'id': str(user.id),
                'username': user.username,
                'real_name': user.real_name,
                'email': user.email,
                'mobile': user.mobile,
                'avatar': user.avatar,
                'department_id': str(user.department_id) if user.department_id else None,
                'organization_id': str(user.organization_id) if user.organization_id else None,
                'roles': list(user.roles.values_list('code', flat=True))
            }
        }

    def get_or_create_user(self, user_info: dict, config: WeWorkConfig) -> User:
        """
        根据企业微信用户信息查找或创建用户

        Args:
            user_info: 企业微信用户信息
            config: 企业微信配置

        Returns:
            User对象
        """
        # 查找已有映射
        mapping = self.mapping_service.get_by_platform_userid(
            'wework',
            user_info['userid']
        )

        if mapping:
            user = mapping.system_user
            # 更新用户信息
            self._update_user_info(user, user_info)
            return user

        # 创建新用户
        if not config.auto_create_user:
            raise ValueError("系统未开启自动创建用户，请联系管理员")

        return self._create_user(user_info, config)

    def _create_user(self, user_info: dict, config: WeWorkConfig) -> User:
        """创建新用户"""
        username = f"ww_{user_info['userid']}"

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            username = f"ww_{user_info['userid']}_{secrets.token_hex(4)}"

        # 获取主部门
        department_id = None
        if user_info.get('main_department'):
            from apps.organizations.models import Department
            try:
                department = Department.objects.get(
                    wework_dept_id=user_info['main_department'],
                    organization=config.organization
                )
                department_id = department.id
            except Department.DoesNotExist:
                pass

        user = User.objects.create(
            username=username,
            real_name=user_info['name'],
            email=user_info.get('email', ''),
            mobile=user_info.get('mobile', ''),
            avatar=user_info.get('avatar', ''),
            organization=config.organization,
            department_id=department_id,
            is_active=True,
            is_staff=False,
            is_superuser=False
        )

        # 设置默认角色
        if config.default_role_id:
            from apps.accounts.models import Role
            try:
                role = Role.objects.get(id=config.default_role_id)
                user.roles.add(role)
            except Role.DoesNotExist:
                pass

        # 创建映射关系
        self.mapping_service.create_or_update_mapping(
            user=user,
            platform='wework',
            platform_userid=user_info['userid'],
            platform_name=user_info['name']
        )

        return user

    def _update_user_info(self, user: User, user_info: dict):
        """更新用户信息"""
        user.real_name = user_info['name']
        if user_info.get('email'):
            user.email = user_info['email']
        if user_info.get('mobile'):
            user.mobile = user_info['mobile']
        if user_info.get('avatar'):
            user.avatar = user_info['avatar']
        user.save(update_fields=['real_name', 'email', 'mobile', 'avatar'])

        # 更新映射
        self.mapping_service.create_or_update_mapping(
            user=user,
            platform='wework',
            platform_userid=user_info['userid'],
            platform_name=user_info['name']
        )
```

---

## API视图

### 1. 企业微信配置管理ViewSet

```python
# apps/sso/views/wework_views.py

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.sso.models import WeWorkConfig, UserMapping
from apps.sso.serializers.wework_serializer import (
    WeWorkConfigSerializer,
    WeWorkConfigDetailSerializer,
    UserMappingSerializer
)
from apps.sso.services.sso_service import WeWorkSSOService


class WeWorkConfigViewSet(BaseModelViewSetWithBatch):
    """企业微信配置管理 ViewSet"""

    queryset = WeWorkConfig.objects.all()
    serializer_class = WeWorkConfigDetailSerializer
    # 自动获得：组织隔离、软删除、批量操作

    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'list':
            return WeWorkConfigSerializer
        return WeWorkConfigDetailSerializer

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public_config(self, request):
        """获取企业微信公开配置（用于前端登录）"""
        try:
            sso_service = WeWorkSSOService()
            config = sso_service.get_config()
            return Response({
                'enabled': True,
                'corp_name': config.corp_name,
                'agent_id': config.agent_id
            })
        except ValueError:
            return Response({
                'enabled': False,
                'message': '企业微信未配置或未启用'
            })

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def auth_url(self, request):
        """获取企业微信授权URL（网页内跳转）"""
        redirect_uri = request.build_absolute_uri('/sso/wework/callback/')

        try:
            sso_service = WeWorkSSOService()
            auth_url = sso_service.get_auth_url(redirect_uri)
            return Response({'auth_url': auth_url})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def qr_url(self, request):
        """获取企业微信扫码登录URL"""
        redirect_uri = request.build_absolute_uri('/sso/wework/callback/')

        try:
            sso_service = WeWorkSSOService()
            qr_url = sso_service.get_qr_connect_url(redirect_uri)
            return Response({'qr_url': qr_url})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def callback(self, request):
        """处理企业微信OAuth回调"""
        code = request.data.get('code')
        state = request.data.get('state')

        if not code or not state:
            return Response({'error': '缺少必要参数'}, status=400)

        try:
            sso_service = WeWorkSSOService()
            result = sso_service.handle_callback(code, state)
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': f'登录失败: {str(e)}'}, status=500)


class UserMappingViewSet(BaseModelViewSetWithBatch):
    """用户平台映射管理 ViewSet"""

    queryset = UserMapping.objects.all()
    serializer_class = UserMappingSerializer
    # 自动获得：组织隔离、软删除、批量操作

    def get_queryset(self):
        """只返回当前用户的映射关系"""
        queryset = super().get_queryset()
        if self.request.user:
            return queryset.filter(system_user=self.request.user)
        return queryset.none()

    @action(detail=False, methods=['post'])
    def bind_wework(self, request):
        """绑定企业微信账号"""
        from apps.sso.adapters.wework_adapter import WeWorkAdapter

        user = request.user
        sso_service = WeWorkSSOService()
        config = sso_service.get_config()
        adapter = WeWorkAdapter(config)

        # 通过用户输入的userid或手机号绑定
        wework_userid = request.data.get('wework_userid')
        mobile = request.data.get('mobile')

        try:
            if wework_userid:
                user_info = adapter.get_user_detail(wework_userid)
            elif mobile:
                # 通过手机号查找用户
                user_list = adapter.get_user_list()
                found = None
                for u in user_list:
                    if u.get('mobile') == mobile:
                        found = u
                        break
                if not found:
                    return Response({'error': '未找到对应的企业微信账号'}, status=404)
                user_info = found
            else:
                return Response({'error': '请提供企业微信userid或手机号'}, status=400)

            # 使用映射服务创建绑定
            sso_service.mapping_service.create_or_update_mapping(
                user=user,
                platform='wework',
                platform_userid=user_info['userid'],
                platform_name=user_info['name']
            )

            return Response({'message': '绑定成功'})

        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['delete'])
    def unbind(self, request, pk=None):
        """解绑指定平台的账号"""
        instance = self.get_object()
        instance.soft_delete()
        return Response({'message': '解绑成功'})

    @action(detail=False, methods=['get'])
    def my_mappings(self, request):
        """获取当前用户的所有平台映射"""
        if not request.user:
            return Response({'error': '未登录'}, status=401)

        sso_service = WeWorkSSOService()
        mappings = sso_service.mapping_service.get_user_mappings(str(request.user.id))

        serializer = self.get_serializer(mappings.values(), many=True)
        return Response(serializer.data)
```

---

## 路由配置

```python
# apps/sso/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sso.views.wework_views import WeWorkConfigViewSet, UserMappingViewSet

app_name = 'sso'

router = DefaultRouter()
# 企业微信配置管理（完整CRUD + 批量操作）
router.register(r'configs', WeWorkConfigViewSet, basename='wework_config')
# 用户映射管理（完整CRUD + 批量操作）
router.register(r'mappings', UserMappingViewSet, basename='user_mapping')

urlpatterns = [
    path('', include(router.urls)),
]
```

### 新的API端点列表

#### 企业微信配置管理
- `GET /api/sso/configs/` - 获取配置列表
- `POST /api/sso/configs/` - 创建配置
- `GET /api/sso/configs/{id}/` - 获取配置详情
- `PUT /api/sso/configs/{id}/` - 更新配置
- `DELETE /api/sso/configs/{id}/` - 删除配置
- `POST /api/sso/configs/batch-delete/` - 批量删除
- `POST /api/sso/configs/batch-restore/` - 批量恢复
- `GET /api/sso/configs/deleted/` - 获取已删除列表
- `POST /api/sso/configs/{id}/restore/` - 恢复单条记录

#### 企业微信登录相关
- `GET /api/sso/configs/public_config/` - 获取公开配置（无需登录）
- `GET /api/sso/configs/auth_url/` - 获取授权URL（无需登录）
- `GET /api/sso/configs/qr_url/` - 获取扫码登录URL（无需登录）
- `POST /api/sso/configs/callback/` - OAuth回调处理（无需登录）

#### 用户映射管理
- `GET /api/sso/mappings/` - 获取当前用户的映射列表
- `POST /api/sso/mappings/bind_wework/` - 绑定企业微信账号
- `DELETE /api/sso/mappings/{id}/unbind/` - 解绑账号
- `GET /api/sso/mappings/my_mappings/` - 获取当前用户的所有平台映射
- `POST /api/sso/mappings/batch-delete/` - 批量删除映射

---

## 过滤器实现

### 1. 企业微信配置过滤器

```python
# apps/sso/filters/wework_filter.py

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.sso.models import WeWorkConfig, UserMapping


class WeWorkConfigFilter(BaseModelFilter):
    """企业微信配置过滤器 - 继承 BaseModelFilter"""

    # 自动继承 BaseModelFilter 的公共字段：
    # - created_at, created_at_from, created_at_to
    # - updated_at_from, updated_at_to
    # - created_by, is_deleted

    # 额外业务字段过滤
    corp_name = filters.CharFilter(lookup_expr='icontains', label='企业名称')
    corp_id = filters.CharFilter(lookup_expr='exact', label='企业ID')
    is_enabled = filters.BooleanFilter(label='是否启用')
    sync_department = filters.BooleanFilter(label='同步部门')
    sync_user = filters.BooleanFilter(label='同步用户')
    auto_create_user = filters.BooleanFilter(label='自动创建用户')

    class Meta(BaseModelFilter.Meta):
        model = WeWorkConfig
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'corp_name', 'corp_id', 'is_enabled',
            'sync_department', 'sync_user', 'auto_create_user'
        ]


class UserMappingFilter(BaseModelFilter):
    """用户映射过滤器 - 继承 BaseModelFilter"""

    # 自动继承 BaseModelFilter 的公共字段

    # 业务字段过滤
    platform = filters.ChoiceFilter(
        choices=UserMapping.PLATFORM_CHOICES,
        label='平台类型'
    )
    platform_name = filters.CharFilter(lookup_expr='icontains', label='平台名称')
    platform_userid = filters.CharFilter(lookup_expr='exact', label='平台用户ID')
    system_user = filters.UUIDFilter(field_name='system_user_id', label='系统用户')

    class Meta(BaseModelFilter.Meta):
        model = UserMapping
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'platform', 'platform_name', 'platform_userid', 'system_user'
        ]
```

---

## 完整集成示例

### 在ViewSet中使用过滤器

```python
# apps/sso/views/wework_views.py

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from apps.sso.filters.wework_filter import WeWorkConfigFilter, UserMappingFilter


class WeWorkConfigViewSet(BaseModelViewSetWithBatch):
    """企业微信配置管理 ViewSet"""

    queryset = WeWorkConfig.objects.all()
    serializer_class = WeWorkConfigDetailSerializer
    # 添加过滤器支持
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WeWorkConfigFilter
    search_fields = ['corp_name', 'corp_id']
    ordering_fields = ['created_at', 'corp_name']
    ordering = ['-created_at']

    # ... 其他方法


class UserMappingViewSet(BaseModelViewSetWithBatch):
    """用户平台映射管理 ViewSet"""

    queryset = UserMapping.objects.all()
    serializer_class = UserMappingSerializer
    # 添加过滤器支持
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserMappingFilter
    search_fields = ['platform_name', 'platform_userid']
    ordering_fields = ['created_at', 'platform']
    ordering = ['-created_at']

    # ... 其他方法
```

### 使用示例

```python
# 示例1: 查询启用的企业微信配置
GET /api/sso/configs/?is_enabled=true

# 示例2: 按创建时间范围查询
GET /api/sso/configs/?created_at_from=2024-01-01&created_at_to=2024-12-31

# 示例3: 搜索企业名称
GET /api/sso/configs/?search=某某公司

# 示例4: 查询当前用户的企业微信映射
GET /api/sso/mappings/?platform=wework

# 示例5: 组合查询
GET /api/sso/mappings/?platform=wework&search=张三
```

---

## 数据库迁移

```bash
# 生成迁移文件
python manage.py makemigrations sso

# 执行迁移
python manage.py migrate
```

---

## JWT Token生成

```python
# apps/accounts/auth.py

import jwt
from datetime import datetime, timedelta
from django.conf import settings

SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', 'your-secret-key')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天


def generate_jwt_token(user) -> str:
    """生成JWT token"""
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'org_id': str(user.organization_id) if user.organization_id else None,
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow(),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_jwt_token(token: str) -> dict:
    """验证JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token已过期')
    except jwt.InvalidTokenError:
        raise ValueError('无效的Token')
```

---

## 迁移指南

### 从旧代码迁移到新基类

#### 1. 序列化器迁移

**旧代码**:
```python
from rest_framework import serializers

class WeWorkConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeWorkConfig
        fields = ['id', 'organization', 'corp_id', 'corp_name', ...]
```

**新代码**:
```python
from apps.common.serializers.base import BaseModelSerializer

class WeWorkConfigSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = WeWorkConfig
        # 自动获得: id, organization, is_deleted, deleted_at,
        #         created_at, updated_at, created_by, custom_fields
        fields = BaseModelSerializer.Meta.fields + [
            'corp_id', 'corp_name', 'agent_id', ...
        ]
```

#### 2. ViewSet 迁移

**旧代码**（函数视图）:
```python
@api_view(['GET'])
def wework_config(request):
    config = WeWorkSSOService.get_config()
    return Response({'corp_name': config.corp_name, ...})
```

**新代码**（ViewSet）:
```python
from apps.common.viewsets.base import BaseModelViewSetWithBatch

class WeWorkConfigViewSet(BaseModelViewSetWithBatch):
    queryset = WeWorkConfig.objects.all()
    serializer_class = WeWorkConfigSerializer
    # 自动获得完整CRUD + 批量操作 + 组织隔离 + 软删除

    @action(detail=False, methods=['get'])
    def public_config(self, request):
        # 自定义业务逻辑
        ...
```

#### 3. Service 迁移

**旧代码**（独立静态方法）:
```python
class WeWorkSSOService:
    @staticmethod
    def get_config(organization_id: int = None) -> WeWorkConfig:
        return WeWorkConfig.objects.get(...)
```

**新代码**（继承BaseCRUDService）:
```python
from apps.common.services.base_crud import BaseCRUDService

class WeWorkConfigService(BaseCRUDService):
    def __init__(self):
        super().__init__(WeWorkConfig)
        # 自动获得: create, update, delete, restore, get, query, paginate

    def get_enabled_config(self, organization_id: int = None) -> WeWorkConfig:
        # 自定义业务方法
        ...
```

#### 4. 过滤器迁移

**旧代码**（手动定义公共字段）:
```python
class WeWorkConfigFilter(filters.FilterSet):
    created_at = filters.DateFromToRangeFilter()
    updated_at_from = filters.DateTimeFilter()
    # ... 需要手动定义所有公共字段

    class Meta:
        model = WeWorkConfig
        fields = ['created_at', 'updated_at_from', ...]
```

**新代码**（继承BaseModelFilter）:
```python
from apps.common.filters.base import BaseModelFilter

class WeWorkConfigFilter(BaseModelFilter):
    # 自动获得所有公共字段过滤
    # - created_at, created_at_from, created_at_to
    # - updated_at_from, updated_at_to
    # - created_by, is_deleted

    # 只需定义业务特定字段
    corp_name = filters.CharFilter(lookup_expr='icontains')

    class Meta(BaseModelFilter.Meta):
        model = WeWorkConfig
        fields = BaseModelFilter.Meta.fields + ['corp_name', ...]
```

### 迁移优势总结

| 方面 | 迁移前 | 迁移后 |
|------|--------|--------|
| **代码行数** | 需要手动实现所有公共功能 | 减少 60-80% 代码量 |
| **序列化器** | 需要手动定义所有公共字段 | 自动继承所有 BaseModel 字段 |
| **ViewSet** | 函数视图，手动实现 CRUD | 自动获得完整 CRUD + 批量操作 |
| **Service** | 静态方法，无统一接口 | 统一的 CRUD 接口，可复用 |
| **过滤器** | 需要重复定义公共字段 | 自动继承公共过滤字段 |
| **组织隔离** | 需要在每个地方手动处理 | 自动应用组织隔离 |
| **软删除** | 需要在每个地方手动处理 | 自动使用软删除 |
| **审计日志** | 需要手动设置创建人/更新人 | 自动记录审计信息 |

---

## 架构优势

### 1. 统一性
所有模块使用相同的基类，代码风格一致，易于理解和维护。

### 2. 可扩展性
基类提供通用功能，子类只需实现业务逻辑，扩展方便。

### 3. 可维护性
公共功能集中在基类中，bug修复和功能升级只需修改基类。

### 4. 标准化
- 统一的响应格式
- 统一的错误处理
- 统一的过滤和排序
- 统一的批量操作接口

### 5. 开发效率
新增模块时，只需定义模型和业务字段，其他功能自动获得。

---

## 边界条件和异常场景测试

### 1. 企业微信适配器异常测试

```python
# tests/test_wework_adapter.py
import pytest
from unittest.mock import Mock, patch
from apps.sso.adapters.wework_adapter import WeWorkAdapter
from apps.sso.models import WeWorkConfig

class WeWorkAdapterTest:
    def setUp(self):
        self.config = Mock(spec=WeWorkConfig)
        self.config.corp_id = "test_corp_id"
        self.config.agent_id = 1000001
        self.config.agent_secret = "test_secret"
        self.adapter = WeWorkAdapter(self.config)

    @patch('requests.get')
    def test_get_access_token_network_error(self, mock_get):
        """测试网络异常处理"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        with pytest.raises(NetworkException) as exc_info:
            self.adapter.get_access_token()

        assert "网络异常" in str(exc_info.value)

    @patch('requests.get')
    def test_get_access_token_api_error(self, mock_get):
        """测试API错误响应"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'errcode': 40001,
            'errmsg': 'corpsecret is invaild'
        }
        mock_get.return_value = mock_response

        with pytest.raises(APIException) as exc_info:
            self.adapter.get_access_token()

        assert "企业微信API调用失败" in str(exc_info.value)

    @patch('requests.get')
    def test_get_access_token_timeout(self, mock_get):
        """测试请求超时"""
        from unittest.mock import patch
        with patch('requests.get', side_effect=requests.exceptions.Timeout()):
            with pytest.raises(NetworkException):
                self.adapter.get_access_token()
```

### 2. SSO服务异常测试

```python
# tests/test_sso_service.py
import pytest
from datetime import timedelta
from django.utils import timezone
from apps.sso.services.sso_service import WeWorkSSOService
from apps.sso.models import OAuthState

class WeWorkSSOServiceTest:
    def setUp(self):
        self.service = WeWorkSSOService()

    def test_invalid_oauth_state(self):
        """测试无效的OAuth状态"""
        # 测试不存在的state
        result = self.service.validate_and_consume_state('invalid_state', 'wework')
        assert result == {}

    def test_expired_oauth_state(self):
        """测试过期的OAuth状态"""
        # 创建已过期的state
        expired_time = timezone.now() - timedelta(minutes=5)
        OAuthState.objects.create(
            state='expired_state',
            platform='wework',
            session_data={'test': 'data'},
            expires_at=expired_time
        )

        result = self.service.validate_and_consume_state('expired_state', 'wework')
        assert result == {}

    def test_concurrent_oauth_state_access(self):
        """测试并发访问同一个state"""
        # 创建有效的state
        OAuthState.objects.create(
            state='concurrent_state',
            platform='wework',
            session_data={'test': 'data'},
            expires_at=timezone.now() + timedelta(minutes=5)
        )

        # 第一次消费
        result1 = self.service.validate_and_consume_state('concurrent_state', 'wework')
        assert result1 == {'test': 'data'}

        # 第二次消费应该返回空
        result2 = self.service.validate_and_consume_state('concurrent_state', 'wework')
        assert result2 == {}

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_user_info_by_code')
    def test_callback_missing_parameters(self, mock_get_user_info):
        """测试回调缺少必要参数"""
        mock_get_user_info.return_value = {
            'userid': 'test_user',
            'name': 'Test User'
        }

        with pytest.raises(ValidationException):
            self.service.handle_callback(code='', state='valid_state')

        with pytest.raises(ValidationException):
            self.service.handle_callback(code='test_code', state='')

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_user_info_by_code')
    def test_callback_invalid_state(self, mock_get_user_info):
        """测试无效的回调state"""
        mock_get_user_info.return_value = {
            'userid': 'test_user',
            'name': 'Test User'
        }

        with pytest.raises(ValidationException) as exc_info:
            self.service.handle_callback(code='test_code', state='invalid_state')

        assert "无效的state参数" in str(exc_info.value)
```

### 3. 用户映射边界测试

```python
# tests/test_user_mapping.py
import pytest
from apps.sso.services.sso_service import UserMappingService
from apps.accounts.models import User

class UserMappingServiceTest:
    def setUp(self):
        self.service = UserMappingService()

    def test_duplicate_platform_userid(self):
        """测试重复的平台用户ID"""
        # 创建第一个映射
        user1 = User.objects.create(username='user1')
        mapping1 = self.service.create_or_update_mapping(
            user=user1,
            platform='wework',
            platform_userid='same_userid',
            platform_name='User 1'
        )

        # 创建第二个映射，应该抛出异常
        user2 = User.objects.create(username='user2')

        with pytest.raises(ValidationException) as exc_info:
            self.service.create_or_update_mapping(
                user=user2,
                platform='wework',
                platform_userid='same_userid',  # 相同的用户ID
                platform_name='User 2'
            )

        assert "平台用户ID已存在" in str(exc_info.value)

    def test_platform_choices_validation(self):
        """测试平台选择验证"""
        user = User.objects.create(username='test_user')

        # 测试无效的平台类型
        with pytest.raises(ValidationException):
            self.service.create_or_update_mapping(
                user=user,
                platform='invalid_platform',  # 无效的平台
                platform_userid='test_userid'
            )

        # 测试有效的平台类型
        for platform in ['wework', 'dingtalk', 'feishu']:
            mapping = self.service.create_or_update_mapping(
                user=user,
                platform=platform,
                platform_userid=f'{platform}_userid'
            )
            assert mapping.platform == platform

    def test_long_platform_userid(self):
        """测试超长平台用户ID"""
        user = User.objects.create(username='test_user')

        # 测试超过限制的用户ID长度
        long_userid = 'a' * 101  # 超过100字符限制

        with pytest.raises(ValidationException) as exc_info:
            self.service.create_or_update_mapping(
                user=user,
                platform='wework',
                platform_userid=long_userid
            )

        assert "平台用户ID长度不能超过100字符" in str(exc_info.value)
```

### 4. 批量操作异常测试

```python
# tests/test_batch_operations.py
import pytest
from django.test import TestCase
from apps.sso.models import WeWorkConfig, UserMapping
from apps.sso.views.wework_views import WeWorkConfigViewSet, UserMappingViewSet
from rest_framework.test import APIClient

class BatchOperationsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.config_viewset = WeWorkConfigViewSet()
        self.mapping_viewset = UserMappingViewSet()

    def test_batch_delete_nonexistent_ids(self):
        """测试批量删除不存在的ID"""
        # 测试不存在的ID列表
        nonexistent_ids = ['00000000-0000-0000-0000-000000000001',
                          '00000000-0000-0000-0000-000000000002']

        # 创建批量删除请求
        response = self.client.post('/api/sso/configs/batch-delete/',
                                  {'ids': nonexistent_ids},
                                  format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['summary']['total'], 2)
        self.assertEqual(data['summary']['succeeded'], 0)
        self.assertEqual(data['summary']['failed'], 2)

    def test_batch_mixed_ids(self):
        """测试批量操作混合有效和无效ID"""
        # 创建一个有效的配置
        config = WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id="test_corp",
            corp_name="Test Corp",
            agent_id=1000001,
            agent_secret="test_secret"
        )

        # 混合ID列表
        mixed_ids = [str(config.id), '00000000-0000-0000-0000-000000000001']

        # 批量删除
        response = self.client.post('/api/sso/configs/batch-delete/',
                                  {'ids': mixed_ids},
                                  format='json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['summary']['total'], 2)
        self.assertEqual(data['summary']['succeeded'], 1)
        self.assertEqual(data['summary']['failed'], 1)

    def test_batch_update_validation(self):
        """测试批量更新数据验证"""
        # 创建批量更新请求，缺少必需字段
        response = self.client.post('/api/sso/configs/batch-update/',
                                  {'ids': ['id1'], 'data': {}},
                                  format='json')

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
```

---

## 测试建议

### 单元测试

```python
# tests/test_sso_services.py

from django.test import TestCase
from apps.sso.services.sso_service import WeWorkConfigService, UserMappingService

class WeWorkConfigServiceTest(TestCase):
    def setUp(self):
        self.service = WeWorkConfigService()

    def test_get_enabled_config(self):
        # 测试获取启用的配置
        config = self.service.get_enabled_config()
        self.assertIsNotNone(config)
        self.assertTrue(config.is_enabled)

    def test_get_config_by_corp_id(self):
        # 测试根据企业ID获取配置
        config = self.service.get_config_by_corp_id('test_corp_id')
        self.assertIsNotNone(config)


class UserMappingServiceTest(TestCase):
    def setUp(self):
        self.service = UserMappingService()

    def test_create_or_update_mapping(self):
        # 测试创建或更新映射
        mapping = self.service.create_or_update_mapping(
            user=self.user,
            platform='wework',
            platform_userid='test_userid',
            platform_name='Test User'
        )
        self.assertEqual(mapping.platform, 'wework')
```

### 集成测试

```python
# tests/test_sso_api.py

from rest_framework.test import APITestCase
from django.urls import reverse

class WeWorkConfigAPITest(APITestCase):
    def test_list_configs(self):
        # 测试获取配置列表
        url = reverse('sso:wework_config-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_batch_delete(self):
        # 测试批量删除
        url = reverse('sso:wework_config-batch-delete')
        data = {'ids': [uuid1, uuid2]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
```

---

## 后续任务

1. **Phase 2.2**: 实现企业微信通讯录同步
   - 部门同步 Service
   - 用户同步 Service
   - 定时任务配置

2. **Phase 2.3**: 集成消息通知功能
   - 企业微信消息推送
   - 系统通知中心
   - 消息模板管理

3. **Phase 2.4**: 其他第三方平台集成
   - 钉钉 SSO
   - 飞书 SSO
   - 统一适配器接口

---

## 参考文档

- **公共基类文档**: `docs/plans/common_base_features/backend.md`
- **Django REST Framework**: https://www.django-rest-framework.org/
- **企业微信API文档**: https://developer.work.weixin.qq.com/document/
- **Django Filters**: https://django-filter.readthedocs.io/

---

## 16. API规范

### 16.1 统一响应格式

#### 成功响应格式
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "uuid",
        "corp_id": "wwa123456789",
        "corp_name": "测试企业",
        "agent_id": 1000001,
        "is_enabled": true,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z",
        "created_by": {
            "id": "uuid",
            "username": "admin",
            "email": "admin@example.com"
        }
    }
}
```

#### 列表响应格式（分页）
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/sso/configs/?page=2",
        "previous": null,
        "results": [
            {
                "id": "uuid",
                "corp_name": "测试企业",
                "agent_id": 1000001,
                "is_enabled": true,
                "created_at": "2024-01-15T10:00:00Z"
            }
        ]
    }
}
```

#### 错误响应格式
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "corp_id": ["该字段不能为空"]
        }
    }
}
```

### 16.2 标准CRUD接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **列表查询** | GET | `/api/sso/configs/` | 分页查询企业微信配置列表，支持过滤和搜索 |
| **详情查询** | GET | `/api/sso/configs/{id}/` | 获取单个企业微信配置详情信息 |
| **创建配置** | POST | `/api/sso/configs/` | 创建新的企业微信配置 |
| **更新配置** | PUT | `/api/sso/configs/{id}/` | 完整更新企业微信配置信息 |
| **部分更新** | PATCH | `/api/sso/configs/{id}/` | 部分更新企业微信配置信息 |
| **删除配置** | DELETE | `/api/sso/configs/{id}/` | 软删除企业微信配置（物理删除禁止） |
| **已删除列表** | GET | `/api/sso/configs/deleted/` | 查询已删除的企业微信配置列表 |
| **恢复配置** | POST | `/api/sso/configs/{id}/restore/` | 恢复已删除的企业微信配置 |

### 16.3 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量删除** | POST | `/api/sso/configs/batch-delete/` | 批量软删除企业微信配置 |
| **批量恢复** | POST | `/api/sso/configs/batch-restore/` | 批量恢复已删除的企业微信配置 |
| **批量更新** | POST | `/api/sso/configs/batch-update/` | 批量更新企业微信配置状态 |

#### 批量删除请求示例
```http
POST /api/sso/configs/batch-delete/
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

#### 批量操作响应格式
```json
{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": true},
        {"id": "uuid3", "success": true}
    ]
}
```

### 16.4 企业微信登录接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **公开配置** | GET | `/api/sso/configs/public_config/` | 获取企业微信公开配置（无需登录） |
| **授权URL** | GET | `/api/sso/configs/auth_url/` | 获取企业微信授权URL（网页内跳转） |
| **扫码URL** | GET | `/api/sso/configs/qr_url/` | 获取企业微信扫码登录URL |
| **OAuth回调** | POST | `/api/sso/configs/callback/` | 处理企业微信OAuth回调 |

#### OAuth回调请求示例
```json
{
    "code": "CODE123",
    "state": "STATE456"
}
```

#### OAuth回调成功响应示例
```json
{
    "success": true,
    "message": "登录成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user": {
            "id": "uuid",
            "username": "ww_user123",
            "real_name": "张三",
            "email": "zhangsan@example.com",
            "mobile": "13800138000",
            "avatar": "https://example.com/avatar.jpg",
            "organization_id": "org_uuid",
            "roles": ["employee"]
        }
    }
}
```

### 16.5 用户映射管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **映射列表** | GET | `/api/sso/mappings/` | 获取当前用户的平台映射列表 |
| **绑定企业微信** | POST | `/api/sso/mappings/bind_wework/` | 绑定企业微信账号 |
| **解绑账号** | DELETE | `/api/sso/mappings/{id}/unbind/` | 解绑指定平台的账号 |
| **我的映射** | GET | `/api/sso/mappings/my_mappings/` | 获取当前用户的所有平台映射 |
| **批量删除** | POST | `/api/sso/mappings/batch-delete/` | 批量删除映射 |

#### 绑定企业微信请求示例
```json
{
    "wework_userid": "USER123",
    "mobile": "13800138000"
}
```

### 16.6 用户映射CRUD接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **列表查询** | GET | `/api/sso/mappings/` | 分页查询用户映射列表，支持过滤和搜索 |
| **详情查询** | GET | `/api/sso/mappings/{id}/` | 获取单个用户映射详情信息 |
| **创建映射** | POST | `/api/sso/mappings/` | 创建新的用户映射 |
| **更新映射** | PUT | `/api/sso/mappings/{id}/` | 完整更新用户映射信息 |
| **部分更新** | PATCH | `/api/sso/mappings/{id}/` | 部分更新用户映射信息 |
| **删除映射** | DELETE | `/api/sso/mappings/{id}/` | 软删除用户映射记录 |
| **已删除列表** | GET | `/api/sso/mappings/deleted/` | 查询已删除的用户映射列表 |
| **恢复映射** | POST | `/api/sso/mappings/{id}/restore/` | 恢复已删除的用户映射 |

### 16.7 用户映射批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量删除** | POST | `/api/sso/mappings/batch-delete/` | 批量软删除用户映射 |
| **批量恢复** | POST | `/api/sso/mappings/batch-restore/` | 批量恢复已删除的用户映射 |
| **批量更新** | POST | `/api/sso/mappings/batch-update/` | 批量更新用户映射状态 |

### 16.8 OAuth状态管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **列表查询** | GET | `/api/sso/oauth-states/` | 分页查询OAuth状态列表 |
| **详情查询** | GET | `/api/sso/oauth-states/{id}/` | 获取单个OAuth状态详情信息 |
| **创建状态** | POST | `/api/sso/oauth-states/` | 创建新的OAuth状态 |
| **更新状态** | PUT | `/api/sso/oauth-states/{id}/` | 完整更新OAuth状态信息 |
| **部分更新** | PATCH | `/api/sso/oauth-states/{id}/` | 部分更新OAuth状态信息 |
| **删除状态** | DELETE | `/api/sso/oauth-states/{id}/` | 软删除OAuth状态记录 |

### 16.9 标准错误码

| 错误码 | HTTP状态 | 描述 |
|--------|----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已被软删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

### 16.10 扩展接口示例

#### 16.10.1 企业微信状态接口
```http
GET /api/sso/wework/status/
```

响应示例：
```json
{
    "success": true,
    "data": {
        "is_configured": true,
        "is_enabled": true,
        "corp_name": "测试企业",
        "agent_id": 1000001,
        "auth_methods": [
            {
                "method": "oauth",
                "name": "OAuth授权",
                "enabled": true
            },
            {
                "method": "qr_code",
                "name": "扫码登录",
                "enabled": true
            }
        ]
    }
}
```

#### 16.10.2 登录统计接口
```http
GET /api/sso/login/stats/
```

响应示例：
```json
{
    "success": true,
    "data": {
        "total_logins": 150,
        "wework_logins": 120,
        "manual_logins": 30,
        "recent_logins": [
            {
                "date": "2024-01-15",
                "count": 5,
                "method": "wework"
            }
        ],
        "user_agents": [
            {
                "browser": "Chrome",
                "count": 80,
                "percentage": 53.3
            },
            {
                "browser": "WeChat",
                "count": 70,
                "percentage": 46.7
            }
        ]
    }
}
```

#### 16.10.3 平台绑定状态接口
```http
GET /api/sso/mapping/status/
```

响应示例：
```json
{
    "success": true,
    "data": {
        "user_id": "uuid",
        "is_bound": {
            "wework": true,
            "dingtalk": false,
            "feishu": false
        },
        "platforms": [
            {
                "code": "wework",
                "name": "企业微信",
                "bound_at": "2024-01-15T10:00:00Z",
                "platform_userid": "USER123",
                "platform_name": "张三"
            }
        ]
    }
}
```

#### 16.10.4 配置验证接口
```http
POST /api/sso/configs/{id}/validate/
```

请求示例：
```json
{
    "test_type": "connectivity"
}
```

响应示例：
```json
{
    "success": true,
    "message": "配置验证成功",
    "data": {
        "test_type": "connectivity",
        "result": {
            "status": "success",
            "access_token_valid": true,
            "agent_info": {
                "agentid": 1000001,
                "name": "测试应用"
            }
        },
        "tested_at": "2024-01-15T10:00:00Z"
    }
}
```

#### 16.10.5 批量绑定接口
```http
POST /api/sso/mappings/batch-bind/
```

请求示例：
```json
{
    "platform": "wework",
    "user_mappings": [
        {
            "platform_userid": "USER123",
            "platform_name": "张三",
            "system_user_id": "uuid1"
        },
        {
            "platform_userid": "USER456",
            "platform_name": "李四",
            "system_user_id": "uuid2"
        }
    ]
}
```

响应示例：
```json
{
    "success": true,
    "message": "批量绑定完成",
    "summary": {
        "total": 2,
        "succeeded": 2,
        "failed": 0
    },
    "results": [
        {"system_user_id": "uuid1", "platform_userid": "USER123", "success": true},
        {"system_user_id": "uuid2", "platform_userid": "USER456", "success": true}
    ]
}
```

---

## API接口规范

### 统一响应格式

本模块遵循GZEAMS统一API响应格式规范。

#### 成功响应


#### 列表响应


#### 错误响应


### 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 验证失败 |
| UNAUTHORIZED | 401 | 未授权 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 不存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 已删除 |
| SERVER_ERROR | 500 | 服务器错误 |

---

## API接口规范

### 统一响应格式

本模块遵循GZEAMS统一API响应格式规范。

#### 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

#### 列表响应
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [...]
    }
}
```

#### 错误响应
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "验证失败",
        "details": {...}
    }
}
```

### 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 验证失败 |
| UNAUTHORIZED | 401 | 未授权 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 不存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 已删除 |
| SERVER_ERROR | 500 | 服务器错误 |