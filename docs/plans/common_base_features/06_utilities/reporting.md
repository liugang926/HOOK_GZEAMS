# 动态报表系统设计文档

## 1. 设计目标

### 1.1 核心目标
构建基于元数据驱动的动态报表系统，支持用户通过低代码配置方式快速创建可视化数据分析和报表，无需编写代码即可实现复杂的数据聚合与多维分析。

### 1.2 功能特性
- ✅ **独立报表配置模型**：ReportLayout 元数据模型，与 PageLayout 解耦
- ✅ **多样化图表支持**：柱状图、折线图、饼图、面积图、散点图、透视表
- ✅ **灵活数据聚合**：sum/avg/count/max/min/group_concat 等聚合函数
- ✅ **多维度分析**：支持 X 轴维度、Y 轴度量、系列分组、钻取分析
- ✅ **动态过滤条件**：支持时间范围、组织筛选、自定义字段过滤
- ✅ **权限控制集成**：基于组织的数据隔离 + RBAC 报表访问权限
- ✅ **性能优化**：异步查询 + Redis 缓存 + 分页加载

### 1.3 业务价值
- **零代码报表开发**：业务人员自助配置报表，降低开发成本
- **实时数据洞察**：支持资产统计、部门分析、趋势分析等决策场景
- **多组织数据隔离**：自动应用组织过滤，确保数据安全
- **扩展性强**：基于 PostgreSQL JSONB + 元数据引擎，灵活适配新业务

---

## 2. 报表系统数据模型定义

### 2.1 ReportLayout 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | string | max=100, unique | 报表名称 |
| code | string | max=50, unique | 报表编码 |
| description | text | nullable | 报表说明 |
| business_object | ForeignKey | BusinessObject | 数据源对象 |
| data_source_type | string | max=20 | database/api/aggregated |
| report_type | string | max=20 | chart/table/pivot/mixed |
| chart_config | JSONB | default=dict | 图表配置 |
| aggregation_config | JSONB | default=dict | 聚合配置 |
| filter_config | JSONB | default=dict | 过滤器配置 |
| pivot_config | JSONB | nullable | 透视表配置 |
| cache_enabled | boolean | default=True | 启用缓存 |
| cache_ttl | integer | default=300 | 缓存时长(秒) |
| allowed_roles | ManyToManyField | Role | 允许访问的角色 |

### 2.2 ReportExecution 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| report_layout | ForeignKey | ReportLayout | 关联报表 |
| executed_by | ForeignKey | User | 执行人 |
| status | string | max=20 | pending/completed/failed |
| result_data | JSONB | nullable | 结果数据 |
| filters_used | JSONB | default=dict | 使用的过滤条件 |
| executed_at | datetime | auto_now_add | 执行时间 |
| cache_key | string | max=255 | 缓存键 |

### 2.3 ReportFavorite 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| report | ForeignKey | ReportLayout | 关联报表 |
| user | ForeignKey | User | 用户 |
| order | integer | default=0 | 排序 |

---

## 3. 数据模型设计

### 3.1 ReportLayout 核心模型

```python
# apps/system/models.py

from django.db import models
from apps.common.models import BaseModel

class ReportLayout(BaseModel):
    """
    动态报表元数据配置模型
    定义报表的数据源、聚合逻辑、图表类型、过滤器等
    """

    # ===== 基础配置 =====
    name = models.CharField('报表名称', max_length=100, unique=True)
    code = models.CharField('报表编码', max_length=50, unique=True)
    description = models.TextField('报表说明', blank=True)

    # ===== 数据源配置 =====
    business_object = models.ForeignKey(
        'BusinessObject',
        on_delete=models.CASCADE,
        verbose_name='关联业务对象',
        related_name='report_layouts'
    )
    data_source_type = models.CharField(
        '数据源类型',
        max_length=20,
        choices=[
            ('database', '数据库查询'),
            ('api', '外部API'),
            ('aggregated', '聚合查询')
        ],
        default='aggregated'
    )

    # ===== 报表类型 =====
    report_type = models.CharField(
        '报表类型',
        max_length=20,
        choices=[
            ('chart', '图表报表'),
            ('table', '表格报表'),
            ('pivot', '透视表'),
            ('mixed', '混合报表')
        ],
        default='chart'
    )

    # ===== 图表配置（JSONB） =====
    chart_config = models.JSONField(
        '图表配置',
        default=dict,
        help_text="""
        图表类型与视觉配置：
        {
            "chart_type": "bar|line|pie|area|scatter|funnel|gauge",
            "title": "图表标题",
            "x_axis": {"field": "category_code", "label": "资产类别"},
            "y_axis": [
                {"field": "total_value", "label": "总价值", "agg": "sum"}
            ],
            "series": {"field": "org_name", "type": "group"},
            "stack": true,  # 堆叠模式
            "theme": "default|dark|colored"
        }
        """
    )

    # ===== 聚合配置（JSONB） =====
    aggregation_config = models.JSONField(
        '聚合配置',
        default=dict,
        help_text="""
        数据聚合逻辑定义：
        {
            "dimensions": ["category", "department"],  # 分组维度
            "metrics": [
                {"field": "value", "agg": "sum", "alias": "总价值"},
                {"field": "quantity", "agg": "count", "alias": "资产数量"}
            ],
            "filters": {
                "status": "active",
                "created_at": {"$gte": "2024-01-01"}
            },
            "order_by": [{"field": "total_value", "dir": "desc"}],
            "limit": 100
        }
        """
    )

    # ===== 过滤器配置（JSONB） =====
    filter_config = models.JSONField(
        '过滤器配置',
        default=dict,
        help_text="""
        动态过滤条件定义：
        {
            "filters": [
                {
                    "field": "created_at",
                    "label": "创建时间",
                    "type": "date_range",
                    "default": "last_30_days"
                },
                {
                    "field": "category",
                    "label": "资产类别",
                    "type": "select",
                    "options": "query:Category"  # 动态查询选项
                }
            ],
            "required_filters": ["org"]
        }
        """
    )

    # ===== 透视表配置（仅 pivot 类型） =====
    pivot_config = models.JSONField(
        '透视表配置',
        default=dict,
        blank=True,
        help_text="""
        透视表行列定义：
        {
            "rows": ["category", "department"],
            "columns": ["status"],
            "values": [
                {"field": "value", "agg": "sum"},
                {"field": "id", "agg": "count"}
            ]
        }
        """
    )

    # ===== 缓存配置 =====
    cache_enabled = models.BooleanField('启用缓存', default=True)
    cache_ttl = models.IntegerField('缓存时长(秒)', default=300)  # 5分钟

    # ===== 权限配置 =====
    allowed_roles = models.ManyToManyField(
        'accounts.Role',
        verbose_name='允许访问的角色',
        blank=True,
        related_name='allowed_reports'
    )

    class Meta:
        db_table = 'system_report_layout'
        verbose_name = '报表配置'
        verbose_name_plural = '报表配置'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'org']),
            models.Index(fields=['business_object', 'report_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"
```

### 2.2 ReportFavorite 报表收藏模型（可选）

```python
class ReportFavorite(BaseModel):
    """用户收藏的报表"""
    report = models.ForeignKey(ReportLayout, on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    order = models.IntegerField('排序', default=0)

    class Meta:
        db_table = 'system_report_favorite'
        unique_together = ['report', 'user']
```

---

## 3. 后端实现 - MetadataDrivenReportViewSet

### 3.1 核心服务层

```python
# apps/system/services/report_service.py

from typing import Dict, List, Any, Optional
from django.db.models import Sum, Count, Avg, Max, Min, F, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.core.cache import cache
from django.conf import settings
import json

class MetadataReportService:
    """
    元数据驱动的报表服务
    核心能力：
    1. 动态SQL生成（基于聚合配置）
    2. 数据聚合计算（sum/avg/count等）
    3. 多维度数据分析
    4. 缓存管理
    """

    AGGREGATION_FUNCTIONS = {
        'sum': Sum,
        'avg': Avg,
        'count': Count,
        'max': Max,
        'min': Min,
    }

    def __init__(self, report_layout: ReportLayout):
        self.report_layout = report_layout
        self.business_object = report_layout.business_object
        self.aggregation_config = report_layout.aggregation_config
        self.cache_key_prefix = f"report:{report_layout.code}"

    def generate_report_data(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        生成报表数据
        Args:
            filters: 用户自定义过滤条件
        Returns:
            {
                "metadata": {...},  # 报表元数据
                "data": [...],       # 聚合结果
                "chart_config": {...}  # 图表配置
            }
        """
        # 检查缓存
        cache_key = self._get_cache_key(filters)
        if self.report_layout.cache_enabled:
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data

        # 获取业务模型
        model_class = self._get_model_class()

        # 构建查询
        queryset = self._build_queryset(model_class, filters)

        # 执行聚合
        aggregated_data = self._execute_aggregation(queryset)

        # 格式化结果
        result = {
            'metadata': {
                'report_name': self.report_layout.name,
                'report_type': self.report_layout.report_type,
                'chart_type': self.report_layout.chart_config.get('chart_type'),
            },
            'data': aggregated_data,
            'chart_config': self.report_layout.chart_config,
        }

        # 存储缓存
        if self.report_layout.cache_enabled:
            cache.set(cache_key, result, self.report_layout.cache_ttl)

        return result

    def _get_model_class(self):
        """获取业务对象对应的 Django 模型类"""
        model_mapping = {
            'Asset': 'apps.assets.models.Asset',
            'Consumable': 'apps.consumables.models.Consumable',
            'ProcurementRequest': 'apps.procurement.models.ProcurementRequest',
        }
        model_path = model_mapping.get(self.business_object.code)
        if not model_path:
            raise ValueError(f"Unsupported business object: {self.business_object.code}")

        from django.utils.module_loading import import_string
        return import_string(model_path)

    def _build_queryset(self, model_class, filters: Optional[Dict] = None):
        """构建带过滤条件的查询集"""
        queryset = model_class.objects.filter(is_deleted=False)

        # 应用配置中的静态过滤条件
        config_filters = self.aggregation_config.get('filters', {})
        for field, value in config_filters.items():
            if isinstance(value, dict):
                # 支持操作符：$gte, $lte, $in, $like
                for op, val in value.items():
                    if op == '$gte':
                        queryset = queryset.filter(**{f'{field}__gte': val})
                    elif op == '$lte':
                        queryset = queryset.filter(**{f'{field}__lte': val})
                    elif op == '$in':
                        queryset = queryset.filter(**{f'{field}__in': val})
            else:
                queryset = queryset.filter(**{field: value})

        # 应用用户自定义过滤条件
        if filters:
            for field, value in filters.items():
                if value:  # 忽略空值
                    queryset = queryset.filter(**{field: value})

        return queryset

    def _execute_aggregation(self, queryset) -> List[Dict]:
        """执行数据聚合计算"""
        dimensions = self.aggregation_config.get('dimensions', [])
        metrics = self.aggregation_config.get('metrics', [])
        order_by = self.aggregation_config.get('order_by', [])
        limit = self.aggregation_config.get('limit', 100)

        # 构建分组
        if dimensions:
            # 使用 annotate + values 进行分组聚合
            group_by_fields = [f'd_{dim}' for dim in dimensions]
            annotate_dict = {}

            # 构建聚合字段
            for metric in metrics:
                field = metric['field']
                agg_func = metric['agg']
                alias = metric.get('alias', f'{field}_{agg_func}')

                AggFunc = self.AGGREGATION_FUNCTIONS[agg_func]
                annotate_dict[alias] = AggFunc(field)

            # 执行聚合
            group_values = {f'd_{dim}': F(dim) for dim in dimensions}
            result = queryset.annotate(**group_values).values(
                *group_by_fields
            ).annotate(
                **annotate_dict
            )

            # 排序
            for order_item in order_by:
                field = order_item['field']
                direction = '-' if order_item.get('dir') == 'desc' else ''
                result = result.order_by(f'{direction}{field}')

            # 限制数量
            result = result[:limit]

            # 转换为列表
            return list(result)
        else:
            # 无分组，直接聚合
            aggregate_dict = {}
            for metric in metrics:
                field = metric['field']
                agg_func = metric['agg']
                alias = metric.get('alias', f'{field}_{agg_func}')

                AggFunc = self.AGGREGATION_FUNCTIONS[agg_func]
                aggregate_dict[alias] = AggFunc(field)

            result = queryset.aggregate(**aggregate_dict)
            return [result]

    def _get_cache_key(self, filters: Optional[Dict] = None) -> str:
        """生成缓存键"""
        filter_hash = hash(json.dumps(filters, sort_keys=True)) if filters else 'none'
        return f"{self.cache_key_prefix}:{filter_hash}"

    def clear_cache(self, filters: Optional[Dict] = None):
        """清除缓存"""
        cache_key = self._get_cache_key(filters)
        cache.delete(cache_key)
```

### 3.2 ViewSet 接口层

```python
# apps/system/views/report_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.system.models import ReportLayout
from apps.system.services.report_service import MetadataReportService
from apps.system.serializers import ReportLayoutSerializer

class MetadataDrivenReportViewSet(viewsets.ModelViewSet):
    """
    元数据驱动报表接口
    """
    queryset = ReportLayout.objects.filter(is_deleted=False)
    serializer_class = ReportLayoutSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """基于组织 + 权限过滤"""
        queryset = super().get_queryset()

        # 应用组织过滤
        queryset = queryset.filter(org=self.request.user.org)

        # 应用角色权限过滤
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                allowed_roles__in=self.request.user.roles.all()
            )

        return queryset.distinct()

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """
        生成报表数据
        POST /api/system/reports/{id}/generate/
        Body:
        {
            "filters": {
                "created_at": "2024-01-01",
                "category": "IT设备"
            }
        }
        """
        report_layout = self.get_object()
        filters = request.data.get('filters', {})

        # 权限检查
        if not request.user.is_superuser:
            user_roles = request.user.roles.all()
            if not report_layout.allowed_roles.filter(id__in=user_roles).exists():
                return Response(
                    {'error': '无权限访问此报表'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # 生成报表
        service = MetadataReportService(report_layout)
        try:
            result = service.generate_report_data(filters)
            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def clear_cache(self, request, pk=None):
        """清除报表缓存"""
        report_layout = self.get_object()
        service = MetadataReportService(report_layout)
        service.clear_cache()
        return Response({'message': '缓存已清除'})

    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        """获取用户收藏的报表"""
        from apps.system.models import ReportFavorite

        favorites = ReportFavorite.objects.filter(
            user=request.user,
            is_deleted=False
        ).select_related('report').order_by('order')

        data = [
            {
                'id': fav.report.id,
                'name': fav.report.name,
                'code': fav.report.code,
                'report_type': fav.report.report_type,
            }
            for fav in favorites
        ]

        return Response(data)

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """切换收藏状态"""
        from apps.system.models import ReportFavorite

        report_layout = self.get_object()
        favorite, created = ReportFavorite.objects.get_or_create(
            report=report_layout,
            user=request.user,
            defaults={'order': 0}
        )

        if not created:
            # 已存在，则取消收藏（软删除）
            favorite.soft_delete()
            return Response({'favorited': False})
        else:
            return Response({'favorited': True})
```

### 3.3 URL 路由配置

```python
# apps/system/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.system.views.report_views import MetadataDrivenReportViewSet

router = DefaultRouter()
router.register(r'reports', MetadataDrivenReportViewSet, basename='report')

urlpatterns = [
    path('api/system/', include(router.urls)),
]
```

---

## 4. 前端实现

### 4.1 核心组件 - MetadataDrivenReport.vue

```vue
<!-- frontend/src/components/common/MetadataDrivenReport.vue -->

<template>
  <div class="metadata-driven-report">
    <!-- 报表头部 -->
    <div class="report-header">
      <h2>{{ reportConfig.metadata.report_name }}</h2>

      <!-- 过滤器区域 -->
      <div class="filter-bar" v-if="filterConfig.filters">
        <el-form :inline="true" size="small">
          <el-form-item
            v-for="filter in activeFilters"
            :key="filter.field"
            :label="filter.label"
          >
            <!-- 日期范围过滤器 -->
            <el-date-picker
              v-if="filter.type === 'date_range'"
              v-model="filterValues[filter.field]"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              @change="handleFilterChange"
            />

            <!-- 下拉选择过滤器 -->
            <el-select
              v-else-if="filter.type === 'select'"
              v-model="filterValues[filter.field]"
              placeholder="请选择"
              clearable
              @change="handleFilterChange"
            >
              <el-option
                v-for="opt in filter.options"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>

            <!-- 文本输入过滤器 -->
            <el-input
              v-else-if="filter.type === 'text'"
              v-model="filterValues[filter.field]"
              placeholder="请输入"
              clearable
              @change="handleFilterChange"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              icon="Search"
              @click="loadReportData"
              :loading="loading"
            >
              查询
            </el-button>

            <el-button icon="Refresh" @click="resetFilters">
              重置
            </el-button>

            <el-button
              icon="Star"
              :type="isFavorited ? 'warning' : 'default'"
              @click="toggleFavorite"
            >
              {{ isFavorited ? '已收藏' : '收藏' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 图表渲染区域 -->
    <div class="report-content">
      <!-- ECharts 图表 -->
      <div
        v-if="reportConfig.metadata.chart_type !== 'table'"
        ref="chartRef"
        class="chart-container"
        :style="{ height: chartHeight }"
      />

      <!-- 表格报表 -->
      <el-table
        v-else
        :data="reportData"
        border
        stripe
        :height="tableHeight"
      >
        <el-table-column
          v-for="column in tableColumns"
          :key="column.field"
          :prop="column.field"
          :label="column.label"
          :formatter="column.formatter"
        />
      </el-table>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>数据加载中...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import axios from '@/utils/axios'

const props = defineProps({
  reportCode: {
    type: String,
    required: true
  },
  chartHeight: {
    type: String,
    default: '500px'
  },
  tableHeight: {
    type: String,
    default: '600px'
  }
})

const route = useRoute()
const chartRef = ref(null)
const loading = ref(false)
const isFavorited = ref(false)

const reportConfig = ref({
  metadata: {},
  data: [],
  chart_config: {}
})

const filterConfig = ref({
  filters: []
})

const filterValues = ref({})

let chartInstance = null

// ===== 计算属性 =====
const activeFilters = computed(() => {
  return filterConfig.value.filters || []
})

const tableColumns = computed(() => {
  if (!reportConfig.value.data.length) return []

  const firstRow = reportConfig.value.data[0]
  return Object.keys(firstRow).map(key => ({
    field: key,
    label: key,
    formatter: (row) => {
      const value = row[key]
      // 格式化数字（千分位）
      if (typeof value === 'number') {
        return value.toLocaleString()
      }
      return value
    }
  }))
})

const reportData = computed(() => {
  return reportConfig.value.data || []
})

// ===== 核心方法 =====

/**
 * 加载报表元数据配置
 */
async function loadReportConfig() {
  try {
    const { data } = await axios.get(`/api/system/reports/?code=${props.reportCode}`)

    if (data.results && data.results.length > 0) {
      const report = data.results[0]
      filterConfig.value = {
        filters: report.filter_config?.filters || []
      }

      // 初始化过滤器默认值
      initializeFilterDefaults()

      return report
    }
  } catch (error) {
    ElMessage.error('报表配置加载失败')
    console.error(error)
  }
}

/**
 * 加载报表数据
 */
async function loadReportData() {
  loading.value = true

  try {
    // 构建过滤条件
    const filters = buildFilters()

    const { data } = await axios.post(
      `/api/system/reports/${route.params.id || getReportId()}/generate/`,
      { filters }
    )

    reportConfig.value = data

    // 渲染图表
    if (data.metadata.chart_type !== 'table') {
      renderChart()
    }
  } catch (error) {
    ElMessage.error('报表数据加载失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

/**
 * 渲染 ECharts 图表
 */
function renderChart() {
  if (!chartRef.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value)

  const chartType = reportConfig.value.metadata.chart_type
  const chartConfig = reportConfig.value.chart_config
  const data = reportConfig.value.data

  // 构建图表配置
  const option = buildChartOption(chartType, chartConfig, data)

  chartInstance.setOption(option)

  // 响应式
  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
}

/**
 * 构建 ECharts 配置项
 */
function buildChartOption(chartType, chartConfig, data) {
  const xAxisData = data.map(item => item[chartConfig.x_axis.field])
  const seriesData = chartConfig.y_axis.map(yAxis => {
    return {
      name: yAxis.label,
      type: chartType,
      data: data.map(item => item[yAxis.field]),
      stack: chartConfig.stack ? 'total' : null
    }
  })

  return {
    title: {
      text: chartConfig.title || reportConfig.value.metadata.report_name
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: seriesData.map(s => s.name)
    },
    xAxis: {
      type: 'category',
      data: xAxisData
    },
    yAxis: {
      type: 'value'
    },
    series: seriesData
  }
}

/**
 * 构建过滤条件
 */
function buildFilters() {
  const filters = {}

  for (const [field, value] of Object.entries(filterValues.value)) {
    if (value !== null && value !== undefined && value !== '') {
      filters[field] = value
    }
  }

  return filters
}

/**
 * 初始化过滤器默认值
 */
function initializeFilterDefaults() {
  filterConfig.value.filters.forEach(filter => {
    if (filter.default) {
      if (filter.type === 'date_range' && filter.default === 'last_30_days') {
        const end = new Date()
        const start = new Date()
        start.setDate(start.getDate() - 30)
        filterValues.value[filter.field] = [start, end]
      } else {
        filterValues.value[filter.field] = filter.default
      }
    }
  })
}

/**
 * 处理过滤器变化
 */
function handleFilterChange() {
  // 可选：自动触发查询
  // loadReportData()
}

/**
 * 重置过滤器
 */
function resetFilters() {
  filterValues.value = {}
  initializeFilterDefaults()
  loadReportData()
}

/**
 * 切换收藏状态
 */
async function toggleFavorite() {
  try {
    const reportId = getReportId()
    await axios.post(`/api/system/reports/${reportId}/toggle_favorite/`)

    isFavorited.value = !isFavorited.value

    ElMessage.success(
      isFavorited.value ? '已添加到收藏' : '已取消收藏'
    )
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

/**
 * 获取报表ID
 */
function getReportId() {
  return route.params.id || route.query.id
}

// ===== 生命周期 =====
onMounted(async () => {
  await loadReportConfig()
  await loadReportData()
})
</script>

<style scoped lang="scss">
.metadata-driven-report {
  padding: 20px;

  .report-header {
    margin-bottom: 20px;

    h2 {
      margin: 0 0 15px 0;
      font-size: 20px;
      font-weight: 600;
    }

    .filter-bar {
      background: #f5f7fa;
      padding: 15px;
      border-radius: 4px;
    }
  }

  .report-content {
    .chart-container {
      width: 100%;
      border: 1px solid #ebeef5;
      border-radius: 4px;
    }
  }

  .loading-overlay {
    display: flex;
    align-items: center;
    justify-content: center;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    z-index: 999;

    .el-icon {
      font-size: 32px;
      margin-right: 10px;
    }
  }
}
</style>
```

### 4.2 图表组件集成

```javascript
// frontend/src/utils/chart-builder.js

/**
 * 图表构建器工具类
 * 封装 ECharts 配置生成逻辑
 */

import * as echarts from 'echarts'

export class ChartBuilder {
  constructor(chartType, theme = 'default') {
    this.chartType = chartType
    this.theme = theme
    this.option = {
      title: {},
      tooltip: {},
      legend: {},
      xAxis: {},
      yAxis: {},
      series: []
    }
  }

  /**
   * 设置标题
   */
  setTitle(title) {
    this.option.title.text = title
    return this
  }

  /**
   * 设置 X 轴
   */
  setXAxis(field, data) {
    this.option.xAxis = {
      type: 'category',
      data: data
    }
    return this
  }

  /**
   * 设置 Y 轴
   */
  setYAxis(label = '数值') {
    this.option.yAxis = {
      type: 'value',
      name: label
    }
    return this
  }

  /**
   * 添加系列数据
   */
  addSeries(name, data, options = {}) {
    const series = {
      name: name,
      type: this.chartType,
      data: data,
      ...options
    }
    this.option.series.push(series)
    return this
  }

  /**
   * 设置提示框
   */
  setTooltip(trigger = 'axis') {
    this.option.tooltip = {
      trigger: trigger,
      axisPointer: {
        type: 'shadow'
      }
    }
    return this
  }

  /**
   * 设置图例
   */
  setLegend(data) {
    this.option.legend = {
      data: data,
      orient: 'horizontal',
      top: 10
    }
    return this
  }

  /**
   * 构建最终配置
   */
  build() {
    return this.option
  }

  /**
   * 创建图表实例
   */
  static create(dom, option, theme = 'default') {
    const chart = echarts.init(dom, theme)
    chart.setOption(option)
    return chart
  }
}

/**
 * 支持的图表类型枚举
 */
export const ChartTypes = {
  BAR: 'bar',
  LINE: 'line',
  PIE: 'pie',
  AREA: 'area',
  SCATTER: 'scatter',
  FUNNEL: 'funnel',
  GAUGE: 'gauge'
}

/**
 * 主题配置
 */
export const ChartThemes = {
  DEFAULT: 'default',
  DARK: 'dark',
  COLORED: 'colored'
}
```

---

## 5. 使用示例

### 5.1 创建报表配置（管理后台）

```python
# 示例：创建资产价值统计报表

from apps.system.models import ReportLayout, BusinessObject

# 获取业务对象
asset_bo = BusinessObject.objects.get(code='Asset')

# 创建报表配置
report = ReportLayout.objects.create(
    name='资产价值统计报表',
    code='asset_value_stats',
    business_object=asset_bo,
    report_type='chart',
    description='按资产类别统计总价值',

    # 图表配置
    chart_config={
        'chart_type': 'bar',
        'title': '资产价值分布',
        'x_axis': {'field': 'category_name', 'label': '资产类别'},
        'y_axis': [
            {'field': 'total_value', 'label': '总价值(元)', 'agg': 'sum'}
        ],
        'stack': False,
        'theme': 'default'
    },

    # 聚合配置
    aggregation_config={
        'dimensions': ['category_name'],
        'metrics': [
            {'field': 'value', 'agg': 'sum', 'alias': 'total_value'}
        ],
        'order_by': [{'field': 'total_value', 'dir': 'desc'}],
        'limit': 20
    },

    # 过滤器配置
    filter_config={
        'filters': [
            {
                'field': 'created_at',
                'label': '创建时间',
                'type': 'date_range',
                'default': 'last_30_days'
            },
            {
                'field': 'category',
                'label': '资产类别',
                'type': 'select',
                'options': 'query:Category'
            }
        ]
    },

    cache_enabled=True,
    cache_ttl=600  # 10分钟
)

# 设置访问权限
from apps.accounts.models import Role
admin_role = Role.objects.get(code='admin')
report.allowed_roles.add(admin_role)
```

### 5.2 前端路由配置

```javascript
// frontend/src/router/index.js

{
  path: '/reports/:id',
  name: 'ReportDetail',
  component: () => import('@/views/common/ReportDetail.vue'),
  props: true,
  meta: {
    title: '动态报表',
    requiresAuth: true
  }
}
```

```vue
<!-- frontend/src/views/common/ReportDetail.vue -->

<template>
  <div class="report-detail-page">
    <MetadataDrivenReport
      :report-code="reportCode"
      :chart-height="'600px'"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MetadataDrivenReport from '@/components/common/MetadataDrivenReport.vue'

const route = useRoute()
const reportCode = computed(() => route.query.code || 'asset_value_stats')
</script>
```

---

## 6. 性能优化策略

### 6.1 缓存策略
- **Redis 缓存**：报表查询结果缓存（默认5分钟 TTL）
- **缓存键设计**：`report:{code}:{filter_hash}`
- **缓存失效**：数据更新时主动清除相关缓存

### 6.2 查询优化
- **索引优化**：在常用聚合字段（category, department, created_at）建立数据库索引
- **分页加载**：大量数据使用 LIMIT + OFFSET 分页
- **异步计算**：复杂报表使用 Celery 异步任务，前端轮询获取结果

### 6.3 前端优化
- **懒加载**：ECharts 按需引入（减少打包体积）
- **防抖处理**：过滤器变化时延迟触发查询
- **虚拟滚动**：表格数据量大时使用虚拟列表

---

## 7. 扩展功能规划

### 7.1 数据导出
- Excel 导出（使用 openpyxl）
- PDF 导出（使用 ReportLab）
- 图片导出（ECharts toDataURL）

### 7.2 高级分析
- **钻取分析**：点击图表下钻到明细数据
- **对比分析**：支持同期对比、环比分析
- **预测分析**：集成机器学习模型进行趋势预测

### 7.3 报表订阅
- 定时生成报表并发送邮件
- 报表订阅管理（订阅人、发送频率）

---

## 8. 技术栈总结

| 层级 | 技术选型 |
|------|---------|
| 后端框架 | Django 5.0 + DRF |
| 数据库 | PostgreSQL (JSONB) |
| 缓存 | Redis |
| 前端框架 | Vue 3 (Composition API) |
| 图表库 | Apache ECharts 5.x |
| 状态管理 | Pinia |
| 异步任务 | Celery + Redis |

---

## 9. 开发检查清单

- [ ] 创建 ReportLayout 模型及迁移
- [ ] 实现 MetadataReportService 服务层
- [ ] 实现 MetadataDrivenReportViewSet 视图层
- [ ] 配置 URL 路由
- [ ] 前端 MetadataDrivenReport.vue 组件开发
- [ ] ECharts 集成与图表配置
- [ ] 缓存机制实现
- [ ] 权限控制集成
- [ ] 单元测试编写
- [ ] 性能测试与优化

---

## 附录：参考资料

- [ECharts 官方文档](https://echarts.apache.org/zh/index.html)
- [PostgreSQL JSONB 查询优化](https://www.postgresql.org/docs/current/datatype-json.html)
- [Django ORM 聚合查询](https://docs.djangoproject.com/en/5.0/topics/db/aggregation/)
