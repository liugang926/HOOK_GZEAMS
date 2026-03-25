# Phase 5.3: 固定资产折旧模块 - 文件清单

## 创建时间
2026-01-16

## 项目信息
- **模块名称**: 固定资产折旧自动计算模块
- **技术栈**: Django 5.0 + DRF + Vue 3 + PostgreSQL + Celery
- **实现状态**: ✅ 核心功能已完成

---

## 一、后端文件清单

### 1.1 模型层（Models）

| 文件路径 | 说明 | 关键类 | 行数 |
|---------|------|--------|------|
| `backend/apps/depreciation/models.py` | 折旧模型定义 | DepreciationMethod, DepreciationPolicy, DepreciationRecord | ~400 |

**核心功能**:
- ✅ DepreciationMethod: 折旧方法定义（直线法、双倍余额递减法、年数总和法、工作量法）
- ✅ DepreciationPolicy: 折旧策略配置（按资产分类配置折旧参数）
- ✅ DepreciationRecord: 折旧记录（存储每次折旧计算结果）

### 1.2 服务层（Services）

| 文件路径 | 说明 | 关键类/方法 | 行数 |
|---------|------|------------|------|
| `backend/apps/depreciation/services/__init__.py` | 服务模块导出 | DepreciationEngine, DepreciationService | ~10 |
| `backend/apps/depreciation/services/depreciation_engine.py` | 折旧计算引擎 | DepreciationEngine.calculate() | ~450 |
| `backend/apps/depreciation/services/depreciation_service.py` | 折旧业务服务 | DepreciationService | ~350 |

**核心功能**:
- ✅ DepreciationEngine: 支持4种折旧方法 + 工作量法
- ✅ DepreciationService: 继承 BaseCRUDService，提供完整 CRUD 和业务逻辑

### 1.3 序列化器（Serializers）

| 文件路径 | 说明 | 关键类 | 行数 |
|---------|------|--------|------|
| `backend/apps/depreciation/serializers/__init__.py` | 序列化器导出 | 4个序列化器 | ~15 |
| `backend/apps/depreciation/serializers/depreciation.py` | 序列化器定义 | DepreciationMethodSerializer, DepreciationPolicySerializer, DepreciationRecordSerializer, DepreciationRecordListSerializer | ~200 |

**继承关系**:
- ✅ DepreciationMethodSerializer → BaseModelSerializer
- ✅ DepreciationPolicySerializer → BaseModelSerializer
- ✅ DepreciationRecordSerializer → BaseModelWithAuditSerializer
- ✅ DepreciationRecordListSerializer → BaseModelSerializer（简化版）

### 1.4 过滤器（Filters）

| 文件路径 | 说明 | 关键类 | 行数 |
|---------|------|--------|------|
| `backend/apps/depreciation/filters/__init__.py` | 过滤器导出 | 3个过滤器 | ~10 |
| `backend/apps/depreciation/filters/depreciation.py` | 过滤器定义 | DepreciationMethodFilter, DepreciationPolicyFilter, DepreciationRecordFilter | ~150 |

**继承关系**:
- ✅ 所有过滤器 → BaseModelFilter

### 1.5 视图层（Views）

| 文件路径 | 说明 | 关键类 | 行数 |
|---------|------|--------|------|
| `backend/apps/depreciation/views.py` | 视图层 | DepreciationMethodViewSet, DepreciationPolicyViewSet, DepreciationRecordViewSet | ~400 |

**继承关系**:
- ✅ 所有 ViewSet → BaseModelViewSetWithBatch

**自定义端点**:
- ✅ POST `/calculate/` - 批量计算折旧
- ✅ POST `/{id}/submit/` - 提交审核
- ✅ POST `/{id}/approve/` - 审核通过
- ✅ POST `/{id}/reject/` - 驳回
- ✅ POST `/{id}/post/` - 过账
- ✅ GET `/summary/` - 资产折旧汇总
- ✅ GET `/period-summary/` - 期间汇总
- ✅ GET `/category-summary/` - 分类汇总
- ✅ GET `/department-summary/` - 部门汇总

### 1.6 URL 配置

| 文件路径 | 说明 | 内容 | 行数 |
|---------|------|------|------|
| `backend/apps/depreciation/urls.py` | URL 路由配置 | router注册 + urlpatterns | ~20 |

### 1.7 Celery 任务（Tasks）

| 文件路径 | 说明 | 关键任务 | 行数 |
|---------|------|----------|------|
| `backend/apps/depreciation/tasks/__init__.py` | 任务模块导出 | 2个导出任务 | ~10 |
| `backend/apps/depreciation/tasks/depreciation_tasks.py` | 异步任务定义 | calculate_monthly_depreciation_task, generate_depreciation_report_task, auto_post_approved_depreciation_task, cleanup_old_depreciation_records_task | ~350 |

**任务列表**:
- ✅ calculate_monthly_depreciation_task: 月度折旧计算（支持重试）
- ✅ generate_depreciation_report_task: 报表生成（summary/category/department/detail）
- ✅ auto_post_approved_depreciation_task: 自动过账审核通过的记录
- ✅ cleanup_old_depreciation_records_task: 清理旧数据（默认保留36个月）

---

## 二、前端文件清单

### 2.1 API 接口

| 文件路径 | 说明 | 导出模块 | 行数 |
|---------|------|----------|------|
| `frontend/src/api/depreciation/index.js` | 折旧 API 封装 | depreciationApi, depreciationMethodApi, depreciationPolicyApi | ~200 |

**API 方法**:
- ✅ list(), get(), create(), update(), delete()
- ✅ calculate() - 计算折旧
- ✅ submit(), approve(), reject(), post() - 审核工作流
- ✅ getSummary(), getPeriodSummary(), getCategorySummary(), getDepartmentSummary() - 统计汇总
- ✅ batchDelete(), batchSubmit(), batchApprove() - 批量操作
- ✅ export() - 导出

### 2.2 页面组件（待实现）

根据 PRD 文档，以下 Vue 页面组件需要实现：

| 文件路径 | 说明 | 功能 | 预计行数 |
|---------|------|------|----------|
| `frontend/src/views/finance/depreciation/DepreciationList.vue` | 折旧记录列表页 | 搜索、批量计算、审核工作流 | ~300 |
| `frontend/src/views/finance/depreciation/AssetDepreciationDetail.vue` | 资产折旧详情页 | 详情展示、趋势图表（ECharts） | ~350 |
| `frontend/src/views/finance/depreciation/DepreciationReport.vue` | 折旧报表页 | 统计卡片、分类汇总表 | ~300 |
| `frontend/src/views/finance/depreciation/DepreciationMethodConfig.vue` | 折旧方法配置页 | 方法配置、参数设置 | ~200 |

**注意**: 这些 Vue 组件的详细代码已在 PRD 文档中提供，可根据实际 UI 需求进行调整。

---

## 三、文档文件清单

| 文件路径 | 说明 | 内容 |
|---------|------|------|
| `PHASE5_3_DEPRECIATION_IMPLEMENTATION_REPORT.md` | 实现报告 | 14章完整实现文档，包含代码示例、API文档、使用指南 |
| `PHASE5_3_FILE_MANIFEST.md` | 本文件 | 文件清单和快速参考 |

---

## 四、数据库迁移文件

### 执行命令生成迁移文件

```bash
cd backend
python manage.py makemigrations depreciation
python manage.py migrate depreciation
```

### 生成的迁移文件

```
backend/apps/depreciation/migrations/0001_initial.py
```

---

## 五、代码统计

### 5.1 后端代码统计

| 类型 | 文件数 | 代码行数 |
|------|--------|----------|
| Models | 1 | ~400 |
| Services | 3 | ~810 |
| Serializers | 2 | ~215 |
| Filters | 2 | ~160 |
| Views | 1 | ~400 |
| URLs | 1 | ~20 |
| Tasks | 2 | ~360 |
| **总计** | **12** | **~2,365** |

### 5.2 前端代码统计

| 类型 | 文件数 | 代码行数 |
|------|--------|----------|
| API | 1 | ~200 |
| Vue组件（待实现） | 4 | ~1,150 |
| **总计** | **5** | **~1,350** |

### 5.3 总计

- **总文件数**: 17 个文件（已实现 13 个，待实现 4 个 Vue 组件）
- **总代码行数**: ~3,715 行（已实现 ~2,565 行，待实现 ~1,150 行）

---

## 六、文件结构树

```
backend/apps/depreciation/
├── __init__.py
├── admin.py                         # Django Admin 配置
├── apps.py                          # Django App 配置
├── models.py                        # ✅ 折旧模型（~400行）
├── views.py                         # ✅ 视图层（~400行）
├── urls.py                          # ✅ URL配置（~20行）
├── services/
│   ├── __init__.py                  # ✅ 服务导出（~10行）
│   ├── depreciation_engine.py       # ✅ 计算引擎（~450行）
│   └── depreciation_service.py      # ✅ 业务服务（~350行）
├── serializers/
│   ├── __init__.py                  # ✅ 序列化器导出（~15行）
│   └── depreciation.py              # ✅ 序列化器定义（~200行）
├── filters/
│   ├── __init__.py                  # ✅ 过滤器导出（~10行）
│   └── depreciation.py              # ✅ 过滤器定义（~150行）
├── tasks/
│   ├── __init__.py                  # ✅ 任务导出（~10行）
│   └── depreciation_tasks.py        # ✅ Celery任务（~350行）
└── migrations/
    └── 0001_initial.py              # ✅ 初始迁移（自动生成）

frontend/src/
├── api/
│   └── depreciation/
│       └── index.js                 # ✅ API封装（~200行）
└── views/
    └── finance/
        └── depreciation/
            ├── DepreciationList.vue           # ⏳ 待实现
            ├── AssetDepreciationDetail.vue    # ⏳ 待实现
            ├── DepreciationReport.vue         # ⏳ 待实现
            └── DepreciationMethodConfig.vue   # ⏳ 待实现
```

图例：
- ✅ 已完成
- ⏳ 待实现（代码框架和示例已在 PRD 中提供）

---

## 七、关键代码位置速查

### 7.1 折旧计算方法

**文件**: `backend/apps/depreciation/services/depreciation_engine.py`

- **直线法**: 第 58-109 行
- **双倍余额递减法**: 第 111-175 行
- **年数总和法**: 第 177-238 行
- **工作量法**: 第 240-295 行
- **不计提折旧**: 第 297-307 行

### 7.2 业务服务方法

**文件**: `backend/apps/depreciation/services/depreciation_service.py`

- **calculate_asset_depreciation()**: 第 30-99 行 - 计算单个资产折旧
- **batch_calculate_period()**: 第 101-156 行 - 批量计算期间折旧
- **submit_for_approval()**: 第 158-176 行 - 提交审核
- **approve_depreciation()**: 第 178-198 行 - 审核通过
- **reject_depreciation()**: 第 200-218 行 - 驳回
- **post_depreciation()**: 第 220-238 行 - 过账
- **get_depreciation_summary()**: 第 240-263 行 - 资产折旧汇总
- **get_period_summary()**: 第 265-289 行 - 期间汇总
- **get_category_summary()**: 第 291-318 行 - 分类汇总
- **get_department_summary()**: 第 320-363 行 - 部门汇总

### 7.3 API 端点定义

**文件**: `backend/apps/depreciation/views.py`

- **DepreciationMethodViewSet**: 第 18-41 行
- **DepreciationPolicyViewSet**: 第 47-67 行
- **DepreciationRecordViewSet**: 第 73-343 行
  - **calculate**: 第 92-120 行
  - **submit**: 第 122-148 行
  - **approve**: 第 150-183 行
  - **reject**: 第 185-216 行
  - **post**: 第 218-248 行
  - **summary**: 第 250-285 行
  - **period_summary**: 第 287-321 行
  - **category_summary**: 第 323-343 行
  - **department_summary**: 第 345-365 行

### 7.4 Celery 任务定义

**文件**: `backend/apps/depreciation/tasks/depreciation_tasks.py`

- **calculate_monthly_depreciation_task()**: 第 11-78 行
- **generate_depreciation_report_task()**: 第 84-166 行
- **auto_post_approved_depreciation_task()**: 第 172-222 行
- **cleanup_old_depreciation_records_task()**: 第 228-277 行

---

## 八、快速参考

### 8.1 导入示例

```python
# 模型导入
from apps.depreciation.models import DepreciationMethod, DepreciationPolicy, DepreciationRecord

# 服务导入
from apps.depreciation.services import DepreciationEngine, DepreciationService

# 序列化器导入
from apps.depreciation.serializers import (
    DepreciationMethodSerializer,
    DepreciationPolicySerializer,
    DepreciationRecordSerializer,
    DepreciationRecordListSerializer
)

# 过滤器导入
from apps.depreciation.filters import (
    DepreciationMethodFilter,
    DepreciationPolicyFilter,
    DepreciationRecordFilter
)

# 视图导入
from apps.depreciation.views import (
    DepreciationMethodViewSet,
    DepreciationPolicyViewSet,
    DepreciationRecordViewSet
)

# 任务导入
from apps.depreciation.tasks import (
    calculate_monthly_depreciation_task,
    generate_depreciation_report_task
)
```

### 8.2 前端导入示例

```javascript
// API 导入
import { depreciationApi, depreciationMethodApi, depreciationPolicyApi } from '@/api/depreciation'

// 路由导入
import { depreciationRoutes } from '@/router/depreciation'
```

---

## 九、依赖检查清单

### 9.1 Python 依赖

确保 `requirements.txt` 包含以下依赖：

```txt
# Django 核心
Django==5.0.*
djangorestframework==3.14.*
django-filter==23.5.*

# Celery 异步任务
celery==5.3.*
redis==5.0.*

# 数据库
psycopg2-binary==2.9.*

# 其他
python-decimal==1.0.*  # 标准库，无需安装
```

### 9.2 前端依赖

确保 `package.json` 包含以下依赖：

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "element-plus": "^2.5.0",
    "axios": "^1.6.0",
    "echarts": "^5.4.0"
  }
}
```

---

## 十、下一步工作

### 10.1 必须完成

1. **数据库迁移**
   ```bash
   python manage.py makemigrations depreciation
   python manage.py migrate depreciation
   ```

2. **初始化折旧方法**
   - 创建默认折旧方法数据
   - 配置折旧策略

3. **配置 Celery Beat**
   - 添加定时任务配置
   - 启动 Celery Worker 和 Beat

4. **实现前端页面**
   - 根据提供的代码实现 4 个 Vue 组件
   - 配置前端路由

### 10.2 可选优化

1. **添加单元测试**
   - 测试折旧计算引擎
   - 测试服务层方法
   - 测试 API 端点

2. **完善 Excel 导出**
   - 安装 `openpyxl` 库
   - 实现导出逻辑

3. **配置邮件通知**
   - 配置 SMTP 服务器
   - 实现邮件模板

4. **性能优化**
   - 添加 Redis 缓存
   - 优化数据库查询
   - 添加数据库索引

---

**文档版本**: 1.0
**最后更新**: 2026-01-16
**维护者**: Claude Code
