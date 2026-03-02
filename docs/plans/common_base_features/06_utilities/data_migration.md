# 配置版本化与数据迁移

## 1. 设计目标

### 1.1 核心需求
- **字段配置变更支持**: 允许业务对象字段定义动态演进，支持字段重命名、类型转换、删除等操作
- **新旧数据共存**: 保证不同版本配置下的数据能够同时存在和访问，避免业务中断
- **平滑迁移**: 提供可控的数据迁移路径，支持批量数据转换和回滚机制
- **版本追溯**: 记录所有配置变更历史，支持版本对比和回退
- **业务连续性**: 迁移过程不影响线上业务，支持零停机迁移

### 1.2 设计原则
- **向后兼容**: 新版本配置应能读取旧版本数据
- **渐进式迁移**: 支持按需迁移，避免一次性大规模数据转换
- **幂等性**: 迁移操作可重复执行，不会产生重复数据或数据丢失
- **原子性**: 单条记录的迁移操作是原子的，失败时不影响其他数据
- **可监控**: 提供迁移进度跟踪和详细的执行日志

---

## 2. 数据迁移模型定义

### 2.1 SchemaMigration 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| business_object | ForeignKey | BusinessObject | 关联业务对象 |
| from_version | integer | NOT NULL | 源版本号 |
| to_version | integer | NOT NULL | 目标版本号 |
| total_records | integer | default=0 | 总记录数 |
| migrated_records | integer | default=0 | 已迁移记录数 |
| failed_records | integer | default=0 | 失败记录数 |
| status | string | max=50 | pending/running/completed/failed/rolled_back |
| started_at | datetime | nullable | 开始时间 |
| completed_at | datetime | nullable | 完成时间 |
| error_message | text | blank=True | 错误信息 |
| migration_config | JSONB | default=dict | 迁移配置快照 |

### 2.2 MigrationLog 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| migration | ForeignKey | SchemaMigration | 关联迁移任务 |
| action | string | max=50 | migrate/rollback |
| status | string | max=20 | success/failed |
| error_message | text | nullable | 错误信息 |
| executed_at | datetime | auto_now_add | 执行时间 |

### 2.3 FieldDefinition 模型扩展字段

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| version | integer | default=1 | 版本号 |
| is_deprecated | boolean | default=False | 是否已废弃 |
| is_active | boolean | default=True | 是否启用 |
| supersedes | ForeignKey | self (nullable) | 替代的旧版本字段 |
| migration_config | JSONB | default=dict | 迁移配置（转换器等） |

### 2.4 DynamicData 模型扩展字段

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| schema_version | integer | default=1 | Schema版本号 |
| data_version | integer | default=1 | 数据版本号 |
| migration_status | string | max=50 | pending/in_progress/completed/failed |
| last_migration_at | datetime | nullable | 最后迁移时间 |

---

## 3. 模型扩展

### 3.1 FieldDefinition 模型扩展

```python
from django.db import models
from django.core.exceptions import ValidationError
from apps.common.models import BaseModel

class FieldDefinition(BaseModel):
    """
    字段定义模型（支持版本化）
    """
    # === 基础字段 ===
    business_object = models.ForeignKey(
        'BusinessObject',
        on_delete=models.CASCADE,
        related_name='field_definitions',
        verbose_name='所属业务对象'
    )
    name = models.CharField(max_length=100, verbose_name='字段名称')
    label = models.CharField(max_length=200, verbose_name='字段标签')
    field_type = models.CharField(
        max_length=50,
        choices=[
            ('text', '文本'),
            ('number', '数字'),
            ('date', '日期'),
            ('datetime', '日期时间'),
            ('boolean', '布尔值'),
            ('reference', '引用'),
            ('formula', '公式'),
            ('subtable', '子表'),
            ('attachment', '附件'),
        ],
        verbose_name='字段类型'
    )

    # === 版本化字段 ===
    version = models.IntegerField(default=1, verbose_name='版本号')
    is_deprecated = models.BooleanField(default=False, verbose_name='是否已废弃')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    supersedes = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='deprecated_by',
        verbose_name='替代的旧版本字段'
    )

    # === 迁移配置 ===
    migration_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='迁移配置',
        help_text='字段迁移映射规则和转换逻辑'
    )

    # === 字段属性 ===
    options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='字段选项',
        help_text='存储字段的具体配置（required, default, validation_rules等）'
    )
    display_order = models.IntegerField(default=0, verbose_name='显示顺序')

    class Meta:
        db_table = 'system_field_definition'
        verbose_name = '字段定义'
        verbose_name_plural = '字段定义'
        unique_together = [['business_object', 'name', 'version']]
        ordering = ['business_object', 'display_order', 'id']

    def __str__(self):
        return f'{self.business_object.name} - {self.label} (v{self.version})'

    def clean(self):
        """验证字段定义"""
        if self.supersedes and self.supersedes.business_object != self.business_object:
            raise ValidationError('只能替代同一业务对象下的字段')

        if self.supersedes and self.supersedes.version >= self.version:
            raise ValidationError('新字段版本号必须大于被替代的旧字段版本号')

    def get_migration_strategy(self):
        """获取字段迁移策略"""
        return self.migration_config.get('strategy', 'copy')

    def is_compatible_with(self, data_version):
        """检查字段是否与指定数据版本兼容"""
        if not self.is_deprecated:
            return True
        # 检查数据版本是否在字段的有效版本范围内
        valid_from = self.supersedes.version if self.supersedes else 1
        return data_version >= valid_from
```

### 2.2 DynamicData 模型扩展

```python
class DynamicData(BaseModel):
    """
    动态数据模型（支持版本化）
    """
    # === 关联关系 ===
    business_object = models.ForeignKey(
        'BusinessObject',
        on_delete=models.CASCADE,
        related_name='dynamic_data',
        verbose_name='业务对象'
    )

    # === 版本控制 ===
    schema_version = models.IntegerField(
        default=1,
        verbose_name='Schema版本号',
        help_text='数据创建时使用的Schema版本'
    )
    data_version = models.IntegerField(
        default=1,
        verbose_name='数据版本号',
        help_text='当前数据的实际版本（经过迁移后可能大于schema_version）'
    )

    # === 动态数据存储 ===
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='动态字段数据'
    )

    # === 业务标识 ===
    external_id = models.CharField(
        max_length=200,
        unique=True,
        null=True,
        blank=True,
        verbose_name='外部系统ID'
    )
    title = models.CharField(max_length=500, verbose_name='数据标题')

    # === 迁移状态 ===
    migration_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', '待迁移'),
            ('in_progress', '迁移中'),
            ('completed', '已完成'),
            ('failed', '失败'),
        ],
        default='completed',
        verbose_name='迁移状态'
    )
    last_migration_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后迁移时间'
    )

    class Meta:
        db_table = 'system_dynamic_data'
        verbose_name = '动态数据'
        verbose_name_plural = '动态数据'
        indexes = [
            models.Index(fields=['business_object', 'schema_version']),
            models.Index(fields=['business_object', 'data_version']),
            models.Index(fields=['migration_status']),
        ]

    def __str__(self):
        return f'{self.business_object.name} - {self.title} (v{self.data_version})'

    def needs_migration(self, target_version):
        """检查是否需要迁移到目标版本"""
        return self.data_version < target_version

    def get_field_value(self, field_name, field_definition):
        """
        获取字段值（支持多版本兼容）
        - 优先从当前版本字段读取
        - 如果字段不存在，尝试从旧版本字段读取
        """
        # 直接读取
        if field_name in self.custom_fields:
            return self.custom_fields[field_name]

        # 如果字段被废弃，尝试从旧字段名读取
        if field_definition.is_deprecated and field_definition.supersedes:
            old_field_name = field_definition.supersedes.name
            return self.custom_fields.get(old_field_name)

        return None

    def set_field_value(self, field_name, value):
        """设置字段值"""
        self.custom_fields[field_name] = value
```

### 2.3 SchemaMigrationLog 模型

```python
class SchemaMigrationLog(BaseModel):
    """
    Schema迁移日志模型
    """
    business_object = models.ForeignKey(
        'BusinessObject',
        on_delete=models.CASCADE,
        related_name='migration_logs',
        verbose_name='业务对象'
    )

    # === 版本信息 ===
    from_version = models.IntegerField(verbose_name='源版本')
    to_version = models.IntegerField(verbose_name='目标版本')

    # === 迁移统计 ===
    total_records = models.IntegerField(default=0, verbose_name='总记录数')
    migrated_records = models.IntegerField(default=0, verbose_name='已迁移记录数')
    failed_records = models.IntegerField(default=0, verbose_name='失败记录数')

    # === 执行信息 ===
    status = models.CharField(
        max_length=50,
        choices=[
            ('pending', '待执行'),
            ('running', '执行中'),
            ('completed', '已完成'),
            ('failed', '失败'),
            ('rolled_back', '已回滚'),
        ],
        default='pending',
        verbose_name='状态'
    )
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    error_message = models.TextField(blank=True, verbose_name='错误信息')

    # === 配置快照 ===
    migration_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='迁移配置快照'
    )

    class Meta:
        db_table = 'system_schema_migration_log'
        verbose_name = 'Schema迁移日志'
        verbose_name_plural = 'Schema迁移日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.business_object.name}: v{self.from_version} -> v{self.to_version}'
```

---

## 3. 数据迁移服务

### 3.1 SchemaMigrationService 核心服务

```python
from typing import Dict, List, Any, Optional, Callable
from django.db import transaction
from django.utils import timezone
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    DynamicData,
    SchemaMigrationLog
)
import logging

logger = logging.getLogger(__name__)


class SchemaMigrationService:
    """
    Schema迁移服务
    负责处理字段配置变更后的数据迁移
    """

    def __init__(self, business_object: BusinessObject):
        self.business_object = business_object
        self.migration_log = None

    def migrate_to_version(
        self,
        target_version: int,
        batch_size: int = 100,
        async_task: bool = False
    ) -> SchemaMigrationLog:
        """
        迁移数据到目标版本

        Args:
            target_version: 目标Schema版本号
            batch_size: 批量处理大小
            async_task: 是否异步执行（使用Celery）

        Returns:
            SchemaMigrationLog: 迁移日志记录
        """
        current_version = self._get_current_schema_version()
        if current_version >= target_version:
            raise ValueError(f'当前版本 {current_version} 已大于或等于目标版本 {target_version}')

        # 创建迁移日志
        self.migration_log = SchemaMigrationLog.objects.create(
            business_object=self.business_object,
            from_version=current_version,
            to_version=target_version,
            status='pending',
            migration_config=self._build_migration_config(current_version, target_version)
        )

        if async_task:
            # 异步执行迁移
            from apps.system.tasks import execute_schema_migration
            execute_schema_migration.delay(self.migration_log.id, batch_size)
        else:
            # 同步执行迁移
            self._execute_migration(batch_size)

        return self.migration_log

    def _get_current_schema_version(self) -> int:
        """获取当前Schema版本号"""
        latest_field = FieldDefinition.objects.filter(
            business_object=self.business_object
        ).order_by('-version').first()

        return latest_field.version if latest_field else 1

    def _build_migration_config(self, from_version: int, to_version: int) -> Dict:
        """
        构建迁移配置
        分析从from_version到to_version之间的所有字段变更
        """
        config = {
            'from_version': from_version,
            'to_version': to_version,
            'field_mappings': {},
            'field_transformations': {},
            'deprecated_fields': [],
            'new_fields': []
        }

        # 获取所有相关字段定义
        fields = FieldDefinition.objects.filter(
            business_object=self.business_object,
            version__gte=from_version,
            version__lte=to_version
        ).order_by('version')

        for field in fields:
            # 新增字段
            if field.version > from_version and not field.supersedes:
                config['new_fields'].append({
                    'name': field.name,
                    'version': field.version,
                    'default_value': field.options.get('default')
                })

            # 废弃字段
            elif field.is_deprecated and field.version == from_version:
                config['deprecated_fields'].append({
                    'name': field.name,
                    'replaced_by': field.deprecated_by.first().name if field.deprecated_by.exists() else None
                })

            # 字段映射（重命名或类型转换）
            elif field.supersedes:
                config['field_mappings'][field.supersedes.name] = field.name
                if field.migration_config.get('transformer'):
                    config['field_transformations'][field.name] = field.migration_config['transformer']

        return config

    @transaction.atomic
    def _execute_migration(self, batch_size: int = 100):
        """执行数据迁移（事务性）"""
        try:
            self.migration_log.status = 'running'
            self.migration_log.started_at = timezone.now()
            self.migration_log.save()

            logger.info(f'开始迁移 {self.business_object.name} '
                       f'从 v{self.migration_log.from_version} 到 v{self.migration_log.to_version}')

            # 获取需要迁移的数据
            queryset = DynamicData.objects.filter(
                business_object=self.business_object,
                data_version__lt=self.migration_log.to_version,
                migration_status='completed'
            )

            self.migration_log.total_records = queryset.count()
            self.migration_log.save()

            # 批量迁移数据
            migrated_count = 0
            failed_count = 0

            for offset in range(0, queryset.count(), batch_size):
                batch = queryset[offset:offset + batch_size]

                for data_record in batch:
                    try:
                        self._migrate_record(data_record)
                        migrated_count += 1
                    except Exception as e:
                        logger.error(f'迁移记录 {data_record.id} 失败: {str(e)}')
                        failed_count += 1
                        data_record.migration_status = 'failed'
                        data_record.save()

                # 更新进度
                self.migration_log.migrated_records = migrated_count
                self.migration_log.failed_records = failed_count
                self.migration_log.save()

            # 完成迁移
            self.migration_log.status = 'completed'
            self.migration_log.completed_at = timezone.now()
            self.migration_log.save()

            logger.info(f'迁移完成: 成功 {migrated_count}, 失败 {failed_count}')

        except Exception as e:
            logger.error(f'迁移失败: {str(e)}')
            self.migration_log.status = 'failed'
            self.migration_log.error_message = str(e)
            self.migration_log.completed_at = timezone.now()
            self.migration_log.save()
            raise

    def _migrate_record(self, data_record: DynamicData):
        """迁移单条数据记录"""
        config = self.migration_log.migration_config
        new_custom_fields = data_record.custom_fields.copy()

        # 1. 处理字段映射（重命名字段）
        for old_name, new_name in config['field_mappings'].items():
            if old_name in new_custom_fields:
                new_custom_fields[new_name] = new_custom_fields.pop(old_name)

        # 2. 处理字段转换（类型转换或值转换）
        for field_name, transformer in config['field_transformations'].items():
            if field_name in new_custom_fields:
                try:
                    new_custom_fields[field_name] = self._apply_transformer(
                        new_custom_fields[field_name],
                        transformer
                    )
                except Exception as e:
                    logger.warning(f'字段 {field_name} 转换失败: {str(e)}')

        # 3. 处理新增字段（设置默认值）
        for new_field in config['new_fields']:
            field_name = new_field['name']
            if field_name not in new_custom_fields:
                new_custom_fields[field_name] = new_field.get('default_value')

        # 4. 处理废弃字段（可选：保留或删除）
        # 默认策略：保留旧字段数据（向后兼容）
        # 如果需要删除，可以在migration_config中配置 remove_deprecated_fields: true

        # 更新数据记录
        data_record.custom_fields = new_custom_fields
        data_record.data_version = self.migration_log.to_version
        data_record.migration_status = 'completed'
        data_record.last_migration_at = timezone.now()
        data_record.save()

    def _apply_transformer(self, value: Any, transformer: Dict) -> Any:
        """
        应用字段转换器

        支持的转换类型:
        - type_cast: 类型转换（string->number, string->boolean等）
        - value_map: 值映射（枚举值转换）
        - formula: 公式计算
        - custom: 自定义函数
        """
        transform_type = transformer.get('type')

        if transform_type == 'type_cast':
            target_type = transformer.get('target_type')
            return self._type_cast(value, target_type)

        elif transform_type == 'value_map':
            mapping = transformer.get('mapping', {})
            return mapping.get(value, value)

        elif transform_type == 'formula':
            formula = transformer.get('formula')
            # 使用simpleeval安全计算公式
            from simpleeval import simple_eval
            return simple_eval(formula, names={'value': value})

        elif transform_type == 'custom':
            # 调用自定义转换函数
            func_path = transformer.get('function')
            module_path, func_name = func_path.rsplit('.', 1)
            from importlib import import_module
            module = import_module(module_path)
            func = getattr(module, func_name)
            return func(value, transformer.get('params', {}))

        return value

    def _type_cast(self, value: Any, target_type: str) -> Any:
        """类型转换"""
        if value is None:
            return None

        try:
            if target_type == 'string':
                return str(value)
            elif target_type == 'number':
                return float(value)
            elif target_type == 'integer':
                return int(float(value))
            elif target_type == 'boolean':
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif target_type == 'date':
                from datetime import datetime
                if isinstance(value, str):
                    return datetime.strptime(value, '%Y-%m-%d').date()
                return value
            elif target_type == 'datetime':
                from datetime import datetime
                if isinstance(value, str):
                    return datetime.fromisoformat(value)
                return value
            else:
                return value
        except (ValueError, TypeError) as e:
            logger.warning(f'类型转换失败: {value} -> {target_type}, 错误: {str(e)}')
            return None

    def rollback_migration(self) -> bool:
        """回滚迁移（如果有备份）"""
        if self.migration_log.status != 'completed':
            raise ValueError('只能回滚已完成的迁移')

        try:
            # TODO: 实现回滚逻辑（需要迁移时备份数据）
            self.migration_log.status = 'rolled_back'
            self.migration_log.save()
            return True
        except Exception as e:
            logger.error(f'回滚失败: {str(e)}')
            return False
```

### 3.2 字段映射转换工具

```python
class FieldMapper:
    """
    字段映射转换工具
    用于处理复杂的字段映射和数据转换逻辑
    """

    @staticmethod
    def create_field_mapping(
        old_field: FieldDefinition,
        new_field: FieldDefinition,
        transformer: Optional[Dict] = None
    ) -> Dict:
        """
        创建字段映射配置

        Args:
            old_field: 旧字段定义
            new_field: 新字段定义
            transformer: 转换器配置

        Returns:
            字段映射配置字典
        """
        mapping = {
            'old_field_name': old_field.name,
            'new_field_name': new_field.name,
            'old_field_type': old_field.field_type,
            'new_field_type': new_field.field_type,
            'transformer': transformer or {}
        }

        # 自动生成类型转换器
        if old_field.field_type != new_field.field_type:
            mapping['transformer'] = {
                'type': 'type_cast',
                'target_type': new_field.field_type
            }

        return mapping

    @staticmethod
    def create_value_mapping(
        field: FieldDefinition,
        value_map: Dict[str, Any]
    ) -> Dict:
        """
        创建值映射配置

        用于枚举值或分类值的转换

        Example:
            create_value_mapping(
                field,
                {
                    'active': '1',
                    'inactive': '0',
                    'pending': '2'
                }
            )
        """
        return {
            'field_name': field.name,
            'transformer': {
                'type': 'value_map',
                'mapping': value_map
            }
        }

    @staticmethod
    def create_formula_transformer(
        field: FieldDefinition,
        formula: str
    ) -> Dict:
        """
        创建公式转换器

        Example:
            create_formula_transformer(field, 'value * 1.1')
        """
        return {
            'field_name': field.name,
            'transformer': {
                'type': 'formula',
                'formula': formula
            }
        }

    @staticmethod
    def create_custom_transformer(
        field: FieldDefinition,
        function_path: str,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        创建自定义转换器

        Args:
            field: 字段定义
            function_path: 函数路径（如 'apps.utils.transformers.format_phone'）
            params: 额外参数

        Example:
            create_custom_transformer(
                field,
                'apps.assets.utils.transformers.format_phone_number',
                {'country_code': '+86'}
            )
        """
        return {
            'field_name': field.name,
            'transformer': {
                'type': 'custom',
                'function': function_path,
                'params': params or {}
            }
        }
```

### 3.3 批量数据迁移管理器

```python
class BulkMigrationManager:
    """
    批量数据迁移管理器
    用于管理大规模数据迁移任务
    """

    def __init__(self):
        self.active_migrations = {}

    def start_migration(
        self,
        business_object_id: int,
        target_version: int,
        options: Optional[Dict] = None
    ) -> str:
        """
        启动批量迁移任务

        Returns:
            任务ID
        """
        from apps.system.models import BusinessObject

        business_object = BusinessObject.objects.get(id=business_object_id)
        service = SchemaMigrationService(business_object)

        options = options or {}
        migration_log = service.migrate_to_version(
            target_version=target_version,
            batch_size=options.get('batch_size', 100),
            async_task=options.get('async', True)
        )

        task_id = f'migration_{migration_log.id}'
        self.active_migrations[task_id] = {
            'log_id': migration_log.id,
            'status': 'running',
            'started_at': timezone.now()
        }

        return task_id

    def get_migration_progress(self, task_id: str) -> Dict:
        """获取迁移进度"""
        if task_id not in self.active_migrations:
            raise ValueError('任务不存在')

        task_info = self.active_migrations[task_id]
        log_id = task_info['log_id']

        migration_log = SchemaMigrationLog.objects.get(id=log_id)

        return {
            'task_id': task_id,
            'status': migration_log.status,
            'total_records': migration_log.total_records,
            'migrated_records': migration_log.migrated_records,
            'failed_records': migration_log.failed_records,
            'progress_percent': (
                migration_log.migrated_records / migration_log.total_records * 100
                if migration_log.total_records > 0 else 0
            ),
            'started_at': migration_log.started_at,
            'completed_at': migration_log.completed_at,
            'error_message': migration_log.error_message
        }

    def cancel_migration(self, task_id: str) -> bool:
        """取消迁移任务"""
        if task_id not in self.active_migrations:
            return False

        # TODO: 实现取消逻辑（通过Celery revoke）
        task_info = self.active_migrations[task_id]
        log_id = task_info['log_id']

        migration_log = SchemaMigrationLog.objects.get(id=log_id)
        if migration_log.status == 'running':
            migration_log.status = 'cancelled'
            migration_log.save()

        return True

    def retry_failed_migration(self, log_id: int) -> bool:
        """重试失败的迁移"""
        migration_log = SchemaMigrationLog.objects.get(id=log_id)

        if migration_log.status != 'failed':
            raise ValueError('只能重试失败的迁移任务')

        # 重置状态并重新执行
        migration_log.status = 'pending'
        migration_log.error_message = ''
        migration_log.failed_records = 0
        migration_log.save()

        # 重新执行迁移
        from apps.system.tasks import execute_schema_migration
        execute_schema_migration.delay(log_id, 100)

        return True
```

---

## 4. 版本兼容层

### 4.1 MetadataDrivenSerializer 多版本支持

```python
from rest_framework import serializers
from apps.system.models import FieldDefinition, DynamicData

class MetadataDrivenSerializer(serializers.Serializer):
    """
    元数据驱动的序列化器（支持多版本字段）
    """

    def __init__(self, *args, **kwargs):
        self.business_object = kwargs.pop('business_object', None)
        self.schema_version = kwargs.pop('schema_version', None)
        self.data_version = kwargs.pop('data_version', None)

        super().__init__(*args, **kwargs)

        if self.business_object:
            self._build_fields()

    def _build_fields(self):
        """根据字段定义动态构建字段"""
        # 获取适用的字段定义
        fields = self._get_applicable_fields()

        for field_def in fields:
            field_instance = self._create_field(field_def)
            self.fields[field_def.name] = field_instance

    def _get_applicable_fields(self) -> List[FieldDefinition]:
        """
        获取适用的字段定义
        - 如果指定了schema_version，使用该版本的字段
        - 否则使用最新版本的启用字段
        """
        queryset = FieldDefinition.objects.filter(
            business_object=self.business_object,
            is_active=True
        )

        if self.schema_version:
            # 获取指定版本的字段
            queryset = queryset.filter(version=self.schema_version)
        else:
            # 获取最新版本字段（排除已废弃的字段）
            queryset = queryset.filter(is_deprecated=False)

        return queryset.order_by('display_order')

    def _create_field(self, field_def: FieldDefinition) -> serializers.Field:
        """根据字段定义创建序列化器字段"""
        field_type = field_def.field_type
        options = field_def.options or {}

        field_params = {
            'required': options.get('required', False),
            'allow_null': options.get('allow_null', True),
            'label': field_def.label,
            'help_text': options.get('help_text', ''),
        }

        # 设置默认值
        if 'default' in options:
            field_params['default'] = options['default']

        # 根据字段类型创建对应的序列化器字段
        if field_type == 'text':
            field_params['max_length'] = options.get('max_length', 200)
            return serializers.CharField(**field_params)

        elif field_type == 'number':
            return serializers.FloatField(**field_params)

        elif field_type == 'integer':
            return serializers.IntegerField(**field_params)

        elif field_type == 'date':
            return serializers.DateField(**field_params)

        elif field_type == 'datetime':
            return serializers.DateTimeField(**field_params)

        elif field_type == 'boolean':
            return serializers.BooleanField(**field_params)

        elif field_type == 'reference':
            # 引用字段（外键）
            return serializers.IntegerField(
                **{**field_params, 'allow_null': True}
            )

        elif field_type == 'subtable':
            # 子表字段（嵌套序列化器）
            return serializers.ListField(
                child=serializers.DictField(),
                **{**field_params, 'required': False}
            )

        elif field_type == 'attachment':
            # 附件字段
            return serializers.ListField(
                child=serializers.CharField(),
                **{**field_params, 'required': False}
            )

        else:
            # 默认文本字段
            return serializers.CharField(**field_params)

    def to_representation(self, instance):
        """
        序列化时处理多版本兼容
        - 优先使用当前版本字段
        - 如果字段不存在，尝试从旧版本字段读取
        """
        data = super().to_representation(instance)

        # 如果是DynamicData实例，处理custom_fields
        if isinstance(instance, DynamicData):
            # 获取所有适用的字段定义
            fields = self._get_applicable_fields()

            for field_def in fields:
                # 如果字段在custom_fields中不存在，尝试从旧字段读取
                if field_def.name not in data and field_def.is_deprecated:
                    old_field = field_def.supersedes
                    if old_field and old_field.name in instance.custom_fields:
                        data[field_def.name] = instance.custom_fields[old_field.name]

        return data

    def to_internal_value(self, data):
        """
        反序列化时处理多版本兼容
        - 支持旧版本字段名自动映射到新字段名
        """
        # 获取字段映射关系
        field_mappings = self._get_field_mappings()

        # 应用字段映射
        for old_name, new_name in field_mappings.items():
            if old_name in data and new_name not in data:
                data[new_name] = data.pop(old_name)

        return super().to_internal_value(data)

    def _get_field_mappings(self) -> Dict[str, str]:
        """获取字段映射关系（旧字段名 -> 新字段名）"""
        mappings = {}

        fields = FieldDefinition.objects.filter(
            business_object=self.business_object,
            is_deprecated=False,
            supersedes__isnull=False
        )

        for field in fields:
            if field.supersedes:
                mappings[field.supersedes.name] = field.name

        return mappings
```

### 4.2 版本兼容的查询服务

```python
class VersionAwareQueryService:
    """
    版本感知的查询服务
    提供跨版本数据查询能力
    """

    def __init__(self, business_object: BusinessObject):
        self.business_object = business_object

    def query_data(
        self,
        filters: Optional[Dict] = None,
        schema_version: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict]:
        """
        查询动态数据（支持多版本）

        Args:
            filters: 过滤条件（支持新版本和旧版本字段名）
            schema_version: 指定Schema版本（None表示最新版本）
            order_by: 排序字段

        Returns:
            标准化后的数据列表（使用最新版本字段名）
        """
        queryset = DynamicData.objects.filter(
            business_object=self.business_object
        )

        if schema_version:
            queryset = queryset.filter(schema_version=schema_version)

        # 应用过滤条件（处理字段映射）
        if filters:
            queryset = self._apply_filters(queryset, filters, schema_version)

        # 排序
        if order_by:
            queryset = queryset.order_by(order_by)

        # 标准化数据（统一使用最新版本字段名）
        return [
            self._normalize_data(record, schema_version)
            for record in queryset
        ]

    def _apply_filters(self, queryset, filters: Dict, schema_version: Optional[int]):
        """
        应用过滤条件（支持旧版本字段名）
        """
        # 获取字段映射关系
        field_mappings = self._get_reverse_field_mappings(schema_version)

        # 转换旧字段名到新字段名
        normalized_filters = {}
        for field_name, value in filters.items():
            normalized_name = field_mappings.get(field_name, field_name)
            filter_key = f'custom_fields__{normalized_name}'
            normalized_filters[filter_key] = value

        return queryset.filter(**normalized_filters)

    def _normalize_data(self, record: DynamicData, schema_version: Optional[int]) -> Dict:
        """
        标准化数据记录（统一使用最新版本字段名）
        """
        # 获取目标版本的字段定义
        if schema_version:
            fields = FieldDefinition.objects.filter(
                business_object=self.business_object,
                version=schema_version
            )
        else:
            # 使用最新版本
            fields = FieldDefinition.objects.filter(
                business_object=self.business_object,
                is_deprecated=False
            )

        normalized_data = {
            'id': record.id,
            'title': record.title,
            'schema_version': record.schema_version,
            'data_version': record.data_version,
            'custom_fields': {}
        }

        for field in fields:
            value = record.get_field_value(field.name, field)
            normalized_data['custom_fields'][field.name] = value

        return normalized_data

    def _get_reverse_field_mappings(self, schema_version: Optional[int]) -> Dict[str, str]:
        """
        获取反向字段映射（新字段名 -> 旧字段名）
        用于将旧版本字段名映射到最新版本字段名
        """
        mappings = {}

        fields = FieldDefinition.objects.filter(
            business_object=self.business_object,
            supersedes__isnull=False
        )

        for field in fields:
            # 映射: 旧字段名 -> 新字段名
            if field.supersedes:
                mappings[field.supersedes.name] = field.name

        return mappings
```

### 4.3 向后兼容的API视图

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.models import BusinessObject, DynamicData
from apps.system.serializers import MetadataDrivenSerializer

class VersionAwareModelViewSet(viewsets.ModelViewSet):
    """
    版本感知的模型视图集
    支持多版本数据的CRUD操作
    """

    def get_serializer(self, *args, **kwargs):
        """
        获取序列化器（自动注入版本信息）
        """
        business_object = self.get_business_object()
        schema_version = self.request.query_params.get('schema_version')

        serializer_class = self.get_serializer_class()

        return serializer_class(
            *args,
            business_object=business_object,
            schema_version=schema_version,
            **kwargs
        )

    def get_business_object(self) -> BusinessObject:
        """获取业务对象（子类需实现）"""
        raise NotImplementedError

    def list(self, request, *args, **kwargs):
        """
        列表接口（支持多版本查询）
        Query Parameters:
            - schema_version: 指定Schema版本（可选）
            - data_version: 指定数据版本（可选）
        """
        schema_version = request.query_params.get('schema_version')
        data_version = request.query_params.get('data_version')

        queryset = self.get_queryset()

        if schema_version:
            queryset = queryset.filter(schema_version=schema_version)

        if data_version:
            queryset = queryset.filter(data_version=data_version)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        详情接口（支持多版本数据）
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def migrate(self, request):
        """
        触发数据迁移

        Request Body:
            {
                "target_version": 2,
                "batch_size": 100,
                "async": true
            }
        """
        target_version = request.data.get('target_version')
        batch_size = request.data.get('batch_size', 100)
        async_mode = request.data.get('async', True)

        business_object = self.get_business_object()

        service = SchemaMigrationService(business_object)
        migration_log = service.migrate_to_version(
            target_version=target_version,
            batch_size=batch_size,
            async_task=async_mode
        )

        return Response({
            'migration_id': migration_log.id,
            'status': migration_log.status,
            'from_version': migration_log.from_version,
            'to_version': migration_log.to_version,
            'total_records': migration_log.total_records
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def migration_status(self, request, pk=None):
        """获取迁移状态"""
        try:
            migration_log = SchemaMigrationLog.objects.get(id=pk)
            manager = BulkMigrationManager()

            progress = manager.get_migration_progress(f'migration_{pk}')

            return Response(progress)
        except SchemaMigrationLog.DoesNotExist:
            return Response(
                {'error': '迁移任务不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
```

---

## 5. 实施指南

### 5.1 字段变更场景处理

#### 场景1: 字段重命名
```python
# 1. 创建新版本字段定义
new_field = FieldDefinition.objects.create(
    business_object=asset_object,
    name='asset_code_new',  # 新字段名
    label='资产编码',
    field_type='text',
    version=2,  # 新版本
    supersedes=old_field,  # 指向旧字段
    options={'required': True, 'max_length': 50}
)

# 2. 执行数据迁移
service = SchemaMigrationService(asset_object)
migration_log = service.migrate_to_version(target_version=2)
```

#### 场景2: 字段类型转换
```python
# 1. 配置转换器
new_field = FieldDefinition.objects.create(
    business_object=asset_object,
    name='purchase_price',
    label='采购价格',
    field_type='number',  # 从text改为number
    version=2,
    supersedes=old_field,
    migration_config={
        'strategy': 'transform',
        'transformer': {
            'type': 'type_cast',
            'target_type': 'number'
        }
    }
)

# 2. 执行迁移（自动转换数据类型）
service.migrate_to_version(target_version=2)
```

#### 场景3: 字段值映射（枚举值变更）
```python
# 1. 配置值映射转换器
new_field = FieldDefinition.objects.create(
    business_object=asset_object,
    name='status',
    label='状态',
    field_type='text',
    version=2,
    supersedes=old_field,
    migration_config={
        'strategy': 'transform',
        'transformer': {
            'type': 'value_map',
            'mapping': {
                '0': 'inactive',
                '1': 'active',
                '2': 'pending'
            }
        }
    }
)
```

#### 场景4: 字段拆分
```python
# 1. 原字段: full_name (文本)
# 2. 拆分为: first_name 和 last_name

# 创建自定义转换器
def split_full_name(value, params):
    parts = value.split()
    return {
        'first_name': parts[0] if parts else '',
        'last_name': ' '.join(parts[1:]) if len(parts) > 1 else ''
    }

# 配置迁移
first_name_field = FieldDefinition.objects.create(
    business_object=asset_object,
    name='first_name',
    label='名',
    field_type='text',
    version=2,
    migration_config={
        'strategy': 'custom',
        'transformer': {
            'type': 'custom',
            'function': 'apps.utils.migrations.split_full_name',
            'params': {}
        }
    }
)
```

### 5.2 迁移流程最佳实践

#### 阶段1: 准备阶段
1. **分析影响范围**
   - 统计受影响的数据量
   - 识别依赖关系（其他对象/字段的引用）

2. **设计迁移方案**
   - 定义字段映射关系
   - 编写数据转换逻辑
   - 制定回滚计划

3. **测试环境验证**
   - 在测试环境执行迁移
   - 验证数据完整性
   - 性能测试（评估迁移时间）

#### 阶段2: 执行阶段
1. **创建迁移任务**
   ```python
   service = SchemaMigrationService(business_object)
   migration_log = service.migrate_to_version(
       target_version=2,
       batch_size=500,  # 根据数据量调整
       async_task=True  # 使用异步任务
   )
   ```

2. **监控迁移进度**
   ```python
   manager = BulkMigrationManager()
   progress = manager.get_migration_progress(f'migration_{migration_log.id}')
   print(f"进度: {progress['progress_percent']:.2f}%")
   ```

3. **处理失败记录**
   - 查看失败日志
   - 修复数据问题
   - 重试失败记录

#### 阶段3: 验证阶段
1. **数据一致性检查**
   - 对比迁移前后数据量
   - 验证关键字段的值

2. **功能测试**
   - 测试业务功能是否正常
   - 验证新旧版本数据都能正常访问

3. **性能测试**
   - 测试查询性能
   - 优化索引（如有必要）

### 5.3 回滚策略

#### 方案1: 保留旧字段（推荐）
```python
# 1. 迁移时保留旧字段
migration_config = {
    'remove_deprecated_fields': False  # 不删除旧字段
}

# 2. 回滚时切换字段定义
old_field.is_deprecated = False
new_field.is_active = False
old_field.save()
new_field.save()
```

#### 方案2: 数据备份恢复
```python
# 1. 迁移前备份数据
backup_data = DynamicData.objects.filter(
    business_object=business_object
).values()

# 2. 存储备份
import json
with open(f'backup_{business_object.name}_{timezone.now().date()}.json', 'w') as f:
    json.dump(list(backup_data), f)

# 3. 回滚时恢复数据
with open(backup_file, 'r') as f:
    backup_data = json.load(f)
    for record in backup_data:
        DynamicData.objects.filter(id=record['id']).update(**record)
```

---

## 6. 监控与告警

### 6.1 迁移监控指标

```python
class MigrationMonitor:
    """
    迁移监控器
    跟踪迁移过程的各项指标
    """

    def __init__(self, migration_log: SchemaMigrationLog):
        self.migration_log = migration_log

    def get_metrics(self) -> Dict:
        """获取迁移指标"""
        return {
            'migration_id': self.migration_log.id,
            'status': self.migration_log.status,
            'progress_percent': self._calculate_progress(),
            'average_speed': self._calculate_speed(),  # 记录/秒
            'estimated_time_remaining': self._estimate_time_remaining(),
            'error_rate': self._calculate_error_rate(),
            'failed_records_sample': self._get_failed_records_sample()
        }

    def _calculate_progress(self) -> float:
        """计算进度百分比"""
        if self.migration_log.total_records == 0:
            return 0.0
        return (
            self.migration_log.migrated_records /
            self.migration_log.total_records * 100
        )

    def _calculate_speed(self) -> float:
        """计算迁移速度（记录/秒）"""
        if not self.migration_log.started_at:
            return 0.0

        elapsed = (
            timezone.now() - self.migration_log.started_at
        ).total_seconds()

        if elapsed == 0:
            return 0.0

        return self.migration_log.migrated_records / elapsed

    def _estimate_time_remaining(self) -> Optional[int]:
        """估算剩余时间（秒）"""
        speed = self._calculate_speed()
        if speed == 0:
            return None

        remaining = (
            self.migration_log.total_records -
            self.migration_log.migrated_records
        )

        return int(remaining / speed)

    def _calculate_error_rate(self) -> float:
        """计算错误率"""
        total_processed = (
            self.migration_log.migrated_records +
            self.migration_log.failed_records
        )

        if total_processed == 0:
            return 0.0

        return self.migration_log.failed_records / total_processed * 100

    def _get_failed_records_sample(self, limit: int = 10) -> List[Dict]:
        """获取失败记录样本"""
        failed_data = DynamicData.objects.filter(
            business_object=self.migration_log.business_object,
            migration_status='failed'
        ).values('id', 'title', 'custom_fields')[:limit]

        return list(failed_data)
```

### 6.2 告警规则

```python
class MigrationAlertService:
    """
    迁移告警服务
    """

    ALERT_RULES = {
        'high_error_rate': {
            'condition': lambda metrics: metrics['error_rate'] > 5.0,  # 错误率>5%
            'severity': 'warning',
            'message': '迁移错误率过高: {error_rate}%'
        },
        'stuck': {
            'condition': lambda metrics: (
                metrics['status'] == 'running' and
                metrics['average_speed'] < 1.0  # 速度<1记录/秒
            ),
            'severity': 'warning',
            'message': '迁移速度过慢: {average_speed} 记录/秒'
        },
        'failed': {
            'condition': lambda metrics: metrics['status'] == 'failed',
            'severity': 'critical',
            'message': '迁移失败: {error_message}'
        },
        'timeout': {
            'condition': lambda metrics: (
                metrics['estimated_time_remaining'] and
                metrics['estimated_time_remaining'] > 86400  # 超过24小时
            ),
            'severity': 'warning',
            'message': '预计迁移时间过长: {estimated_time_remaining} 秒'
        }
    }

    def check_alerts(self, migration_log: SchemaMigrationLog) -> List[Dict]:
        """检查告警规则"""
        monitor = MigrationMonitor(migration_log)
        metrics = monitor.get_metrics()

        alerts = []
        for rule_name, rule in self.ALERT_RULES.items():
            if rule['condition'](metrics):
                alerts.append({
                    'rule': rule_name,
                    'severity': rule['severity'],
                    'message': rule['message'].format(**metrics)
                })

        return alerts

    def send_alert(self, alert: Dict):
        """发送告警通知"""
        # TODO: 集成告警通道（邮件/钉钉/企业微信）
        logger.warning(f"迁移告警: {alert['message']}")
```

---

## 7. 总结

### 7.1 核心能力
- **版本化字段管理**: 支持字段定义的版本演进和变更追溯
- **平滑数据迁移**: 提供可控的批量数据迁移机制
- **向后兼容**: 新旧版本数据共存，保证业务连续性
- **灵活转换**: 支持类型转换、值映射、公式计算等多种数据转换策略
- **可监控可回滚**: 完善的迁移监控和回滚机制

### 7.2 使用场景
- 字段重命名/类型转换
- 枚举值变更
- 字段拆分/合并
- 复杂业务逻辑变更
- Schema升级

### 7.3 后续优化方向
- **自动化迁移建议**: 基于AI分析字段变更，自动生成迁移方案
- **可视化迁移工具**: 提供Web界面管理迁移任务
- **增量迁移**: 支持增量数据迁移（仅迁移变更部分）
- **跨对象迁移**: 支持跨业务对象的数据迁移
- **性能优化**: 使用数据库原生批量操作提升迁移速度

---

**文档版本**: 1.0
**最后更新**: 2026-01-15
**维护者**: GZEAMS开发团队
