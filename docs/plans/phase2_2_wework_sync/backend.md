# Phase 2.2: 企业微信通讯录同步 - 后端实现

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
- SyncException: 同步过程异常

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

## 模型定义

### 1. 同步日志模型

```python
# apps/sso/models.py

from django.db import models
from apps.common.models import BaseModel


class SyncLog(BaseModel):
    """同步日志记录"""

    class Meta:
        db_table = 'sso_sync_log'
        verbose_name = '同步日志'
        verbose_name_plural = '同步日志'
        ordering = ['-created_at']

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='sync_logs',
        verbose_name='组织'
    )

    sync_type = models.CharField(
        max_length=20,
        choices=[
            ('department', '部门同步'),
            ('user', '用户同步'),
            ('full', '全量同步'),
        ],
        verbose_name='同步类型'
    )

    sync_source = models.CharField(
        max_length=20,
        default='wework',
        verbose_name='同步来源'
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('running', '运行中'),
            ('success', '成功'),
            ('failed', '失败'),
            ('partial', '部分成功'),
        ],
        default='running',
        verbose_name='状态'
    )

    started_at = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')

    # 统计信息
    total_count = models.IntegerField(default=0, verbose_name='总数')
    created_count = models.IntegerField(default=0, verbose_name='新增数量')
    updated_count = models.IntegerField(default=0, verbose_name='更新数量')
    deleted_count = models.IntegerField(default=0, verbose_name='删除数量')
    failed_count = models.IntegerField(default=0, verbose_name='失败数量')

    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    error_details = models.JSONField(default=dict, blank=True, verbose_name='错误详情')

    @property
    def duration(self):
        """计算同步耗时"""
        if self.finished_at:
            delta = self.finished_at - self.started_at
            return int(delta.total_seconds())
        return None

    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.get_status_display()}"
```

### 2. 部门模型扩展

```python
# apps/organizations/models.py

class Department(BaseModel):
    """部门模型 - 添加企业微信字段"""

    # ... 原有字段 ...

    # 企业微信关联字段
    wework_dept_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='企业微信部门ID'
    )

    wework_parent_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='企业微信父部门ID'
    )
```

---

## 企业微信适配器扩展

### 同步相关API方法

```python
# apps/sso/adapters/wework_adapter.py

import requests
from typing import List, Dict, Optional
from django.conf import settings


class WeWorkAdapter:
    """企业微信API适配器 - 同步方法扩展"""

    API_BASE = "https://qyapi.weixin.qq.com/cgi-bin"

    def __init__(self, config):
        self.config = config
        self._access_token = None
        self._token_expires_at = None

    def get_department_list(self, id: Optional[int] = None) -> List[Dict]:
        """
        获取部门列表

        Args:
            id: 部门ID。获取指定部门及其子部门

        Returns:
            部门列表
        """
        token = self.get_access_token()
        url = f"{self.API_BASE}/department/list"

        params = {
            "access_token": token,
        }

        if id is not None:
            params["id"] = id

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"获取部门列表失败: {data['errmsg']}")

        return data['department']

    def get_department_users(self, department_id: int, fetch_child: bool = False) -> List[Dict]:
        """
        获取部门成员详情

        Args:
            department_id: 部门ID
            fetch_child: 是否递归获取子部门成员

        Returns:
            用户列表
        """
        token = self.get_access_token()
        url = f"{self.API_BASE}/user/list"

        params = {
            "access_token": token,
            "department_id": department_id,
            "fetch_child": 1 if fetch_child else 0
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"获取部门成员失败: {data['errmsg']}")

        return data.get('userlist', [])

    def get_user_info(self, user_id: str) -> Dict:
        """
        获取成员详细信息

        Args:
            user_id: 用户ID

        Returns:
            用户信息
        """
        token = self.get_access_token()
        url = f"{self.API_BASE}/user/get"

        params = {
            "access_token": token,
            "userid": user_id
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"获取用户信息失败: {data['errmsg']}")

        return data

    def batch_get_user_info(self, user_ids: List[str]) -> List[Dict]:
        """
        批量获取成员详细信息

        Args:
            user_ids: 用户ID列表，最多100个

        Returns:
            用户信息列表
        """
        if len(user_ids) > 100:
            raise ValueError("批量获取用户信息每次最多100个")

        token = self.get_access_token()
        url = f"{self.API_BASE}/user/batchget"

        payload = {
            "access_token": token,
            "useridlist": user_ids
        }

        response = requests.post(url, json=payload, timeout=10)
        data = response.json()

        if data['errcode'] != 0:
            raise Exception(f"批量获取用户信息失败: {data['errmsg']}")

        return data.get('userlist', [])

    def get_department_id_by_name(self, name: str, parent_id: int = 1) -> Optional[int]:
        """
        根据名称获取部门ID（模糊匹配）

        Args:
            name: 部门名称
            parent_id: 父部门ID

        Returns:
            部门ID，未找到返回None
        """
        departments = self.get_department_list(parent_id)

        for dept in departments:
            if name in dept['name']:
                return dept['id']

        return None
```

---

## 同步服务

### 核心同步服务（使用 BaseCRUDService）

```python
# apps/sso/services/wework_sync_service.py

import logging
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction

from apps.sso.models import WeWorkConfig, SyncLog, UserMapping
from apps.sso.adapters.wework_adapter import WeWorkAdapter
from apps.organizations.models import Department
from apps.accounts.models import User
from apps.common.context import get_current_organization
from apps.common.services.base_crud import BaseCRUDService

logger = logging.getLogger(__name__)


class WeWorkSyncService:
    """企业微信同步服务 - 使用公共CRUD基类"""

    def __init__(self, config: WeWorkConfig):
        self.config = config
        self.adapter = WeWorkAdapter(config)
        self.organization = config.organization
        self.log: Optional[SyncLog] = None
        self.errors = []

        # 使用 BaseCRUDService 管理 SyncLog
        self.sync_log_service = BaseCRUDService(SyncLog)

    # ==================== 全量同步 ====================

    def full_sync(self) -> SyncLog:
        """
        全量同步（部门 + 用户）

        Returns:
            SyncLog: 同步日志记录
        """
        # 使用 BaseCRUDService 创建同步日志
        self.log = self.sync_log_service.create(
            data={
                'organization': self.organization,
                'sync_type': 'full',
                'sync_source': 'wework',
                'status': 'running'
            }
        )

        logger.info(f"开始全量同步: organization={self.organization.id}")

        try:
            # 1. 同步部门
            dept_stats = self.sync_departments()

            # 2. 同步用户
            user_stats = self.sync_users()

            # 3. 更新部门层级关系
            self._update_department_hierarchy()

            # 4. 使用 BaseCRUDService 更新同步日志
            self.log = self.sync_log_service.update(
                instance_id=self.log.id,
                data={
                    'status': 'success',
                    'total_count': dept_stats['total'] + user_stats['total'],
                    'created_count': dept_stats['created'] + user_stats['created'],
                    'updated_count': dept_stats['updated'] + user_stats['updated'],
                    'deleted_count': dept_stats.get('deleted', 0),
                    'failed_count': len(self.errors),
                    'finished_at': timezone.now()
                }
            )

            logger.info(f"全量同步完成: total={self.log.total_count}, "
                       f"created={self.log.created_count}, updated={self.log.updated_count}")

        except Exception as e:
            logger.error(f"全量同步失败: {str(e)}", exc_info=True)

            # 使用 BaseCRUDService 更新失败状态
            self.sync_log_service.update(
                instance_id=self.log.id,
                data={
                    'status': 'failed',
                    'error_message': str(e),
                    'error_details': {
                        'errors': self.errors[:10]  # 只保留前10个错误
                    },
                    'finished_at': timezone.now()
                }
            )
            raise

        return self.log

    # ==================== 部门同步 ====================

    def sync_departments(self) -> Dict:
        """
        同步部门结构

        Returns:
            统计信息
        """
        logger.info("开始同步部门")

        # 使用 BaseCRUDService 管理部门
        dept_service = BaseCRUDService(Department)

        # 获取企业微信部门列表
        wework_depts = self.adapter.get_department_list()
        stats = {
            'total': len(wework_depts),
            'created': 0,
            'updated': 0,
            'deleted': 0
        }

        # 查询现有部门 - 使用 BaseCRUDService 的 query 方法
        existing_depts = dept_service.query(
            filters={
                'organization': self.organization,
                'wework_dept_id__isnull': False
            }
        )

        # 构建现有部门映射 {wework_id: local_dept}
        dept_map = {
            d.wework_dept_id: d
            for d in existing_depts
        }

        # 记录已处理的部门ID
        processed_ids = set()

        for wework_dept in wework_depts:
            wework_id = str(wework_dept['id'])
            processed_ids.add(wework_id)

            try:
                if wework_id in dept_map:
                    # 更新现有部门 - 使用 BaseCRUDService 的 update 方法
                    dept = dept_map[wework_id]
                    old_name = dept.name

                    dept_service.update(
                        instance_id=dept.id,
                        data={
                            'name': wework_dept['name'],
                            'wework_parent_id': wework_dept.get('parentid'),
                            'order': wework_dept.get('order', 0)
                        }
                    )
                    stats['updated'] += 1

                    logger.debug(f"更新部门: {old_name} -> {wework_dept['name']}")
                else:
                    # 创建新部门 - 使用 BaseCRUDService 的 create 方法
                    dept_service.create(
                        data={
                            'organization': self.organization,
                            'name': wework_dept['name'],
                            'wework_dept_id': wework_id,
                            'wework_parent_id': wework_dept.get('parentid'),
                            'order': wework_dept.get('order', 0),
                            'is_active': True
                        }
                    )
                    stats['created'] += 1

                    logger.debug(f"创建部门: {wework_dept['name']}")

            except Exception as e:
                error_msg = f"同步部门失败 {wework_dept['name']}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)

        logger.info(f"部门同步完成: {stats}")
        return stats

    def _update_department_hierarchy(self):
        """更新部门层级关系（建立父子关联）"""
        # 使用 BaseCRUDService 查询部门
        dept_service = BaseCRUDService(Department)

        depts = dept_service.query(
            filters={
                'organization': self.organization,
                'wework_dept_id__isnull': False
            }
        )

        for dept in depts:
            if dept.wework_parent_id is not None:
                # 使用 BaseCRUDService 查询父部门
                parent_depts = dept_service.query(
                    filters={
                        'organization': self.organization,
                        'wework_dept_id': str(dept.wework_parent_id)
                    }
                )

                parent = parent_depts.first()

                if parent and dept.parent_id != parent.id:
                    dept_service.update(
                        instance_id=dept.id,
                        data={
                            'parent': parent,
                            'path': f"{parent.path}/{dept.code}" if parent.path else f"/{dept.code}"
                        }
                    )

        logger.debug("部门层级关系更新完成")

    # ==================== 用户同步 ====================

    def sync_users(self) -> Dict:
        """
        同步用户信息

        Returns:
            统计信息
        """
        logger.info("开始同步用户")

        # 使用 BaseCRUDService 管理用户
        user_service = BaseCRUDService(User)

        # 获取所有部门
        wework_depts = self.adapter.get_department_list()
        stats = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'deleted': 0
        }

        # 查询现有用户映射
        user_mappings = UserMapping.objects.filter(
            platform='wework',
            system_user__organization=self.organization
        ).select_related('system_user')

        user_map = {
            m.platform_userid: (m.system_user, m)
            for m in user_mappings
        }

        # 记录已处理的用户ID
        processed_user_ids = set()

        for dept in wework_depts:
            try:
                # 获取部门下成员列表
                wework_users = self.adapter.get_department_users(dept['id'])
                stats['total'] += len(wework_users)

                for wework_user in wework_users:
                    user_id = wework_user['userid']
                    processed_user_ids.add(user_id)

                    try:
                        if user_id in user_map:
                            # 更新现有用户 - 使用 BaseCRUDService
                            user, mapping = user_map[user_id]
                            self._update_user_from_wework(user, wework_user, user_service)
                            stats['updated'] += 1
                        else:
                            # 创建新用户 - 使用 BaseCRUDService
                            user = self._create_user_from_wework(wework_user, user_service)
                            stats['created'] += 1

                        # 同步用户部门关系
                        self._sync_user_departments(user, wework_user.get('department', []))

                    except Exception as e:
                        error_msg = f"同步用户失败 {wework_user.get('name', user_id)}: {str(e)}"
                        logger.error(error_msg)
                        self.errors.append(error_msg)

            except Exception as e:
                error_msg = f"获取部门成员失败 {dept.get('name', dept['id'])}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)

        logger.info(f"用户同步完成: {stats}")
        return stats

    def _create_user_from_wework(self, wework_user: Dict, user_service: BaseCRUDService) -> User:
        """从企业微信用户创建系统用户 - 使用 BaseCRUDService"""
        user = user_service.create(
            data={
                'username': f"ww_{wework_user['userid']}",
                'real_name': wework_user['name'],
                'email': wework_user.get('email', ''),
                'mobile': wework_user.get('mobile', ''),
                'organization': self.organization,
                'is_active': True,
                'avatar': wework_user.get('avatar', '')
            }
        )

        # 创建用户映射
        UserMapping.objects.create(
            platform='wework',
            platform_userid=wework_user['userid'],
            platform_name=wework_user['name'],
            system_user=user
        )

        logger.debug(f"创建用户: {user.real_name}")
        return user

    def _update_user_from_wework(self, user: User, wework_user: Dict, user_service: BaseCRUDService):
        """从企业微信用户信息更新系统用户 - 使用 BaseCRUDService"""
        update_data = {}

        if user.real_name != wework_user['name']:
            update_data['real_name'] = wework_user['name']

        email = wework_user.get('email', '')
        if user.email != email and email:
            update_data['email'] = email

        mobile = wework_user.get('mobile', '')
        if user.mobile != mobile and mobile:
            update_data['mobile'] = mobile

        avatar = wework_user.get('avatar', '')
        if user.avatar != avatar and avatar:
            update_data['avatar'] = avatar

        if update_data:
            # 使用 BaseCRUDService 更新用户
            user_service.update(
                instance_id=user.id,
                data=update_data
            )

            # 更新映射中的名称
            UserMapping.objects.filter(
                platform='wework',
                platform_userid=wework_user['userid'],
                system_user=user
            ).update(platform_name=wework_user['name'])

            logger.debug(f"更新用户: {user.real_name}")

    def _sync_user_departments(self, user: User, dept_ids: List[int]):
        """同步用户部门关系"""
        # 清除现有部门关系
        user.departments.clear()

        # 添加新部门关系
        main_dept = None

        for dept_id in dept_ids:
            dept = Department.objects.filter(
                organization=self.organization,
                wework_dept_id=str(dept_id)
            ).first()

            if dept:
                user.departments.add(dept)

                # 企业微信第一个部门为主部门
                if main_dept is None:
                    main_dept = dept

        # 设置主部门
        if main_dept and user.department_id != main_dept.id:
            user.department = main_dept
            user.save(update_fields=['department'])

    # ==================== 增量同步 ====================

    def incremental_sync(self, since: timezone.datetime) -> SyncLog:
        """
        增量同步（仅同步变更的数据）

        Args:
            since: 同步起始时间

        Note:
            企业微信API不直接支持增量查询，
            这里通过全量对比实现增量效果
        """
        # 使用 BaseCRUDService 创建同步日志
        self.log = self.sync_log_service.create(
            data={
                'organization': self.organization,
                'sync_type': 'full',  # 企业微信无真正的增量API
                'sync_source': 'wework',
                'status': 'running'
            }
        )

        logger.info(f"开始增量同步: since={since}")

        try:
            dept_stats = self.sync_departments()
            user_stats = self.sync_users()

            # 使用 BaseCRUDService 更新同步日志
            self.sync_log_service.update(
                instance_id=self.log.id,
                data={
                    'status': 'success',
                    'total_count': dept_stats['total'] + user_stats['total'],
                    'created_count': dept_stats['created'] + user_stats['created'],
                    'updated_count': dept_stats['updated'] + user_stats['updated'],
                    'finished_at': timezone.now()
                }
            )

        except Exception as e:
            logger.error(f"增量同步失败: {str(e)}", exc_info=True)

            # 使用 BaseCRUDService 更新失败状态
            self.sync_log_service.update(
                instance_id=self.log.id,
                data={
                    'status': 'failed',
                    'error_message': str(e),
                    'finished_at': timezone.now()
                }
            )
            raise

        return self.log

    # ==================== 仅同步部门 ====================

    def sync_departments_only(self) -> SyncLog:
        """仅同步部门 - 使用 BaseCRUDService"""
        # 使用 BaseCRUDService 创建同步日志
        self.log = self.sync_log_service.create(
            data={
                'organization': self.organization,
                'sync_type': 'department',
                'sync_source': 'wework',
                'status': 'running'
            }
        )

        try:
            stats = self.sync_departments()
            self._update_department_hierarchy()

            # 使用 BaseCRUDService 更新同步日志
            self.sync_log_service.update(
                instance_id=self.log.id,
                data={
                    'status': 'success',
                    'total_count': stats['total'],
                    'created_count': stats['created'],
                    'updated_count': stats['updated'],
                    'finished_at': timezone.now()
                }
            )

        except Exception as e:
            # 使用 BaseCRUDService 更新失败状态
            self.sync_log_service.update(
                instance_id=self.log.id,
                data={
                    'status': 'failed',
                    'error_message': str(e),
                    'finished_at': timezone.now()
                }
            )
            raise

        return self.log

    # ==================== 仅同步用户 ====================

    def sync_users_only(self) -> SyncLog:
        """仅同步用户 - 使用 BaseCRUDService"""
        # 使用 BaseCRUDService 创建同步日志
        self.log = self.sync_log_service.create(
            data={
                'organization': self.organization,
                'sync_type': 'user',
                'sync_source': 'wework',
                'status': 'running'
            }
        )

        try:
            stats = self.sync_users()

            # 使用 BaseCRUDService 更新同步日志
            self.sync_log_service.update(
                instance_id=self.log.id,
                data={
                    'status': 'success',
                    'total_count': stats['total'],
                    'created_count': stats['created'],
                    'updated_count': stats['updated'],
                    'finished_at': timezone.now()
                }
            )

        except Exception as e:
            # 使用 BaseCRUDService 更新失败状态
            self.sync_log_service.update(
                instance_id=self.log.id,
                data={
                    'status': 'failed',
                    'error_message': str(e),
                    'finished_at': timezone.now()
                }
            )
            raise

        return self.log
```

---

## 过滤器

### 同步日志过滤器（使用 BaseModelFilter）

```python
# apps/sso/filters/sync.py

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.sso.models import SyncLog


class SyncLogFilter(BaseModelFilter):
    """同步日志过滤器 - 继承公共基类"""

    # 业务字段过滤
    sync_type = filters.ChoiceFilter(
        choices=SyncLog.SyncTypeChoices,
        label='同步类型'
    )

    sync_source = filters.ChoiceFilter(
        choices=SyncLog.SourceChoices,
        label='同步来源'
    )

    status = filters.ChoiceFilter(
        choices=SyncLog.StatusChoices,
        label='状态'
    )

    # 时间范围过滤（继承自 BaseModelFilter，但可以扩展）
    started_at = filters.DateFromToRangeFilter(label='同步时间范围')

    # 统计字段过滤
    total_count = filters.NumberFilter(label='总数')
    total_count_gte = filters.NumberFilter(field_name='total_count', lookup_expr='gte', label='总数（最小）')
    total_count_lte = filters.NumberFilter(field_name='total_count', lookup_expr='lte', label='总数（最大）')

    failed_count_gte = filters.NumberFilter(field_name='failed_count', lookup_expr='gte', label='失败数（最小）')

    class Meta(BaseModelFilter.Meta):
        model = SyncLog
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'sync_type', 'sync_source', 'status',
            'started_at', 'total_count', 'total_count_gte', 'total_count_lte',
            'failed_count_gte'
        ]
```

### 使用过滤器

```python
# 在 ViewSet 中应用过滤器

from apps.sso.filters.sync import SyncLogFilter

class SyncViewSet(BaseModelViewSetWithBatch):
    """同步管理API"""

    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    filterset_class = SyncLogFilter  # 应用自定义过滤器

    # 继承自 BaseModelViewSet 的过滤器功能：
    # - 自动支持创建时间范围过滤（created_at, created_at_from, created_at_to）
    # - 自动支持更新时间范围过滤（updated_at_from, updated_at_to）
    # - 自动支持创建人过滤（created_by）
    # - 自动支持软删除状态过滤（is_deleted）
    # - 额外的业务字段过滤（sync_type, status, 等）
```

---

## Celery 异步任务

### 同步任务定义

```python
# apps/sso/tasks.py

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def sync_wework_contacts(self, org_id: int, sync_type: str = 'full'):
    """
    同步企业微信通讯录

    Args:
        org_id: 组织ID
        sync_type: 同步类型 (full/department/user)

    Returns:
        同步日志ID
    """
    from apps.sso.models import WeWorkConfig
    from apps.sso.services.wework_sync_service import WeWorkSyncService

    # 防止重复任务
    lock_key = f"sync_wework_lock_{org_id}"
    if cache.get(lock_key):
        logger.warning(f"同步任务正在执行中: org_id={org_id}")
        return {'status': 'duplicate', 'org_id': org_id}

    try:
        cache.set(lock_key, True, timeout=3600)  # 1小时锁

        config = WeWorkConfig.objects.get(
            organization_id=org_id,
            is_enabled=True
        )

        service = WeWorkSyncService(config)

        if sync_type == 'department':
            log = service.sync_departments_only()
        elif sync_type == 'user':
            log = service.sync_users_only()
        else:
            log = service.full_sync()

        logger.info(f"同步任务完成: org_id={org_id}, log_id={log.id}")

        return {
            'org_id': org_id,
            'sync_log_id': log.id,
            'status': log.status,
            'stats': {
                'total': log.total_count,
                'created': log.created_count,
                'updated': log.updated_count,
                'failed': log.failed_count,
            }
        }

    except WeWorkConfig.DoesNotExist:
        logger.error(f"企业微信配置不存在: org_id={org_id}")
        return {'status': 'not_found', 'org_id': org_id}

    except Exception as exc:
        logger.error(f"同步任务失败: org_id={org_id}, error={str(exc)}", exc_info=True)
        raise

    finally:
        cache.delete(lock_key)


@shared_task
def sync_all_orgs_wework():
    """同步所有启用了企业微信的组织"""
    from apps.sso.models import WeWorkConfig

    configs = WeWorkConfig.objects.filter(is_enabled=True)

    results = []
    for config in configs:
        result = sync_wework_contacts.delay(config.organization_id)
        results.append({
            'org_id': config.organization_id,
            'task_id': result.id
        })

    logger.info(f"已启动 {len(results)} 个组织的同步任务")
    return results


@shared_task
def cleanup_old_sync_logs(days: int = 30):
    """
    清理旧的同步日志

    Args:
        days: 保留天数
    """
    from datetime import timedelta
    from apps.sso.models import SyncLog
    from django.utils import timezone

    cutoff_date = timezone.now() - timedelta(days=days)

    deleted_count = SyncLog.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['success', 'failed']
    ).delete()

    logger.info(f"清理了 {deleted_count} 条旧同步日志")
    return deleted_count
```

### Celery Beat 配置

```python
# backend/config/celery.py

from celery.schedules import crontab

app.conf.beat_schedule = {
    # 每天凌晨2点全量同步
    'sync-wework-contacts-daily': {
        'task': 'apps.sso.tasks.sync_all_orgs_wework',
        'schedule': crontab(hour=2, minute=0),
    },

    # 每小时增量同步（实际是全量，但频率高）
    'sync-wework-contacts-hourly': {
        'task': 'apps.sso.tasks.sync_all_orgs_wework',
        'schedule': crontab(minute=0),
    },

    # 每周清理旧日志
    'cleanup-old-sync-logs': {
        'task': 'apps.sso.tasks.cleanup_old_sync_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
        'args': (30,)  # 保留30天
    },
}
```

---

## 序列化器

```python
# apps/sso/serializers/sync.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.sso.models import SyncLog


class SyncLogSerializer(BaseModelSerializer):
    """同步日志序列化器 - 继承公共基类"""

    # 额外的业务字段
    duration = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)
    sync_source_display = serializers.CharField(source='get_sync_source_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SyncLog
        # 继承公共字段 + 业务字段
        fields = BaseModelSerializer.Meta.fields + [
            'sync_type',
            'sync_type_display',
            'sync_source',
            'sync_source_display',
            'status',
            'status_display',
            'started_at',
            'finished_at',
            'duration',
            'total_count',
            'created_count',
            'updated_count',
            'deleted_count',
            'failed_count',
            'error_message',
            'error_details',
        ]

    def get_duration(self, obj):
        """获取同步耗时（秒）"""
        if obj.finished_at and obj.started_at:
            return int((obj.finished_at - obj.started_at).total_seconds())
        return None


class SyncLogDetailSerializer(BaseModelWithAuditSerializer):
    """同步日志详情序列化器 - 包含完整审计信息"""

    duration = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = SyncLog
        # 继承所有审计字段 + 业务字段
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'sync_type',
            'sync_type_display',
            'sync_source',
            'status',
            'status_display',
            'started_at',
            'finished_at',
            'duration',
            'total_count',
            'created_count',
            'updated_count',
            'deleted_count',
            'failed_count',
            'error_message',
            'error_details',
        ]

    def get_duration(self, obj):
        """获取同步耗时（秒）"""
        if obj.finished_at and obj.started_at:
            return int((obj.finished_at - obj.started_at).total_seconds())
        return None


class SyncStatusSerializer(serializers.Serializer):
    """同步状态响应"""

    status = serializers.CharField()
    last_sync_time = serializers.DateTimeField(allow_null=True)
    stats = serializers.DictField()


class SyncTriggerSerializer(serializers.Serializer):
    """触发同步请求"""

    sync_type = serializers.ChoiceField(
        choices=['full', 'department', 'user'],
        default='full',
        required=False
    )
```

---

## API 视图

```python
# apps/sso/api/sync.py

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.sso.models import SyncLog, WeWorkConfig
from apps.sso.serializers.sync import SyncLogSerializer, SyncLogDetailSerializer
from apps.sso.tasks import sync_wework_contacts
from apps.common.context import get_current_organization
from django.shortcuts import get_object_or_404


class SyncViewSet(BaseModelViewSetWithBatch):
    """同步管理API - 继承公共基类"""

    # 基础配置 - 自动获得组织隔离、软删除、批量操作等功能
    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'retrieve':
            return SyncLogDetailSerializer
        return SyncLogSerializer

    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """
        手动触发同步

        请求体:
            sync_type: full/department/user (可选，默认full)
        """
        from apps.sso.serializers.sync import SyncTriggerSerializer

        serializer = SyncTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sync_type = serializer.validated_data.get('sync_type', 'full')

        config = get_object_or_404(
            WeWorkConfig,
            organization=get_current_organization(),
            is_enabled=True
        )

        # 检查是否有正在运行的任务
        running_log = SyncLog.objects.filter(
            organization=config.organization,
            status='running'
        ).first()

        if running_log:
            return Response({
                'error': '已有同步任务正在运行中',
                'log_id': running_log.id
            }, status=status.HTTP_409_CONFLICT)

        # 异步执行同步
        task = sync_wework_contacts.delay(config.organization_id, sync_type)

        return Response({
            'task_id': task.id,
            'message': '同步任务已启动',
            'sync_type': sync_type
        })

    @action(detail=False, methods=['get'])
    def logs(self, request):
        """
        获取同步日志列表

        注意：此方法继承自 BaseModelViewSet，自动支持：
        - 组织隔离
        - 分页
        - 排序
        - 搜索
        """
        # 基础查询已由 get_queryset() 自动处理
        return super().list(request)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """获取当前同步状态"""
        last_log = SyncLog.objects.filter(
            organization=get_current_organization()
        ).order_by('-created_at').first()

        if not last_log:
            return Response({
                'status': 'never_synced',
                'last_sync_time': None,
                'stats': {}
            })

        return Response({
            'status': last_log.status,
            'last_sync_time': last_log.started_at,
            'stats': {
                'total': last_log.total_count,
                'created': last_log.created_count,
                'updated': last_log.updated_count,
                'deleted': last_log.deleted_count,
                'failed': last_log.failed_count,
            }
        })

    @action(detail=False, methods=['get'])
    def config(self, request):
        """获取同步配置"""
        try:
            config = WeWorkConfig.objects.get(
                organization=get_current_organization(),
                is_enabled=True
            )
            return Response({
                'enabled': True,
                'corp_name': config.corp_name,
                'agent_id': config.agent_id,
                'auto_sync_enabled': True,  # 可扩展为配置项
            })
        except WeWorkConfig.DoesNotExist:
            return Response({
                'enabled': False,
                'message': '企业微信未配置或未启用'
            })

    # 以下批量操作方法由 BaseModelViewSetWithBatch 自动提供：
    # - POST /batch-delete/    批量软删除日志
    # - POST /batch-restore/   批量恢复日志
    # - POST /batch-update/    批量更新日志
    # - GET  /deleted/         查看已删除日志
```

---

## URL 配置

```python
# apps/sso/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.sso.api.sync import SyncViewSet

router = DefaultRouter()
router.register(r'sync', SyncViewSet, basename='sync')

urlpatterns = [
    path('api/sso/', include(router.urls)),
]
```

---

## 更新总结

### 使用公共基类的好处

通过使用新的公共基类，企业微信同步模块获得了以下优势：

#### 1. 序列化器（BaseModelSerializer）
```python
# 旧代码：需要手动定义所有公共字段
class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = ['id', 'organization', 'created_at', ...]  # 冗长

# 新代码：自动继承公共字段
class SyncLogSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = SyncLog
        fields = BaseModelSerializer.Meta.fields + ['sync_type', ...]  # 简洁
```

**优势**：
- 自动处理 BaseModel 的所有公共字段（id, organization, is_deleted, etc.）
- 自动序列化 custom_fields 动态字段
- 统一审计字段输出格式
- 减少代码重复，降低维护成本

#### 2. ViewSet（BaseModelViewSetWithBatch）
```python
# 旧代码：需要手动实现组织隔离、软删除等功能
class SyncViewSet(viewsets.ViewSet):
    def get_queryset(self):
        return SyncLog.objects.filter(organization=...)  # 手动过滤

# 新代码：自动获得所有功能
class SyncViewSet(BaseModelViewSetWithBatch):
    queryset = SyncLog.objects.all()  # 自动组织隔离
```

**优势**：
- 自动应用组织隔离和软删除过滤
- 自动设置审计字段（created_by, updated_by）
- 自动使用软删除而非物理删除
- 免费获得批量操作接口：
  - POST /batch-delete/  批量软删除
  - POST /batch-restore/ 批量恢复
  - POST /batch-update/  批量更新
  - GET /deleted/  查看已删除记录

#### 3. Service（BaseCRUDService）
```python
# 旧代码：直接操作 ORM
SyncLog.objects.create(organization=..., sync_type='full', ...)
log.status = 'success'
log.save()

# 新代码：使用统一的服务接口
log = sync_log_service.create(data={'sync_type': 'full', ...})
log = sync_log_service.update(instance_id=log.id, data={'status': 'success'})
```

**优势**：
- 统一的 CRUD 操作接口
- 自动处理组织隔离和软删除
- 支持复杂查询场景（filters, search, order_by）
- 内置分页支持
- 更易于测试和 Mock

#### 4. 过滤器（BaseModelFilter）
```python
# 旧代码：需要手动定义公共字段过滤
class SyncLogFilter(filters.FilterSet):
    created_at = filters.DateFromToRangeFilter()
    created_by = filters.UUIDFilter()
    # ... 更多重复代码

# 新代码：继承公共过滤字段
class SyncLogFilter(BaseModelFilter):
    sync_type = filters.ChoiceFilter(...)  # 仅定义业务字段
```

**优势**：
- 自动继承公共字段过滤（创建时间、更新时间、创建人、软删除状态）
- 统一的时间范围过滤接口
- 减少重复代码
- 易于扩展业务字段过滤

### 代码行数对比

| 组件 | 旧代码行数 | 新代码行数 | 减少比例 |
|------|-----------|-----------|----------|
| **序列化器** | ~50 行 | ~30 行 | 40% |
| **ViewSet** | ~150 行 | ~80 行 | 47% |
| **Service** | ~200 行 | ~120 行 | 40% |
| **过滤器** | ~40 行 | ~20 行 | 50% |
| **总计** | ~440 行 | ~250 行 | **43%** |

### 功能增强

使用公共基类后，企业微信同步模块自动获得了以下额外功能：

1. **批量操作**：一键批量删除/恢复/更新同步日志
2. **审计追踪**：完整的创建人、更新人信息记录
3. **软删除保护**：防止误删导致的同步数据丢失
4. **高级过滤**：按时间范围、创建人、状态等多维度查询同步记录
5. **统一异常处理**：自动化的错误处理和日志记录
6. **分页支持**：自动分页，无需手动实现

### 迁移建议

如果要将现有的企业微信同步代码迁移到使用公共基类：

1. **逐步迁移**：先迁移序列化器，再迁移 ViewSet，最后迁移 Service
2. **保持兼容**：公共基类向后兼容，不影响现有功能
3. **测试充分**：迁移后务必进行完整的单元测试和集成测试
4. **文档更新**：及时更新 API 文档，反映新的批量操作接口

---

## 边界条件和异常场景测试

### 1. 同步服务异常测试

```python
# tests/test_wework_sync_service.py
import pytest
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from unittest.mock import Mock, patch
from apps.sso.models import WeWorkConfig, SyncLog
from apps.sso.services.wework_sync_service import WeWorkSyncService
from apps.sso.adapters.wework_adapter import WeWorkAdapter

class WeWorkSyncServiceTest(TestCase):
    def setUp(self):
        self.organization = self.create_organization()
        self.config = WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id="test_corp",
            corp_name="Test Corp",
            agent_id=1000001,
            agent_secret="test_secret"
        )
        self.service = WeWorkSyncService(self.config)

    def test_duplicate_sync_running(self):
        """测试同时运行多个同步任务"""
        # 创建一个正在运行的同步日志
        SyncLog.objects.create(
            organization=self.organization,
            sync_type='full',
            status='running'
        )

        # 尝试启动新的同步应该返回None或抛出异常
        result = self.service.full_sync()
        self.assertIsNone(result)

    def test_organization_mismatch(self):
        """测试组织不匹配的情况"""
        # 创建另一个组织的部门
        other_org = self.create_organization(name="Other Org")
        other_dept = self.create_department(
            organization=other_org,
            wework_dept_id="12345"
        )

        # 同步时不应该处理其他组织的数据
        with patch.object(self.service.adapter, 'get_department_list') as mock_get_depts:
            mock_get_depts.return_value = [{
                'id': 1,
                'name': 'Test Dept',
                'parentid': 0,
                'order': 1
            }]

            stats = self.service.sync_departments()

            # 应该只处理当前组织的部门
            self.assertEqual(stats['created'], 1)
            self.assertEqual(stats['updated'], 0)

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_list')
    def test_large_department_tree(self, mock_get_depts):
        """测试处理大量部门的情况"""
        # 模拟企业微信返回大量部门
        large_dept_tree = []
        for i in range(500):  # 500个部门
            large_dept_tree.append({
                'id': i + 1,
                'name': f'部门{i + 1}',
                'parentid': i if i > 0 else 0,
                'order': i
            })
        mock_get_depts.return_value = large_dept_tree

        # 执行同步
        stats = self.service.sync_departments()

        # 验证处理完成
        self.assertEqual(stats['total'], 500)
        self.assertEqual(stats['created'], 500)

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_users')
    def test_department_users_pagination(self, mock_get_users):
        """测试部门用户分页处理"""
        mock_get_users.return_value = [{
            'userid': f'user_{i}',
            'name': f'User {i}',
            'email': f'user{i}@test.com'
        } for i in range(200)]  # 200个用户

        # 执行用户同步
        stats = self.service.sync_users()

        # 验证用户数量
        self.assertEqual(stats['total'], 200)
        self.assertEqual(stats['created'], 200)

    def test_sync_with_invalid_config(self):
        """测试配置异常的情况"""
        # 禁用配置
        self.config.is_enabled = False
        self.config.save()

        # 尝试同步应该抛出异常
        with self.assertRaises(ValueError):
            self.service.full_sync()

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_access_token')
    def test_token_expiration_handling(self, mock_get_token):
        """测试token过期处理"""
        # 模拟token过期
        mock_get_token.side_effect = [
            "valid_token",  # 第一次调用返回有效token
            "expired_token",  # 第二次调用返回过期token
        ]

        # 验证是否正确处理token过期
        with patch('apps.sso.adapters.wework_adapter.requests.get') as mock_request:
            mock_response = Mock()
            mock_response.json.return_value = {
                'errcode': 40014,
                'errmsg': 'access_token expired'
            }
            mock_request.return_value = mock_response

            # 第二次调用应该抛出异常
            with self.assertRaises(Exception):
                self.service.adapter.get_user_info('test_user')

    def test_partial_sync_error_handling(self):
        """测试部分同步失败的处理"""
        # 模拟部门同步成功，用户同步失败
        with patch.object(self.service, 'sync_departments') as mock_sync_depts, \
             patch.object(self.service, 'sync_users') as mock_sync_users:
            mock_sync_depts.return_value = {
                'total': 10,
                'created': 5,
                'updated': 5,
                'deleted': 0
            }
            mock_sync_users.side_effect = Exception("用户同步失败")

            # 验证异常是否被正确处理
            with self.assertRaises(Exception):
                self.service.full_sync()

            # 验证同步日志状态为failed
            self.log = SyncLog.objects.filter(
                organization=self.organization,
                status='failed'
            ).first()
            self.assertIsNotNone(self.log)
            self.assertIn("用户同步失败", self.log.error_message)

    def test_sync_idempotency(self):
        """测试同步的幂等性"""
        # 创建一些已有数据
        dept = self.create_department(
            organization=self.organization,
            wework_dept_id="12345",
            name="Test Dept"
        )

        # 模拟企业微信返回相同的数据
        with patch.object(self.service.adapter, 'get_department_list') as mock_get_depts:
            mock_get_depts.return_value = [{
                'id': 12345,
                'name': 'Test Dept',
                'parentid': 0,
                'order': 1
            }]

            # 执行两次同步
            stats1 = self.service.sync_departments()
            stats2 = self.service.sync_departments()

            # 第一次应该有更新，第二次应该是无变更
            self.assertEqual(stats1['updated'], 1)
            self.assertEqual(stats2['updated'], 0)
            self.assertEqual(stats2['created'], 0)

    def test_concurrent_user_mapping(self):
        """测试并发用户映射处理"""
        from apps.accounts.models import User
        from apps.sso.models import UserMapping

        # 创建测试用户
        user1 = User.objects.create(
            username='test_user',
            organization=self.organization
        )
        user2 = User.objects.create(
            username='test_user_2',
            organization=self.organization
        )

        # 创建相同的平台用户映射
        UserMapping.objects.create(
            platform='wework',
            platform_userid='same_userid',
            system_user=user1
        )

        # 尝试为user2创建相同的映射应该抛出异常
        with self.assertRaises(Exception):
            UserMapping.objects.create(
                platform='wework',
                platform_userid='same_userid',
                system_user=user2
            )

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.batch_get_user_info')
    def test_batch_user_info_limit(self, mock_batch_get):
        """测试批量获取用户信息限制"""
        # 尝试获取超过100个用户
        user_ids = [f'user_{i}' for i in range(101)]

        # 验证是否抛出正确异常
        with self.assertRaises(ValueError) as exc_info:
            self.service.adapter.batch_get_user_info(user_ids)

        assert "批量获取用户信息每次最多100个" in str(exc_info.value)
```

### 2. Celery 任务异常测试

```python
# tests/test_wework_tasks.py
import pytest
from unittest.mock import Mock, patch
from celery.exceptions import Retry
from apps.sso.tasks import sync_wework_contacts, cleanup_old_sync_logs
from apps.sso.models import WeWorkConfig, SyncLog

class WeWorkTasksTest:
    def setUp(self):
        self.organization = self.create_organization()
        self.config = WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id="test_corp",
            corp_name="Test Corp",
            agent_id=1000001,
            agent_secret="test_secret"
        )

    @patch('apps.sso.tasks.cache')
    def test_duplicate_task_prevention(self, mock_cache):
        """测试重复任务防止机制"""
        # 模拟已有任务在运行
        mock_cache.get.return_value = True

        result = sync_wework_contacts(self.organization.id)

        # 验证返回duplicate状态
        self.assertEqual(result['status'], 'duplicate')
        self.assertEqual(result['org_id'], self.organization.id)

    @patch('apps.sso.tasks.WeWorkSyncService')
    def task_retry_mechanism(self, mock_sync_service):
        """测试任务重试机制"""
        # 模拟服务初始化失败
        mock_sync_service.side_effect = Exception("Service initialization failed")

        # 验证是否触发重试
        with pytest.raises(Retry):
            sync_wework_contacts(self.organization.id)

    @patch('apps.sso.tasks.SyncLog')
    def test_task_lock_release(self, mock_sync_log):
        """测试任务锁释放"""
        from django.core.cache import cache

        # 模拟任务正常执行
        with patch('apps.sso.tasks.cache.get', return_value=False):
            with patch('apps.sso.tasks.cache.set'):
                result = sync_wework_contacts(self.organization.id)
                self.assertEqual(result['status'], 'success')

        # 验证锁被正确释放
        mock_cache_delete = cache.delete
        mock_cache_delete.assert_called_once()

    def test_cleanup_old_sync_logs(self):
        """测试清理旧同步日志"""
        # 创建不同状态的日志
        SyncLog.objects.create(
            organization=self.organization,
            sync_type='full',
            status='success',
            created_at=timezone.now() - timedelta(days=35)  # 35天前
        )
        SyncLog.objects.create(
            organization=self.organization,
            sync_type='full',
            status='failed',
            created_at=timezone.now() - timedelta(days=35)  # 35天前
        )
        SyncLog.objects.create(
            organization=self.organization,
            sync_type='full',
            status='success',
            created_at=timezone.now() - timedelta(days=25)  # 25天前
        )

        # 执行清理任务
        result = cleanup_old_sync_logs(30)

        # 验证只删除了30天前的日志
        self.assertEqual(result, 2)

        # 验证25天前的日志仍然存在
        remaining_logs = SyncLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        self.assertEqual(remaining_logs.count(), 1)

### 3. API 异常测试

```python
# tests/test_sync_api.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

class SyncAPITest:
    def setUp(self):
        self.client = APIClient()
        self.organization = self.create_organization()
        self.config = WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id="test_corp",
            corp_name="Test Corp",
            agent_id=1000001,
            agent_secret="test_secret"
        )

    def test_trigger_sync_without_auth(self):
        """测试未认证用户触发同步"""
        response = self.client.post('/api/sso/sync/trigger/')

        self.assertEqual(response.status_code, 401)
        self.assertIn('Authentication credentials', response.data['detail'])

    @patch('apps.sso.services.wework_sync_service.WeWorkSyncService')
    def test_concurrent_sync_trigger(self, mock_sync_service):
        """测试并发触发同步"""
        # 模拟已有同步任务在运行
        mock_service = Mock()
        mock_service.full_sync.return_value = None
        mock_sync_service.return_value = mock_service

        # 创建一个运行的日志
        from apps.sso.models import SyncLog
        SyncLog.objects.create(
            organization=self.organization,
            sync_type='full',
            status='running'
        )

        # 尝试触发同步
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/sso/sync/trigger/')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('同步任务正在运行中', response.data['error'])

    def test_invalid_sync_type(self):
        """测试无效的同步类型"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/sso/sync/trigger/', {
            'sync_type': 'invalid_type'
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('invalid_type', response.data['sync_type'])

    def test_sync_status_endpoint(self):
        """测试同步状态端点"""
        # 测试从未同步的状态
        response = self.client.get('/api/sso/sync/status/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'never_synced')
        self.assertIsNone(response.data['last_sync_time'])

        # 创建一个已完成的同步日志
        from apps.sso.models import SyncLog
        SyncLog.objects.create(
            organization=self.organization,
            sync_type='full',
            status='success',
            started_at=timezone.now() - timedelta(hours=1),
            total_count=100,
            created_count=50
        )

        response = self.client.get('/api/sso/sync/status/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertIsNotNone(response.data['last_sync_time'])

    def test_config_endpoint_without_wework(self):
        """测试未配置企业微信的情况"""
        # 禁用配置
        self.config.is_enabled = False
        self.config.save()

        response = self.client.get('/api/sso/sync/config/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['enabled'])
        self.assertIn('未配置', response.data['message'])

    @patch('apps.sso.services.wework_sync_service.WeWorkSyncService')
    def test_sync_statistics_accuracy(self, mock_sync_service):
        """测试同步统计准确性"""
        # 模拟返回统计信息
        mock_service = Mock()
        mock_service.full_sync.return_value = Mock(
            total_count=100,
            created_count=50,
            updated_count=30,
            deleted_count=5,
            failed_count=0
        )
        mock_sync_service.return_value = mock_service

        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/sso/sync/trigger/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('task_id', response.data)
        self.assertEqual(response.data['sync_type'], 'full')
```

---

## 17. API 规范

### 17.1 统一响应格式

#### 成功响应格式
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "sync_type": "full",
        "sync_source": "wework",
        "status": "success",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:35:00Z",
        "created_by": "550e8400-e29b-41d4-a716-446655440000",
        "organization": "550e8400-e29b-41d4-a716-446655440000",
        "started_at": "2024-01-15T10:30:00Z",
        "finished_at": "2024-01-15T10:35:00Z",
        "total_count": 100,
        "created_count": 50,
        "updated_count": 30,
        "deleted_count": 5,
        "failed_count": 0
    }
}
```

#### 列表响应格式（分页）
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/sso/sync/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "sync_type": "full",
                "sync_source": "wework",
                "status": "success",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z",
                "created_by": "550e8400-e29b-41d4-a716-446655440000",
                "organization": "550e8400-e29b-41d4-a716-446655440000"
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
            "sync_type": ["该字段不能为空"]
        }
    }
}
```

### 17.2 标准CRUD接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **同步日志列表** | GET | `/api/sso/sync/` | 分页查询同步日志，支持过滤和搜索 |
| **同步日志详情** | GET | `/api/sso/sync/{id}/` | 获取单个同步日志详情信息 |
| **创建同步日志** | POST | `/api/sso/sync/` | 创建新的同步日志 |
| **更新同步日志** | PUT | `/api/sso/sync/{id}/` | 完整更新同步日志信息 |
| **部分更新同步日志** | PATCH | `/api/sso/sync/{id}/` | 部分更新同步日志信息 |
| **软删除同步日志** | DELETE | `/api/sso/sync/{id}/` | 软删除同步日志（标记为已删除） |
| **同步日志列表（已删除）** | GET | `/api/sso/sync/deleted/` | 查看已删除的同步日志列表 |
| **恢复同步日志** | POST | `/api/sso/sync/{id}/restore/` | 恢复已删除的同步日志 |

### 17.3 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量软删除同步日志** | POST | `/api/sso/sync/batch-delete/` | 批量软删除同步日志 |
| **批量恢复同步日志** | POST | `/api/sso/sync/batch-restore/` | 批量恢复已删除的同步日志 |
| **批量更新同步日志** | POST | `/api/sso/sync/batch-update/` | 批量更新同步日志信息 |

#### 批量删除请求示例
```http
POST /api/sso/sync/batch-delete/
{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

#### 批量更新请求示例
```http
POST /api/sso/sync/batch-update/
{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ],
    "data": {
        "status": "failed",
        "error_message": "同步失败"
    }
}
```

### 17.4 企业微信同步管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **触发手动同步** | POST | `/api/sso/sync/trigger/` | 手动触发企业微信通讯录同步 |
| **同步状态查询** | GET | `/api/sso/sync/status/` | 获取当前同步状态和统计信息 |
| **同步日志查询** | GET | `/api/sso/sync/logs/` | 查询同步日志（继承列表接口） |
| **同步配置查询** | GET | `/api/sso/sync/config/` | 获取企业微信同步配置信息 |
| **部门同步** | POST | `/api/sso/sync/departments/` | 仅同步部门结构 |
| **用户同步** | POST | `/api/sso/sync/users/` | 仅同步用户信息 |

#### 触发同步请求示例
```http
POST /api/sso/sync/trigger/
Content-Type: application/json

{
    "sync_type": "full"
}
```

#### 触发同步响应示例
```json
{
    "success": true,
    "message": "同步任务已启动",
    "data": {
        "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "sync_type": "full"
    }
}
```

### 17.5 部门管理接口（扩展）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **部门列表** | GET | `/api/organizations/departments/` | 获取组织部门树 |
| **部门详情** | GET | `/api/organizations/departments/{id}/` | 获取单个部门详情 |
| **创建部门** | POST | `/api/organizations/departments/` | 创建新部门 |
| **更新部门** | PUT | `/api/organizations/departments/{id}/` | 更新部门信息 |
| **软删除部门** | DELETE | `/api/organizations/departments/{id}/` | 软删除部门 |

### 17.6 标准错误码

| 错误码 | HTTP状态 | 描述 |
|--------|----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未认证访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不被允许 |
| `CONFLICT` | 409 | 资源冲突（如已有同步任务在运行） |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已被软删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

### 17.7 扩展接口示例

#### 17.7.1 同步任务状态轮询
```python
# 客户端轮询示例
import requests
import time

# 1. 触发同步
response = requests.post('/api/sso/sync/trigger/',
                        json={'sync_type': 'full'},
                        headers={'Authorization': 'Bearer token'})
task_id = response.json()['data']['task_id']

# 2. 轮询状态
while True:
    status_response = requests.get('/api/sso/sync/status/',
                                 headers={'Authorization': 'Bearer token'})
    status = status_response.json()['data']['status']

    if status in ['success', 'failed']:
        break
    time.sleep(5)
```

#### 17.7.2 大批量同步处理
```python
# 分页处理大量同步日志的示例
def batch_process_sync_logs(sync_service, log_ids, batch_size=100):
    """分批处理同步日志"""
    for i in range(0, len(log_ids), batch_size):
        batch = log_ids[i:i + batch_size]
        # 使用批量更新接口
        sync_service.batch_update(
            instance_ids=batch,
            data={'processed': True}
        )
        # 避免服务器压力
        time.sleep(1)
```

#### 17.7.3 同步数据验证
```python
# 验证同步数据完整性的示例
def validate_sync_integrity(sync_log):
    """验证同步数据完整性"""
    expected_total = sync_log.total_count
    actual_sum = (sync_log.created_count +
                 sync_log.updated_count +
                 sync_log.deleted_count +
                 sync_log.failed_count)

    if expected_total != actual_sum:
        raise Exception(
            f"同步数据不一致：期望{expected_total}，"
            f"实际{actual_sum}"
        )
```

#### 17.7.4 企业微信适配器使用示例
```python
# 使用企业微信适配器的示例
from apps.sso.adapters.wework_adapter import WeWorkAdapter

# 初始化适配器
config = get_wework_config()
adapter = WeWorkAdapter(config)

# 获取部门列表
departments = adapter.get_department_list()

# 获取部门成员
users = adapter.get_department_users(dept_id=123, fetch_child=True)

# 批量获取用户信息
user_details = adapter.batch_get_user_info(['user1', 'user2'])
```

### 17.8 权限和安全

#### 17.8.1 权限要求
- 所有同步管理API需要认证
- 用户需要具备组织管理员权限
- 普通用户只能查看自己组织的同步日志

#### 17.8.2 安全措施
- 所有API调用记录到IntegrationLog
- 敏感数据（如企业微信secret）加密存储
- 同步操作通过Celery异步执行，防止阻塞
- 实现分布式锁，防止重复同步任务

#### 17.8.3 速率限制
- 触发同步接口：每分钟最多10次
- 状态查询接口：每秒最多5次
- 批量操作接口：每小时最多100次

---

## 后续任务

1. Phase 2.3: 实现企业微信消息推送通知
2. 扩展支持钉钉、飞书的通讯录同步
3. 完善同步日志的统计分析和可视化功能
4. 实现同步任务的失败重试和告警机制
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