# Phase 5.4: 财务报表生成 - 总览

## 概述

本模块实现固定资产相关财务报表的自动化生成功能，支持资产明细表、折旧汇总表、增减变动表等多种报表类型，满足企业财务核算和审计需求。

---

## 1. 业务背景

### 1.1 当前痛点

| 痛点 | 说明 | 影响 |
|------|------|------|
| **报表缺失** | 无标准财务报表输出 | 财务核算困难，审计不便 |
| **人工统计** | 依赖Excel手工统计 | 效率低下，易出错 |
| **格式不统一** | 各部门报表格式不一致 | 数据汇总困难 |
| **数据滞后** | 报表更新不及时 | 决策数据不准确 |

### 1.2 业务目标

- **报表自动化**：支持一键生成各类标准报表
- **格式标准化**：采用统一的报表格式和模板
- **数据实时性**：基于最新资产数据生成报表
- **多维度分析**：支持按部门、类别、时间等多维度统计

---

## 2. 模块架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         财务报表生成                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐         │
│  │  报表模板      │ → │  报表引擎      │ → │  报表生成      │         │
│  │  Template     │   │  Engine       │   │  Generator    │         │
│  └───────────────┘   └───────────────┘   └───────────────┘         │
│         ↓                   ↓                   ↓                     │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐         │
│  │  报表类型      │   │  数据查询      │   │  输出格式      │         │
│  │  - 明细表      │   │  - 聚合查询    │   │  - PDF        │         │
│  │  - 汇总表      │   │  - 多表关联    │   │  - Excel      │         │
│  │  - 分析表      │   │  - 数据计算    │   │  - HTML       │         │
│  └───────────────┘   └───────────────┘   └───────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 报表类型

### 3.1 资产明细表 (Asset Detail Report)

| 字段 | 说明 |
|------|------|
| 资产编号 | 唯一标识 |
| 资产名称 | 资产名称 |
| 资产类别 | 分类信息 |
| 原值 | 购入原值 |
| 累计折旧 | 截止当前累计折旧 |
| 净值 | 资产净值 |
| 使用部门 | 使用部门 |
| 存放地点 | 存放位置 |
| 使用状态 | 在用/闲置/维修中 |
| 入账日期 | 入账时间 |

### 3.2 折旧汇总表 (Depreciation Summary Report)

| 维度 | 说明 |
|------|------|
| 按类别 | 各类别资产的折旧汇总 |
| 按部门 | 各部门资产的折旧汇总 |
| 按期间 | 各期间的折旧汇总 |
| 按年限 | 各使用年限资产的折旧汇总 |

### 3.3 资产增减变动表 (Asset Change Report)

| 内容 | 说明 |
|------|------|
| 期初余额 | 期初资产数量和原值 |
| 本期增加 | 本期新增资产 |
| 本期减少 | 本期减少资产（处置/调出） |
| 期末余额 | 期末资产数量和原值 |

### 3.4 资产处置明细表 (Asset Disposal Report)

| 内容 | 说明 |
|------|------|
| 处置资产 | 资产基本信息 |
| 处置原因 | 处置原因说明 |
| 处置方式 | 报废/出售/捐赠等 |
| 处置日期 | 处置时间 |
| 原值/净值 | 处置时价值 |
| 处置收入 | 处置获得金额 |
| 处置损益 | 处置收益或损失 |

---

## 4. 报表模板配置

### 4.1 模板结构

```json
{
  "template_code": "ASSET_DETAIL",
  "template_name": "资产明细表",
  "version": "1.0",
  "layout": {
    "page_size": "A4",
    "orientation": "landscape",
    "margins": {
      "top": 20,
      "bottom": 20,
      "left": 15,
      "right": 15
    }
  },
  "sections": [
    {
      "type": "header",
      "title": "固定资产明细表",
      "subtitle": "{{ period }}",
      "show_logo": true,
      "show_org_name": true
    },
    {
      "type": "filters",
      "fields": ["department", "category", "location", "status"]
    },
    {
      "type": "table",
      "data_source": "assets",
      "columns": [
        {"field": "asset_no", "title": "资产编号", "width": 120},
        {"field": "asset_name", "title": "资产名称", "width": 200},
        {"field": "category.name", "title": "资产类别", "width": 120},
        {"field": "original_value", "title": "原值", "width": 120, "format": "currency"},
        {"field": "accumulated_depreciation", "title": "累计折旧", "width": 120, "format": "currency"},
        {"field": "net_value", "title": "净值", "width": 120, "format": "currency"},
        {"field": "department.name", "title": "使用部门", "width": 120},
        {"field": "location.name", "title": "存放地点", "width": 120},
        {"field": "status_display", "title": "使用状态", "width": 100}
      ],
      "show_footer": true,
      "footer_rows": [
        {"type": "sum", "fields": ["original_value", "accumulated_depreciation", "net_value"]}
      ]
    },
    {
      "type": "summary",
      "fields": ["total_assets", "total_original_value", "total_net_value"]
    },
    {
      "type": "signature",
      "positions": ["制表人", "审核人", "批准人"]
    }
  ]
}
```

### 4.2 数据源配置

```python
# 数据源类型
DATA_SOURCE_TYPES = [
    ('model', '模型查询'),
    ('sql', '自定义SQL'),
    ('api', '外部API'),
    ('aggregate', '聚合计算'),
]

# 预定义数据源
DATA_SOURCES = {
    'assets': {
        'type': 'model',
        'model': 'assets.Asset',
        'default_fields': ['asset_no', 'asset_name', 'category', 'original_value'],
        'filters': ['department', 'category', 'status', 'location'],
        'order_by': ['asset_no'],
    },
    'depreciations': {
        'type': 'model',
        'model': 'assets.AssetDepreciation',
        'default_fields': ['period', 'depreciation_amount', 'accumulated_depreciation'],
        'filters': ['period_from', 'period_to', 'asset_category'],
    },
    'asset_changes': {
        'type': 'aggregate',
        'query': 'calculate_asset_changes',
        'parameters': ['period_from', 'period_to', 'group_by'],
    }
}
```

---

## 5. 报表生成引擎

### 5.1 生成流程

```
用户请求
    ↓
选择报表类型
    ↓
设置筛选条件
    ↓
报表引擎处理
    ↓
┌─────────────┐
│ 查询数据    │
│ 应用模板    │
│ 计算汇总    │
│ 生成输出    │
└─────────────┘
    ↓
返回报表文件/预览
```

### 5.2 报表引擎组件

```python
class ReportEngine:
    """报表生成引擎"""

    def generate(report_type, params, output_format):
        """生成报表
        Args:
            report_type: 报表类型代码
            params: 筛选参数
            output_format: 输出格式 (pdf/excel/html)
        Returns:
            报表文件或预览数据
        """
        # 1. 加载报表模板
        template = load_template(report_type)

        # 2. 构建数据查询
        data = query_data(template, params)

        # 3. 应用模板渲染
        rendered = render_template(template, data)

        # 4. 生成输出文件
        return export_output(rendered, output_format)
```

---

## 6. 与其他模块的集成

| 集成点 | 关联模块 | 集成方式 |
|--------|---------|---------|
| 资产数据 | phase1_4 | 读取资产基础数据 |
| 折旧数据 | phase5_3 | 读取折旧计算结果 |
| 凭证数据 | phase5_2 | 关联财务凭证 |
| 处置数据 | phase1_7 | 读取资产处置记录 |
| 部门数据 | phase2_1 | 按部门分组统计 |

---

## 7. 定时报表

### 7.1 定时报表任务

| 报表 | 频率 | 触发时间 |
|------|------|----------|
| 月度资产明细表 | 每月 | 每月1日 |
| 月度折旧汇总表 | 每月 | 每月5日 |
| 季度资产分析表 | 每季度 | 每季首月10日 |
| 年度资产报告 | 每年 | 每年1月15日 |

### 7.2 报表订阅

用户可以订阅报表，自动推送到邮箱或系统通知。

---

## 8. 报表权限控制

| 权限类型 | 说明 |
|----------|------|
| 查看权限 | 控制用户可以查看哪些报表 |
| 导出权限 | 控制用户是否可以导出报表 |
| 数据范围 | 基于部门/组织的数据权限 |
| 敏感字段 | 对敏感字段（如原值）进行脱敏 |

---

## 9. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 模型设计、服务层、API |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 页面组件、交互设计 |
| [test.md](./test.md) | 测试计划 |

---

## 10. 后续任务

1. 实现报表模板管理
2. 实现报表生成引擎
3. 实现各类报表生成逻辑
4. 实现报表导出功能
5. 实现定时报表任务
6. 实现报表订阅功能
