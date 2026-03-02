# Phase 5.4: 财务报表生成 - 后端实现

## 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法、组织隔离 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤 |

---

## 1. 数据模型设计

### 1.1 报表模板 (ReportTemplate)

```python
# apps/reports/models.py

from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class ReportTemplate(BaseModel):
    """
    报表模板
    定义报表的结构和格式
    """
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '启用'),
        ('archived', '归档'),
    ]

    # 基本信息
    template_code = models.CharField(max_length=50, unique=True, verbose_name='模板代码')
    template_name = models.CharField(max_length=200, verbose_name='模板名称')
    description = models.TextField(blank=True, verbose_name='模板描述')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')

    # 报表类型
    report_type = models.CharField(
        max_length=50,
        choices=[
            ('asset_detail', '资产明细表'),
            ('depreciation_summary', '折旧汇总表'),
            ('asset_change', '资产增减变动表'),
            ('disposal_detail', '资产处置明细表'),
            ('category_analysis', '类别分析表'),
            ('department_analysis', '部门分析表'),
            ('custom', '自定义报表'),
        ],
        verbose_name='报表类型'
    )

    # 模板配置
    template_config = models.JSONField(default=dict, verbose_name='模板配置')
    # 包含: layout, sections, columns, styles, etc.

    # 数据源配置
    data_source = models.JSONField(default=dict, verbose_name='数据源配置')
    # {
    #   "type": "model|sql|api|aggregate",
    #   "model": "assets.Asset",
    #   "fields": [...],
    #   "filters": [...],
    #   "order_by": [...]
    # }

    # 权限配置
    required_permission = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='所需权限',
        help_text='查看此报表需要的权限代码'
    )

    # 是否可编辑
    is_system = models.BooleanField(default=False, verbose_name='系统模板')
    allow_export = models.BooleanField(default=True, verbose_name='允许导出')

    # 版本信息
    version = models.CharField(max_length=20, default='1.0', verbose_name='版本号')
    parent_template = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='versions',
        verbose_name='父模板'
    )

    class Meta:
        db_table = 'report_template'
        verbose_name = '报表模板'
        verbose_name_plural = '报表模板'
        ordering = ['report_type', 'template_code']
        indexes = [
            models.Index(fields=['template_code']),
            models.Index(fields=['report_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.template_name} ({self.template_code})"


class ReportTemplateSection(BaseModel):
    """
    报表模板节区
    定义报表的各个组成部分
    """
    SECTION_TYPES = [
        ('header', '表头'),
        ('filters', '筛选条件'),
        ('table', '数据表格'),
        ('chart', '图表'),
        ('summary', '汇总信息'),
        ('footer', '表尾'),
        ('signature', '签字区'),
        ('custom', '自定义'),
    ]

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='报表模板'
    )

    # 节区信息
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES, verbose_name='节区类型')
    section_name = models.CharField(max_length=100, verbose_name='节区名称')
    sequence = models.IntegerField(default=0, verbose_name='排序')

    # 节区配置
    section_config = models.JSONField(default=dict, verbose_name='节区配置')
    # 对于table类型: columns, show_footer, etc.
    # 对于chart类型: chart_type, data_field, etc.

    # 显示条件
    display_condition = models.JSONField(null=True, blank=True, verbose_name='显示条件')

    class Meta:
        db_table = 'report_template_section'
        verbose_name = '报表模板节区'
        verbose_name_plural = '报表模板节区'
        ordering = ['template', 'sequence']

    def __str__(self):
        return f"{self.template.template_name} - {self.section_name}"
```

### 1.2 报表生成记录 (ReportGeneration)

```python
class ReportGeneration(BaseModel):
    """
    报表生成记录
    记录报表生成历史
    """
    STATUS_CHOICES = [
        ('pending', '生成中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]

    # 关联模板
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.PROTECT,
        related_name='generations',
        verbose_name='报表模板'
    )

    # 生成信息
    generation_no = models.CharField(max_length=50, unique=True, verbose_name='生成编号')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')

    # 报表参数
    report_params = models.JSONField(default=dict, verbose_name='报表参数')
    # {
    #   "period_from": "2024-01-01",
    #   "period_to": "2024-01-31",
    #   "department_id": 1,
    #   "category_id": 2,
    #   ...
    # }

    # 输出信息
    output_format = models.CharField(
        max_length=10,
        choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('html', 'HTML')],
        verbose_name='输出格式'
    )
    file_path = models.CharField(max_length=500, null=True, blank=True, verbose_name='文件路径')
    file_size = models.IntegerField(null=True, blank=True, verbose_name='文件大小')

    # 生成信息
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='generated_reports',
        verbose_name='生成人'
    )
    generated_at = models.DateTimeField(null=True, blank=True, verbose_name='生成时间')
    generation_duration = models.IntegerField(null=True, blank=True, verbose_name='耗时(秒)')

    # 错误信息
    error_message = models.TextField(null=True, blank=True, verbose_name='错误信息')

    # 报表数据缓存
    cached_data = models.JSONField(null=True, blank=True, verbose_name='缓存数据')

    class Meta:
        db_table = 'report_generation'
        verbose_name = '报表生成记录'
        verbose_name_plural = '报表生成记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['generation_no']),
            models.Index(fields=['template']),
            models.Index(fields=['status']),
            models.Index(fields=['generated_by']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.generation_no} - {self.template.template_name}"
```

### 1.3 定时报表任务 (ReportSchedule)

```python
class ReportSchedule(BaseModel):
    """
    定时报表任务
    配置自动生成报表的计划任务
    """
    FREQUENCY_CHOICES = [
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('quarterly', '每季度'),
        ('yearly', '每年'),
    ]

    # 基本信息
    schedule_name = models.CharField(max_length=200, verbose_name='任务名称')
    schedule_code = models.CharField(max_length=50, unique=True, verbose_name='任务代码')

    # 关联模板
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='报表模板'
    )

    # 调度配置
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, verbose_name='执行频率')
    cron_expression = models.CharField(max_length=100, verbose_name='Cron表达式')
    timezone = models.CharField(max_length=50, default='Asia/Shanghai', verbose_name='时区')

    # 报表参数
    default_params = models.JSONField(default=dict, verbose_name='默认参数')
    output_format = models.CharField(
        max_length=10,
        choices=[('pdf', 'PDF'), ('excel', 'Excel')],
        default='pdf',
        verbose_name='输出格式'
    )

    # 生效时间
    valid_from = models.DateField(verbose_name='生效开始日期')
    valid_until = models.DateField(null=True, blank=True, verbose_name='生效结束日期')

    # 状态
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    last_run_at = models.DateTimeField(null=True, blank=True, verbose_name='上次运行时间')
    next_run_at = models.DateTimeField(null=True, blank=True, verbose_name='下次运行时间')

    class Meta:
        db_table = 'report_schedule'
        verbose_name = '定时报表任务'
        verbose_name_plural = '定时报表任务'
        ordering = ['schedule_code']
        indexes = [
            models.Index(fields=['schedule_code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['next_run_at']),
        ]

    def __str__(self):
        return f"{self.schedule_name} ({self.frequency})"


class ReportSubscription(BaseModel):
    """
    报表订阅
    用户订阅报表，自动推送
    """
    # 关联调度任务
    schedule = models.ForeignKey(
        ReportSchedule,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='调度任务'
    )

    # 订阅用户
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_subscriptions',
        verbose_name='订阅人'
    )

    # 推送方式
    delivery_methods = models.JSONField(
        default=list,
        verbose_name='推送方式',
        help_text='["email", "system", "webhook"]'
    )

    # 邮件配置
    email = models.EmailField(null=True, blank=True, verbose_name='邮箱地址')
    email_subject = models.CharField(max_length=200, blank=True, verbose_name='邮件主题')

    # Webhook配置
    webhook_url = models.URLField(max_length=500, null=True, blank=True, verbose_name='Webhook URL')

    # 状态
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'report_subscription'
        verbose_name = '报表订阅'
        verbose_name_plural = '报表订阅'
        unique_together = [['schedule', 'subscriber']]
        ordering = ['schedule', 'subscriber']

    def __str__(self):
        return f"{self.schedule.schedule_name} - {self.subscriber.username}"
```

---

## 2. 报表引擎设计

### 2.1 报表引擎核心

```python
# apps/reports/engine.py

from typing import Dict, Any, List
from django.db.models import Q, Sum, Count, F, Value
from django.db.models.functions import Coalesce
from apps.reports.models import ReportTemplate, ReportGeneration
from apps.assets.models import Asset, AssetDepreciation
import time


class ReportEngine:
    """报表生成引擎"""

    @staticmethod
    def generate_report(template_code: str, params: Dict[str, Any], output_format: str = 'pdf', user=None) -> ReportGeneration:
        """生成报表
        Args:
            template_code: 模板代码
            params: 报表参数（筛选条件等）
            output_format: 输出格式 pdf/excel/html
            user: 生成用户
        Returns:
            ReportGeneration: 报表生成记录
        """
        start_time = time.time()

        # 1. 加载模板
        template = ReportTemplate.objects.get(template_code=template_code, status='active')

        # 2. 创建生成记录
        generation = ReportGeneration.objects.create(
            generation_no=ReportEngine._generate_no(),
            template=template,
            report_params=params,
            output_format=output_format,
            generated_by=user,
            org=user.org if user else template.org,
            created_by=user,
        )

        try:
            # 3. 查询数据
            data = ReportEngine._query_data(template, params, user)

            # 4. 缓存数据用于预览
            generation.cached_data = data

            # 5. 应用模板渲染
            rendered = ReportEngine._render_template(template, data, params)

            # 6. 生成输出文件
            if output_format != 'html':
                file_path = ReportEngine._export_file(rendered, output_format, generation)
                generation.file_path = file_path
                generation.file_size = len(rendered)

            # 7. 更新状态
            generation.status = 'success'
            generation.generated_at = timezone.now()
            generation.generation_duration = int(time.time() - start_time)
            generation.save()

        except Exception as e:
            generation.status = 'failed'
            generation.error_message = str(e)
            generation.save()
            raise

        return generation

    @staticmethod
    def _generate_no() -> str:
        """生成报表编号"""
        from django.utils import timezone
        prefix = f"RPT{timezone.now().strftime('%Y%m%H%M%S')}"
        import random
        suffix = random.randint(1000, 9999)
        return f"{prefix}{suffix}"

    @staticmethod
    def _query_data(template: ReportTemplate, params: Dict[str, Any], user=None) -> Dict[str, Any]:
        """查询报表数据"""
        data_source = template.data_source
        source_type = data_source.get('type', 'model')

        if source_type == 'model':
            return ReportEngine._query_model(data_source, params, user)
        elif source_type == 'sql':
            return ReportEngine._query_sql(data_source, params)
        elif source_type == 'aggregate':
            return ReportEngine._query_aggregate(data_source, params, user)
        else:
            raise ValueError(f"不支持的数据源类型: {source_type}")

    @staticmethod
    def _query_model(data_source: Dict, params: Dict, user=None) -> Dict[str, Any]:
        """查询模型数据"""
        from django.apps import apps

        model_path = data_source['model']
        app_label, model_name = model_path.split('.')
        Model = apps.get_model(app_label, model_name)

        # 构建查询
        queryset = Model.objects.all()

        # 应用数据权限
        if user:
            queryset = queryset.filter(org=user.org)

        # 应用筛选条件
        filters = data_source.get('filters', [])
        for filter_config in filters:
            field = filter_config['field']
            param_key = filter_config.get('param_key', field)
            if param_key in params and params[param_key]:
                queryset = queryset.filter(**{field: params[param_key]})

        # 应用日期范围
        if 'period_from' in params and params['period_from']:
            queryset = queryset.filter(created_at__gte=params['period_from'])
        if 'period_to' in params and params['period_to']:
            queryset = queryset.filter(created_at__lte=params['period_to'])

        # 字段选择
        fields = data_source.get('fields', [])
        if fields:
            queryset = queryset.values(*fields)

        # 排序
        order_by = data_source.get('order_by', [])
        if order_by:
            queryset = queryset.order_by(*order_by)

        # 分页
        page = params.get('page', 1)
        page_size = params.get('page_size', 10000)
        offset = (page - 1) * page_size

        total = queryset.count()
        data = list(queryset[offset:offset + page_size])

        return {
            'data': data,
            'total': total,
            'page': page,
            'page_size': page_size
        }

    @staticmethod
    def _query_aggregate(data_source: Dict, params: Dict, user=None) -> Dict[str, Any]:
        """聚合查询"""
        query_type = data_source.get('query')

        if query_type == 'asset_by_department':
            return ReportEngine._aggregate_asset_by_department(params, user)
        elif query_type == 'asset_by_category':
            return ReportEngine._aggregate_asset_by_category(params, user)
        elif query_type == 'depreciation_summary':
            return ReportEngine._aggregate_depreciation_summary(params, user)
        elif query_type == 'asset_change':
            return ReportEngine._aggregate_asset_change(params, user)
        else:
            raise ValueError(f"不支持的聚合查询: {query_type}")

    @staticmethod
    def _aggregate_asset_by_department(params: Dict, user=None) -> Dict[str, Any]:
        """按部门统计资产"""
        queryset = Asset.objects.filter(org=user.org if user else None)

        # 应用筛选
        if params.get('category_id'):
            queryset = queryset.filter(category_id=params['category_id'])
        if params.get('status'):
            queryset = queryset.filter(status=params['status'])

        # 分组统计
        result = queryset.values('department__name', 'department__id').annotate(
            count=Count('id'),
            total_original=Coalesce(Sum('original_value'), 0),
            total_depreciation=Coalesce(Sum('accumulated_depreciation'), 0),
            total_net=Coalesce(Sum(F('original_value') - F('accumulated_depreciation')), 0)
        ).order_by('-total_net')

        return {
            'data': list(result),
            'summary': {
                'total_departments': len(result),
                'total_assets': sum(r['count'] for r in result),
                'total_original': sum(r['total_original'] for r in result),
                'total_net': sum(r['total_net'] for r in result),
            }
        }

    @staticmethod
    def _aggregate_depreciation_summary(params: Dict, user=None) -> Dict[str, Any]:
        """折旧汇总统计"""
        period_from = params.get('period_from')
        period_to = params.get('period_to')

        queryset = AssetDepreciation.objects.filter(org=user.org if user else None)

        if period_from:
            queryset = queryset.filter(period__gte=period_from)
        if period_to:
            queryset = queryset.filter(period__lte=period_to)

        # 按期间统计
        by_period = queryset.values('period').annotate(
            count=Count('id'),
            total_depreciation=Coalesce(Sum('depreciation_amount'), 0)
        ).order_by('period')

        # 按类别统计
        by_category = queryset.values('asset__category__name').annotate(
            total_depreciation=Coalesce(Sum('depreciation_amount'), 0)
        ).order_by('-total_depreciation')

        return {
            'by_period': list(by_period),
            'by_category': list(by_category),
            'summary': {
                'total_depreciation': sum(r['total_depreciation'] for r in by_period),
                'total_periods': len(by_period),
            }
        }

    @staticmethod
    def _aggregate_asset_change(params: Dict, user=None) -> Dict[str, Any]:
        """资产增减变动统计"""
        from apps.lifecycle.models import DisposalRequest
        from django.utils import timezone
        from datetime import timedelta

        period_from = params.get('period_from', (timezone.now() - timedelta(days=30)).date())
        period_to = params.get('period_to', timezone.now().date())

        # 期初余额
        beginning_assets = Asset.objects.filter(
            org=user.org if user else None,
            purchase_date__lt=period_from
        ).aggregate(
            count=Count('id'),
            total_original=Coalesce(Sum('original_value'), 0)
        )

        # 本期增加
        added_assets = Asset.objects.filter(
            org=user.org if user else None,
            purchase_date__gte=period_from,
            purchase_date__lte=period_to
        ).aggregate(
            count=Count('id'),
            total_original=Coalesce(Sum('original_value'), 0)
        )

        # 本期减少（处置）
        removed_assets = DisposalRequest.objects.filter(
            org=user.org if user else None,
            status='completed',
            created_at__date__gte=period_from,
            created_at__date__lte=period_to
        ).aggregate(
            count=Count('id'),
            total_original=Coalesce(Sum('items__original_value'), 0)
        )

        # 期末余额
        ending_assets = Asset.objects.filter(
            org=user.org if user else None,
            purchase_date__lte=period_to
        ).exclude(
            status__in=['lost', 'disposed']
        ).aggregate(
            count=Count('id'),
            total_original=Coalesce(Sum('original_value'), 0),
            total_net=Coalesce(Sum(F('original_value') - F('accumulated_depreciation')), 0)
        )

        return {
            'beginning': beginning_assets,
            'added': added_assets,
            'removed': removed_assets,
            'ending': ending_assets,
            'period': {
                'from': str(period_from),
                'to': str(period_to)
            }
        }

    @staticmethod
    def _render_template(template: ReportTemplate, data: Dict, params: Dict) -> str:
        """渲染模板"""
        from jinja2 import Template

        template_config = template.template_config
        sections = template_config.get('sections', [])

        rendered_parts = []

        for section in sections:
            section_type = section.get('type')
            section_data = ReportEngine._get_section_data(section_type, section, data, params)

            # 应用模板
            if section.get('template'):
                jinja_template = Template(section['template'])
                rendered = jinja_template.render(**section_data)
            else:
                rendered = ReportEngine._render_section_default(section_type, section_data)

            rendered_parts.append(rendered)

        return '\n'.join(rendered_parts)

    @staticmethod
    def _get_section_data(section_type: str, section_config: Dict, data: Dict, params: Dict) -> Dict:
        """获取节区数据"""
        if section_type == 'header':
            return {
                'title': section_config.get('title'),
                'subtitle': section_config.get('subtitle', ''),
                'period': params.get('period', ''),
                'org_name': params.get('org_name', ''),
            }
        elif section_type == 'table':
            table_data = data.get('data', [])
            columns = section_config.get('columns', [])
            return {
                'columns': columns,
                'rows': table_data,
                'total': data.get('total', len(table_data)),
            }
        elif section_type == 'summary':
            return data.get('summary', {})
        elif section_type == 'signature':
            return {
                'positions': section_config.get('positions', []),
            }
        else:
            return {}

    @staticmethod
    def _render_section_default(section_type: str, data: Dict) -> str:
        """默认节区渲染"""
        if section_type == 'header':
            return f"<h1>{data.get('title', '')}</h1>"
        elif section_type == 'table':
            # 简单HTML表格渲染
            rows = data.get('rows', [])
            if not rows:
                return ''
            headers = [col.get('title', col['field']) for col in data.get('columns', [])]
            return f"<table><tr><th>{'</th><th>'.join(headers)}</th></tr></table>"
        else:
            return ''

    @staticmethod
    def _export_file(rendered: str, output_format: str, generation: ReportGeneration) -> str:
        """导出文件"""
        import os
        from django.conf import settings

        # 创建文件目录
        file_dir = os.path.join(settings.MEDIA_ROOT, 'reports', generation.generation_no[:6])
        os.makedirs(file_dir, exist_ok=True)

        if output_format == 'pdf':
            from apps.reports.exporters import PDFExporter
            exporter = PDFExporter()
        elif output_format == 'excel':
            from apps.reports.exporters import ExcelExporter
            exporter = ExcelExporter()
        else:
            raise ValueError(f"不支持的导出格式: {output_format}")

        file_path = exporter.export(rendered, file_dir, generation.generation_no)
        return file_path
```

### 2.2 预定义报表生成器

```python
# apps/reports/generators.py

class AssetDetailReportGenerator:
    """资产明细表生成器"""

    @staticmethod
    def generate(params: Dict, user=None) -> Dict:
        """生成资产明细表数据"""
        queryset = Asset.objects.filter(org=user.org if user else None)

        # 应用筛选
        if params.get('department_id'):
            queryset = queryset.filter(department_id=params['department_id'])
        if params.get('category_id'):
            queryset = queryset.filter(category_id=params['category_id'])
        if params.get('location_id'):
            queryset = queryset.filter(location_id=params['location_id'])
        if params.get('status'):
            queryset = queryset.filter(status=params['status'])

        # 排序和分页
        queryset = queryset.select_related('category', 'department', 'location').order_by('asset_no')

        page = params.get('page', 1)
        page_size = params.get('page_size', 1000)

        from django.core.paginator import Paginator
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # 转换为字典
        data = []
        for asset in page_obj:
            data.append({
                'asset_no': asset.asset_no,
                'asset_name': asset.asset_name,
                'category_name': asset.category.name if asset.category else '',
                'specification': asset.specification or '',
                'original_value': float(asset.original_value),
                'accumulated_depreciation': float(asset.accumulated_depreciation),
                'net_value': float(asset.net_value),
                'department_name': asset.department.name if asset.department else '',
                'location_name': asset.location.name if asset.location else '',
                'status_display': asset.get_status_display(),
                'purchase_date': str(asset.purchase_date) if asset.purchase_date else '',
            })

        # 汇总
        total_original = sum(r['original_value'] for r in data)
        total_depreciation = sum(r['accumulated_depreciation'] for r in data)
        total_net = sum(r['net_value'] for r in data)

        return {
            'data': data,
            'summary': {
                'total_count': paginator.count,
                'total_original': total_original,
                'total_depreciation': total_depreciation,
                'total_net': total_net,
            }
        }


class DepreciationSummaryReportGenerator:
    """折旧汇总表生成器"""

    @staticmethod
    def generate(params: Dict, user=None) -> Dict:
        """生成折旧汇总表数据"""
        period_from = params.get('period_from')
        period_to = params.get('period_to')

        queryset = AssetDepreciation.objects.filter(org=user.org if user else None)

        if period_from:
            queryset = queryset.filter(period__gte=period_from)
        if period_to:
            queryset = queryset.filter(period__lte=period_to)

        queryset = queryset.select_related('asset', 'asset__category').order_by('period', 'asset__asset_no')

        # 按类别汇总
        by_category = {}
        for dep in queryset:
            category = dep.asset.category.name if dep.asset.category else '未分类'
            if category not in by_category:
                by_category[category] = {
                    'count': 0,
                    'total_depreciation': 0,
                }
            by_category[category]['count'] += 1
            by_category[category]['total_depreciation'] += float(dep.depreciation_amount)

        # 转换为列表
        category_list = [
            {
                'category': k,
                **v
            }
            for k, v in by_category.items()
        ]

        # 按期间汇总
        by_period = queryset.values('period').annotate(
            count=Count('id'),
            total_depreciation=Coalesce(Sum('depreciation_amount'), 0)
        ).order_by('period')

        return {
            'by_category': category_list,
            'by_period': list(by_period),
            'summary': {
                'total_depreciation': sum(c['total_depreciation'] for c in category_list),
                'total_count': sum(c['count'] for c in category_list),
            }
        }


class AssetChangeReportGenerator:
    """资产增减变动表生成器"""

    @staticmethod
    def generate(params: Dict, user=None) -> Dict:
        """生成资产增减变动表数据"""
        return ReportEngine._query_aggregate(
            {'query': 'asset_change'},
            params,
            user
        )
```

### 2.3 文件导出器

```python
# apps/reports/exporters.py

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side


class PDFExporter:
    """PDF导出器"""

    def export(self, data: str or Dict, output_dir: str, filename: str) -> str:
        """导出PDF"""
        import os
        file_path = os.path.join(output_dir, f"{filename}.pdf")

        # 创建PDF
        doc = SimpleDocTemplate(
            file_path,
            pagesize=landscape(A4),
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )

        # 构建内容
        elements = []
        styles = getSampleStyleSheet()

        if isinstance(data, dict):
            # 表格数据
            elements.extend(self._build_table(data, styles))
        else:
            # HTML渲染
            elements.extend(self._build_from_html(data, styles))

        # 生成PDF
        doc.build(elements)

        return file_path

    def _build_table(self, data: Dict, styles):
        """构建表格"""
        elements = []

        # 标题
        if data.get('title'):
            title = Paragraph(data['title'], styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12*mm))

        # 表头
        columns = data.get('columns', [])
        headers = [col.get('title', col['field']) for col in columns]
        rows = [headers]

        # 数据行
        for row_data in data.get('rows', []):
            row = [str(row_data.get(col['field'], '')) for col in columns]
            rows.append(row)

        # 创建表格
        table = Table(rows)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)

        return elements


class ExcelExporter:
    """Excel导出器"""

    def export(self, data: str or Dict, output_dir: str, filename: str) -> str:
        """导出Excel"""
        import os
        file_path = os.path.join(output_dir, f"{filename}.xlsx")

        # 创建工作簿
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "报表数据"

        if isinstance(data, dict):
            self._build_table_excel(ws, data)
        else:
            # HTML解析
            pass

        # 保存
        wb.save(file_path)

        return file_path

    def _build_table_excel(self, ws, data: Dict):
        """构建Excel表格"""
        # 标题
        if data.get('title'):
            ws['A1'] = data['title']
            ws['A1'].font = Font(size=16, bold=True)
            ws.merge_cells('A1:Z1')

        row = 3

        # 表头
        columns = data.get('columns', [])
        for col_idx, col in enumerate(columns, 1):
            cell = ws.cell(row=row, column=col_idx)
            cell.value = col.get('title', col['field'])
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='DDDDDD', end_color='DDDDDD', fill_type='solid')

        row += 1

        # 数据
        for row_data in data.get('rows', []):
            for col_idx, col in enumerate(columns, 1):
                value = row_data.get(col['field'], '')
                cell = ws.cell(row=row, column=col_idx)
                cell.value = value
            row += 1

        # 自动调整列宽
        for col in ws.columns:
            max_length = 0
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[col[0].column_letter].width = adjusted_width
```

---

## 3. 序列化器设计

### 3.1 报表模板序列化器

```python
# apps/reports/serializers.py

from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.reports.models import ReportTemplate, ReportTemplateSection, ReportGeneration, ReportSchedule, ReportSubscription


class ReportTemplateSerializer(BaseModelSerializer):
    """报表模板序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = ReportTemplate
        fields = BaseModelSerializer.Meta.fields + [
            'template_code', 'template_name', 'description', 'status',
            'report_type', 'template_config', 'data_source',
            'required_permission', 'is_system', 'allow_export',
            'version', 'parent_template'
        ]


class ReportTemplateDetailSerializer(BaseModelWithAuditSerializer):
    """报表模板详情序列化器（包含完整审计信息）"""

    sections = serializers.SerializerMethodField()

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = ReportTemplate
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'template_code', 'template_name', 'description', 'status',
            'report_type', 'template_config', 'data_source',
            'required_permission', 'is_system', 'allow_export',
            'version', 'parent_template', 'sections'
        ]

    def get_sections(self, obj):
        """获取模板节区"""
        sections = obj.sections.all().order_by('sequence')
        return ReportTemplateSectionSerializer(sections, many=True).data


class ReportTemplateSectionSerializer(BaseModelSerializer):
    """报表模板节区序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = ReportTemplateSection
        fields = BaseModelSerializer.Meta.fields + [
            'template', 'section_type', 'section_name',
            'sequence', 'section_config', 'display_condition'
        ]


class ReportGenerationSerializer(BaseModelSerializer):
    """报表生成记录序列化器"""

    template = ReportTemplateSerializer(read_only=True)
    generated_by = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = ReportGeneration
        fields = BaseModelSerializer.Meta.fields + [
            'template', 'generation_no', 'status', 'report_params',
            'output_format', 'file_path', 'file_size',
            'generated_by', 'generated_at', 'generation_duration',
            'error_message', 'cached_data'
        ]

    def get_generated_by(self, obj):
        """获取生成人信息"""
        from apps.accounts.serializers import UserSerializer
        if obj.generated_by:
            return UserSerializer(obj.generated_by).data
        return None


class ReportScheduleSerializer(BaseModelSerializer):
    """定时报表任务序列化器"""

    template = ReportTemplateSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ReportSchedule
        fields = BaseModelSerializer.Meta.fields + [
            'schedule_name', 'schedule_code', 'template',
            'frequency', 'cron_expression', 'timezone',
            'default_params', 'output_format',
            'valid_from', 'valid_until',
            'is_active', 'last_run_at', 'next_run_at'
        ]


class ReportSubscriptionSerializer(BaseModelSerializer):
    """报表订阅序列化器"""

    schedule = ReportScheduleSerializer(read_only=True)
    subscriber = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = ReportSubscription
        fields = BaseModelSerializer.Meta.fields + [
            'schedule', 'subscriber', 'delivery_methods',
            'email', 'email_subject', 'webhook_url', 'is_active'
        ]

    def get_subscriber(self, obj):
        """获取订阅人信息"""
        from apps.accounts.serializers import UserSerializer
        return UserSerializer(obj.subscriber).data
```

---

## 4. 过滤器设计

### 4.1 报表过滤器

```python
# apps/reports/filters.py

from apps.common.filters.base import BaseModelFilter
from apps.reports.models import ReportTemplate, ReportGeneration, ReportSchedule


class ReportTemplateFilter(BaseModelFilter):
    """报表模板过滤器"""

    # 业务字段过滤
    template_code = filters.CharFilter(lookup_expr='icontains', label='模板代码')
    template_name = filters.CharFilter(lookup_expr='icontains', label='模板名称')
    report_type = filters.ChoiceFilter(choices=ReportTemplate.STATUS_CHOICES, label='报表类型')
    status = filters.ChoiceFilter(choices=ReportTemplate.STATUS_CHOICES, label='状态')
    is_system = filters.BooleanFilter(label='系统模板')

    class Meta(BaseModelFilter.Meta):
        model = ReportTemplate
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'template_code', 'template_name', 'report_type',
            'status', 'is_system'
        ]


class ReportGenerationFilter(BaseModelFilter):
    """报表生成记录过滤器"""

    # 业务字段过滤
    generation_no = filters.CharFilter(lookup_expr='icontains', label='生成编号')
    template = filters.UUIDFilter(field_name='template_id', label='报表模板')
    status = filters.ChoiceFilter(choices=ReportGeneration.STATUS_CHOICES, label='状态')
    output_format = filters.ChoiceFilter(choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('html', 'HTML')], label='输出格式')

    # 时间范围过滤（生成时间）
    generated_at_from = filters.DateTimeFilter(field_name='generated_at', lookup_expr='gte', label='生成时间（起始）')
    generated_at_to = filters.DateTimeFilter(field_name='generated_at', lookup_expr='lte', label='生成时间（结束）')

    class Meta(BaseModelFilter.Meta):
        model = ReportGeneration
        fields = BaseModelFilter.Meta.fields + [
            'generation_no', 'template', 'status', 'output_format',
            'generated_at_from', 'generated_at_to'
        ]


class ReportScheduleFilter(BaseModelFilter):
    """定时报表任务过滤器"""

    # 业务字段过滤
    schedule_name = filters.CharFilter(lookup_expr='icontains', label='任务名称')
    schedule_code = filters.CharFilter(lookup_expr='icontains', label='任务代码')
    template = filters.UUIDFilter(field_name='template_id', label='报表模板')
    frequency = filters.ChoiceFilter(choices=ReportSchedule.FREQUENCY_CHOICES, label='执行频率')
    is_active = filters.BooleanFilter(label='是否启用')

    class Meta(BaseModelFilter.Meta):
        model = ReportSchedule
        fields = BaseModelFilter.Meta.fields + [
            'schedule_name', 'schedule_code', 'template',
            'frequency', 'is_active'
        ]
```

---

## API规范

### 1. 统一响应格式

所有报告相关接口均遵循统一响应格式：

#### 成功响应示例
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "RPT202501001",
        "title": "2025年1月资产折旧报表",
        "type": "depreciation_report",
        "status": "generated",
        "created_at": "2025-01-15T10:30:00Z"
    }
}
```

#### 列表响应示例（分页）
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/reports/reports/?page=2",
        "previous": null,
        "results": [...]
    }
}
```

#### 失败响应示例
```json
{
    "success": false,
    "error": {
        "code": "REPORT_GENERATION_ERROR",
        "message": "报告生成失败：数据源连接异常"
    }
}
```

### 2. 错误码定义

| 错误码 | HTTP状态码 | 说明 |
|--------|-------------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已被软删除 |
| `REPORT_GENERATION_ERROR` | 400 | 报告生成错误 |
| `TEMPLATE_NOT_FOUND` | 404 | 报告模板不存在 |
| `DATA_SOURCE_ERROR` | 400 | 数据源错误 |
| `FILE_FORMAT_ERROR` | 400 | 文件格式错误 |
| `FILE_TOO_LARGE` | 413 | 文件过大 |
| `PERMISSION_DENIED` | 403 | 导出权限不足 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

### 3. 标准CRUD接口

#### 3.1 报告管理

##### 列表查询
```http
GET /api/reports/reports/?type=asset_summary&status=generated&page=1&page_size=20
```

查询参数：
- `type`: 报告类型（可选）
- `status`: 状态（可选）
- `created_at_from`: 创建时间开始（可选）
- `created_at_to`: 创建时间结束（可选）
- `organization`: 组织ID（可选）

##### 创建报告
```http
POST /api/reports/reports/
{
    "code": "RPT202501001",
    "title": "2025年1月资产折旧报表",
    "type": "depreciation_report",
    "template": "550e8400-e29b-41d4-a716-446655440001",
    "parameters": {
        "period": "2025-01",
        "include_accumulated": true,
        "format": "excel"
    },
    "organization": "550e8400-e29b-41d4-a716-446655440000"
}
```

##### 获取详情
```http
GET /api/reports/reports/{id}/
```

响应：
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "RPT202501001",
        "title": "2025年1月资产折旧报表",
        "type": "depreciation_report",
        "template": {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "标准折旧报表模板"
        },
        "parameters": {
            "period": "2025-01",
            "include_accumulated": true,
            "format": "excel"
        },
        "status": "generated",
        "file_path": "/reports/RPT202501001.xlsx",
        "file_size": 2048000,
        "created_at": "2025-01-15T10:30:00Z",
        "created_by": {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "username": "admin"
        }
    }
}
```

##### 更新报告
```http
PUT /api/reports/reports/{id}/
```

##### 部分更新
```http
PATCH /api/reports/reports/{id}/
```

##### 软删除
```http
DELETE /api/reports/reports/{id}/
```

##### 已删除记录列表
```http
GET /api/reports/reports/deleted/
```

##### 恢复记录
```http
POST /api/reports/reports/{id}/restore/
```

#### 3.2 报告模板管理

##### 列表查询
```http
GET /api/reports/templates/?category=asset&page=1&page_size=20
```

##### 创建模板
```http
POST /api/reports/templates/
{
    "name": "标准资产汇总报表",
    "description": "按部门统计资产价值汇总",
    "category": "asset",
    "template_type": "excel",
    "schema": {
        "layout": "grid",
        "sections": [...],
        "fields": [...]
    },
    "is_active": true,
    "organization": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 3.3 报告计划管理

##### 列表查询
```http
GET /api/reports/schedules/?is_active=true&page=1&page_size=20
```

##### 创建计划
```http
POST /api/reports/schedules/
{
    "name": "月度折旧报表自动生成",
    "description": "每月自动生成折旧报表",
    "template": "550e8400-e29b-41d4-a716-446655440001",
    "cron_expression": "0 0 2 1 * ?",
    "parameters": {
        "format": "excel",
        "email_recipients": ["finance@company.com"]
    },
    "is_active": true,
    "organization": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 4. 批量操作

#### 4.1 批量删除报告
```http
POST /api/reports/reports/batch-delete/
{
    "ids": ["id1", "id2", "id3"]
}
```

成功响应：
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
        {"id": "id1", "success": true},
        {"id": "id2", "success": true},
        {"id": "id3", "success": true}
    ]
}
```

#### 4.2 批量导出报告
```http
POST /api/reports/reports/batch-export/
{
    "ids": ["id1", "id2", "id3"],
    "format": "pdf"
}
```

响应：
```json
{
    "success": true,
    "message": "批量导出完成",
    "data": {
        "total": 3,
        "succeeded": 3,
        "failed": 0,
        "download_urls": [
            "/download/RPT202501001.pdf",
            "/download/RPT202501002.pdf",
            "/download/RPT202501003.pdf"
        ]
    }
}
```

#### 4.3 批量更新报告参数
```http
POST /api/reports/reports/batch-update-params/
{
    "ids": ["id1", "id2", "id3"],
    "parameters": {
        "include_charts": true,
        "format": "pdf"
    }
}
```

### 5. 报告生成接口

#### 5.1 立即生成报告
```http
POST /api/reports/generate/
{
    "template_id": "550e8400-e29b-41d4-a716-446655440001",
    "parameters": {
        "period": "2025-01",
        "format": "excel"
    }
}
```

响应：
```json
{
    "success": true,
    "message": "报告生成任务已创建",
    "data": {
        "task_id": "task_20250115001",
        "estimated_time": 30,
        "status": "processing"
    }
}
```

#### 5.2 查询生成状态
```http
GET /api/reports/generate/status/{task_id}/
```

响应：
```json
{
    "success": true,
    "data": {
        "task_id": "task_20250115001",
        "status": "completed",
        "progress": 100,
        "report_id": "550e8400-e29b-41d4-a716-446655440002",
        "file_path": "/reports/RPT202501001.xlsx",
        "error_message": null
    }
}
```

### 6. 报告导出接口

#### 6.1 导出为Excel
```http
GET /api/reports/reports/{id}/export/excel/
```

响应：文件流下载

#### 6.2 导出为PDF
```http
GET /api/reports/reports/{id}/export/pdf/
```

响应：文件流下载

#### 6.3 导出为CSV
```http
GET /api/reports/reports/{id}/export/csv/
```

响应：文件流下载

### 7. 报告预览接口

#### 7.1 获取预览数据
```http
GET /api/reports/reports/{id}/preview/
```

响应：
```json
{
    "success": true,
    "data": {
        "template_name": "标准资产折旧报表",
        "preview_data": {
            "headers": ["资产编号", "资产名称", "原值", "本月折旧", "累计折旧", "净值"],
            "rows": [
                ["ZC001", "笔记本电脑", 50000, 833.33, 10000, 40000],
                ["ZC002", "办公桌", 10000, 83.33, 1000, 9000]
            ]
        },
        "total_rows": 150,
        "summary": {
            "total_original_value": 10000000,
            "total_monthly_depreciation": 83333.33,
            "total_accumulated_depreciation": 1000000,
            "total_net_value": 9000000
        }
    }
}
```

#### 7.2 获取缩略图
```http
GET /api/reports/reports/{id}/thumbnail/
```

响应：图片文件流

### 8. 数据源接口

#### 8.1 列出可用数据源
```http
GET /api/reports/data-sources/
```

响应：
```json
{
    "success": true,
    "data": {
        "sources": [
            {
                "id": "ds_asset",
                "name": "资产主数据",
                "type": "database",
                "description": "资产基本信息、折旧记录等"
            },
            {
                "id": "ds_finance",
                "name": "财务数据",
                "type": "api",
                "description": "总账科目、余额等财务数据"
            }
        ]
    }
}
```

#### 8.2 测试数据源连接
```http
POST /api/reports/data-sources/test/
{
    "source_id": "ds_asset",
    "connection_params": {...}
}
```

### 9. 报告订阅接口

#### 9.1 创建订阅
```http
POST /api/reports/subscriptions/
{
    "name": "月度折旧报表订阅",
    "report_template": "550e8400-e29b-41d4-a716-446655440001",
    "delivery_schedule": "monthly",
    "format": "excel",
    "email_recipients": ["finance@company.com", "manager@company.com"],
    "is_active": true
}
```

#### 9.2 管理订阅
```http
GET /api/reports/subscriptions/
POST /api/reports/subscriptions/{id}/activate/
POST /api/reports/subscriptions/{id}/deactivate/
DELETE /api/reports/subscriptions/{id}/
```

### 5.1 标准 CRUD 端点（继承 BaseModelViewSet 自动提供）

详见 `common_base_features/api.md` 中的标准 API 规范。

所有报表相关的模型（ReportTemplate、ReportGeneration、ReportSchedule、ReportSubscription）均继承自BaseModel，因此自动获得以下标准端点：

**报表模板标准端点**：
- `GET /api/reports/templates/` - 列表查询（分页、过滤、搜索）
- `GET /api/reports/templates/{id}/` - 获取单条记录
- `POST /api/reports/templates/` - 创建新记录
- `PUT /api/reports/templates/{id}/` - 完整更新
- `PATCH /api/reports/templates/{id}/` - 部分更新
- `DELETE /api/reports/templates/{id}/` - 软删除
- `GET /api/reports/templates/deleted/` - 查看已删除记录
- `POST /api/reports/templates/{id}/restore/` - 恢复已删除记录

**批量操作端点**：
- `POST /api/reports/templates/batch-delete/` - 批量软删除
- `POST /api/reports/templates/batch-restore/` - 批量恢复
- `POST /api/reports/templates/batch-update/` - 批量更新

**报表生成记录标准端点**：
- `GET /api/reports/generations/` - 列表查询（分页、过滤、搜索）
- `GET /api/reports/generations/{id}/` - 获取单条记录
- `POST /api/reports/generations/` - 创建新记录
- `PUT /api/reports/generations/{id}/` - 完整更新
- `PATCH /api/reports/generations/{id}/` - 部分更新
- `DELETE /api/reports/generations/{id}/` - 软删除
- `GET /api/reports/generations/deleted/` - 查看已删除记录
- `POST /api/reports/generations/{id}/restore/` - 恢复已删除记录

**批量操作端点**：
- `POST /api/reports/generations/batch-delete/` - 批量软删除
- `POST /api/reports/generations/batch-restore/` - 批量恢复
- `POST /api/reports/generations/batch-update/` - 批量更新

**定时报表任务标准端点**：
- `GET /api/reports/schedules/` - 列表查询
- `GET /api/reports/schedules/{id}/` - 获取单条记录
- 以及其他标准CRUD和批量操作端点

**报表订阅标准端点**：
- `GET /api/reports/subscriptions/` - 列表查询
- `GET /api/reports/subscriptions/{id}/` - 获取单条记录
- 以及其他标准CRUD和批量操作端点

**标准响应格式**：
- 成功响应：`{success: true, message: "...", data: {...}}`
- 列表响应：`{success: true, data: {count, next, previous, results}}`
- 错误响应：`{success: false, error: {code, message, details}}`
- 批量操作响应：`{success/failed, message, summary: {total, succeeded, failed}, results: [...]}`

**标准错误码**：
- `VALIDATION_ERROR` (400) - 请求数据验证失败
- `UNAUTHORIZED` (401) - 未授权访问
- `PERMISSION_DENIED` (403) - 权限不足
- `NOT_FOUND` (404) - 资源不存在
- `ORGANIZATION_MISMATCH` (403) - 组织不匹配
- `SOFT_DELETED` (410) - 资源已删除
- `SERVER_ERROR` (500) - 服务器内部错误

---

## 6. 视图层设计

### 6.1 报表视图

```python
# apps/reports/views.py

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.reports.models import ReportTemplate, ReportGeneration, ReportSchedule, ReportSubscription
from apps.reports.serializers import (
    ReportTemplateSerializer, ReportTemplateDetailSerializer,
    ReportGenerationSerializer, ReportScheduleSerializer,
    ReportSubscriptionSerializer
)
from apps.reports.filters import ReportTemplateFilter, ReportGenerationFilter, ReportScheduleFilter
from apps.reports.services import ReportService
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class ReportTemplateViewSet(BaseModelViewSetWithBatch):
    """报表模板 ViewSet"""

    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    filterset_class = ReportTemplateFilter
    # 自动获得：组织隔离、软删除、批量操作

    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'retrieve':
            return ReportTemplateDetailSerializer
        return ReportTemplateSerializer

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """生成报表

        POST /api/reports/templates/{id}/generate/
        {
            "report_params": {...},
            "output_format": "pdf"
        }
        """
        template = self.get_object()
        report_params = request.data.get('report_params', {})
        output_format = request.data.get('output_format', 'pdf')

        # 调用报表引擎生成报表
        from apps.reports.engine import ReportEngine
        generation = ReportEngine.generate_report(
            template_code=template.template_code,
            params=report_params,
            output_format=output_format,
            user=request.user
        )

        serializer = ReportGenerationSerializer(generation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """预览报表数据

        POST /api/reports/templates/{id}/preview/
        {
            "report_params": {...}
        }
        """
        template = self.get_object()
        report_params = request.data.get('report_params', {})

        # 获取预览数据
        data = ReportService.get_report_preview(
            template_code=template.template_code,
            params=report_params,
            user=request.user
        )

        return Response(data)


class ReportGenerationViewSet(BaseModelViewSetWithBatch):
    """报表生成记录 ViewSet"""

    queryset = ReportGeneration.objects.all()
    serializer_class = ReportGenerationSerializer
    filterset_class = ReportGenerationFilter
    # 自动获得：组织隔离、软删除、批量操作

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载报表文件

        GET /api/reports/generations/{id}/download/
        """
        generation = self.get_object()

        if not generation.file_path:
            return Response(
                {'detail': '报表文件不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 返回文件下载响应
        from django.http import FileResponse
        import os

        if os.path.exists(generation.file_path):
            return FileResponse(
                open(generation.file_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(generation.file_path)
            )

        return Response(
            {'detail': '文件不存在'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=['get'])
    def my_reports(self, request):
        """获取我的报表生成记录

        GET /api/reports/generations/my-reports/
        """
        queryset = self.queryset.filter(generated_by=request.user)
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ReportScheduleViewSet(BaseModelViewSetWithBatch):
    """定时报表任务 ViewSet"""

    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer
    filterset_class = ReportScheduleFilter
    # 自动获得：组织隔离、软删除、批量操作

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        """订阅报表

        POST /api/reports/schedules/{id}/subscribe/
        {
            "delivery_methods": ["email", "system"],
            "email": "user@example.com",
            "webhook_url": "https://example.com/webhook"
        }
        """
        schedule = self.get_object()

        subscription = ReportService.subscribe_schedule(
            schedule_id=schedule.id,
            user=request.user,
            data=request.data
        )

        serializer = ReportSubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def subscriptions(self, request, pk=None):
        """获取报表的订阅列表

        GET /api/reports/schedules/{id}/subscriptions/
        """
        schedule = self.get_object()
        subscriptions = schedule.subscriptions.all()

        serializer = ReportSubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取启用的调度任务

        GET /api/reports/schedules/active/
        """
        queryset = self.queryset.filter(is_active=True)
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ReportSubscriptionViewSet(BaseModelViewSetWithBatch):
    """报表订阅 ViewSet"""

    queryset = ReportSubscription.objects.all()
    serializer_class = ReportSubscriptionSerializer
    # 自动获得：组织隔离、软删除、批量操作

    def get_queryset(self):
        """只返回当前用户的订阅"""
        queryset = super().get_queryset()
        return queryset.filter(subscriber=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """切换订阅状态

        POST /api/reports/subscriptions/{id}/toggle/
        """
        subscription = self.get_object()
        subscription.is_active = not subscription.is_active
        subscription.save()

        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
```

---

## 6. 服务层设计

### 6.1 报表服务

```python
# apps/reports/services.py

from apps.common.services.base_crud import BaseCRUDService
from apps.reports.models import ReportTemplate, ReportSchedule, ReportSubscription
from typing import List, Dict, Any, Optional
from django.db.models import Q


class ReportService(BaseCRUDService):
    """报表服务 - 继承公共CRUD基类"""

    def __init__(self):
        super().__init__(ReportTemplate)

    def get_available_templates(self, user) -> List[ReportTemplate]:
        """获取用户可用的报表模板"""
        queryset = self.query(filters={'status': 'active'})

        # 应用权限过滤
        if not user.is_admin:
            queryset = queryset.filter(
                Q(required_permission__isnull=True) |
                Q(required_permission__in=user.permissions.all())
            )

        return queryset

    def get_report_preview(self, template_code: str, params: Dict, user=None) -> Dict:
        """获取报表预览数据"""
        from apps.reports.models import ReportTemplate
        from apps.reports.engine import ReportEngine

        template = ReportTemplate.objects.get(template_code=template_code)

        # 查询数据
        data = ReportEngine._query_data(template, params, user)

        return {
            'template': {
                'code': template.template_code,
                'name': template.template_name,
                'config': template.template_config,
            },
            'data': data,
        }

    def create_schedule(self, user, data: Dict) -> ReportSchedule:
        """创建定时报表"""
        schedule = ReportSchedule.objects.create(
            schedule_name=data['schedule_name'],
            schedule_code=data['schedule_code'],
            template_id=data['template_id'],
            frequency=data['frequency'],
            cron_expression=data['cron_expression'],
            default_params=data.get('default_params', {}),
            output_format=data.get('output_format', 'pdf'),
            valid_from=data['valid_from'],
            valid_until=data.get('valid_until'),
            org=user.org,
            created_by=user,
        )

        return schedule

    def subscribe_schedule(self, schedule_id: int, user, data: Dict) -> ReportSubscription:
        """订阅报表"""
        from apps.reports.models import ReportSchedule, ReportSubscription

        schedule = ReportSchedule.objects.get(id=schedule_id)

        subscription, created = ReportSubscription.objects.get_or_create(
            schedule=schedule,
            subscriber=user,
            defaults={
                'delivery_methods': data.get('delivery_methods', ['system']),
                'email': data.get('email'),
                'webhook_url': data.get('webhook_url'),
                'org': user.org,
            }
        )

        return subscription


class ReportScheduleService(BaseCRUDService):
    """定时报表任务服务"""

    def __init__(self):
        super().__init__(ReportSchedule)

    def get_pending_schedules(self) -> List[ReportSchedule]:
        """获取待执行的调度任务"""
        from django.utils import timezone
        now = timezone.now()

        queryset = self.query(filters={
            'is_active': True,
            'next_run_at__lte': now
        })

        return queryset

    def calculate_next_run(self, schedule: ReportSchedule) -> datetime:
        """计算下次运行时间"""
        from croniter import croniter
        from django.utils import timezone

        cron = croniter(schedule.cron_expression, timezone.now())
        return cron.get_next(datetime)

---

## 7. URL路由配置

### 7.1 路由定义

```python
# apps/reports/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reports.views import (
    ReportTemplateViewSet,
    ReportGenerationViewSet,
    ReportScheduleViewSet,
    ReportSubscriptionViewSet
)

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet, basename='report-template')
router.register(r'generations', ReportGenerationViewSet, basename='report-generation')
router.register(r'schedules', ReportScheduleViewSet, basename='report-schedule')
router.register(r'subscriptions', ReportSubscriptionViewSet, basename='report-subscription')

urlpatterns = [
    path('', include(router.urls)),
]
```

---

## 8. 定时任务

```python
# apps/reports/tasks.py

from celery import shared_task
from apps.reports.models import ReportSchedule, ReportSubscription
from apps.reports.engine import ReportEngine


@shared_task
def execute_scheduled_reports():
    """执行定时报表"""
    from django.utils import timezone

    now = timezone.now()

    # 查找需要执行的任务
    schedules = ReportSchedule.objects.filter(
        is_active=True,
        next_run_at__lte=now
    )

    for schedule in schedules:
        try:
            # 生成报表
            generation = ReportEngine.generate_report(
                template_code=schedule.template.template_code,
                params=schedule.default_params,
                output_format=schedule.output_format
            )

            # 推送给订阅者
            for subscription in schedule.subscriptions.filter(is_active=True):
                send_report_to_subscriber.delay(generation.id, subscription.id)

            # 更新下次运行时间
            schedule.last_run_at = now
            schedule.next_run_at = calculate_next_run(schedule)
            schedule.save()

        except Exception as e:
            # 记录错误
            pass


@shared_task
def send_report_to_subscriber(generation_id: int, subscription_id: int):
    """发送报表给订阅者"""
    from apps.reports.models import ReportGeneration, ReportSubscription

    generation = ReportGeneration.objects.get(id=generation_id)
    subscription = ReportSubscription.objects.get(id=subscription_id)

    delivery_methods = subscription.delivery_methods

    if 'email' in delivery_methods and subscription.email:
        # 发送邮件
        send_report_email(generation, subscription)

    if 'system' in delivery_methods:
        # 系统通知
        send_report_notification(generation, subscription)

    if 'webhook' in delivery_methods and subscription.webhook_url:
        # Webhook推送
        send_report_webhook(generation, subscription)


def calculate_next_run(schedule: ReportSchedule) -> datetime:
    """计算下次运行时间"""
    from croniter import croniter
    from django.utils import timezone

    cron = croniter(schedule.cron_expression, timezone.now())
    return cron.get_next(datetime)
```

---

## 9. 权限配置

```python
# apps/reports/permissions.py

from apps.reports.models import ReportTemplate
from django.db.models import Q


class ReportPermission:
    """报表权限"""

    # 报表权限代码
    PERMISSIONS = {
        'view_asset_detail': '查看资产明细表',
        'view_depreciation_summary': '查看折旧汇总表',
        'view_asset_change': '查看资产增减变动表',
        'view_disposal_detail': '查看资产处置明细表',
        'export_report': '导出报表',
        'manage_template': '管理报表模板',
        'manage_schedule': '管理定时报表',
    }

    @staticmethod
    def check_permission(user, template_code: str) -> bool:
        """检查用户是否有权限查看报表"""
        if user.is_admin:
            return True

        template = ReportTemplate.objects.get(template_code=template_code)
        if not template.required_permission:
            return True

        return user.has_perm(template.required_permission)

    @staticmethod
    def filter_data_by_permission(queryset, user):
        """根据权限过滤数据"""
        if user.is_admin:
            return queryset

        # 基于部门的数据权限
        if hasattr(user, 'department'):
            return queryset.filter(department=user.department)

        return queryset.none()
```

---

## 10. 后续任务

1. 实现HTML模板渲染
2. 实现图表生成功能
3. 实现更多预定义报表
4. 优化大数据量报表性能
5. 实现报表缓存机制
6. 实现邮件/Webhook推送

---

## 11. 文件结构总结

### 11.1 后端模块结构

```
backend/apps/reports/
├── __init__.py
├── apps.py
├── models.py                    # 数据模型（ReportTemplate, ReportGeneration, ReportSchedule, ReportSubscription）
├── serializers.py               # 序列化器（继承 BaseModelSerializer）
├── filters.py                   # 过滤器（继承 BaseModelFilter）
├── views.py                     # 视图集（继承 BaseModelViewSetWithBatch）
├── services.py                  # 服务层（继承 BaseCRUDService）
├── engine.py                    # 报表引擎核心
├── generators.py                # 预定义报表生成器
├── exporters.py                 # PDF/Excel导出器
├── tasks.py                     # Celery定时任务
├── permissions.py               # 权限控制
├── urls.py                      # URL路由
└── admin.py                     # Django Admin配置
```

### 11.2 API端点总结

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/reports/templates/` | GET/POST | 报表模板列表/创建 |
| `/api/reports/templates/{id}/` | GET/PUT/PATCH/DELETE | 报表模板详情/更新/删除 |
| `/api/reports/templates/{id}/generate/` | POST | 生成报表 |
| `/api/reports/templates/{id}/preview/` | POST | 预览报表数据 |
| `/api/reports/generations/` | GET/POST | 报表生成记录列表/创建 |
| `/api/reports/generations/{id}/` | GET | 报表生成记录详情 |
| `/api/reports/generations/{id}/download/` | GET | 下载报表文件 |
| `/api/reports/generations/my-reports/` | GET | 我的报表记录 |
| `/api/reports/schedules/` | GET/POST | 定时报表任务列表/创建 |
| `/api/reports/schedules/{id}/` | GET/PUT/PATCH/DELETE | 定时报表任务详情/更新/删除 |
| `/api/reports/schedules/{id}/subscribe/` | POST | 订阅报表 |
| `/api/reports/schedules/{id}/subscriptions/` | GET | 获取订阅列表 |
| `/api/reports/schedules/active/` | GET | 获取启用的调度任务 |
| `/api/reports/subscriptions/` | GET/POST | 我的订阅列表/创建 |
| `/api/reports/subscriptions/{id}/` | GET/DELETE | 订阅详情/取消订阅 |
| `/api/reports/subscriptions/{id}/toggle/` | POST | 切换订阅状态 |

### 11.3 核心特性

通过使用公共基类，报表模块自动获得以下能力：

1. **组织隔离**：所有数据自动按组织过滤
2. **软删除**：删除操作自动使用软删除，支持恢复
3. **批量操作**：支持批量删除、批量恢复、批量更新
4. **审计日志**：自动记录创建人、创建时间、更新时间
5. **动态字段**：支持 custom_fields 存储动态扩展数据
6. **统一过滤**：支持时间范围、创建人等公共字段过滤
7. **分页查询**：自动支持标准分页

---

## 12. 边界条件和异常场景测试用例

### 12.1 报表生成测试用例

#### 12.1.1 数据量边界测试

**测试目标**：验证报表生成功能在数据量极大情况下的性能和稳定性

**正常场景测试**：
```python
def test_large_dataset_report_generation(self):
    """大数据量表生成测试"""
    # 创建10000条资产数据
    assets = []
    for i in range(10000):
        asset = AssetFactory(
            code=f'ASSET_{i:05d}',
            purchase_price=Decimal(str(1000 + i % 500)),
            purchase_date=timezone.now() - timedelta(days=30*i)
        )
        assets.append(asset)

    # 生成资产明细表
    params = {
        'template_id': template.id,
        'filters': {
            'org_id': self.org.id,
            'created_at_from': '2020-01-01',
            'created_at_to': timezone.now().strftime('%Y-%m-%d')
        }
    }

    # 测试执行时间（应在30秒内完成）
    start_time = time.time()
    result = ReportEngine.generate('asset_detail', params)
    end_time = time.time()

    # 断言
    self.assertLess(end_time - start_time, 30)
    self.assertEqual(result['total_count'], 10000)
    self.assertIn('data', result)
```

**异常场景测试**：
```python
def test_empty_dataset_handling(self):
    """空数据集处理测试"""
    # 清空测试数据
    Asset.objects.filter(org=self.org).delete()

    params = {'template_id': template.id}

    # 应该返回空数据而非报错
    result = ReportEngine.generate('asset_detail', params)

    self.assertEqual(result['total_count'], 0)
    self.assertEqual(len(result['data']), 0)
    self.assertIn('summary', result)

def test_zero_amount_validation(self):
    """零金额数据处理测试"""
    # 创建金额为0的资产
    asset = AssetFactory(
        purchase_price=Decimal('0'),
        residual_rate=0
    )

    result = ReportEngine.generate('asset_detail', params)

    # 应该正确处理零金额，不报错
    self.assertIsInstance(result['data'][0]['purchase_price'], Decimal)
    self.assertEqual(result['data'][0]['purchase_price'], 0)
```

#### 12.1.2 时间范围边界测试

**测试目标**：验证时间范围参数的各种边界情况

```python
def test_date_range_boundary_conditions(self):
    """时间范围边界条件测试"""
    # 创建测试数据
    asset1 = AssetFactory(purchase_date='2020-01-01')
    asset2 = AssetFactory(purchase_date='2025-12-31')
    asset3 = AssetFactory(purchase_date='2030-01-01')

    test_cases = [
        {
            'name': '最小日期边界',
            'params': {'created_at_from': '0001-01-01'},
            'expected_count': 3
        },
        {
            'name': '最大日期边界',
            'params': {'created_at_to': '9999-12-31'},
            'expected_count': 3
        },
        {
            'name': '未来日期过滤',
            'params': {'created_at_from': timezone.now().year + 10},
            'expected_count': 1  # 只有2030年的数据
        },
        {
            'name': '无效日期格式',
            'params': {'created_at_from': '2020/13/01'},  # 无效月份
            'should_raise': True
        }
    ]

    for case in test_cases:
        with self.subTest(case['name']):
            if case.get('should_raise'):
                with self.assertRaises(ValueError):
                    ReportEngine.generate('asset_detail', case['params'])
            else:
                result = ReportEngine.generate('asset_detail', case['params'])
                self.assertEqual(result['total_count'], case['expected_count'])
```

### 12.2 导出功能测试用例

#### 12.2.1 文件格式边界测试

**测试目标**：验证不同格式导出的边界条件

```python
class ReportExportTestCase(APITestCase):
    """报表导出测试用例"""

    def setUp(self):
        self.template = ReportTemplateFactory(
            report_type='asset_detail',
            allow_export=True
        )
        self.org = OrganizationFactory()
        self.user = UserFactory(org=self.org)

    def test_export_formats_boundary(self):
        """导出格式边界测试"""
        # 创建测试数据
        for i in range(1001):  # 超过1000行
            AssetFactory(org=self.org)

        params = {'template_id': self.template.id}

        # 测试不同格式的导出
        formats_to_test = ['pdf', 'excel', 'csv', 'json']

        for format_type in formats_to_test:
            with self.subTest(f'Test {format_type} export'):
                try:
                    result = ReportEngine.export(
                        'asset_detail',
                        params,
                        format_type=format_type
                    )

                    # 验证文件生成
                    self.assertIsNotNone(result['file_path'])
                    self.assertTrue(os.path.exists(result['file_path']))

                    # 验证文件大小（不应为0）
                    file_size = os.path.getsize(result['file_path'])
                    self.assertGreater(file_size, 0)

                except Exception as e:
                    # 某些格式可能不支持，应该返回明确的错误信息
                    self.assertIn(str(e), ['Unsupported format', 'Format not supported'])

    def test_export_memory_usage(self):
        """导出内存使用测试"""
        # 创建大量数据测试内存使用
        for i in range(5000):
            AssetFactory(org=self.org)

        params = {'template_id': self.template.id}

        # 监控内存使用
        import psutil
        process = psutil.Process()
        start_memory = process.memory_info().rss

        result = ReportEngine.export('asset_detail', params, format_type='excel')

        end_memory = process.memory_info().rss
        memory_increase = end_memory - start_memory

        # 内存增长不应超过500MB
        self.assertLess(memory_increase, 500 * 1024 * 1024)
```

#### 12.2.2 导出异常处理测试

```python
def test_export_exception_scenarios(self):
    """导出异常场景测试"""
        # 测试各种异常情况

        # 1. 磁盘空间不足（模拟）
        with patch('os.statvfs') as mock_stat:
            mock_stat.return_value.f_bavail = 0  # 无可用空间
            mock_stat.return_value.f_frsize = 1024

            with self.assertRaises(InsufficientDiskSpaceError):
                ReportEngine.export('asset_detail', params, format_type='pdf')

        # 2. 权限不足
        with patch('os.makedirs') as mock_makedirs:
            mock_makedirs.side_effect = PermissionError("Permission denied")

            with self.assertRaises(PermissionError):
                ReportEngine.export('asset_detail', params, format_type='excel')

        # 3. 模板损坏
        self.template.template_config = {'invalid': 'config'}
        self.template.save()

        with self.assertRaises(TemplateConfigError):
            ReportEngine.export('asset_detail', params, format_type='pdf')
```

### 12.3 定时任务测试用例

#### 12.3.1 任务调度边界测试

**测试目标**：验证定时任务在各种边界条件下的执行稳定性

```python
class ScheduledReportTestCase(TestCase):
    """定时报表测试用例"""

    def setUp(self):
        self.org = OrganizationFactory()
        self.template = ReportTemplateFactory(
            report_type='depreciation_summary'
        )

    def test_task_schedule_boundary(self):
        """任务调度边界测试"""
        # 测试各种调度时间
        test_schedules = [
            ('0 0 1 * *', '每月1号凌晨'),  # 正常
            ('0 0 29 2 *', '闰年2月29号'),  # 边界日期
            ('0 0 23 31 *', '每月31号'),  # 可能不存在的日期
            ('0 0 0 13 *', '每月13号凌晨'),  # 正常
            ('0 0 * * 7', '每周日凌晨'),  # 周调度
        ]

        for cron_expr, description in test_schedules:
            with self.subTest(f'Test schedule: {description}'):
                # 创建调度任务
                schedule = ScheduledReport.objects.create(
                    name=f'Test_{description}',
                    template=self.template,
                    cron_expression=cron_expr,
                    org=self.org
                )

                # 验证cron表达式有效性
                self.assertIsNotNone(schedule.next_run_time())

    def test_task_retry_mechanism(self):
        """任务重试机制测试"""
        # 创建一个会失败的任务
        schedule = ScheduledReport.objects.create(
            name='Fail_Test',
            template=self.template,
            cron_expression='0 0 * * *',  # 每小时执行
            org=self.org
        )

        # 模拟任务失败
        with patch('apps.reports.tasks.generate_scheduled_report') as mock_task:
            mock_task.side_effect = Exception("模拟失败")

            # 第一次执行失败
            result = schedule.execute()
            self.assertFalse(result['success'])

            # 第二次重试
            mock_task.side_effect = None  # 恢复正常
            result = schedule.execute()
            self.assertTrue(result['success'])
```

### 12.4 权限和访问控制测试

#### 12.4.1 越权访问测试

```python
class ReportPermissionTestCase(APITestCase):
    """报表权限测试用例"""

    def setUp(self):
        # 创建不同组织的用户和模板
        self.org1 = OrganizationFactory(name="公司A")
        self.org2 = OrganizationFactory(name="公司B")

        self.user1 = UserFactory(org=self.org1)
        self.user2 = UserFactory(org=self.org2)

        self.template1 = ReportTemplateFactory(
            report_type='asset_detail',
            required_permission='report.view_asset'
        )
        self.template2 = ReportTemplateFactory(
            report_type='depreciation_summary',
            required_permission='report.view_depreciation'
        )

    def test_cross_organization_data_isolation(self):
        """跨组织数据隔离测试"""
        # 在org1创建数据
        asset1 = AssetFactory(org=self.org1, code='ZC001')

        # 在org2创建数据
        asset2 = AssetFactory(org=self.org2, code='ZC002')

        # 测试org1用户只能看到自己的数据
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/reports/asset-detail/?template_id={self.template1.id}')

        self.assertEqual(response.data['total_count'], 1)
        self.assertEqual(response.data['data'][0]['code'], 'ZC001')

        # 测试org2用户只能看到自己的数据
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f'/api/reports/asset-detail/?template_id={self.template1.id}')

        self.assertEqual(response.data['total_count'], 1)
        self.assertEqual(response.data['data'][0]['code'], 'ZC002')

    def test_permission_boundary_conditions(self):
        """权限边界条件测试"""
        # 创建无权限的用户
        user_no_perm = UserFactory(org=self.org1)
        user_no_perm.user_permissions.clear()

        # 测试无权限访问
        self.client.force_authenticate(user=user_no_perm)
        response = self.client.get(f'/api/reports/asset-detail/?template_id={self.template1.id}')

        self.assertEqual(response.status_code, 403)

        # 测试过期用户（已离职）
        user_no_perm.is_active = False
        user_no_perm.save()

        response = self.client.get(f'/api/reports/asset-detail/?template_id={self.template1.id}')
        self.assertEqual(response.status_code, 401)
```

### 12.5 性能和并发测试

#### 12.5.1 并发生成测试

```python
class ReportConcurrencyTestCase(TestCase):
    """报表并发测试用例"""

    def setUp(self):
        self.org = OrganizationFactory()
        self.template = ReportTemplateFactory(
            report_type='asset_detail'
        )
        # 创建大量测试数据
        for i in range(5000):
            AssetFactory(org=self.org)

    def test_concurrent_report_generation(self):
        """并发报表生成测试"""
        params = {'template_id': self.template.id}

        # 创建多个并发任务
        import concurrent.futures
        import threading

        results = []
        errors = []

        def generate_report():
            try:
                result = ReportEngine.generate('asset_detail', params)
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        # 并发执行10个报表生成任务
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(generate_report) for _ in range(10)]
            concurrent.futures.wait(futures)

        # 验证结果
        self.assertEqual(len(errors), 0)  # 没有错误
        self.assertEqual(len(results), 10)  # 10个都完成

        # 验证结果一致性
        for i in range(1, len(results)):
            self.assertEqual(results[0]['total_count'], results[i]['total_count'])

    def test_memory_leak_detection(self):
        """内存泄漏检测测试"""
        import psutil
        import gc

        # 初始内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # 重复执行报表生成
        for i in range(100):
            params = {'template_id': self.template.id}
            result = ReportEngine.generate('asset_detail', params)

            # 手动触发垃圾回收
            gc.collect()

            # 检查内存增长
            current_memory = process.memory_info().rss
            memory_growth = current_memory - initial_memory

            # 内存增长不应超过100MB
            self.assertLess(memory_growth, 100 * 1024 * 1024,
                          f"内存泄漏检测：第{i}次执行后内存增长过大")
```

### 12.6 数据完整性测试

#### 12.6.1 数据一致性测试

```python
class ReportDataIntegrityTestCase(TestCase):
    """报表数据完整性测试用例"""

    def test_data_consistency_across_formats(self):
        """跨格式数据一致性测试"""
        # 创建测试数据
        asset = AssetFactory(
            purchase_price=Decimal('1234.56'),
            residual_value=Decimal('100.00')
        )

        params = {'template_id': self.template.id}

        # 生成不同格式的报表
        pdf_data = ReportEngine.export('asset_detail', params, format_type='pdf')
        excel_data = ReportEngine.export('asset_detail', params, format_type='excel')
        json_data = ReportEngine.export('asset_detail', params, format_type='json')

        # 验证数据一致性
        # 1. 总数量应该一致
        self.assertEqual(pdf_data['total_count'], excel_data['total_count'])
        self.assertEqual(pdf_data['total_count'], json_data['total_count'])

        # 2. 关键字段应该一致
        if pdf_data['data'] and excel_data['data'] and json_data['data']:
            pdf_record = pdf_data['data'][0]
            excel_record = excel_data['data'][0]
            json_record = json_data['data'][0]

            # 比较关键字段
            key_fields = ['id', 'code', 'name', 'purchase_price']
            for field in key_fields:
                self.assertEqual(
                    str(pdf_record.get(field, '')),
                    str(excel_record.get(field, '')),
                    f"PDF和Excel在{field}字段不一致"
                )
                self.assertEqual(
                    str(pdf_record.get(field, '')),
                    str(json_record.get(field, '')),
                    f"PDF和JSON在{field}字段不一致"
                )

    def test_data_validation_under_corruption(self):
        """数据损坏时的验证测试"""
        # 创建一个有问题的模板配置
        self.template.template_config = {
            'columns': [
                {'field': 'nonexistent_field'},  # 不存在的字段
                {'field': 'purchase_price', 'format': 'invalid_format'}  # 无效格式
            ]
        }
        self.template.save()

        # 应该能够处理而不崩溃，返回警告或跳过无效字段
        result = ReportEngine.generate('asset_detail', {'template_id': self.template.id})

        # 验证系统仍然返回数据，但可能缺少某些字段
        self.assertIsNotNone(result)
        self.assertIn('data', result)
```

### 12.7 回归测试用例

#### 12.7.1 向后兼容性测试

```python
class ReportRegressionTestCase(TestCase):
    """报表回归测试用例"""

    def test_backward_compatibility(self):
        """向后兼容性测试"""
        # 测试旧版本的API调用仍然有效
        old_api_params = {
            'template': self.template.template_code,
            'format': 'json',
            'filters': {
                'org': self.org.id
            }
        }

        # 应该能够处理旧格式参数
        try:
            result = ReportEngine.legacy_generate(old_api_params)
            self.assertIsNotNone(result)
        except NotImplementedError:
            # 如果不支持旧API，应该返回明确的错误信息
            pass

    def test_database_schema_migration(self):
        """数据库迁移测试"""
        # 模拟字段变更场景
        try:
            # 临时修改模型字段
            old_field = Asset._meta.get_field('purchase_price')
            Asset._meta.remove_field('purchase_price')

            # 测试报表生成
            result = ReportEngine.generate('asset_detail', params)

            # 验证系统能处理字段缺失的情况
            self.assertIn('warning', result)

        finally:
            # 恢复字段
            Asset._meta.add_field('purchase_price', old_field)
```

### 12.8 测试覆盖率要求

#### 12.8.1 核心功能覆盖率

**必须达到100%测试覆盖的功能模块**：
1. 报表模板 CRUD 操作
2. 数据查询和过滤逻辑
3. 导出功能核心逻辑
4. 权限验证机制
5. 组织隔离逻辑
6. 软删除和恢复功能

**必须测试的异常场景**：
1. 数据库连接失败
2. 网络超时
3. 磁盘空间不足
4. 内存不足
5. 权限变更
6. 配置文件损坏
7. 并发修改冲突

#### 12.8.2 性能指标要求

**性能基准测试**：
1. 1000条数据报表生成时间 < 5秒
2. 10000条数据报表生成时间 < 30秒
3. 50000条数据报表生成时间 < 120秒
4. 并发10个报表请求平均响应时间 < 10秒
5. 内存使用增长率 < 10MB/1000条记录

---

所有Phase已完成！
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