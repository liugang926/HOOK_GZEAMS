# Phase 5.4: 财务报表生成 - 测试计划

## 1. 测试概述

### 1.1 测试范围

| 模块 | 测试内容 |
|------|----------|
| 报表模板 | 模板创建、配置、权限控制 |
| 报表生成 | 数据查询、模板渲染、文件导出 |
| 定时报表 | 调度配置、定时执行、订阅推送 |
| 报表导出 | PDF生成、Excel生成 |

### 1.2 测试策略

| 测试类型 | 工具/框架 | 覆盖范围 |
|----------|-----------|----------|
| 单元测试 | pytest | 报表引擎、数据查询 |
| API测试 | pytest + requests | REST API接口 |
| 集成测试 | pytest | 完整报表生成流程 |
| 性能测试 | pytest | 大数据量报表生成 |

---

## 2. 单元测试

### 2.1 报表引擎测试

```python
# apps/reports/tests/test_engine.py

import pytest
from apps.reports.engine import ReportEngine
from apps.reports.models import ReportTemplate, ReportGeneration
from apps.assets.models import Asset


@pytest.mark.django_db
class TestReportEngine:
    """报表引擎测试"""

    def test_generate_report_no(self):
        """测试生成报表编号"""
        no1 = ReportEngine._generate_no()
        no2 = ReportEngine._generate_no()

        assert no1.startswith('RPT')
        assert no2.startswith('RPT')
        assert no1 != no2

    def test_query_model_data(self, asset_template, assets, user):
        """测试模型数据查询"""
        data_source = asset_template.data_source
        params = {
            'department_id': None,
            'category_id': None,
        }

        data = ReportEngine._query_model(data_source, params, user)

        assert 'data' in data
        assert 'total' in data
        assert data['total'] == len(assets)

    def test_query_aggregate_by_department(self, assets, user):
        """测试按部门聚合查询"""
        data_source = {
            'type': 'aggregate',
            'query': 'asset_by_department'
        }
        params = {}

        data = ReportEngine._query_aggregate(data_source, params, user)

        assert 'data' in data
        assert 'summary' in data
        assert 'total_departments' in data['summary']

    def test_query_aggregate_depreciation_summary(self, depreciations, user):
        """测试折旧汇总查询"""
        data_source = {
            'type': 'aggregate',
            'query': 'depreciation_summary'
        }
        params = {
            'period_from': '2024-01',
            'period_to': '2024-12'
        }

        data = ReportEngine._query_aggregate(data_source, params, user)

        assert 'by_period' in data
        assert 'by_category' in data
        assert 'summary' in data

    def test_get_section_data_header(self):
        """测试获取表头节区数据"""
        section_config = {
            'type': 'header',
            'title': '测试报表',
            'subtitle': '2024年1月'
        }
        data = {}

        result = ReportEngine._get_section_data('header', section_config, data, {})

        assert result['title'] == '测试报表'

    def test_get_section_data_table(self, sample_report_data):
        """测试获取表格节区数据"""
        section_config = {
            'type': 'table',
            'columns': [
                {'field': 'asset_no', 'title': '资产编号'},
                {'field': 'asset_name', 'title': '资产名称'}
            ]
        }

        result = ReportEngine._get_section_data('table', section_config, sample_report_data, {})

        assert 'columns' in result
        assert 'rows' in result
        assert len(result['columns']) == 2


@pytest.mark.django_db
class TestAssetDetailReportGenerator:
    """资产明细表生成器测试"""

    def test_generate_basic(self, assets, user):
        """测试基本生成"""
        from apps.reports.generators import AssetDetailReportGenerator

        params = {
            'department_id': None,
            'category_id': None,
        }

        result = AssetDetailReportGenerator.generate(params, user)

        assert 'data' in result
        assert 'summary' in result
        assert result['summary']['total_count'] == len(assets)

    def test_filter_by_department(self, assets, department, user):
        """测试按部门筛选"""
        from apps.reports.generators import AssetDetailReportGenerator

        # 将部分资产分配给部门
        dept_assets = assets[:5]
        for asset in dept_assets:
            asset.department = department
            asset.save()

        params = {'department_id': department.id}
        result = AssetDetailReportGenerator.generate(params, user)

        assert result['summary']['total_count'] == 5

    def test_filter_by_category(self, assets, category, user):
        """测试按类别筛选"""
        from apps.reports.generators import AssetDetailReportGenerator

        # 设置资产类别
        for asset in assets:
            asset.category = category
            asset.save()

        params = {'category_id': category.id}
        result = AssetDetailReportGenerator.generate(params, user)

        assert all(r['category_name'] == category.name for r in result['data'])

    def test_summary_calculation(self, assets, user):
        """测试汇总计算"""
        from apps.reports.generators import AssetDetailReportGenerator

        params = {}
        result = AssetDetailReportGenerator.generate(params, user)

        summary = result['summary']

        # 验证汇总值
        expected_original = sum(a.original_value for a in assets)
        expected_net = sum(a.net_value for a in assets)

        assert abs(summary['total_original'] - expected_original) < 0.01
        assert abs(summary['total_net'] - expected_net) < 0.01


@pytest.mark.django_db
class TestDepreciationSummaryReportGenerator:
    """折旧汇总表生成器测试"""

    def test_generate_by_category(self, depreciations, user):
        """测试按类别汇总"""
        from apps.reports.generators import DepreciationSummaryReportGenerator

        params = {
            'period_from': '2024-01',
            'period_to': '2024-12'
        }

        result = DepreciationSummaryReportGenerator.generate(params, user)

        assert 'by_category' in result
        assert 'by_period' in result

    def test_summary_totals(self, depreciations, user):
        """测试汇总总计"""
        from apps.reports.generators import DepreciationSummaryReportGenerator

        params = {}
        result = DepreciationSummaryReportGenerator.generate(params, user)

        summary = result['summary']
        expected_total = sum(d.depreciation_amount for d in depreciations)

        assert abs(summary['total_depreciation'] - expected_total) < 0.01


@pytest.mark.django_db
class TestAssetChangeReportGenerator:
    """资产增减变动表生成器测试"""

    def test_generate(self, assets, user):
        """测试生成增减变动表"""
        from apps.reports.generators import AssetChangeReportGenerator
        from datetime import date, timedelta
        from apps.lifecycle.models import DisposalRequest

        # 创建一些处置记录
        today = date.today()
        DisposalRequest.objects.create(
            request_no='DS2024010001',
            applicant=user,
            department_id=user.department_id,
            request_date=today,
            disposal_type='scrap',
            disposal_reason='测试',
            org=user.org,
            created_by=user,
        )

        params = {
            'period_from': str(today - timedelta(days=30)),
            'period_to': str(today)
        }

        result = AssetChangeReportGenerator.generate(params, user)

        assert 'beginning' in result
        assert 'added' in result
        assert 'removed' in result
        assert 'ending' in result
```

### 2.2 导出器测试

```python
# apps/reports/tests/test_exporters.py

import pytest
import os
from apps.reports.exporters import PDFExporter, ExcelExporter
from django.conf import settings


@pytest.mark.django_db
class TestPDFExporter:
    """PDF导出器测试"""

    def test_export_simple_table(self, tmp_path, sample_table_data):
        """测试导出简单表格"""
        exporter = PDFExporter()

        file_path = exporter.export(sample_table_data, str(tmp_path), 'test_report')

        assert os.path.exists(file_path)
        assert file_path.endswith('.pdf')
        assert os.path.getsize(file_path) > 0

    def test_export_with_title(self, tmp_path):
        """测试带标题的导出"""
        data = {
            'title': '测试报表',
            'columns': [
                {'field': 'name', 'title': '名称'},
                {'field': 'value', 'title': '数值'}
            ],
            'rows': [
                {'name': '项目1', 'value': 100},
                {'name': '项目2', 'value': 200}
            ]
        }

        exporter = PDFExporter()
        file_path = exporter.export(data, str(tmp_path), 'title_test')

        assert os.path.exists(file_path)


@pytest.mark.django_db
class TestExcelExporter:
    """Excel导出器测试"""

    def test_export_simple_table(self, tmp_path, sample_table_data):
        """测试导出简单表格"""
        exporter = ExcelExporter()

        file_path = exporter.export(sample_table_data, str(tmp_path), 'test_report')

        assert os.path.exists(file_path)
        assert file_path.endswith('.xlsx')

        # 验证文件可以被openpyxl读取
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        assert wb.active.max_row > 0
        wb.close()

    def test_export_with_formulas(self, tmp_path):
        """测试带公式的导出"""
        data = {
            'title': '销售报表',
            'columns': [
                {'field': 'product', 'title': '产品'},
                {'field': 'quantity', 'title': '数量'},
                {'field': 'price', 'title': '单价'},
                {'field': 'amount', 'title': '金额', 'formula': '=quantity*price'}
            ],
            'rows': [
                {'product': 'A', 'quantity': 10, 'price': 100},
                {'product': 'B', 'quantity': 5, 'price': 200}
            ]
        }

        exporter = ExcelExporter()
        file_path = exporter.export(data, str(tmp_path), 'formula_test')

        assert os.path.exists(file_path)
```

---

## 3. API集成测试

```python
# apps/reports/tests/test_api.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


@pytest.mark.django_db
class TestReportTemplateAPI:
    """报表模板API测试"""

    @pytest.fixture
    def api_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_templates(self, api_client, templates):
        """测试获取模板列表"""
        url = reverse('template-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= len(templates)

    def test_get_template(self, api_client, template):
        """测试获取模板详情"""
        url = reverse('template-detail', kwargs={'code': template.template_code})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['template_code'] == template.template_code

    def test_create_template(self, api_client, user):
        """测试创建模板"""
        url = reverse('template-list')
        data = {
            'template_code': 'CUSTOM_TEST',
            'template_name': '自定义测试报表',
            'report_type': 'custom',
            'description': '测试用',
            'template_config': {},
            'data_source': {
                'type': 'model',
                'model': 'assets.Asset'
            }
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_update_template(self, api_client, template):
        """测试更新模板"""
        url = reverse('template-detail', kwargs={'code': template.template_code})
        data = {
            'template_name': '更新后的名称',
            'description': '更新描述'
        }

        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestReportGenerationAPI:
    """报表生成API测试"""

    @pytest.fixture
    def api_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_generate_report(self, api_client, template, user):
        """测试生成报表"""
        url = reverse('generate')
        data = {
            'template_code': template.template_code,
            'params': {},
            'output_format': 'pdf'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'generation_no' in response.data

    def test_preview_report(self, api_client, template):
        """测试预览报表"""
        url = reverse('preview')
        data = {
            'template_code': template.template_code,
            'params': {}
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data

    def test_get_generation_status(self, api_client, generation):
        """测试获取生成状态"""
        url = reverse('generation-detail', kwargs={'id': generation.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == generation.id

    def test_list_generations(self, api_client, generations):
        """测试获取生成记录列表"""
        url = reverse('generation-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= len(generations)

    def test_download_report(self, api_client, completed_generation):
        """测试下载报表"""
        url = reverse('generation-download', kwargs={'id': completed_generation.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # 验证返回的是文件
        assert response['Content-Type'] in ['application/pdf', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']


@pytest.mark.django_db
class TestScheduleAPI:
    """定时报表API测试"""

    @pytest.fixture
    def api_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_schedules(self, api_client, schedules):
        """测试获取调度列表"""
        url = reverse('schedule-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_create_schedule(self, api_client, template, user):
        """测试创建调度"""
        url = reverse('schedule-list')
        data = {
            'schedule_name': '月度测试报表',
            'schedule_code': 'TEST_MONTHLY',
            'template_id': template.id,
            'frequency': 'monthly',
            'cron_expression': '0 0 2 1 * *',
            'valid_from': '2024-01-01'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_toggle_schedule(self, api_client, schedule):
        """测试启用/停用调度"""
        original_status = schedule.is_active

        url = reverse('schedule-toggle', kwargs={'id': schedule.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] != original_status


@pytest.mark.django_db
class TestSubscriptionAPI:
    """报表订阅API测试"""

    @pytest.fixture
    def api_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_my_subscriptions(self, api_client, subscriptions):
        """测试获取我的订阅"""
        url = reverse('my-subscriptions')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_subscribe_report(self, api_client, schedule, user):
        """测试订阅报表"""
        url = reverse('subscription-list')
        data = {
            'schedule_id': schedule.id,
            'delivery_methods': ['email'],
            'email': 'test@example.com'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_unsubscribe_report(self, api_client, subscription):
        """测试取消订阅"""
        url = reverse('subscription-detail', kwargs={'id': subscription.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
```

---

## 4. 集成测试

```python
# apps/reports/tests/test_integration.py

@pytest.mark.django_db
class TestReportGenerationWorkflow:
    """报表生成完整流程测试"""

    def test_complete_generation_workflow(self, org, user, assets):
        """测试完整的报表生成流程"""
        from apps.reports.engine import ReportEngine
        from apps.reports.models import ReportTemplate, ReportGeneration

        # 1. 创建模板
        template = ReportTemplate.objects.create(
            template_code='INTEGRATION_TEST',
            template_name='集成测试报表',
            report_type='asset_detail',
            status='active',
            org=org,
            created_by=user,
            template_config={
                'sections': [{
                    'type': 'table',
                    'columns': [
                        {'field': 'asset_no', 'title': '编号'},
                        {'field': 'asset_name', 'title': '名称'}
                    ]
                }]
            },
            data_source={
                'type': 'model',
                'model': 'assets.Asset',
                'fields': ['asset_no', 'asset_name']
            }
        )

        # 2. 生成报表
        generation = ReportEngine.generate_report(
            template_code=template.template_code,
            params={},
            output_format='html',  # 使用HTML避免文件生成
            user=user
        )

        # 3. 验证生成记录
        assert generation.status == 'success'
        assert generation.template == template
        assert generation.generated_by == user

        # 4. 验证数据缓存
        assert generation.cached_data is not None
        assert 'data' in generation.cached_data

    def test_schedule_and_execute(self, org, user, template):
        """测试调度配置和执行"""
        from apps.reports.models import ReportSchedule
        from apps.reports.tasks import execute_scheduled_reports

        # 1. 创建调度任务
        schedule = ReportSchedule.objects.create(
            schedule_name='测试调度',
            schedule_code='TEST_SCHEDULE',
            template=template,
            frequency='daily',
            cron_expression='0 0 * * * *',
            valid_from='2024-01-01',
            next_run_at=timezone.now(),
            is_active=True,
            org=org,
            created_by=user,
        )

        # 2. 执行调度
        execute_scheduled_reports()

        # 3. 验证执行结果
        schedule.refresh_from_db()
        assert schedule.last_run_at is not None

        # 4. 验证报表已生成
        generations = template.generations.filter(
            generated_by__isnull=True  # 系统生成的
        )
        assert generations.exists()
```

---

## 5. 性能测试

```python
# apps/reports/tests/test_performance.py

@pytest.mark.django_db
@pytest.mark.performance
class TestReportPerformance:
    """报表性能测试"""

    def test_large_asset_report_generation(self, large_asset_set, user, template):
        """测试大数据量资产报表生成"""
        from apps.reports.engine import ReportEngine
        import time

        start_time = time.time()
        generation = ReportEngine.generate_report(
            template_code=template.template_code,
            params={},
            output_format='html',
            user=user
        )
        elapsed = time.time() - start_time

        # 验证性能：10000条资产应在30秒内生成
        assert elapsed < 30
        assert generation.status == 'success'

    def test_aggregation_query_performance(self, many_assets, user):
        """测试聚合查询性能"""
        from apps.reports.engine import ReportEngine
        import time

        data_source = {
            'type': 'aggregate',
            'query': 'asset_by_department'
        }
        params = {}

        start_time = time.time()
        result = ReportEngine._query_aggregate(data_source, params, user)
        elapsed = time.time() - start_time

        # 验证性能：聚合查询应在5秒内完成
        assert elapsed < 5
        assert 'data' in result

    def test_concurrent_report_generation(self, template, user):
        """测试并发报表生成"""
        from apps.reports.engine import ReportEngine
        from concurrent.futures import ThreadPoolExecutor
        import time

        def generate_report():
            return ReportEngine.generate_report(
                template_code=template.template_code,
                params={},
                output_format='html',
                user=user
            )

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_report) for _ in range(10)]
            results = [f.result() for f in futures]
        elapsed = time.time() - start_time

        # 验证所有生成都成功
        assert all(r.status == 'success' for r in results)
        # 验证总时间合理
        assert elapsed < 60
```

---

## 6. Fixtures配置

```python
# apps/reports/tests/conftest.py

import pytest
from django.utils import timezone
from apps.reports.models import ReportTemplate, ReportGeneration, ReportSchedule
from apps.assets.models import Asset, AssetCategory, AssetDepreciation
from apps.organizations.models import Department


@pytest.fixture
def template(org, user):
    return ReportTemplate.objects.create(
        template_code='ASSET_DETAIL',
        template_name='固定资产明细表',
        report_type='asset_detail',
        description='包含资产基本信息',
        status='active',
        template_config={
            'sections': [{
                'type': 'table',
                'title': '资产明细',
                'columns': [
                    {'field': 'asset_no', 'title': '资产编号', 'width': 120},
                    {'field': 'asset_name', 'title': '资产名称', 'width': 200},
                    {'field': 'original_value', 'title': '原值', 'width': 120, 'format': 'currency'},
                    {'field': 'net_value', 'title': '净值', 'width': 120, 'format': 'currency'},
                ]
            }]
        },
        data_source={
            'type': 'model',
            'model': 'assets.Asset',
            'fields': ['asset_no', 'asset_name', 'original_value', 'net_value'],
            'filters': [
                {'field': 'department_id', 'param_key': 'department_id'},
                {'field': 'category_id', 'param_key': 'category_id'},
            ],
            'order_by': ['asset_no']
        },
        org=org,
        created_by=user,
    )


@pytest.fixture
def templates(org, user):
    return [
        ReportTemplate.objects.create(
            template_code=f'TEMPLATE_{i}',
            template_name=f'测试报表{i}',
            report_type='asset_detail',
            status='active',
            template_config={},
            data_source={'type': 'model', 'model': 'assets.Asset'},
            org=org,
            created_by=user,
        )
        for i in range(3)
    ]


@pytest.fixture
def sample_table_data():
    return {
        'columns': [
            {'field': 'name', 'title': '名称'},
            {'field': 'value', 'title': '数值'}
        ],
        'rows': [
            {'name': '项目A', 'value': 100},
            {'name': '项目B', 'value': 200},
            {'name': '项目C', 'value': 300}
        ]
    }


@pytest.fixture
def sample_report_data(assets):
    return {
        'data': [
            {
                'asset_no': a.asset_no,
                'asset_name': a.asset_name,
                'original_value': float(a.original_value),
                'net_value': float(a.net_value)
            }
            for a in assets[:10]
        ],
        'summary': {
            'total_count': 10,
            'total_original': 50000.00,
            'total_net': 45000.00
        }
    }


@pytest.fixture
def generation(template, user):
    return ReportGeneration.objects.create(
        template=template,
        generation_no='RPT20240115123456789',
        status='success',
        report_params={},
        output_format='pdf',
        generated_by=user,
        org=template.org,
        created_by=user,
    )


@pytest.fixture
def completed_generation(generation):
    generation.status = 'success'
    generation.file_path = '/media/reports/test.pdf'
    generation.generated_at = timezone.now()
    generation.save()
    return generation


@pytest.fixture
def generations(generation):
    # 返回多个生成记录
    return [generation]


@pytest.fixture
def schedule(template, user):
    return ReportSchedule.objects.create(
        schedule_name='月度资产报表',
        schedule_code='MONTHLY_ASSET',
        template=template,
        frequency='monthly',
        cron_expression='0 0 2 1 * *',
        valid_from='2024-01-01',
        is_active=True,
        next_run_at=timezone.now(),
        org=template.org,
        created_by=user,
    )


@pytest.fixture
def schedules(schedule):
    return [schedule]


@pytest.fixture
def subscription(schedule, user):
    return schedule.subscriptions.create(
        subscriber=user,
        delivery_methods=['system'],
        org=user.org,
    )


@pytest.fixture
def subscriptions(subscription):
    return [subscription]


@pytest.fixture
def large_asset_set(org, category):
    # 创建大量资产用于性能测试
    return Asset.objects.bulk_create([
        Asset(
            asset_no=f'ZC2024{i:06d}',
            asset_name=f'测试资产{i}',
            category=category,
            original_value=5000,
            org=org,
        )
        for i in range(10000)
    ])
```

---

## 7. 测试执行

```bash
# 运行所有报表测试
pytest apps/reports/tests/

# 运行特定测试文件
pytest apps/reports/tests/test_engine.py

# 运行API测试
pytest apps/reports/tests/test_api.py

# 运行性能测试
pytest apps/reports/tests/ -m performance

# 生成覆盖率报告
pytest --cov=apps.reports --cov-report=html apps/reports/tests/
```
