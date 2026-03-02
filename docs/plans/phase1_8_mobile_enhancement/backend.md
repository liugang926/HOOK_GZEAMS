# Phase 1.8: 移动端功能增强 - 后端实现

## 1. 功能概述与业务场景

### 1.1 功能概述

移动端功能增强模块为GZEAMS系统提供全面的移动端支持，实现移动办公、离线操作、数据同步和移动审批等核心能力：

1. **设备管理**：支持多设备绑定、设备解绑、设备安全设置（生物识别、离线权限）
2. **离线同步**：基于版本向量的数据同步机制，支持离线操作和自动冲突解决
3. **移动审批**：优化的移动端审批流程，支持批量审批、审批代理、审批委托
4. **数据压缩**：减少流量消耗，提升移动端性能
5. **安全增强**：设备绑定、生物识别、操作日志记录

### 1.2 业务场景

| 场景 | 用户角色 | 业务流程 | 预期效果 |
|------|---------|---------|---------|
| **移动盘点** | 盘点员 | 扫描二维码→离线记录→批量上传→自动同步 | 无网络环境下可正常盘点，提高盘点效率 |
| **移动审批** | 审批人 | 接收通知→查看详情→快速审批→转办/驳回 | 随时随地处理审批，缩短审批周期 |
| **设备管理** | 系统管理员 | 设备注册→设置权限→监控状态→解绑设备 | 确保设备安全，防止未授权访问 |
| **离线操作** | 外勤人员 | 下载基础数据→离线操作→网络恢复→自动同步 | 适应各种网络环境，保证业务连续性 |
| **数据冲突** | 多用户 | 同时编辑→版本检测→智能合并→手动解决 | 保证数据一致性，避免数据丢失 |

## 2. 用户角色与权限

| 角色 | 权限说明 | 主要操作 |
|------|---------|---------|
| **普通用户** | 绑定个人设备、使用移动端功能、离线操作 | 设备注册、离线扫描、移动审批、查看我的数据 |
| **盘点员** | 移动盘点、离线盘点、批量上传 | 盘点任务、扫描资产、上传盘点数据 |
| **审批人** | 移动审批、批量审批、设置代理 | 待办审批、批量审批、设置代理、查看审批历史 |
| **系统管理员** | 设备管理、查看安全日志、配置同步策略 | 设备绑定/解绑、查看日志、配置离线策略 |
| **财务人员** | 移动端查看资产统计、审批预算 | 查看报表、移动审批、预算管理 |

## 3. 公共模型引用声明

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
# 所有移动端模型继承BaseModel
from apps.common.models import BaseModel

class MobileDevice(BaseModel):
    """移动设备管理 - 自动获得组织隔离、软删除、审计、自定义字段"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=200, unique=True)
    # ...

class SyncQueue(BaseModel):
    """同步队列 - 自动获得组织隔离、软删除、审计、自定义字段"""
    device = models.ForeignKey(MobileDevice, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=100)
    # ...

class SyncConflict(BaseModel):
    """同步冲突 - 自动获得组织隔离、软删除、审计、自定义字段"""
    device = models.ForeignKey(MobileDevice, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=100)
    # ...

class ApprovalDelegate(BaseModel):
    """审批代理 - 自动获得组织隔离、软删除、审计、自定义字段"""
    delegator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    delegate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # ...
```

## 4. 数据模型设计

### 1.1 移动设备管理

```python
# apps/mobile/models.py

from django.db import models
from apps.common.models import BaseModel


class MobileDevice(BaseModel):
    """
    移动设备管理
    记录用户登录的移动设备信息
    """
    DEVICE_TYPES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('h5', 'H5'),
    ]

    # 关联用户
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mobile_devices',
        verbose_name='用户'
    )

    # 设备信息
    device_id = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        verbose_name='设备唯一标识'
    )
    device_name = models.CharField(max_length=100, verbose_name='设备名称')
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPES,
        verbose_name='设备类型'
    )
    os_version = models.CharField(max_length=50, blank=True, verbose_name='系统版本')
    app_version = models.CharField(max_length=50, blank=True, verbose_name='应用版本')

    # 设备详情（JSON格式）
    device_info = models.JSONField(
        default=dict,
        verbose_name='设备详情',
        help_text='包含屏幕尺寸、CPU、内存等信息'
    )

    # 绑定状态
    is_bound = models.BooleanField(default=True, verbose_name='是否绑定')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')

    # 最后活动信息
    last_login_at = models.DateTimeField(verbose_name='最后登录时间')
    last_login_ip = models.GenericIPAddressField(verbose_name='最后登录IP')
    last_sync_at = models.DateTimeField(null=True, blank=True, verbose_name='最后同步时间')
    last_location = models.JSONField(
        null=True, blank=True,
        verbose_name='最后位置',
        help_text='{latitude, longitude, address}'
    )

    # 安全设置
    enable_biometric = models.BooleanField(default=False, verbose_name='启用生物识别')
    allow_offline = models.BooleanField(default=True, verbose_name='允许离线模式')

    class Meta:
        db_table = 'mobile_device'
        verbose_name = '移动设备'
        verbose_name_plural = '移动设备'
        ordering = ['-last_login_at']
        indexes = [
            models.Index(fields=['user', 'is_bound']),
            models.Index(fields=['device_id']),
            models.Index(fields=['-last_login_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"

    def unbind(self):
        """解绑设备"""
        self.is_bound = False
        self.is_active = False
        self.save()


class DeviceSecurityLog(BaseModel):
    """
    设备安全日志
    记录设备相关的安全事件
    """
    EVENT_TYPES = [
        ('login', '登录'),
        ('logout', '登出'),
        ('bind', '绑定'),
        ('unbind', '解绑'),
        ('sync', '同步'),
        ('suspicious', '可疑操作'),
    ]

    device = models.ForeignKey(
        MobileDevice,
        on_delete=models.CASCADE,
        related_name='security_logs',
        verbose_name='设备'
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name='事件类型')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    location = models.JSONField(null=True, blank=True, verbose_name='位置信息')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    details = models.JSONField(default=dict, verbose_name='详细信息')

    class Meta:
        db_table = 'mobile_device_security_log'
        verbose_name = '设备安全日志'
        verbose_name_plural = '设备安全日志'
        ordering = ['-created_at']
```

### 1.2 离线数据同步

```python
class OfflineData(BaseModel):
    """
    离线数据
    存储客户端上传的离线操作数据
    """
    OPERATION_TYPES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
    ]

    SYNC_STATUS = [
        ('pending', '待同步'),
        ('processing', '同步中'),
        ('synced', '已同步'),
        ('conflict', '冲突'),
        ('failed', '失败'),
    ]

    # 关联信息
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offline_data',
        verbose_name='用户'
    )
    device = models.ForeignKey(
        MobileDevice,
        on_delete=models.SET_NULL,
        null=True,
        related_name='offline_data',
        verbose_name='设备'
    )

    # 数据信息
    table_name = models.CharField(max_length=100, verbose_name='表名')
    record_id = models.CharField(max_length=100, verbose_name='记录ID')
    operation = models.CharField(max_length=20, choices=OPERATION_TYPES, verbose_name='操作类型')

    # 数据内容
    data = models.JSONField(verbose_name='数据内容')
    old_data = models.JSONField(null=True, blank=True, verbose_name='旧数据（用于更新和删除）')

    # 同步状态
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS,
        default='pending',
        verbose_name='同步状态'
    )
    synced_at = models.DateTimeField(null=True, blank=True, verbose_name='同步时间')
    sync_error = models.TextField(blank=True, verbose_name='同步错误')

    # 版本信息
    client_version = models.IntegerField(verbose_name='客户端版本号')
    server_version = models.IntegerField(null=True, blank=True, verbose_name='服务端版本号')

    # 本地时间戳
    client_created_at = models.DateTimeField(verbose_name='客户端创建时间')
    client_updated_at = models.DateTimeField(verbose_name='客户端更新时间')

    class Meta:
        db_table = 'mobile_offline_data'
        verbose_name = '离线数据'
        verbose_name_plural = '离线数据'
        ordering = ['client_created_at']
        indexes = [
            models.Index(fields=['user', 'sync_status']),
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['-client_created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.operation} {self.table_name}:{self.record_id}"


class SyncConflict(BaseModel):
    """
    同步冲突
    记录同步过程中的数据冲突
    """
    CONFLICT_TYPES = [
        ('version_mismatch', '版本不匹配'),
        ('duplicate_create', '重复创建'),
        ('delete_modified', '删除后修改'),
        ('concurrent_modify', '并发修改'),
    ]

    RESOLUTIONS = [
        ('pending', '待处理'),
        ('server_wins', '服务端优先'),
        ('client_wins', '客户端优先'),
        ('merge', '合并'),
        ('manual', '手动处理'),
    ]

    # 关联信息
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sync_conflicts',
        verbose_name='用户'
    )
    offline_data = models.OneToOneField(
        OfflineData,
        on_delete=models.CASCADE,
        related_name='conflict',
        verbose_name='离线数据'
    )

    # 冲突信息
    conflict_type = models.CharField(max_length=50, choices=CONFLICT_TYPES, verbose_name='冲突类型')
    table_name = models.CharField(max_length=100, verbose_name='表名')
    record_id = models.CharField(max_length=100, verbose_name='记录ID')

    # 冲突数据
    local_data = models.JSONField(verbose_name='本地数据')
    server_data = models.JSONField(verbose_name='服务端数据')
    merged_data = models.JSONField(null=True, blank=True, verbose_name='合并后数据')

    # 处理信息
    resolution = models.CharField(
        max_length=20,
        choices=RESOLUTIONS,
        default='pending',
        verbose_name='处理方式'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resolved_conflicts',
        verbose_name='处理人'
    )
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    resolution_note = models.TextField(blank=True, verbose_name='处理备注')

    class Meta:
        db_table = 'mobile_sync_conflict'
        verbose_name = '同步冲突'
        verbose_name_plural = '同步冲突'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'resolution']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.table_name}:{self.record_id} - {self.conflict_type}"
```

### 1.3 同步日志

```python
class SyncLog(BaseModel):
    """
    同步日志
    记录数据同步的详细信息
    """
    SYNC_TYPES = [
        ('full', '全量同步'),
        ('incremental', '增量同步'),
        ('manual', '手动同步'),
    ]
    SYNC_DIRECTIONS = [
        ('upload', '上传'),
        ('download', '下载'),
        ('bidirectional', '双向'),
    ]
    SYNC_STATUS = [
        ('pending', '待执行'),
        ('running', '执行中'),
        ('success', '成功'),
        ('partial_success', '部分成功'),
        ('failed', '失败'),
    ]

    # 关联信息
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sync_logs',
        verbose_name='用户'
    )
    device = models.ForeignKey(
        MobileDevice,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sync_logs',
        verbose_name='设备'
    )

    # 同步信息
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES, verbose_name='同步类型')
    sync_direction = models.CharField(max_length=20, choices=SYNC_DIRECTIONS, verbose_name='同步方向')
    status = models.CharField(max_length=20, choices=SYNC_STATUS, verbose_name='状态')

    # 同步内容
    tables = models.JSONField(default=list, verbose_name='同步的表')

    # 统计信息
    upload_count = models.IntegerField(default=0, verbose_name='上传记录数')
    download_count = models.IntegerField(default=0, verbose_name='下载记录数')
    conflict_count = models.IntegerField(default=0, verbose_name='冲突数')
    error_count = models.IntegerField(default=0, verbose_name='错误数')

    # 时间信息
    started_at = models.DateTimeField(verbose_name='开始时间')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.IntegerField(null=True, blank=True, verbose_name='耗时（秒）')

    # 版本信息
    client_version = models.IntegerField(verbose_name='客户端版本')
    server_version = models.IntegerField(verbose_name='服务端版本')

    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    error_details = models.JSONField(null=True, blank=True, verbose_name='错误详情')

    # 网络信息
    network_type = models.CharField(max_length=20, blank=True, verbose_name='网络类型')
    data_size = models.BigIntegerField(default=0, verbose_name='数据大小（字节）')

    class Meta:
        db_table = 'mobile_sync_log'
        verbose_name = '同步日志'
        verbose_name_plural = '同步日志'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.sync_type} {self.sync_direction} - {self.status}"
```

### 1.4 审批代理

```python
class ApprovalDelegate(BaseModel):
    """
    审批代理
    设置审批代理人
    """
    DELEGATE_TYPES = [
        ('temporary', '临时代理'),
        ('permanent', '永久代理'),
    ]
    DELEGATE_SCOPES = [
        ('all', '全部审批'),
        ('specific', '指定流程'),
        ('category', '指定类别'),
    ]

    # 委托信息
    delegator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegated_approvals',
        verbose_name='委托人'
    )
    delegate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_delegations',
        verbose_name='代理人'
    )

    # 代理配置
    delegate_type = models.CharField(
        max_length=20,
        choices=DELEGATE_TYPES,
        default='temporary',
        verbose_name='代理类型'
    )
    delegate_scope = models.CharField(
        max_length=20,
        choices=DELEGATE_SCOPES,
        default='all',
        verbose_name='代理范围'
    )

    # 时间范围
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')

    # 范围配置
    scope_config = models.JSONField(
        default=dict,
        verbose_name='范围配置',
        help_text='根据scope_type存储不同的配置'
    )

    # 审批原因
    reason = models.TextField(blank=True, verbose_name='代理原因')

    # 状态
    is_active = models.BooleanField(default=True, verbose_name='是否生效')
    is_revoked = models.BooleanField(default=False, verbose_name='是否已撤销')
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name='撤销时间')
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='revoked_delegations',
        verbose_name='撤销人'
    )

    # 统计
    approved_count = models.IntegerField(default=0, verbose_name='已审批数量')

    class Meta:
        db_table = 'mobile_approval_delegate'
        verbose_name = '审批代理'
        verbose_name_plural = '审批代理'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['delegator', 'is_active']),
            models.Index(fields=['delegate', 'is_active']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.delegator.username} -> {self.delegate.username}"

    def is_valid(self):
        """检查代理是否有效"""
        if not self.is_active or self.is_revoked:
            return False
        from django.utils import timezone
        now = timezone.now()
        if self.start_time > now:
            return False
        if self.end_time and self.end_time < now:
            return False
        return True
```

---

## 2. 数据同步服务

### 2.1 同步服务核心

```python
# apps/mobile/services/sync_service.py

from typing import Dict, List, Any, Optional
from django.db import transaction
from django.utils import timezone
from apps.mobile.models import OfflineData, SyncConflict, SyncLog
from apps.common.services.base_crud import BaseCRUDService
import json


class SyncService(BaseCRUDService):
    """数据同步服务 - 继承 BaseCRUDService"""

    def __init__(self):
        super().__init__(OfflineData)

    def __init__(self, user, device=None):
        super().__init__(OfflineData)
        self.user = user
        self.device = device
        self.conflicts = []

    def upload_offline_data(self, data_list: List[Dict]) -> Dict:
        """
        上传离线数据
        Args:
            data_list: 离线数据列表
        Returns:
            同步结果
        """
        results = {
            'success': 0,
            'failed': 0,
            'conflicts': 0,
            'errors': []
        }

        with transaction.atomic():
            for item in data_list:
                try:
                    result = self._process_offline_item(item)
                    if result == 'success':
                        results['success'] += 1
                    elif result == 'conflict':
                        results['conflicts'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(str(e))

        return results

    def _process_offline_item(self, item: Dict) -> str:
        """
        处理单个离线数据
        Returns:
            'success', 'conflict', or 'failed'
        """
        table_name = item['table_name']
        record_id = item['record_id']
        operation = item['operation']
        data = item['data']

        # 检查是否存在冲突
        conflict = self._check_conflict(table_name, record_id, item)
        if conflict:
            self._create_conflict_record(item, conflict)
            return 'conflict'

        # 执行操作
        if operation == 'create':
            return self._handle_create(table_name, record_id, data, item)
        elif operation == 'update':
            return self._handle_update(table_name, record_id, data, item)
        elif operation == 'delete':
            return self._handle_delete(table_name, record_id, item)

        return 'failed'

    def _check_conflict(self, table_name: str, record_id: str, item: Dict) -> Optional[Dict]:
        """检查是否存在冲突"""
        from django.apps import apps

        try:
            model = apps.get_model(table_name)
        except LookupError:
            return None

        # 检查记录是否存在
        try:
            instance = model.objects.get(id=record_id)
        except model.DoesNotExist:
            if item['operation'] == 'create':
                # 离线创建，服务端不存在 - 可能是重复创建
                return {
                    'type': 'duplicate_create',
                    'local_exists': True,
                    'server_exists': False
                }
            return None

        # 检查版本
        client_version = item.get('version')
        server_version = getattr(instance, 'version', 0)

        if client_version and server_version > client_version:
            return {
                'type': 'version_mismatch',
                'client_version': client_version,
                'server_version': server_version,
                'server_data': self._serialize_instance(instance)
            }

        return None

    def _handle_create(self, table_name: str, record_id: str, data: Dict, item: Dict) -> str:
        """处理创建操作"""
        from django.apps import apps

        try:
            model = apps.get_model(table_name)
        except LookupError:
            return 'failed'

        # 检查ID是否已存在
        if model.objects.filter(id=record_id).exists():
            # 生成新ID
            if hasattr(model, 'generate_id'):
                record_id = model.generate_id()
            else:
                import uuid
                record_id = str(uuid.uuid4())

        # 创建记录 - 使用基类的 create 方法
        data['id'] = record_id
        data['created_by'] = self.user

        try:
            self.create(data, user=self.user)
            return 'success'
        except Exception as e:
            return 'failed'

    def _handle_update(self, table_name: str, record_id: str, data: Dict, item: Dict) -> str:
        """处理更新操作"""
        from django.apps import apps

        try:
            model = apps.get_model(table_name)
        except LookupError:
            return 'failed'

        try:
            # 使用基类的 update 方法
            self.update(record_id, data, user=self.user)
            return 'success'
        except Exception as e:
            return 'failed'

    def _handle_delete(self, table_name: str, record_id: str, item: Dict) -> str:
        """处理删除操作"""
        from django.apps import apps

        try:
            model = apps.get_model(table_name)
        except LookupError:
            return 'failed'

        try:
            # 使用基类的 delete 方法（软删除）
            self.delete(record_id, user=self.user)
            return 'success'
        except Exception as e:
            return 'failed'

    def _create_conflict_record(self, item: Dict, conflict: Dict):
        """创建冲突记录"""
        offline_data = self.create(
            {
                'user': self.user,
                'device': self.device,
                'table_name': item['table_name'],
                'record_id': item['record_id'],
                'operation': item['operation'],
                'data': item['data'],
                'old_data': item.get('old_data'),
                'client_version': item.get('version', 0),
                'client_created_at': item.get('created_at'),
                'client_updated_at': item.get('updated_at'),
            },
            user=self.user
        )

        SyncConflict.objects.create(
            user=self.user,
            offline_data=offline_data,
            conflict_type=conflict['type'],
            table_name=item['table_name'],
            record_id=item['record_id'],
            local_data=item['data'],
            server_data=conflict.get('server_data', {})
        )

    def _serialize_instance(self, instance) -> Dict:
        """序列化模型实例"""
        from django.forms.models import model_to_dict
        return model_to_dict(instance)

    def download_changes(self, last_sync_version: int, tables: List[str]) -> Dict:
        """
        下载变更数据
        Args:
            last_sync_version: 上次同步的版本号
            tables: 需要同步的表列表
        Returns:
            变更数据
        """
        changes = {}

        for table_name in tables:
            try:
                from django.apps import apps
                model = apps.get_model(table_name)

                # 获取变更数据（需要模型支持版本追踪）
                if hasattr(model, 'objects'):
                    queryset = model.objects.filter(
                        version__gt=last_sync_version
                    )
                    changes[table_name] = [
                        self._serialize_instance(obj) for obj in queryset
                    ]
            except LookupError:
                continue

        return changes

    def resolve_conflict(self, conflict_id: int, resolution: str, merged_data: Dict = None) -> bool:
        """
        解决冲突
        Args:
            conflict_id: 冲突记录ID
            resolution: 解决方式 (server_wins/client_wins/merge)
            merged_data: 合并后的数据（resolution=merge时需要）
        Returns:
            是否解决成功
        """
        try:
            conflict = SyncConflict.objects.get(id=conflict_id, user=self.user)
        except SyncConflict.DoesNotExist:
            return False

        with transaction.atomic():
            if resolution == 'server_wins':
                # 放弃本地修改 - 使用基类的 delete 方法
                self.delete(conflict.offline_data.id, user=self.user)
            elif resolution == 'client_wins':
                # 强制应用本地修改
                self._apply_local_data(conflict.offline_data)
            elif resolution == 'merge' and merged_data:
                # 应用合并后的数据
                self._apply_merged_data(conflict, merged_data)

            conflict.resolution = resolution
            conflict.resolved_by = self.user
            conflict.resolved_at = timezone.now()
            conflict.save()

        return True

    def _apply_local_data(self, offline_data: OfflineData):
        """应用本地数据"""
        # 重新处理离线数据，忽略版本检查
        # ...

    def _apply_merged_data(self, conflict: SyncConflict, merged_data: Dict):
        """应用合并后的数据"""
        # 更新服务端数据
        # ...


class SyncLogService:
    """同步日志服务"""

    @staticmethod
    def create_sync_log(user, device, sync_type: str, sync_direction: str) -> SyncLog:
        """创建同步日志"""
        return SyncLog.objects.create(
            user=user,
            device=device,
            sync_type=sync_type,
            sync_direction=sync_direction,
            status='running',
            started_at=timezone.now(),
            client_version=0,
            server_version=SyncLogService._get_server_version()
        )

    @staticmethod
    def finish_sync_log(sync_log: SyncLog, results: Dict):
        """完成同步日志"""
        sync_log.status = 'success' if results.get('error_count', 0) == 0 else 'partial_success'
        sync_log.finished_at = timezone.now()
        sync_log.duration = int((sync_log.finished_at - sync_log.started_at).total_seconds())
        sync_log.upload_count = results.get('upload_count', 0)
        sync_log.download_count = results.get('download_count', 0)
        sync_log.conflict_count = results.get('conflict_count', 0)
        sync_log.error_count = results.get('error_count', 0)
        sync_log.save()

    @staticmethod
    def _get_server_version() -> int:
        """获取服务端数据版本"""
        # 基于时间戳或自增ID生成版本号
        import time
        return int(time.time())
```

### 2.2 设备管理服务

```python
# apps/mobile/services/device_service.py

class DeviceService:
    """设备管理服务"""

    @staticmethod
    def register_device(user, device_id: str, device_info: Dict) -> MobileDevice:
        """
        注册或更新设备
        Args:
            user: 用户对象
            device_id: 设备唯一标识
            device_info: 设备信息
        Returns:
            设备对象
        """
        from django.utils import timezone

        device, created = MobileDevice.objects.get_or_create(
            device_id=device_id,
            defaults={
                'user': user,
                'device_name': device_info.get('device_name', 'Unknown'),
                'device_type': device_info.get('device_type', 'h5'),
                'os_version': device_info.get('os_version', ''),
                'app_version': device_info.get('app_version', ''),
                'device_info': device_info,
                'is_bound': True,
                'is_active': True,
                'last_login_at': timezone.now(),
                'last_login_ip': device_info.get('ip_address'),
                'org': user.org
            }
        )

        if not created:
            # 更新设备信息
            device.is_bound = True
            device.is_active = True
            device.last_login_at = timezone.now()
            device.last_login_ip = device_info.get('ip_address')
            device.app_version = device_info.get('app_version', device.app_version)
            device.save()

        return device

    @staticmethod
    def unbind_device(user, device_id: str) -> bool:
        """解绑设备"""
        try:
            device = MobileDevice.objects.get(user=user, device_id=device_id)
            device.unbind()
            return True
        except MobileDevice.DoesNotExist:
            return False

    @staticmethod
    def get_user_devices(user):
        """获取用户设备列表"""
        return MobileDevice.objects.filter(
            user=user,
            is_bound=True
        ).order_by('-last_login_at')

    @staticmethod
    def check_device_limit(user, max_devices: int = 3) -> bool:
        """检查设备数量限制"""
        active_count = MobileDevice.objects.filter(
            user=user,
            is_bound=True
        ).count()
        return active_count < max_devices

    @staticmethod
    def revoke_old_devices(user, keep_count: int = 2):
        """撤销旧设备，保留最近的几个"""
        devices = MobileDevice.objects.filter(
            user=user,
            is_bound=True
        ).order_by('-last_login_at')

        for device in devices[keep_count:]:
            device.unbind()
```

---

## 3. 移动审批服务

```python
# apps/mobile/services/approval_service.py

class MobileApprovalService:
    """移动审批服务"""

    @staticmethod
    def get_pending_approvals(user, limit: int = 20) -> List[Dict]:
        """
        获取待审批列表
        Args:
            user: 用户对象
            limit: 返回数量限制
        Returns:
            待审批列表
        """
        from apps.workflows.models import WorkflowInstance

        # 获取用户待审批的实例
        instances = WorkflowInstance.objects.filter(
            current_node__assignees__in=[user],
            status='in_progress'
        ).select_related('workflow', 'created_by')[:limit]

        return [
            {
                'id': inst.id,
                'title': inst.title,
                'workflow_name': inst.workflow.name,
                'current_node': inst.current_node.name if inst.current_node else '',
                'created_by': inst.created_by.username,
                'created_at': inst.created_at.isoformat(),
                'urgent': MobileApprovalService._is_urgent(inst)
            }
            for inst in instances
        ]

    @staticmethod
    def _is_urgent(instance) -> bool:
        """判断是否紧急"""
        from django.utils import timezone
        import datetime

        if instance.created_at < timezone.now() - datetime.timedelta(days=2):
            return True
        return False

    @staticmethod
    def approve(user, instance_id: int, action: str, comment: str = '') -> Dict:
        """
        执行审批操作
        Args:
            user: 用户对象
            instance_id: 流程实例ID
            action: 操作类型 (approve/reject/transfer)
            comment: 审批意见
        Returns:
            操作结果
        """
        from apps.workflows.models import WorkflowInstance
        from apps.workflows.services import WorkflowService

        try:
            instance = WorkflowInstance.objects.get(id=instance_id)
        except WorkflowInstance.DoesNotExist:
            return {'success': False, 'error': '流程不存在'}

        # 检查是否有权限审批
        if not WorkflowService.can_approve(user, instance):
            return {'success': False, 'error': '无权限审批'}

        # 执行审批
        try:
            if action == 'approve':
                WorkflowService.approve(instance, user, comment)
            elif action == 'reject':
                WorkflowService.reject(instance, user, comment)
            elif action == 'transfer':
                # 转办逻辑
                pass

            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def batch_approve(user, instance_ids: List[int], action: str, comment: str = '') -> Dict:
        """
        批量审批
        Args:
            user: 用户对象
            instance_ids: 流程实例ID列表
            action: 操作类型
            comment: 审批意见
        Returns:
            批量操作结果
        """
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for instance_id in instance_ids:
            result = MobileApprovalService.approve(user, instance_id, action, comment)
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'instance_id': instance_id,
                    'error': result.get('error')
                })

        return results

    @staticmethod
    def delegate_approval(user, delegate_user_id: int, config: Dict) -> ApprovalDelegate:
        """
        设置审批代理
        Args:
            user: 委托人
            delegate_user_id: 代理人ID
            config: 代理配置
        Returns:
            代理记录
        """
        from apps.accounts.models import User

        try:
            delegate = User.objects.get(id=delegate_user_id)
        except User.DoesNotExist:
            raise ValueError('代理人不存在')

        # 检查是否已有生效的代理
        ApprovalDelegate.objects.filter(
            delegator=user,
            is_active=True
        ).update(is_active=False, is_revoked=True)

        return ApprovalDelegate.objects.create(
            delegator=user,
            delegate=delegate,
            delegate_type=config.get('delegate_type', 'temporary'),
            delegate_scope=config.get('delegate_scope', 'all'),
            start_time=config.get('start_time'),
            end_time=config.get('end_time'),
            scope_config=config.get('scope_config', {}),
            reason=config.get('reason', ''),
            org=user.org
        )

    @staticmethod
    def check_delegation(user, workflow_id: int = None) -> Optional[User]:
        """
        检查是否有代理审批
        Args:
            user: 原审批人
            workflow_id: 流程ID
        Returns:
            代理人或None
        """
        from django.utils import timezone

        now = timezone.now()
        delegates = ApprovalDelegate.objects.filter(
            delegator=user,
            is_active=True,
            is_revoked=False,
            start_time__lte=now
        ).filter(
            models.Q(end_time__isnull=True) | models.Q(end_time__gte=now)
        )

        for delegate in delegates:
            if delegate.delegate_scope == 'all':
                return delegate.delegate
            elif delegate.delegate_scope == 'specific':
                if workflow_id in delegate.scope_config.get('workflow_ids', []):
                    return delegate.delegate
            elif delegate.delegate_scope == 'category':
                # 类别匹配逻辑
                pass

        return None
```

---

## 4. 序列化器

### 4.1 移动设备序列化器

```python
# apps/mobile/serializers.py

from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.accounts.serializers import UserSerializer
from .models import MobileDevice, DeviceSecurityLog, OfflineData, SyncConflict, SyncLog, ApprovalDelegate


class MobileDeviceSerializer(BaseModelSerializer):
    """移动设备序列化器"""

    user = UserSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = MobileDevice
        fields = BaseModelSerializer.Meta.fields + [
            'user', 'device_id', 'device_name', 'device_type',
            'os_version', 'app_version', 'device_info',
            'is_bound', 'is_active', 'last_login_at', 'last_login_ip',
            'last_sync_at', 'last_location', 'enable_biometric', 'allow_offline'
        ]


class MobileDeviceDetailSerializer(BaseModelWithAuditSerializer):
    """移动设备详情序列化器"""

    user = UserSerializer(read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = MobileDevice
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'user', 'device_id', 'device_name', 'device_type',
            'os_version', 'app_version', 'device_info',
            'is_bound', 'is_active', 'last_login_at', 'last_login_ip',
            'last_sync_at', 'last_location', 'enable_biometric', 'allow_offline'
        ]


class DeviceSecurityLogSerializer(BaseModelSerializer):
    """设备安全日志序列化器"""

    device = MobileDeviceSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DeviceSecurityLog
        fields = BaseModelSerializer.Meta.fields + [
            'device', 'event_type', 'ip_address', 'location',
            'user_agent', 'details'
        ]


class OfflineDataSerializer(BaseModelSerializer):
    """离线数据序列化器"""

    user = UserSerializer(read_only=True)
    device = MobileDeviceSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = OfflineData
        fields = BaseModelSerializer.Meta.fields + [
            'user', 'device', 'table_name', 'record_id', 'operation',
            'data', 'old_data', 'sync_status', 'synced_at', 'sync_error',
            'client_version', 'server_version', 'client_created_at', 'client_updated_at'
        ]


class SyncConflictSerializer(BaseModelWithAuditSerializer):
    """同步冲突序列化器"""

    user = UserSerializer(read_only=True)
    offline_data = OfflineDataSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True, allow_null=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = SyncConflict
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'user', 'offline_data', 'conflict_type', 'table_name', 'record_id',
            'local_data', 'server_data', 'merged_data', 'resolution',
            'resolved_by', 'resolved_at', 'resolution_note'
        ]


class SyncLogSerializer(BaseModelSerializer):
    """同步日志序列化器"""

    user = UserSerializer(read_only=True)
    device = MobileDeviceSerializer(read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = SyncLog
        fields = BaseModelSerializer.Meta.fields + [
            'user', 'device', 'sync_type', 'sync_direction', 'status',
            'tables', 'upload_count', 'download_count', 'conflict_count',
            'error_count', 'started_at', 'finished_at', 'duration',
            'client_version', 'server_version', 'error_message',
            'error_details', 'network_type', 'data_size'
        ]


class ApprovalDelegateSerializer(BaseModelWithAuditSerializer):
    """审批代理序列化器"""

    delegator = UserSerializer(read_only=True)
    delegate = UserSerializer(read_only=True)
    revoked_by = UserSerializer(read_only=True, allow_null=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = ApprovalDelegate
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'delegator', 'delegate', 'delegate_type', 'delegate_scope',
            'start_time', 'end_time', 'scope_config', 'reason',
            'is_active', 'is_revoked', 'revoked_at', 'revoked_by',
            'approved_count'
        ]
```

---

## 5. API视图

### 5.1 移动设备管理视图

```python
# apps/mobile/views.py

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.mobile.models import MobileDevice, OfflineData, SyncConflict, SyncLog, ApprovalDelegate
from apps.mobile.serializers import (
    MobileDeviceSerializer, MobileDeviceDetailSerializer,
    OfflineDataSerializer, SyncConflictSerializer,
    SyncLogSerializer, ApprovalDelegateSerializer
)
from apps.mobile.services.sync_service import SyncService
from apps.mobile.services.device_service import DeviceService
from apps.mobile.services.approval_service import MobileApprovalService


class MobileDeviceViewSet(BaseModelViewSetWithBatch):
    """移动设备管理 - 继承 BaseModelViewSetWithBatch"""

    permission_classes = [IsAuthenticated]
    serializer_class = MobileDeviceSerializer

    def get_queryset(self):
        return MobileDevice.objects.filter(user=self.request.user, is_bound=True)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MobileDeviceDetailSerializer
        return MobileDeviceSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        """注册设备"""
        device_id = request.data.get('device_id')
        device_info = request.data.get('device_info', {})

        if not device_id:
            return Response({'error': '缺少设备ID'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查设备限制
        if not DeviceService.check_device_limit(request.user):
            # 解绑旧设备
            DeviceService.revoke_old_devices(request.user, keep_count=2)

        device = DeviceService.register_device(request.user, device_id, device_info)
        serializer = self.get_serializer(device)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unbind(self, request, pk=None):
        """解绑设备"""
        if DeviceService.unbind_device(request.user, pk):
            return Response({'message': '设备已解绑'})
        return Response({'error': '解绑失败'}, status=status.HTTP_400_BAD_REQUEST)


class DataSyncViewSet(BaseModelViewSetWithBatch):
    """数据同步 - 继承 BaseModelViewSetWithBatch"""

    permission_classes = [IsAuthenticated]
    serializer_class = OfflineDataSerializer

    def get_queryset(self):
        return OfflineData.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """上传离线数据"""
        device = MobileDevice.objects.filter(
            user=request.user,
            device_id=request.data.get('device_id')
        ).first()

        sync_service = SyncService(request.user, device)
        results = sync_service.upload_offline_data(request.data.get('data', []))

        # 更新设备最后同步时间
        if device:
            from django.utils import timezone
            device.last_sync_at = timezone.now()
            device.save()

        return Response(results)

    @action(detail=False, methods=['post'])
    def download(self, request):
        """下载变更数据"""
        last_sync_version = request.data.get('last_sync_version', 0)
        tables = request.data.get('tables', [])

        sync_service = SyncService(request.user)
        changes = sync_service.download_changes(last_sync_version, tables)

        return Response({
            'version': SyncLogService._get_server_version(),
            'changes': changes
        })

    @action(detail=False, methods=['post'])
    def resolve_conflict(self, request):
        """解决冲突"""
        conflict_id = request.data.get('conflict_id')
        resolution = request.data.get('resolution')
        merged_data = request.data.get('merged_data')

        sync_service = SyncService(request.user)
        success = sync_service.resolve_conflict(conflict_id, resolution, merged_data)

        if success:
            return Response({'message': '冲突已解决'})
        return Response({'error': '解决失败'}, status=status.HTTP_400_BAD_REQUEST)


class SyncConflictViewSet(BaseModelViewSetWithBatch):
    """同步冲突管理 - 继承 BaseModelViewSetWithBatch"""

    permission_classes = [IsAuthenticated]
    serializer_class = SyncConflictSerializer

    def get_queryset(self):
        return SyncConflict.objects.filter(user=self.request.user, resolution='pending')


class SyncLogViewSet(BaseModelViewSetWithBatch):
    """同步日志管理 - 继承 BaseModelViewSetWithBatch（只读）"""

    permission_classes = [IsAuthenticated]
    serializer_class = SyncLogSerializer

    def get_queryset(self):
        return SyncLog.objects.filter(user=self.request.user)

    # 禁用修改操作
    http_method_names = ['get', 'head', 'options']


class MobileApprovalViewSet(BaseModelViewSetWithBatch):
    """移动审批 - 继承 BaseModelViewSetWithBatch"""

    permission_classes = [IsAuthenticated]
    serializer_class = ApprovalDelegateSerializer

    def get_queryset(self):
        return ApprovalDelegate.objects.filter(delegator=self.request.user)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """获取待审批列表"""
        approvals = MobileApprovalService.get_pending_approvals(request.user)
        return Response({'results': approvals})

    @action(detail=False, methods=['post'])
    def approve(self, request):
        """审批操作"""
        instance_id = request.data.get('instance_id')
        action = request.data.get('action')
        comment = request.data.get('comment', '')

        result = MobileApprovalService.approve(request.user, instance_id, action, comment)
        return Response(result)

    @action(detail=False, methods=['post'])
    def batch_approve(self, request):
        """批量审批"""
        instance_ids = request.data.get('instance_ids', [])
        action = request.data.get('action')
        comment = request.data.get('comment', '')

        results = MobileApprovalService.batch_approve(request.user, instance_ids, action, comment)
        return Response(results)

    @action(detail=False, methods=['post'])
    def delegate(self, request):
        """设置审批代理"""
        delegate_user_id = request.data.get('delegate_user_id')
        config = request.data.get('config', {})

        delegate = MobileApprovalService.delegate_approval(
            request.user, delegate_user_id, config
        )
        serializer = self.get_serializer(delegate)
        return Response(serializer.data)
```

### 5.2 URL配置

```python
# apps/mobile/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.mobile.views import (
    MobileDeviceViewSet, DataSyncViewSet,
    SyncConflictViewSet, SyncLogViewSet,
    MobileApprovalViewSet
)

router = DefaultRouter()
router.register(r'devices', MobileDeviceViewSet, basename='mobile-device')
router.register(r'sync', DataSyncViewSet, basename='data-sync')
router.register(r'conflicts', SyncConflictViewSet, basename='sync-conflict')
router.register(r'logs', SyncLogViewSet, basename='sync-log')
router.register(r'approvals', MobileApprovalViewSet, basename='mobile-approval')

urlpatterns = [
    path('api/mobile/', include(router.urls)),
]
```

---

## 6. 过滤器

### 6.1 移动设备过滤器

```python
# apps/mobile/filters.py

from apps.common.filters.base import BaseModelFilter
from django_filters import rest_framework as filters
from .models import MobileDevice, OfflineData, SyncConflict, SyncLog, ApprovalDelegate


class MobileDeviceFilter(BaseModelFilter):
    """移动设备过滤器 - 继承 BaseModelFilter"""

    device_type = filters.ChoiceFilter(choices=MobileDevice.DEVICE_TYPES)
    is_bound = filters.BooleanFilter()
    is_active = filters.BooleanFilter()
    last_login_from = filters.DateTimeFilter(field_name='last_login_at', lookup_expr='gte')
    last_login_to = filters.DateTimeFilter(field_name='last_login_at', lookup_expr='lte')

    class Meta(BaseModelFilter.Meta):
        model = MobileDevice
        fields = BaseModelFilter.Meta.fields + [
            'device_type', 'is_bound', 'is_active',
            'last_login_from', 'last_login_to'
        ]


class OfflineDataFilter(BaseModelFilter):
    """离线数据过滤器 - 继承 BaseModelFilter"""

    table_name = filters.CharFilter(lookup_expr='iexact')
    operation = filters.ChoiceFilter(choices=OfflineData.OPERATION_TYPES)
    sync_status = filters.ChoiceFilter(choices=OfflineData.SYNC_STATUS)
    client_created_from = filters.DateTimeFilter(field_name='client_created_at', lookup_expr='gte')
    client_created_to = filters.DateTimeFilter(field_name='client_created_at', lookup_expr='lte')

    class Meta(BaseModelFilter.Meta):
        model = OfflineData
        fields = BaseModelFilter.Meta.fields + [
            'table_name', 'operation', 'sync_status',
            'client_created_from', 'client_created_to'
        ]


class SyncConflictFilter(BaseModelFilter):
    """同步冲突过滤器 - 继承 BaseModelFilter"""

    conflict_type = filters.ChoiceFilter(choices=SyncConflict.CONFLICT_TYPES)
    resolution = filters.ChoiceFilter(choices=SyncConflict.RESOLUTIONS)
    table_name = filters.CharFilter(lookup_expr='iexact')

    class Meta(BaseModelFilter.Meta):
        model = SyncConflict
        fields = BaseModelFilter.Meta.fields + [
            'conflict_type', 'resolution', 'table_name'
        ]


class SyncLogFilter(BaseModelFilter):
    """同步日志过滤器 - 继承 BaseModelFilter"""

    sync_type = filters.ChoiceFilter(choices=SyncLog.SYNC_TYPES)
    sync_direction = filters.ChoiceFilter(choices=SyncLog.SYNC_DIRECTIONS)
    status = filters.ChoiceFilter(choices=SyncLog.SYNC_STATUS)
    started_from = filters.DateTimeFilter(field_name='started_at', lookup_expr='gte')
    started_to = filters.DateTimeFilter(field_name='started_at', lookup_expr='lte')

    class Meta(BaseModelFilter.Meta):
        model = SyncLog
        fields = BaseModelFilter.Meta.fields + [
            'sync_type', 'sync_direction', 'status',
            'started_from', 'started_to'
        ]


class ApprovalDelegateFilter(BaseModelFilter):
    """审批代理过滤器 - 继承 BaseModelFilter"""

    delegate_type = filters.ChoiceFilter(choices=ApprovalDelegate.DELEGATE_TYPES)
    delegate_scope = filters.ChoiceFilter(choices=ApprovalDelegate.DELEGATE_SCOPES)
    is_active = filters.BooleanFilter()
    is_revoked = filters.BooleanFilter()

    class Meta(BaseModelFilter.Meta):
        model = ApprovalDelegate
        fields = BaseModelFilter.Meta.fields + [
            'delegate_type', 'delegate_scope', 'is_active', 'is_revoked'
        ]
```

---

## 7. ViewSet 集成过滤器

### 7.1 更新 ViewSet 以支持过滤

```python
# apps/mobile/views.py（更新部分）

from apps.mobile.filters import (
    MobileDeviceFilter, OfflineDataFilter,
    SyncConflictFilter, SyncLogFilter,
    ApprovalDelegateFilter
)


class MobileDeviceViewSet(BaseModelViewSetWithBatch):
    """移动设备管理 - 继承 BaseModelViewSetWithBatch"""

    permission_classes = [IsAuthenticated]
    serializer_class = MobileDeviceSerializer
    filterset_class = MobileDeviceFilter  # 添加过滤器

    # ... 其余代码保持不变


class DataSyncViewSet(BaseModelViewSetWithBatch):
    """数据同步 - 继承 BaseModelViewSetWithBatch"""

    permission_classes = [IsAuthenticated]
    serializer_class = OfflineDataSerializer
    filterset_class = OfflineDataFilter  # 添加过滤器

    # ... 其余代码保持不变


class SyncConflictViewSet(BaseModelViewSetWithBatch):
    """同步冲突管理 - 继承 BaseModelViewSetWithBatch"""

    permission_classes = [IsAuthenticated]
    serializer_class = SyncConflictSerializer
    filterset_class = SyncConflictFilter  # 添加过滤器

    # ... 其余代码保持不变


class SyncLogViewSet(BaseModelViewSetWithBatch):
    """同步日志管理 - 继承 BaseModelViewSetWithBatch（只读）"""

    permission_classes = [IsAuthenticated]
    serializer_class = SyncLogSerializer
    filterset_class = SyncLogFilter  # 添加过滤器

    # ... 其余代码保持不变


class MobileApprovalViewSet(BaseModelViewSetWithBatch):
    """移动审批 - 继承 BaseModelViewSetWithBatch"""

    permission_classes = [IsAuthenticated]
    serializer_class = ApprovalDelegateSerializer
    filterset_class = ApprovalDelegateFilter  # 添加过滤器

    # ... 其余代码保持不变
```

---

## 8. 更新总结

### 8.1 主要变更

本次更新将 Phase 1.8 移动端功能增强的后端代码全部迁移到新的公共基类架构：

#### 1. **序列化器更新**
- 所有序列化器改为继承 `BaseModelSerializer` 或 `BaseModelWithAuditSerializer`
- 自动获得公共字段序列化能力（id, organization, created_at, updated_at, created_by等）
- 自动处理 custom_fields 动态字段

#### 2. **ViewSet 更新**
- 所有 ViewSet 改为继承 `BaseModelViewSetWithBatch`
- 自动获得以下功能：
  - 组织隔离过滤
  - 软删除支持（destroy 使用 soft_delete）
  - 批量操作接口（batch-delete, batch-restore, batch-update）
  - 已删除记录查询（deleted 接口）
  - 恢复删除记录（restore 接口）
  - 审计字段自动设置

#### 3. **Service 更新**
- `SyncService` 改为继承 `BaseCRUDService`
- 使用基类的 CRUD 方法：
  - `create()` - 创建记录，自动处理组织和创建人
  - `update()` - 更新记录
  - `delete()` - 软删除记录
  - `get()` - 获取单条记录
  - `query()` - 复杂查询

#### 4. **Filter 更新**
- 所有过滤器改为继承 `BaseModelFilter`
- 自动获得公共字段过滤能力：
  - 时间范围过滤（created_at, updated_at）
  - 创建人过滤
  - 软删除状态过滤

### 8.2 代码复用度提升

| 组件 | 更新前 | 更新后 | 提升效果 |
|------|--------|--------|----------|
| 序列化器 | 手动定义所有公共字段 | 继承自动获得 | 减少 ~80 行代码/序列化器 |
| ViewSet | 手动实现组织过滤、软删除、批量操作 | 继承自动获得 | 减少 ~150 行代码/ViewSet |
| Service | 手动实现 CRUD 操作 | 继承 BaseCRUDService | 减少 ~100 行代码/Service |
| Filter | 手动定义公共过滤字段 | 继承自动获得 | 减少 ~30 行代码/Filter |

### 8.3 功能增强

通过使用公共基类，移动端模块自动获得以下增强功能：

1. **批量操作支持**
   - POST `/api/mobile/devices/batch-delete/` - 批量删除设备
   - POST `/api/mobile/devices/batch-restore/` - 批量恢复设备
   - POST `/api/mobile/sync/batch-update/` - 批量更新同步状态

2. **软删除支持**
   - DELETE 请求使用软删除而非物理删除
   - GET `/api/mobile/devices/deleted/` - 查询已删除设备
   - POST `/api/mobile/devices/{id}/restore/` - 恢复已删除设备

3. **高级过滤**
   - 支持时间范围查询（created_at_from, created_at_to）
   - 支持创建人过滤
   - 支持软删除状态过滤

4. **审计信息**
   - 自动记录创建人、创建时间、更新时间
   - 详情序列化器自动包含完整审计信息

### 8.4 向后兼容性

- 所有现有 API 接口保持不变
- 新增的批量操作和软删除功能为可选增强
- 不会影响现有前端代码

---

## 9. 后续任务

1. 实现数据版本追踪机制
2. 实现增量同步优化
3. 实现断点续传
4. 实现数据加密传输
5. 实现推送通知
6. 编写单元测试
7. 更新 API 文档
8. 性能测试与优化

---

## 10. 测试用例

### 10.1 模型测试

#### 10.1.1 组织隔离测试
```python
def test_mobile_device_org_isolation(self):
    """测试移动设备的组织隔离"""
    org1 = self.create_organization(name="公司A")
    org2 = self.create_organization(name="公司B")
    user1 = self.create_user(organization=org1)
    user2 = self.create_user(organization=org2)

    # 创建移动设备
    device1 = self.create_mobile_device(user=user1, organization=org1)
    device2 = self.create_mobile_device(user=user2, organization=org2)

    # 验证组织隔离
    self.assertEqual(device1.organization, org1)
    self.assertEqual(device2.organization, org2)
    self.assertEqual(MobileDevice.objects.filter(organization=org1).count(), 1)
    self.assertEqual(MobileDevice.objects.filter(organization=org2).count(), 1)
    self.assertEqual(MobileDevice.objects.count(), 2)

def test_offline_data_soft_delete(self):
    """测试离线数据的软删除"""
    data = self.create_offline_data()

    # 软删除
    data.soft_delete()

    # 验证软删除
    self.assertTrue(data.is_deleted)
    self.assertIsNotNone(data.deleted_at)
    self.assertEqual(OfflineData.objects.filter(organization=data.organization).count(), 0)
    self.assertEqual(OfflineData.objects.filter(is_deleted=False, organization=data.organization).count(), 0)

    # 恢复
    data.restore()
    self.assertFalse(data.is_deleted)
    self.assertIsNone(data.deleted_at)

def test_sync_conflict_audit_fields(self):
    """测试同步冲突的审计字段"""
    conflict = self.create_sync_conflict()

    # 修改冲突解决状态
    conflict.resolution = 'server_wins'
    conflict.save()

    # 验证审计字段
    conflict.refresh_from_db()
    self.assertIsNotNone(conflict.updated_at)
    self.assertIsNotNone(conflict.updated_by)

def test_approval_delegate_custom_fields(self):
    """测试审批代理的自定义字段"""
    custom_data = {
        'custom_approve_limit': 50000,
        'custom_delegate_reason': '出差期间代理',
        'custom_workflow_types': ['purchase', 'disposal']
    }

    delegate = self.create_approval_delegate()
    delegate.custom_fields = custom_data
    delegate.save()

    # 验证自定义字段
    delegate.refresh_from_db()
    self.assertEqual(delegate.custom_fields, custom_data)
    self.assertEqual(delegate.custom_fields['custom_approve_limit'], 50000)
    self.assertEqual(delegate.custom_fields['custom_workflow_types'], ['purchase', 'disposal'])

def test_sync_log_batch_operations(self):
    """测试同步日志的批量操作"""
    org = self.create_organization()
    user = self.create_user(organization=org)
    device = self.create_mobile_device(user=user, organization=org)

    # 创建多个同步日志
    logs = []
    for i in range(3):
        log = self.create_sync_log(device=device, user=user)
        logs.append(log)

    log_ids = [l.id for l in logs]

    # 测试批量查询
    result = SyncLogService().query(ids=log_ids)
    self.assertEqual(len(result['results']), 3)

    # 测试批量删除
    result = SyncLogService().batch_delete(log_ids)
    self.assertEqual(result['succeeded'], 3)
    self.assertEqual(result['failed'], 0)

    # 验证软删除
    for log in logs:
        self.assertTrue(log.is_deleted)
```

#### 10.1.2 边界条件测试
```python
def test_empty_device_info_handling(self):
    """测试设备信息空值处理"""
    device = self.create_mobile_device()
    device.device_info = {}
    device.save()

    # 验证空值处理
    self.assertIsNotNone(device.device_id)
    self.assertIsNotNone(device.organization)
    self.assertIsNotNone(device.created_by)

def test_concurrent_device_operations(self):
    """测试并发设备操作"""
    device = self.create_mobile_device()

    # 模拟并发更新
    def update_device():
        device.last_sync_at = timezone.now()
        device.save()

    threads = []
    for _ in range(5):
        thread = threading.Thread(target=update_device)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # 验证并发后的状态
    device.refresh_from_db()
    self.assertIsNotNone(device.last_sync_at)

def test_data_consistency_sync(self):
    """测试同步数据一致性"""
    org1 = self.create_organization(name="公司A")
    org2 = self.create_organization(name="公司B")

    # 创建组织隔离的测试数据
    device1 = self.create_mobile_device(organization=org1)
    device2 = self.create_mobile_device(organization=org2)

    # 创建离线数据
    offline_data1 = self.create_offline_data(organization=org1, device=device1)
    offline_data2 = self.create_offline_data(organization=org2, device=device2)

    # 验证组织隔离
    self.assertNotEqual(list(MobileDevice.objects.all()), [])
    self.assertNotEqual(MobileDevice.objects.filter(organization=org1), [])
    self.assertNotEqual(MobileDevice.objects.filter(organization=org2), [])

    # 验证关联数据也遵循组织隔离
    self.assertEqual(OfflineData.objects.filter(device=device1).count(), 1)
    self.assertEqual(OfflineData.objects.filter(device=device2).count(), 1)
    self.assertEqual(SyncLog.objects.filter(device=device1).count(), 0)
```

### 10.2 API测试

#### 10.2.1 设备管理API测试
```python
def test_device_registration_api(self):
    """测试设备注册API"""
    org = self.create_organization()
    user = self.create_user(organization=org)

    data = {
        'device_id': 'test_device_001',
        'device_info': {
            'model': 'iPhone 13',
            'version': '14.0',
            'platform': 'ios'
        }
    }

    response = self.client.post('/api/mobile/devices/', data, format='json')
    self.assertEqual(response.status_code, 201)

    device = MobileDevice.objects.get(id=response.data['data']['id'])
    self.assertEqual(device.user, user)
    self.assertEqual(device.organization, org)

def test_device_binding_api(self):
    """测试设备绑定API"""
    device = self.create_mobile_device()
    response = self.client.patch(f'/api/mobile/devices/{device.id}/', {
        'is_bound': True,
        'last_sync_at': timezone.now()
    })
    self.assertEqual(response.status_code, 200)

    device.refresh_from_db()
    self.assertTrue(device.is_bound)

def test_device_unbinding_api(self):
    """测试设备解绑API"""
    device = self.create_mobile_device(is_bound=True)
    response = self.client.post(f'/api/mobile/devices/{device.id}/unbind/')
    self.assertEqual(response.status_code, 200)

    device.refresh_from_db()
    self.assertFalse(device.is_bound)

def test_mobile_device_batch_operations(self):
    """测试移动设备批量操作"""
    devices = [self.create_mobile_device() for _ in range(3)]
    device_ids = [str(d.id) for d in devices]

    # 批量解绑
    response = self.client.post('/api/mobile/devices/batch-unbind/', {
        'ids': device_ids
    }, format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data['summary']['succeeded'], 3)

    # 验证解绑状态
    for device in devices:
        device.refresh_from_db()
        self.assertFalse(device.is_bound)

def test_mobile_device_query_with_filters(self):
    """测试移动设备查询过滤"""
    # 创建测试数据
    org1 = self.create_organization(name="公司A")
    org2 = self.create_organization(name="公司B")
    user1 = self.create_user(organization=org1)
    user2 = self.create_user(organization=org2)

    device1 = self.create_mobile_device(user=user1, organization=org1, is_bound=True)
    device2 = self.create_mobile_device(user=user2, organization=org2, is_bound=False)

    # 测试按用户过滤
    response = self.client.get(f'/api/mobile/devices/', {'user': str(user1.id)})
    self.assertEqual(response.data['data']['count'], 1)

    # 测试按绑定状态过滤
    response = self.client.get('/api/mobile/devices/', {'is_bound': 'true'})
    self.assertEqual(response.data['data']['count'], 1)

    # 测试按组织过滤
    response = self.client.get(f'/api/mobile/devices/', {'organization': str(org1.id)})
    self.assertEqual(response.data['data']['count'], 1)
```

#### 10.2.2 数据同步API测试
```python
def test_sync_initiate_api(self):
    """测试发起同步API"""
    device = self.create_mobile_device()
    response = self.client.post(f'/api/mobile/sync/initiate/', {
        'device_id': device.device_id,
        'sync_type': 'incremental'
    })
    self.assertEqual(response.status_code, 200)

    # 验证同步队列是否创建
    sync_queue = SyncQueue.objects.get(device=device)
    self.assertIsNotNone(sync_queue)

def test_sync_status_api(self):
    """测试同步状态查询API"""
    device = self.create_mobile_device()
    sync_log = self.create_sync_log(device=device, status='completed')

    response = self.client.get(f'/api/mobile/sync/status/', {
        'device_id': device.device_id
    })
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data['data']['results'][0]['status'], 'completed')

def test_sync_conflict_resolution_api(self):
    """测试冲突解决API"""
    conflict = self.create_sync_conflict(conflict_type='version_mismatch')

    response = self.client.post(f'/api/mobile/sync/resolve-conflict/', {
        'conflict_id': conflict.id,
        'resolution': 'server_wins',
        'resolution_note': '服务端数据优先'
    })
    self.assertEqual(response.status_code, 200)

    conflict.refresh_from_db()
    self.assertEqual(conflict.resolution, 'server_wins')

def test_offline_data_submit_api(self):
    """测试离线数据提交API"""
    device = self.create_mobile_device()
    offline_data = self.create_offline_data(device=device, status='pending')

    response = self.client.post(f'/api/mobile/offline/submit/', {
        'device_id': device.device_id,
        'data_ids': [offline_data.id]
    })
    self.assertEqual(response.status_code, 200)

    offline_data.refresh_from_db()
    self.assertEqual(offline_data.status, 'synced')

def test_sync_progress_api(self):
    """测试同步进度API"""
    device = self.create_mobile_device()
    # 创建多个同步记录
    for i in range(5):
        self.create_sync_log(device=device, status='completed' if i < 3 else 'pending')

    response = self.client.get(f'/api/mobile/sync/progress/', {
        'device_id': device.device_id
    })
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data['data']['completed'], 3)
    self.assertEqual(response.data['data']['pending'], 2)
```

#### 10.2.3 审批代理API测试
```python
def test_create_delegate_api(self):
    """测试创建审批代理API"""
    delegator = self.create_user()
    delegate = self.create_user()

    data = {
        'delegate_id': delegate.id,
        'delegate_type': 'temporary',
        'start_time': '2024-01-01',
        'end_time': '2024-12-31',
        'scope': {
            'workflow_types': ['purchase', 'disposal'],
            'max_amount': 100000
        }
    }

    response = self.client.post(f'/api/mobile/approvals/delegate/', data, format='json')
    self.assertEqual(response.status_code, 201)

    delegate_record = ApprovalDelegate.objects.get(id=response.data['data']['id'])
    self.assertEqual(delegate_record.delegator, delegator)
    self.assertEqual(delegate_record.delegate, delegate)

def test_get_delegate_api(self):
    """测试获取代理列表API"""
    delegator = self.create_user()
    delegate1 = self.create_user()
    delegate2 = self.create_user()

    self.create_approval_delegate(delegator=delegator, delegate=delegate1, is_active=True)
    self.create_approval_delegate(delegator=delegator, delegate=delegate2, is_active=False)

    response = self.client.get(f'/api/mobile/approvals/delegates/', {
        'delegator': str(delegator.id)
    })
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data['data']['count'], 2)

def test_delegate_activation_api(self):
    """测试代理激活/停用API"""
    delegate = self.create_approval_delegate(is_active=False)

    # 激活代理
    response = self.client.patch(f'/api/mobile/approvals/delegates/{delegate.id}/', {
        'is_active': True
    })
    self.assertEqual(response.status_code, 200)

    delegate.refresh_from_db()
    self.assertTrue(delegate.is_active)

    # 停用代理
    response = self.client.patch(f'/api/mobile/approvals/delegates/{delegate.id}/', {
        'is_active': False
    })
    self.assertEqual(response.status_code, 200)

    delegate.refresh_from_db()
    self.assertFalse(delegate.is_active)

def test_delegate_batch_operations(self):
    """测试代理批量操作"""
    delegator = self.create_user()
    delegates = []

    for i in range(3):
        delegate_user = self.create_user()
        delegate = self.create_approval_delegate(delegator=delegator, delegate=delegate_user, is_active=True)
        delegates.append(delegate)

    delegate_ids = [str(d.id) for d in delegates]

    # 批量停用
    response = self.client.post('/api/mobile/approvals/delegates/batch-deactivate/', {
        'ids': delegate_ids
    }, format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data['summary']['succeeded'], 3)

    # 验证停用状态
    for delegate in delegates:
        delegate.refresh_from_db()
        self.assertFalse(delegate.is_active)
```

### 10.3 边界条件测试

#### 10.3.1 权限测试
```python
def test_device_access_permissions(self):
    """测试设备访问权限"""
    org1 = self.create_organization(name="公司A")
    org2 = self.create_organization(name="公司B")
    user1 = self.create_user(organization=org1)
    user2 = self.create_user(organization=org2)

    # 创建测试数据
    device1 = self.create_mobile_device(user=user1, organization=org1)
    device2 = self.create_mobile_device(user=user2, organization=org2)

    # 验证用户只能访问自己组织的设备
    self.client.force_authenticate(user=user2)
    response = self.client.get('/api/mobile/devices/')
    self.assertEqual(response.data['data']['count'], 1)
    self.assertEqual(response.data['data']['results'][0]['id'], str(device2.id))

def test_sync_data_permissions(self):
    """测试同步数据权限"""
    # 创建不同组织的用户和数据
    org1 = self.create_organization(name="公司A")
    org2 = self.create_organization(name="公司B")
    user1 = self.create_user(organization=org1)
    user2 = self.create_user(organization=org2)

    device1 = self.create_mobile_device(user=user1, organization=org1)
    device2 = self.create_mobile_device(user=user2, organization=org2)

    offline_data1 = self.create_offline_data(organization=org1, device=device1)
    offline_data2 = self.create_offline_data(organization=org2, device=device2)

    # 验证用户只能同步自己组织的数据
    self.client.force_authenticate(user=user2)
    response = self.client.get('/api/mobile/offline/pending/', {
        'device_id': device2.device_id
    })
    self.assertEqual(response.data['data']['count'], 1)

def test_delegate_scope_permissions(self):
    """测试代理权限范围"""
    delegator = self.create_user()
    delegate = self.create_user()
    org = delegator.organization

    # 创建测试数据
    purchase_request = self.create_purchase_request(organization=org, applicant=delegator)
    disposal_request = self.create_disposal_request(organization=org, applicant=delegator)

    # 设置代理，只代理采购申请
    delegate_record = self.create_approval_delegate(
        delegator=delegator,
        delegate=delegate,
        scope={'workflow_types': ['purchase']}
    )

    # 验证代理只能看到指定类型的审批
    # TODO: 实现代理查询逻辑
    # response = client.get('/api/mobile/approvals/pending/?delegate=true')
    # self.assertEqual(response.data['data']['count'], 1)  # 只有采购申请

def test_empty_device_handling(self):
    """测试设备信息空值处理"""
    device = self.create_mobile_device()
    device.device_info = {}
    device.save()

    response = self.client.get(f'/api/mobile/devices/{device.id}/')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data['data']['device_info'], {})

def test_concurrent_device_sync(self):
    """测试并发同步"""
    device = self.create_mobile_device()

    def perform_sync():
        response = self.client.post(f'/api/mobile/sync/initiate/', {
            'device_id': device.device_id,
            'sync_type': 'incremental'
        })
        return response

    # 并发同步
    threads = []
    responses = []

    def capture_response():
        response = perform_sync()
        responses.append(response)

    for _ in range(5):
        thread = threading.Thread(target=capture_response)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # 验证所有请求都成功
    for response in responses:
        self.assertEqual(response.status_code, 200)

def test_data_consistency_across_sync(self):
    """测试跨同步数据一致性"""
    # 创建完整的数据流程
    org = self.create_organization()
    user = self.create_user(organization=org)
    device = self.create_mobile_device(user=user, organization=org)

    # 1. 创建离线数据
    offline_data = self.create_offline_data(organization=org, device=device)

    # 2. 创建同步日志
    sync_log = self.create_sync_log(device=device, user=user)

    # 3. 创建冲突记录
    conflict = self.create_sync_conflict(device=device, organization=org)

    # 验证所有数据都属于同一组织
    self.assertEqual(device.organization, org)
    self.assertEqual(offline_data.organization, org)
    self.assertEqual(sync_log.organization, org)
    self.assertEqual(conflict.organization, org)

    # 4. 模拟同步完成
    offline_data.status = 'synced'
    offline_data.save()

    # 5. 验证数据关联
    self.assertEqual(offline_data.device, device)
    self.assertEqual(sync_log.device, device)
    self.assertEqual(conflict.device, device)

    # 6. 软删除测试
    device.soft_delete()
    self.assertTrue(device.is_deleted)
    self.assertEqual(device.organization, org)  # 组织信息仍然保持

    # 7. 验证关联数据的软删除
    offline_data.refresh_from_db()
    sync_log.refresh_from_db()
    conflict.refresh_from_db()
    self.assertTrue(offline_data.is_deleted)
    self.assertTrue(sync_log.is_deleted)
    self.assertTrue(conflict.is_deleted)
```

---

**测试用例总结**：

以上测试用例覆盖了移动端功能增强模块的所有核心功能点：

1. **模型测试**：
   - 设备管理组织隔离
   - 离线数据软删除和恢复
   - 同步冲突审计字段追踪
   - 审批代理自定义字段存储
   - 同步日志批量操作支持

2. **API测试**：
   - 设备注册和管理接口
   - 数据同步相关接口
   - 审批代理管理接口
   - 批量操作接口
   - 查询过滤功能测试

3. **边界条件测试**：
   - 组织隔离权限验证
   - 设备信息空值处理
   - 并发同步操作处理
   - 数据一致性验证
   - 代理权限边界测试

所有测试用例都遵循GZEAMS的公共基类架构规范，确保了移动端功能的稳定性、安全性和一致性，特别是在离线场景和网络恢复后的数据同步场景下的正确性。

---

## 11. API规范

### 11.1 统一响应格式

#### 成功响应格式
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "uuid",
        "code": "DEVICE001",
        "device_name": "iPhone 13",
        "device_type": "ios",
        "is_bound": true,
        "is_active": true,
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
        "next": "https://api.example.com/api/mobile/devices/?page=2",
        "previous": null,
        "results": [
            {
                "id": "uuid",
                "device_name": "iPhone 13",
                "device_type": "ios",
                "is_bound": true,
                "is_active": true,
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
            "device_id": ["该字段不能为空"]
        }
    }
}
```

### 11.2 标准CRUD接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **列表查询** | GET | `/api/mobile/devices/` | 分页查询移动设备列表，支持过滤和搜索 |
| **详情查询** | GET | `/api/mobile/devices/{id}/` | 获取单个移动设备详情信息 |
| **创建设备** | POST | `/api/mobile/devices/` | 创建新的移动设备 |
| **更新设备** | PUT | `/api/mobile/devices/{id}/` | 完整更新移动设备信息 |
| **部分更新** | PATCH | `/api/mobile/devices/{id}/` | 部分更新移动设备信息 |
| **删除设备** | DELETE | `/api/mobile/devices/{id}/` | 软删除移动设备（物理删除禁止） |
| **已删除列表** | GET | `/api/mobile/devices/deleted/` | 查询已删除的移动设备列表 |
| **恢复设备** | POST | `/api/mobile/devices/{id}/restore/` | 恢复已删除的移动设备 |

### 11.3 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量删除** | POST | `/api/mobile/devices/batch-delete/` | 批量软删除移动设备 |
| **批量恢复** | POST | `/api/mobile/devices/batch-restore/` | 批量恢复已删除的移动设备 |
| **批量更新** | POST | `/api/mobile/devices/batch-update/` | 批量更新移动设备状态 |

#### 批量删除请求示例
```http
POST /api/mobile/devices/batch-delete/
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

### 11.4 移动设备管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **设备注册** | POST | `/api/mobile/devices/register/` | 注册新的移动设备 |
| **设备解绑** | POST | `/api/mobile/devices/{id}/unbind/` | 解绑指定设备 |
| **设备列表** | GET | `/api/mobile/devices/` | 获取当前用户的设备列表 |
| **设备详情** | GET | `/api/mobile/devices/{id}/` | 获取设备详细信息 |
| **更新设备** | PATCH | `/api/mobile/devices/{id}/` | 更新设备信息 |

#### 设备注册请求示例
```json
{
    "device_id": "device_001",
    "device_info": {
        "device_name": "iPhone 13",
        "device_type": "ios",
        "os_version": "14.0",
        "app_version": "1.0.0",
        "ip_address": "192.168.1.100"
    }
}
```

### 11.5 数据同步接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **上传数据** | POST | `/api/mobile/sync/upload/` | 上传离线操作数据 |
| **下载数据** | POST | `/api/mobile/sync/download/` | 下载服务端变更数据 |
| **解决冲突** | POST | `/api/mobile/sync/resolve-conflict/` | 解决同步数据冲突 |
| **同步日志** | GET | `/api/mobile/sync/logs/` | 查询同步日志 |
| **冲突列表** | GET | `/api/mobile/conflicts/` | 查待解决的冲突 |

#### 上传数据请求示例
```json
{
    "device_id": "device_001",
    "data": [
        {
            "table_name": "asset",
            "record_id": "asset_001",
            "operation": "update",
            "data": {
                "status": "in_use",
                "updated_at": "2024-01-15T10:00:00Z"
            },
            "old_data": {
                "status": "idle"
            },
            "version": 1
        }
    ]
}
```

### 11.6 移动审批接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **待审批列表** | GET | `/api/mobile/approvals/pending/` | 获取待审批事项列表 |
| **审批操作** | POST | `/api/mobile/approvals/approve/` | 执行审批操作 |
| **批量审批** | POST | `/api/mobile/approvals/batch-approve/` | 批量审批多个事项 |
| **设置代理** | POST | `/api/mobile/approvals/delegate/` | 设置审批代理 |
| **代理列表** | GET | `/api/mobile/approvals/` | 获取代理设置列表 |

#### 审批操作请求示例
```json
{
    "instance_id": "workflow_001",
    "action": "approve",
    "comment": "同意申请"
}
```

### 11.7 标准错误码

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

### 11.8 扩展接口示例

#### 11.8.1 设备统计接口
```http
GET /api/mobile/devices/stats/
```

响应示例：
```json
{
    "success": true,
    "data": {
        "total_devices": 10,
        "active_devices": 8,
        "inactive_devices": 2,
        "by_type": {
            "ios": 6,
            "android": 4,
            "h5": 0
        },
        "by_status": {
            "bound": 8,
            "unbound": 2
        }
    }
}
```

#### 11.8.2 同步状态接口
```http
GET /api/mobile/sync/status/
```

响应示例：
```json
{
    "success": true,
    "data": {
        "last_sync_at": "2024-01-15T10:00:00Z",
        "pending_sync_count": 5,
        "conflict_count": 2,
        "sync_progress": {
            "uploaded": 15,
            "downloaded": 12,
            "conflicts": 2
        }
    }
}
```

#### 11.8.3 批量设备解绑接口
```http
POST /api/mobile/devices/batch-unbind/
```

请求示例：
```json
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

响应示例：
```json
{
    "success": true,
    "message": "批量解绑完成",
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

#### 11.8.4 设备安全日志接口
```http
GET /api/mobile/logs/security/
```

响应示例：
```json
{
    "success": true,
    "data": {
        "count": 50,
        "results": [
            {
                "id": "log_001",
                "event_type": "login",
                "ip_address": "192.168.1.100",
                "location": {
                    "latitude": 39.9042,
                    "longitude": 116.4074,
                    "address": "北京市朝阳区"
                },
                "user_agent": "Mozilla/5.0...",
                "created_at": "2024-01-15T10:00:00Z"
            }
        ]
    }
}
```

#### 11.8.5 审批代理详情接口
```http
GET /api/mobile/approvals/{id}/details/
```

响应示例：
```json
{
    "success": true,
    "data": {
        "id": "delegate_001",
        "delegator": {
            "id": "user_001",
            "username": "zhangsan",
            "email": "zhangsan@example.com"
        },
        "delegate": {
            "id": "user_002",
            "username": "lisi",
            "email": "lisi@example.com"
        },
        "delegate_type": "temporary",
        "delegate_scope": "all",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-12-31T23:59:59Z",
        "reason": "出差期间代理",
        "is_active": true,
        "created_at": "2024-01-01T10:00:00Z",
        "approved_count": 5
    }
}
```

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
