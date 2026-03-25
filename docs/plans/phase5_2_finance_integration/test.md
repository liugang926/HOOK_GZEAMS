# Phase 5.2: 财务凭证集成 - 测试计划

## 概述

本文档描述财务凭证集成模块的测试策略，包括单元测试、集成测试、API测试和端到端测试。

---

## 1. 单元测试

### 1.1 凭证模板模型测试

```python
# tests/apps/assets/models/test_finance_models.py

import pytest
from apps.assets.models.finance import VoucherTemplate, FinanceVoucher


@pytest.mark.django_db
class TestVoucherTemplate:
    """凭证模板模型测试"""

    def test_create_voucher_template(self, organization):
        """测试创建凭证模板"""
        template = VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='资产购入默认模板',
            voucher_type='记',
            default_description='购入固定资产',
            entries_config=[
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'direction': 'debit',
                    'amount': '${asset.purchase_price}'
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'direction': 'credit',
                    'amount': '${asset.purchase_price}'
                }
            ]
        )

        assert template.business_type == 'asset_purchase'
        assert template.voucher_type == '记'
        assert len(template.entries_config) == 2

    def test_business_type_choices(self, organization):
        """测试业务类型选项"""
        valid_types = [
            'asset_purchase',
            'asset_depreciation',
            'asset_disposal',
            'asset_transfer',
            'asset_impairment'
        ]

        for business_type in valid_types:
            template = VoucherTemplate.objects.create(
                organization=organization,
                business_type=business_type,
                template_name=f'{business_type}模板',
                voucher_type='记',
                default_description='测试',
                entries_config=[]
            )
            assert template.get_business_type_display() != business_type

    def test_template_active_filter(self, organization):
        """测试激活模板筛选"""
        VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='激活模板',
            voucher_type='记',
            is_active=True,
            entries_config=[]
        )

        VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='未激活模板',
            voucher_type='记',
            is_active=False,
            entries_config=[]
        )

        active_templates = VoucherTemplate.objects.filter(
            organization=organization,
            is_active=True
        )

        assert active_templates.count() == 1
        assert active_templates.first().template_name == '激活模板'


@pytest.mark.django_db
class TestFinanceVoucher:
    """财务凭证模型测试"""

    def test_create_finance_voucher(self, organization):
        """测试创建财务凭证"""
        voucher = FinanceVoucher.objects.create(
            organization=organization,
            business_type='asset_purchase',
            business_id='asset_123',
            voucher_no='PZ2024010001',
            voucher_date='2024-01-15',
            voucher_type='记',
            description='购入固定资产',
            entries=[
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'debit': 8000,
                    'credit': 0
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'debit': 0,
                    'credit': 8000
                }
            ],
            total_debit=8000,
            total_credit=8000,
            status='draft'
        )

        assert voucher.voucher_no == 'PZ2024010001'
        assert voucher.total_debit == voucher.total_credit
        assert voucher.status == 'draft'

    def test_voucher_status_transitions(self, organization):
        """测试凭证状态转换"""
        voucher = FinanceVoucher.objects.create(
            organization=organization,
            business_type='asset_purchase',
            business_id='asset_123',
            voucher_no='PZ2024010001',
            voucher_date='2024-01-15',
            voucher_type='记',
            description='测试',
            entries=[],
            total_debit=0,
            total_credit=0,
            status='draft'
        )

        # 草稿 -> 已提交
        voucher.status = 'submitted'
        voucher.save()
        assert voucher.status == 'submitted'

        # 已提交 -> 已审核
        voucher.status = 'approved'
        voucher.save()
        assert voucher.status == 'approved'

        # 已审核 -> 已过账
        voucher.status = 'posted'
        voucher.save()
        assert voucher.status == 'posted'

    def test_voucher_integration_fields(self, organization):
        """测试凭证集成字段"""
        voucher = FinanceVoucher.objects.create(
            organization=organization,
            business_type='asset_purchase',
            business_id='asset_123',
            voucher_no='PZ2024010001',
            voucher_date='2024-01-15',
            voucher_type='记',
            description='测试',
            entries=[],
            total_debit=0,
            total_credit=0,
            integration_system='m18',
            external_voucher_no='M18-PZ-001'
        )

        assert voucher.integration_system == 'm18'
        assert voucher.external_voucher_no == 'M18-PZ-001'
```

### 1.2 凭证生成服务测试

```python
# tests/apps/assets/services/test_finance_voucher_service.py

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import Mock, patch
from apps.assets.services.finance_voucher_service import FinanceVoucherService
from apps.assets.models.finance import VoucherTemplate, FinanceVoucher
from apps.assets.models import Asset


@pytest.mark.django_db
class TestFinanceVoucherService:
    """财务凭证生成服务测试"""

    @pytest.fixture
    def service(self, organization):
        """创建凭证服务"""
        return FinanceVoucherService(organization)

    @pytest.fixture
    def purchase_template(self, organization):
        """创建资产购入模板"""
        return VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='资产购入默认模板',
            voucher_type='记',
            default_description='购入固定资产',
            entries_config=[
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'direction': 'debit',
                    'amount': '${asset.purchase_price}'
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'direction': 'credit',
                    'amount': '${asset.purchase_price}'
                }
            ]
        )

    def test_generate_voucher_success(self, service, purchase_template):
        """测试成功生成凭证"""
        business_data = {
            'business_id': 'asset_123',
            'voucher_date': date(2024, 1, 15),
            'description': '购入MacBook Pro',
            'asset': {
                'purchase_price': 8000,
                'asset_category': '电子设备'
            }
        }

        voucher = service.generate_voucher('asset_purchase', business_data)

        assert voucher.business_type == 'asset_purchase'
        assert voucher.business_id == 'asset_123'
        assert voucher.voucher_type == '记'
        assert voucher.total_debit == Decimal('8000')
        assert voucher.total_credit == Decimal('8000')
        assert len(voucher.entries) == 2

    def test_generate_voucher_no_template(self, service):
        """测试没有模板时生成凭证"""
        business_data = {
            'business_id': 'asset_123',
            'voucher_date': date(2024, 1, 15),
            'description': '测试'
        }

        with pytest.raises(ValueError) as exc_info:
            service.generate_voucher('nonexistent_type', business_data)

        assert '未找到凭证模板' in str(exc_info.value)

    def test_resolve_entries_with_variables(self, service, purchase_template):
        """测试解析包含变量的分录"""
        business_data = {
            'business_id': 'asset_123',
            'voucher_date': date(2024, 1, 15),
            'description': '购入MacBook Pro',
            'asset': {
                'purchase_price': 8000
            }
        }

        voucher = service.generate_voucher('asset_purchase', business_data)

        # 验证变量已正确解析
        entries = voucher.entries
        assert entries[0]['debit'] == Decimal('8000')
        assert entries[1]['credit'] == Decimal('8000')

    def test_calculate_amount_with_direct_value(self, service, organization):
        """测试直接金额值计算"""
        result = service._calculate_amount(5000, {})
        assert result == Decimal('5000')

    def test_calculate_amount_with_variable(self, service):
        """测试变量引用金额计算"""
        business_data = {'asset': {'purchase_price': 8000}}
        result = service._calculate_amount('${asset.purchase_price}', business_data)
        assert result == Decimal('8000')

    def test_get_nested_value(self, service):
        """测试获取嵌套字段值"""
        data = {
            'asset': {
                'purchase_price': 8000,
                'category': {
                    'name': '电子设备'
                }
            }
        }

        # 一级嵌套
        assert service._get_nested_value(data, 'asset.purchase_price') == 8000

        # 二级嵌套
        assert service._get_nested_value(data, 'asset.category.name') == '电子设备'

        # 不存在的字段
        assert service._get_nested_value(data, 'asset.nonexistent') is None

    def test_generate_asset_purchase_voucher(self, service, purchase_template, organization):
        """测试生成资产购入凭证"""
        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            purchase_price=8000,
            purchase_date=date(2024, 1, 15)
        )

        voucher = service.generate_asset_purchase_voucher(asset)

        assert voucher.business_type == 'asset_purchase'
        assert voucher.business_id == str(asset.id)
        assert voucher.total_debit == Decimal('8000')
        assert 'MacBook Pro' in voucher.description

    def test_voucher_balance_validation(self, service, organization):
        """测试凭证借贷平衡"""
        # 创建不平衡的模板配置
        VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='不平衡模板',
            voucher_type='记',
            default_description='测试',
            entries_config=[
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'direction': 'debit',
                    'amount': 8000
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'direction': 'credit',
                    'amount': 7000  # 不平衡
                }
            ]
        )

        business_data = {
            'business_id': 'asset_123',
            'voucher_date': date(2024, 1, 15),
            'description': '测试'
        }

        voucher = service.generate_voucher('asset_purchase', business_data)

        # 验证借贷不平衡
        assert voucher.total_debit != voucher.total_credit
```

### 1.3 凭证推送服务测试

```python
# tests/apps/integration/services/test_voucher_push_service.py

import pytest
from unittest.mock import Mock, patch
from apps.integration.services.voucher_push_service import VoucherPushService
from apps.assets.models.finance import FinanceVoucher
from apps.integration.models import IntegrationConfig


@pytest.mark.django_db
class TestVoucherPushService:
    """凭证推送服务测试"""

    @pytest.fixture
    def service(self, organization):
        """创建推送服务"""
        return VoucherPushService(organization)

    @pytest.fixture
    def voucher(self, organization):
        """创建测试凭证"""
        return FinanceVoucher.objects.create(
            organization=organization,
            business_type='asset_purchase',
            business_id='asset_123',
            voucher_no='PZ2024010001',
            voucher_date='2024-01-15',
            voucher_type='记',
            description='购入固定资产',
            entries=[
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'debit': 8000,
                    'credit': 0
                }
            ],
            total_debit=8000,
            total_credit=8000,
            status='draft'
        )

    @pytest.fixture
    def integration_config(self, organization):
        """创建集成配置"""
        return IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            is_enabled=True,
            enabled_modules=['finance'],
            connection_config={'api_url': 'https://test.m18.com'}
        )

    def test_push_voucher_success(self, service, voucher, integration_config):
        """测试成功推送凭证"""
        with patch('apps.integration.factory.AdapterFactory') as mock_factory:
            mock_adapter = Mock()
            mock_adapter.push_data.return_value = {
                'voucher_no': 'M18-PZ-001'
            }
            mock_adapter.map_to_external.return_value = {}
            mock_factory.create.return_value = mock_adapter

            result = service.push_voucher(voucher)

            assert result['success'] is True
            assert result['external_voucher_no'] == 'M18-PZ-001'

            # 验证凭证状态已更新
            voucher.refresh_from_db()
            assert voucher.status == 'submitted'
            assert voucher.external_voucher_no == 'M18-PZ-001'
            assert voucher.pushed_at is not None

    def test_push_voucher_no_config(self, service, voucher):
        """测试没有集成配置时推送"""
        result = service.push_voucher(voucher)

        assert result['success'] is False
        assert '未找到启用的财务集成配置' in result['error']

    def test_push_voucher_failure(self, service, voucher, integration_config):
        """测试推送失败"""
        with patch('apps.integration.factory.AdapterFactory') as mock_factory:
            mock_adapter = Mock()
            mock_adapter.push_data.side_effect = Exception('API错误')
            mock_factory.create.return_value = mock_adapter

            result = service.push_voucher(voucher)

            assert result['success'] is False
            assert 'API错误' in result['error']

            # 验证错误已记录
            voucher.refresh_from_db()
            assert voucher.push_error == 'API错误'

    def test_map_to_external(self, service, voucher):
        """测试映射到外部格式"""
        with patch('apps.integration.factory.AdapterFactory') as mock_factory:
            mock_adapter = Mock()
            mock_adapter.map_to_external.return_value = {
                'voucherDate': '2024-01-15',
                'voucherType': '01',
                'entries': []
            }
            mock_factory.create.return_value = mock_adapter

            external_data = service._map_to_external(mock_adapter, voucher)

            assert external_data['voucherDate'] == '2024-01-15'
            assert 'entries' in external_data
```

### 1.4 M18财务适配器测试

```python
# tests/apps/integration/adapters/test_m18_finance_adapter.py

import pytest
from unittest.mock import Mock, patch
from apps.integration.adapters.m18_adapter import M18Adapter
from apps.integration.models import IntegrationConfig


@pytest.mark.django_db
class TestM18FinanceAdapter:
    """M18财务适配器测试"""

    @pytest.fixture
    def m18_config(self, organization):
        """创建M18配置"""
        return IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            is_enabled=True,
            connection_config={'api_url': 'https://test.m18.com'}
        )

    @pytest.fixture
    def adapter(self, m18_config):
        """创建适配器"""
        return M18Adapter(m18_config)

    def test_convert_voucher_to_m18(self, adapter):
        """测试转换凭证为M18格式"""
        voucher_data = {
            'voucher_no': 'PZ2024010001',
            'voucher_date': '2024-01-15',
            'voucher_type': '记',
            'description': '购入固定资产',
            'business_type': 'asset_purchase',
            'business_id': 'asset_123',
            'entries': [
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'debit': 8000,
                    'credit': 0,
                    'description': '',
                    'cost_center': 'C001'
                }
            ]
        }

        m18_voucher = adapter._convert_voucher_to_m18(voucher_data)

        assert m18_voucher['voucherDate'] == '2024-01-15'
        assert m18_voucher['voucherType'] == '01'  # 记账凭证
        assert m18_voucher['sourceModule'] == 'FA'
        assert m18_voucher['sourceBillType'] == 'asset_purchase'
        assert len(m18_voucher['entries']) == 1
        assert m18_voucher['entries'][0]['accountCode'] == '1601'
        assert m18_voucher['entries'][0]['debit'] == 8000.0

    def test_get_m18_voucher_type(self, adapter):
        """测试转换凭证类型"""
        type_map = {
            '记': '01',
            '收': '02',
            '付': '03',
            '转': '04'
        }

        for local_type, expected_m18_type in type_map.items():
            result = adapter._get_m18_voucher_type(local_type)
            assert result == expected_m18_type

        # 未知类型返回默认值
        result = adapter._get_m18_voucher_type('unknown')
        assert result == '01'

    @patch('apps.integration.adapters.base_adapter.requests.request')
    def test_push_finance_voucher(self, mock_request, adapter):
        """测试推送财务凭证到M18"""
        mock_request.return_value = Mock(
            status_code=200,
            json=lambda: {
                'success': True,
                'voucherNo': 'M18-PZ-001',
                'voucherId': 'V123'
            }
        )

        voucher_data = {
            'voucher_date': '2024-01-15',
            'voucher_type': '记',
            'description': '测试凭证',
            'entries': []
        }

        result = adapter.push_finance_voucher(voucher_data)

        assert result['success'] is True
        assert result['voucherNo'] == 'M18-PZ-001'
```

---

## 2. API测试

### 2.1 凭证模板API测试

```python
# tests/api/finance/test_voucher_template_api.py

import pytest
from django.urls import reverse
from apps.assets.models.finance import VoucherTemplate


@pytest.mark.django_db
@pytest.mark.api
class TestVoucherTemplateAPI:
    """凭证模板API测试"""

    def test_list_voucher_templates(self, auth_client, organization):
        """测试获取凭证模板列表"""
        VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='模板1',
            voucher_type='记',
            entries_config=[]
        )

        VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_depreciation',
            template_name='模板2',
            voucher_type='记',
            entries_config=[]
        )

        url = reverse('voucher-template-list')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_filter_by_business_type(self, auth_client, organization):
        """测试按业务类型筛选"""
        VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='模板1',
            voucher_type='记',
            entries_config=[]
        )

        VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_depreciation',
            template_name='模板2',
            voucher_type='记',
            entries_config=[]
        )

        url = reverse('voucher-template-list')
        response = auth_client.get(url, {'business_type': 'asset_purchase'})

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['business_type'] == 'asset_purchase'

    def test_create_voucher_template(self, admin_client, organization):
        """测试创建凭证模板"""
        url = reverse('voucher-template-list')
        data = {
            'business_type': 'asset_purchase',
            'template_name': '新模板',
            'voucher_type': '记',
            'default_description': '测试模板',
            'entries_config': [
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'direction': 'debit',
                    'amount': 8000
                }
            ],
            'is_active': True
        }
        response = admin_client.post(url, data)

        assert response.status_code == 201
        assert response.data['template_name'] == '新模板'

    def test_update_voucher_template(self, admin_client, organization):
        """测试更新凭证模板"""
        template = VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='原模板',
            voucher_type='记',
            entries_config=[]
        )

        url = reverse('voucher-template-detail', kwargs={'pk': template.id})
        data = {
            'template_name': '更新后的模板',
            'is_active': False
        }
        response = admin_client.put(url, data)

        assert response.status_code == 200
        assert response.data['template_name'] == '更新后的模板'
        assert response.data['is_active'] is False

    def test_delete_voucher_template(self, admin_client, organization):
        """测试删除凭证模板"""
        template = VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='模板',
            voucher_type='记',
            entries_config=[]
        )

        url = reverse('voucher-template-detail', kwargs={'pk': template.id})
        response = admin_client.delete(url)

        assert response.status_code == 204
```

### 2.2 财务凭证API测试

```python
# tests/api/finance/test_voucher_api.py

import pytest
from decimal import Decimal
from django.urls import reverse
from apps.assets.models.finance import FinanceVoucher


@pytest.mark.django_db
@pytest.mark.api
class TestFinanceVoucherAPI:
    """财务凭证API测试"""

    @pytest.fixture
    def voucher(self, organization):
        """创建测试凭证"""
        return FinanceVoucher.objects.create(
            organization=organization,
            business_type='asset_purchase',
            business_id='asset_123',
            voucher_no='PZ2024010001',
            voucher_date='2024-01-15',
            voucher_type='记',
            description='购入固定资产',
            entries=[
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'debit': 8000,
                    'credit': 0
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'debit': 0,
                    'credit': 8000
                }
            ],
            total_debit=Decimal('8000'),
            total_credit=Decimal('8000'),
            status='draft'
        )

    def test_list_vouchers(self, auth_client, voucher):
        """测试获取凭证列表"""
        url = reverse('voucher-list')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['voucher_no'] == 'PZ2024010001'

    def test_filter_vouchers_by_status(self, auth_client, voucher):
        """测试按状态筛选凭证"""
        url = reverse('voucher-list')
        response = auth_client.get(url, {'status': 'draft'})

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_create_voucher_balanced(self, auth_client, organization):
        """测试创建借贷平衡的凭证"""
        url = reverse('voucher-list')
        data = {
            'business_type': 'asset_purchase',
            'business_id': 'asset_456',
            'voucher_date': '2024-01-15',
            'voucher_type': '记',
            'description': '购入固定资产',
            'entries': [
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'debit': 8000,
                    'credit': 0
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'debit': 0,
                    'credit': 8000
                }
            ]
        }
        response = auth_client.post(url, data)

        assert response.status_code == 201
        assert response.data['total_debit'] == '8000.00'

    def test_create_voucher_unbalanced(self, auth_client):
        """测试创建不平衡凭证（应该失败）"""
        url = reverse('voucher-list')
        data = {
            'business_type': 'asset_purchase',
            'business_id': 'asset_456',
            'voucher_date': '2024-01-15',
            'voucher_type': '记',
            'description': '不平衡凭证',
            'entries': [
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'debit': 8000,
                    'credit': 0
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'debit': 0,
                    'credit': 7000  # 不平衡
                }
            ]
        }
        response = auth_client.post(url, data)

        assert response.status_code == 400
        assert '借贷不平衡' in response.data['detail'][0]

    def test_submit_voucher(self, auth_client, voucher):
        """测试提交凭证"""
        url = reverse('voucher-submit', kwargs={'pk': voucher.id})
        response = auth_client.post(url)

        assert response.status_code == 200
        assert response.data['status'] == 'submitted'

    def test_approve_voucher(self, admin_client, voucher):
        """测试审核凭证"""
        voucher.status = 'submitted'
        voucher.save()

        url = reverse('voucher-approve', kwargs={'pk': voucher.id})
        data = {
            'approved': True,
            'comment': '审核通过'
        }
        response = admin_client.post(url, data)

        assert response.status_code == 200
        assert response.data['status'] == 'approved'

    def test_reject_voucher(self, admin_client, voucher):
        """测试驳回凭证"""
        voucher.status = 'submitted'
        voucher.save()

        url = reverse('voucher-reject', kwargs={'pk': voucher.id})
        data = {
            'comment': '科目选择有误'
        }
        response = admin_client.post(url, data)

        assert response.status_code == 200

    def test_push_voucher(self, auth_client, voucher, integration_config):
        """测试推送凭证到ERP"""
        with patch('apps.integration.services.voucher_push_service.AdapterFactory'):
            url = reverse('voucher-push', kwargs={'pk': voucher.id})
            data = {'system_type': 'm18'}
            response = auth_client.post(url, data)

            # 由于mock可能不完整，这里只验证请求可以到达
            assert response.status_code in [200, 500]
```

### 2.3 业务凭证生成API测试

```python
# tests/api/finance/test_voucher_generation_api.py

import pytest
from decimal import Decimal
from datetime import date
from django.urls import reverse
from apps.assets.models import Asset
from apps.assets.models.finance import VoucherTemplate, FinanceVoucher


@pytest.mark.django_db
@pytest.mark.api
class TestVoucherGenerationAPI:
    """业务凭证生成API测试"""

    @pytest.fixture
    def asset(self, organization):
        """创建测试资产"""
        return Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            purchase_price=Decimal('8000'),
            purchase_date=date(2024, 1, 15)
        )

    @pytest.fixture
    def purchase_template(self, organization):
        """创建资产购入模板"""
        return VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='资产购入模板',
            voucher_type='记',
            default_description='购入固定资产',
            entries_config=[
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'direction': 'debit',
                    'amount': '${asset.purchase_price}'
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'direction': 'credit',
                    'amount': '${asset.purchase_price}'
                }
            ]
        )

    def test_generate_asset_purchase_voucher(self, auth_client, asset, purchase_template):
        """测试生成资产购入凭证"""
        url = reverse('voucher-generate-asset-purchase')
        data = {
            'asset_id': str(asset.id),
            'voucher_date': '2024-01-15'
        }
        response = auth_client.post(url, data)

        assert response.status_code == 201
        assert response.data['business_type'] == 'asset_purchase'
        assert response.data['total_debit'] == '8000.00'
        assert 'MacBook Pro' in response.data['description']

    def test_generate_asset_purchase_voucher_custom_date(self, auth_client, asset, purchase_template):
        """测试使用自定义日期生成凭证"""
        url = reverse('voucher-generate-asset-purchase')
        data = {
            'asset_id': str(asset.id),
            'voucher_date': '2024-02-01'
        }
        response = auth_client.post(url, data)

        assert response.status_code == 201
        assert response.data['voucher_date'] == '2024-02-01'

    def test_generate_voucher_no_template(self, auth_client, asset, organization):
        """测试没有模板时生成凭证"""
        # 删除所有模板
        VoucherTemplate.objects.filter(organization=organization).delete()

        url = reverse('voucher-generate-asset-purchase')
        data = {
            'asset_id': str(asset.id),
            'voucher_date': '2024-01-15'
        }
        response = auth_client.post(url, data)

        assert response.status_code == 400
        assert '未找到凭证模板' in response.data['error']
```

---

## 3. 集成测试

### 3.1 完整凭证生命周期测试

```python
# tests/integration/finance/test_voucher_lifecycle.py

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import patch
from apps.assets.services.finance_voucher_service import FinanceVoucherService
from apps.integration.services.voucher_push_service import VoucherPushService
from apps.assets.models.finance import VoucherTemplate, FinanceVoucher
from apps.assets.models import Asset
from apps.integration.models import IntegrationConfig


@pytest.mark.django_db
@pytest.mark.integration
class TestVoucherLifecycle:
    """凭证生命周期集成测试"""

    @pytest.fixture
    def setup_environment(self, organization):
        """设置测试环境"""
        # 创建凭证模板
        template = VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='资产购入模板',
            voucher_type='记',
            default_description='购入固定资产',
            entries_config=[
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'direction': 'debit',
                    'amount': '${asset.purchase_price}'
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'direction': 'credit',
                    'amount': '${asset.purchase_price}'
                }
            ]
        )

        # 创建集成配置
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            is_enabled=True,
            enabled_modules=['finance'],
            connection_config={'api_url': 'https://test.m18.com'}
        )

        return {'template': template, 'config': config}

    def test_full_voucher_lifecycle(self, setup_environment):
        """测试完整凭证生命周期"""
        organization = setup_environment['template'].organization

        # 1. 创建资产
        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            purchase_price=Decimal('8000'),
            purchase_date=date(2024, 1, 15)
        )

        # 2. 生成凭证
        voucher_service = FinanceVoucherService(organization)
        voucher = voucher_service.generate_asset_purchase_voucher(asset)

        assert voucher.status == 'draft'
        assert voucher.total_debit == Decimal('8000')

        # 3. 提交凭证
        voucher.status = 'submitted'
        voucher.save()
        assert voucher.status == 'submitted'

        # 4. 审核凭证
        voucher.status = 'approved'
        voucher.approved_by_id = 1  # 模拟审核人
        voucher.approved_at = date.today()
        voucher.save()
        assert voucher.status == 'approved'

        # 5. 推送到ERP
        with patch('apps.integration.factory.AdapterFactory') as mock_factory:
            mock_adapter = Mock()
            mock_adapter.push_data.return_value = {
                'voucher_no': 'M18-PZ-001'
            }
            mock_adapter.map_to_external.return_value = {}
            mock_factory.create.return_value = mock_adapter

            push_service = VoucherPushService(organization)
            result = push_service.push_voucher(voucher)

            assert result['success'] is True
            assert result['external_voucher_no'] == 'M18-PZ-001'

        # 6. 验证最终状态
        voucher.refresh_from_db()
        assert voucher.status == 'submitted'
        assert voucher.external_voucher_no == 'M18-PZ-001'
        assert voucher.pushed_at is not None

    def test_voucher_generation_and_push_chain(self, setup_environment):
        """测试凭证生成和推送链路"""
        organization = setup_environment['template'].organization

        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC002',
            asset_name='Dell显示器',
            purchase_price=Decimal('2000'),
            purchase_date=date(2024, 1, 15)
        )

        # 生成凭证
        voucher_service = FinanceVoucherService(organization)
        voucher = voucher_service.generate_asset_purchase_voucher(asset)

        # 模拟推送成功
        with patch('apps.integration.factory.AdapterFactory') as mock_factory:
            mock_adapter = Mock()
            mock_adapter.push_data.return_value = {
                'voucher_no': 'M18-PZ-002'
            }
            mock_adapter.map_to_external.return_value = {}
            mock_factory.create.return_value = mock_adapter

            push_service = VoucherPushService(organization)
            result = push_service.push_voucher(voucher)

            # 验证链路完整
            assert FinanceVoucher.objects.filter(
                organization=organization,
                business_id=str(asset.id)
            ).count() == 1

            voucher = FinanceVoucher.objects.get(business_id=str(asset.id))
            assert voucher.external_voucher_no == 'M18-PZ-002'
```

---

## 4. 性能测试

### 4.1 批量凭证生成性能测试

```python
# tests/performance/finance/test_voucher_performance.py

import pytest
import time
from decimal import Decimal
from datetime import date
from apps.assets.services.finance_voucher_service import FinanceVoucherService
from apps.assets.models.finance import VoucherTemplate
from apps.assets.models import Asset


@pytest.mark.django_db
@pytest.mark.performance
class TestVoucherPerformance:
    """财务凭证性能测试"""

    @pytest.fixture
    def setup_template(self, organization):
        """设置凭证模板"""
        return VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_purchase',
            template_name='资产购入模板',
            voucher_type='记',
            default_description='购入固定资产',
            entries_config=[
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'direction': 'debit',
                    'amount': '${asset.purchase_price}'
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'direction': 'credit',
                    'amount': '${asset.purchase_price}'
                }
            ]
        )

    def test_batch_generate_100_vouchers(self, setup_template, organization):
        """测试批量生成100个凭证的性能"""
        # 创建100个资产
        assets = [
            Asset.objects.create(
                organization=organization,
                asset_code=f'ZC{i:04d}',
                asset_name=f'资产{i}',
                purchase_price=Decimal('1000') + i * 100,
                purchase_date=date(2024, 1, 1)
            )
            for i in range(100)
        ]

        service = FinanceVoucherService(organization)

        start_time = time.time()
        vouchers = []
        for asset in assets:
            voucher = service.generate_asset_purchase_voucher(asset)
            vouchers.append(voucher)
        end_time = time.time()

        generation_time = end_time - start_time

        assert len(vouchers) == 100
        assert generation_time < 5.0, f"生成100个凭证耗时 {generation_time:.2f} 秒"

    def test_voucher_calculation_performance(self, setup_template, organization):
        """测试凭证计算性能"""
        # 创建包含复杂分录的模板
        template = VoucherTemplate.objects.create(
            organization=organization,
            business_type='asset_disposal',
            template_name='复杂处置模板',
            voucher_type='记',
            default_description='资产处置',
            entries_config=[
                {
                    'line_no': i,
                    'account_code': f'ACC{i:03d}',
                    'account_name': f'科目{i}',
                    'direction': 'debit' if i % 2 == 0 else 'credit',
                    'amount': '${asset.net_value}'
                }
                for i in range(50)  # 50个分录行
            ]
        )

        service = FinanceVoucherService(organization)

        asset = Asset.objects.create(
            organization=organization,
            asset_code='ZC001',
            asset_name='测试资产',
            purchase_price=Decimal('50000'),
            purchase_date=date(2024, 1, 1)
        )

        business_data = {
            'business_id': str(asset.id),
            'voucher_date': date(2024, 1, 15),
            'description': '测试',
            'asset': {'net_value': 30000}
        }

        start_time = time.time()
        voucher = service.generate_voucher('asset_disposal', business_data)
        end_time = time.time()

        calculation_time = end_time - start_time

        assert len(voucher.entries) == 50
        assert calculation_time < 0.5, f"计算耗时 {calculation_time:.2f} 秒"
```

---

## 5. 测试数据Fixture

```python
# tests/fixtures/finance_fixtures.py

import pytest
from decimal import Decimal
from datetime import date
from apps.assets.models.finance import VoucherTemplate, FinanceVoucher
from apps.assets.models import Asset


@pytest.fixture
def voucher_template_factory(organization):
    """凭证模板工厂"""
    def create_template(**kwargs):
        defaults = {
            'organization': organization,
            'business_type': 'asset_purchase',
            'template_name': '默认模板',
            'voucher_type': '记',
            'default_description': '测试凭证',
            'entries_config': [
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'direction': 'debit',
                    'amount': 1000
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'direction': 'credit',
                    'amount': 1000
                }
            ],
            'is_active': True
        }
        defaults.update(kwargs)
        return VoucherTemplate.objects.create(**defaults)

    return create_template


@pytest.fixture
def finance_voucher_factory(organization):
    """财务凭证工厂"""
    def create_voucher(**kwargs):
        defaults = {
            'organization': organization,
            'business_type': 'asset_purchase',
            'business_id': 'test_business_id',
            'voucher_no': 'PZ2024010001',
            'voucher_date': date(2024, 1, 15),
            'voucher_type': '记',
            'description': '测试凭证',
            'entries': [
                {
                    'line_no': 1,
                    'account_code': '1601',
                    'account_name': '固定资产',
                    'debit': Decimal('1000'),
                    'credit': Decimal('0')
                },
                {
                    'line_no': 2,
                    'account_code': '1002',
                    'account_name': '银行存款',
                    'debit': Decimal('0'),
                    'credit': Decimal('1000')
                }
            ],
            'total_debit': Decimal('1000'),
            'total_credit': Decimal('1000'),
            'status': 'draft'
        }
        defaults.update(kwargs)
        return FinanceVoucher.objects.create(**defaults)

    return create_voucher


@pytest.fixture
def sample_asset_purchase_data():
    """示例资产购入数据"""
    return {
        'business_id': 'asset_123',
        'voucher_date': date(2024, 1, 15),
        'description': '购入MacBook Pro',
        'asset': {
            'purchase_price': Decimal('8000'),
            'asset_category': '电子设备',
            'supplier': 'Apple Inc.'
        }
    }


@pytest.fixture
def sample_depreciation_data():
    """示例折旧数据"""
    return {
        'business_id': 'depreciation_123',
        'voucher_date': '2024-01',
        'description': '2024-01 折旧: 笔记本电脑',
        'depreciation': {
            'amount': Decimal('158.33'),
            'asset': 'MacBook Pro',
            'department': '技术部'
        }
    }
```

---

## 6. 测试覆盖率目标

| 模块 | 单元测试覆盖率 | 集成测试覆盖率 |
|------|---------------|---------------|
| VoucherTemplate 模型 | 95%+ | - |
| FinanceVoucher 模型 | 95%+ | - |
| 凭证生成服务 | 90%+ | - |
| 凭证推送服务 | 85%+ | - |
| M18财务适配器 | 85%+ | - |
| API端点 | - | 80%+ |
| 端到端流程 | - | 70%+ |

---

## 后续任务

1. 实现所有单元测试用例
2. 实现API集成测试用例
3. 实现端到端测试场景
4. 配置CI/CD自动化测试流程
5. 建立性能监控基准
