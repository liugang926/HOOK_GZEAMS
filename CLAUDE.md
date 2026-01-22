# Claude.md
## Hook Fixed Assets (钩子固定资产) - Project Development Standards & Guidelines

### Code Writing Standards (MUST Follow)
#### ✅ Mandatory: English Comments Only
- **ALL code comments MUST be in English** - No exceptions
- This includes: inline comments, docstrings, class/function descriptions
- Example:
  ```python
  # ✅ Correct - English comment
  def get_active_assets(self):
      """Get all active assets for current organization."""
      return self.queryset.filter(is_deleted=False)

  # ❌ Wrong - Chinese comment
  def get_active_assets(self):
      """获取当前组织的所有活跃资产"""
      return self.queryset.filter(is_deleted=False)
  ```

---

### Project Overview
**Hook Fixed Assets** is a **metadata-driven low-code platform** based on Django & Vue3, dedicated to enterprise-level fixed asset management. Core capabilities include dynamic business object configuration, multi-organization data isolation, complex master-detail relational data processing, visual BPM workflow design, and professional fixed asset inventory & reconciliation management.

- **GitHub Repository**: [https://github.com/liugang926/HOOK_GZEAMS.git](https://github.com/liugang926/HOOK_GZEAMS.git)
- **Primary Reference Benchmark**: [NIIMBOT Hook Fixed Assets](https://yzcweixin.niimbot.com/) (QR code login required)
- **Core Implementation Rule**: UI interaction logic, full asset lifecycle management process, and inventory reconciliation core logic must strictly align with the NIIMBOT benchmark system.

### Core Technology Stack
#### Backend
Django 5.0, Django REST Framework (DRF), PostgreSQL (JSONB for dynamic metadata storage), Redis (cache/queue), Celery (async task processing)

#### Frontend
Vue 3 (Composition API only), Vite build tool, Element Plus UI component library, Pinia state management

#### Middleware & Tools
LogicFlow (visual BPM workflow engine), Docker Compose (containerized deployment & orchestration)

---

### Development Commands (Full & Standard)
#### Environment Setup & Global Startup (Docker - Recommended)
```bash
# Start all dependent services (DB/Redis/Backend/Frontend/Celery Worker) in background
docker-compose up -d

# Real-time view backend service running logs (core debug command)
docker-compose logs -f backend
```

#### Backend (Django) Core Development Commands
```bash
# Execute database migrations + sync low-code dynamic schema metadata
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py sync_schemas

# Create super administrator account for system access
docker-compose exec backend python manage.py createsuperuser
```

#### Frontend (Vue3) Core Development Commands
```bash
# Local development hot-reload mode
npm run dev

# Production build + code packaging
npm run build

# Code specification check & lint repair
npm run lint
```

---

### Core Architecture & Engineering Development Standards
#### 1. Backend Module Structure (Fixed - `backend/apps/`)
All backend business logic follows fixed modularization, no cross-module reference chaos is allowed:
- `common`: **公共基类层 (Base Class Layer)** - Base abstract models, unified serializers/viewsets/services/filters, global shared utilities
  - `models.py`: BaseModel abstract base class (data isolation + soft delete + audit fields)
  - `serializers/base.py`: BaseModelSerializer (auto-serialize common fields + custom_fields)
  - `viewsets/base.py`: BaseModelViewSet (auto org filtering + soft delete + batch operations)
  - `services/base_crud.py`: BaseCRUDService (unified CRUD methods)
  - `filters/base.py`: BaseModelFilter (common field filtering: time range, user, org)
  - `responses/base.py`: BaseResponse (unified API response format)
  - `handlers/exceptions.py`: BaseExceptionHandler (unified error handling)
- `organizations`: Multi-org core architecture | company/department tree structure + cross-org data isolation logic
- `accounts`: User core model + org-based RBAC permission control system
- `sso`: Third-party platform integration | SSO login + org structure sync (WeChat Work / DingTalk / Feishu)
- `system`: Low-code core engine | Business Object metadata, Field Definitions, Page Layout configuration
- `workflows`: BPM workflow engine | LogicFlow-based flow definitions + workflow instance state lifecycle management
- `inventory`: Asset inventory core module | asset snapshot generation, scanning operation logs, inventory reconciliation core logic

#### 2. Mandatory Base Model & Inheritance Specifications (`apps/common/`)
✅ **Rule: All backend components MUST inherit from corresponding base classes** (non-negotiable)

##### A. BaseModel (ORM Models) - `apps/common/models.py`
✅ **All Django ORM models MUST inherit from `BaseModel`** (non-negotiable)
- ✅ Data Isolation: Built-in `org` ForeignKey field + `TenantManager` auto-filter org-scoped data
- ✅ Soft Delete: Contains `is_deleted`(bool) + `deleted_at`(datetime) fields + `soft_delete()` built-in method (physical delete forbidden)
- ✅ Full Audit Log: Standard fields - `created_at`, `updated_at`, `created_by` (track all data operation sources)
- ✅ Dynamic Extension: `custom_fields` (PostgreSQL JSONB type) for storing low-code defined dynamic field data

##### B. BaseModelSerializer (Serializers) - `apps/common/serializers/base.py`
✅ **All DRF Serializers MUST inherit from `BaseModelSerializer`** (non-negotiable)
- ✅ Auto-serialize common fields: `id`, `organization`, `is_deleted`, `deleted_at`, `created_at`, `updated_at`, `created_by`
- ✅ Auto-handle `custom_fields` JSONB field serialization
- ✅ Embed user info in `created_by` field (nested UserSerializer)
- ✅ Support for `flatten_custom_fields` option to expand dynamic fields to top level
- ✅ Extended variant: `BaseModelWithAuditSerializer` includes `updated_by` and `deleted_by` fields

##### C. BaseModelViewSet (ViewSets) - `apps/common/viewsets/base.py`
✅ **All DRF ViewSets MUST inherit from `BaseModelViewSet` or `BaseModelViewSetWithBatch`** (non-negotiable)
- ✅ Auto-apply organization filtering in `get_queryset()` (via TenantManager)
- ✅ Auto-filter soft-deleted records (only show active records by default)
- ✅ Auto-set audit fields: `created_by` in `perform_create()`, `organization_id` from current context
- ✅ Auto-use soft delete in `perform_destroy()` (calls `instance.soft_delete()`)
- ✅ Built-in actions: `/deleted/` (list deleted records), `/{id}/restore/` (restore soft-deleted records)
- ✅ **WithBatch variant**: Includes `BatchOperationMixin` for bulk operations:
  - `POST /batch-delete/` - Bulk soft delete
  - `POST /batch-restore/` - Bulk restore
  - `POST /batch-update/` - Bulk field update
  - Standardized batch response format with success/failure statistics

##### D. BaseCRUDService (Services) - `apps/common/services/base_crud.py`
✅ **All Service classes MUST inherit from `BaseCRUDService`** (non-negotiable)
- ✅ Provides unified CRUD methods: `create()`, `update()`, `delete()` (soft), `restore()`, `get()`, `query()`, `paginate()`
- ✅ Auto-handles organization isolation in all operations
- ✅ Supports complex query scenarios with filters, search, and ordering
- ✅ Built-in pagination support with standardized response format
- ✅ Batch operations: `batch_delete()` with detailed results tracking

##### E. BaseModelFilter (Filters) - `apps/common/filters/base.py`
✅ **All FilterSet classes MUST inherit from `BaseModelFilter`** (non-negotiable)
- ✅ Auto-supports common field filtering: `created_at` range, `updated_at` range, `created_by`, `is_deleted`
- ✅ Time range filters: `created_at_from`, `created_at_to`, `updated_at_from`, `updated_at_to`
- ✅ User filtering: `created_by` (UUID filter)
- ✅ Organization filtering: Automatic org-scoped filtering via TenantManager

##### F. Code Usage Examples (Standard Pattern)
```python
# 1. Model - Always inherit BaseModel
from apps.common.models import BaseModel

class Asset(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    # Automatically inherits: org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields

# 2. Serializer - Always inherit BaseModelSerializer
from apps.common.serializers.base import BaseModelSerializer

class AssetSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + ['code', 'name', 'status']

# 3. Filter - Always inherit BaseModelFilter
from apps.common.filters.base import BaseModelFilter
import django_filters

class AssetFilter(BaseModelFilter):
    code = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(BaseModelFilter.Meta):
        model = Asset
        fields = BaseModelFilter.Meta.fields + ['code', 'status']

# 4. ViewSet - Always inherit BaseModelViewSetWithBatch
from apps.common.viewsets.base import BaseModelViewSetWithBatch

class AssetViewSet(BaseModelViewSetWithBatch):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    filterset_class = AssetFilter
    # Automatically gets: org filtering, soft delete, audit fields, batch operations

# 5. Service - Always inherit BaseCRUDService
from apps.common.services.base_crud import BaseCRUDService

class AssetService(BaseCRUDService):
    def __init__(self):
        super().__init__(Asset)

    def get_by_code(self, code: str):
        """Business-specific method"""
        return self.model_class.objects.get(code=code)
```

#### 3. Core Architectural Design Patterns (Key Standards)
##### A. Multi-Org & Third-Party SSO Synchronization
- Adapter Pattern Core: Abstract `BasePlatformAdapter` as the base class for all third-party platform adapters (unified interface)
- Data Mapping: Persist mapping relations between third-party `userid/unionid` and system `User` model
- Async Sync: Scheduled org/user structure synchronization tasks are all executed via Celery (non-blocking)

##### B. Low-Code Metadata Core Engine
- `BusinessObject`: Defines all configurable enterprise business entities (e.g., Asset, Asset Requisition, Inventory Task)
- `FieldDefinition`: Rich field type support - text/number/reference(FK)/formula(simpleeval)/sub-table nested fields
- `PageLayout`: JSON-structured configuration for form/list field grouping, sort order, field visibility & display rules

##### C. Visual BPM Workflow Engine
- Frontend Visualization: Drag-and-drop workflow designer based on LogicFlow (JSON format for flow definition storage)
- Dynamic Field Permission: Workflow nodes support granular permission configuration (Read-only / Hidden / Editable) for each field, bound with `DynamicForm`
- State Driven: Workflow instance status automatically controls asset lifecycle state transitions

##### D. Asset Inventory & Reconciliation (Align with NIIMBOT Benchmark)
- Snapshot Design Pattern: Generate an immutable asset snapshot at inventory initiation, ensure business changes during inventory do not affect reconciliation results
- Mobile First Adaptation: Optimized for mobile QR-code scanning operations, support offline scanning staging + batch online submission
- Reconciliation Logic: Standardized discrepancy marking, approval for discrepancy settlement, and post-reconciliation asset state synchronization

##### E. Public Base Class Layer (Common Infrastructure)
- **Eliminate Code Duplication**: All common logic (serialization, filtering, soft delete, org isolation) extracted to reusable base classes
- **Consistent Behavior Patterns**: All modules follow identical data processing and error handling approaches
- **Convention over Configuration**: Inherit base classes to get default behaviors; override only when necessary
- **Unified API Standards**: Standardized response formats, error codes, and batch operation interfaces
- **Backend Base Classes** (MUST use):
  - `BaseModelSerializer`: Auto-serialize common fields + custom_fields
  - `BaseModelViewSet` / `BaseModelViewSetWithBatch`: Auto org filtering + soft delete + audit fields + batch operations
  - `BaseCRUDService`: Unified CRUD methods with org isolation
  - `BaseModelFilter`: Common field filtering (time range, user, org)
  - `BaseResponse`: Unified API response format
  - `BaseExceptionHandler`: Unified error handling with standard error codes

---

### Frontend Rendering & Interaction Standards (Strict Compliance)
#### 1. Core Dynamic Rendering Engine (`src/components/engine/`)
- `DynamicForm`: Recursively parse metadata-based page layouts, native support for master-detail table structures + real-time formula calculation (powered by `useFormula.js`)
- `FieldRenderer`: Automatic component dispatch based on metadata field type (User Picker, Dept Tree, Scan Input, Reference Selector, etc.)
- `WorkflowDesigner`: Full-featured visual workflow editor encapsulated based on LogicFlow (unified with backend flow definition JSON schema)

#### 2. Mandatory Page-Level Components (`src/components/common/`)
- `BaseListPage`: Standard list page with search, filtering, pagination, batch operations
- `BaseFormPage`: Standard form page with validation and submit handling
- `BaseDetailPage`: Standard detail page with audit info display

#### 3. Mandatory UI/UX Principles (No Exceptions)
- Benchmark Alignment: Strictly follow NIIMBOT official UI style - concise operation area, high-contrast key buttons (prioritize asset scanning & core operation efficiency)
- Global Error Handling: Unified global request/response interceptors for all API calls, standardized error prompt components (✅ `native alert()` is FORBIDDEN completely)
- Interaction Consistency: Unified loading state, empty state, and operation feedback for all business modules

#### 4. Layout Components (Must Reference)
- `DynamicTabs`: Tab page configuration with drag-drop sorting (reference: `docs/plans/common_base_features/tab_configuration.md`)
- `SectionBlock`: Section container with collapsible sections (reference: `docs/plans/common_base_features/section_block_layout.md`)
- `ColumnManager`: List column display/width/sort configuration (reference: `docs/plans/common_base_features/list_column_configuration.md`)

---

### PRD Documentation Standards (Must Follow)
#### 1. PRD Writing Guide
All new feature PRDs MUST follow the guide in `docs/plans/common_base_features/prd_writing_guide.md`:
- Include public model reference declaration (MUST)
- Specify all base class inheritances
- Define user roles and permissions
- Include API specification and error codes

#### 2. PRD Document Structure (Standard Template)
Every PRD MUST contain these sections:
1. **功能概述与业务场景** - Business background and scenarios
2. **用户角色与权限** - User roles and permission matrix
3. **公共模型引用声明** (MUST HAVE) - Public base class reference table
4. **数据模型设计** - Data models with BaseModel inheritance
5. **API接口设计** - API endpoints following unified format
6. **前端组件设计** - Frontend components using common base
7. **测试用例** - Test cases for model, API, service

#### 3. Public Model Reference Declaration Template
```markdown
## 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |
```

---

### External Integration & ERP Extension Standards (Critical Rules)
#### ✅ Mandatory Development Rules (All Must Comply)
1. **Async First Principle**: All SSO synchronization, ERP data push, complex inventory reconciliation, and batch data processing tasks **MUST** be executed via Celery async tasks (synchronous blocking operations forbidden)
2. **Full Integration Audit Log**: All external third-party API calls are fully recorded in `IntegrationLog` model, including complete request body, response body, request status code, and execution time
3. **Idempotency Guarantee**: All ERP data push operations **MUST** carry a unique `external_id` parameter to prevent duplicate data insertion caused by network retries or repeated requests
4. **Failure Retry Mechanism**: Critical ERP/integration tasks are configured with Celery retry policies (with maximum retry limit) + failure alert notification

---

### API Response Standards & Batch Operations (Strict Compliance)
#### 1. Unified Response Format
✅ **All API endpoints MUST follow standardized response format** (non-negotiable)

##### Success Response Format
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "uuid",
        "code": "ASSET001",
        ...
    }
}
```

##### List Response Format (Paginated)
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/assets/?page=2",
        "previous": null,
        "results": [...]
    }
}
```

##### Error Response Format
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "code": ["该字段不能为空"]
        }
    }
}
```

#### 2. Standard Error Codes
✅ **All error responses MUST use predefined error codes** (non-negotiable)

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request data validation failed |
| `UNAUTHORIZED` | 401 | Unauthorized access |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `METHOD_NOT_ALLOWED` | 405 | Method not allowed |
| `CONFLICT` | 409 | Resource conflict |
| `ORGANIZATION_MISMATCH` | 403 | Organization mismatch |
| `SOFT_DELETED` | 410 | Resource has been deleted |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `SERVER_ERROR` | 500 | Internal server error |

#### 3. Batch Operation Standards
✅ **All batch operations MUST follow standardized request/response format** (non-negotiable)

##### Batch Delete Request
```http
POST /api/{resource}/batch-delete/
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

##### Batch Operation Response (All Success)
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

##### Batch Operation Response (Partial Failure)
```json
{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 3,
        "succeeded": 2,
        "failed": 1
    },
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": false, "error": "记录不存在"},
        {"id": "uuid3", "success": true}
    ]
}
```

##### Standard Batch Endpoints
- `POST /api/{resource}/batch-delete/` - Batch soft delete
- `POST /api/{resource}/batch-restore/` - Batch restore
- `POST /api/{resource}/batch-update/` - Batch field update

#### 4. Standard CRUD Operations
All ModelViewSets automatically provide:
- `GET /api/{resource}/` - List with pagination, filtering, search
- `GET /api/{resource}/{id}/` - Retrieve single record
- `POST /api/{resource}/` - Create new record
- `PUT /api/{resource}/{id}/` - Full update
- `PATCH /api/{resource}/{id}/` - Partial update
- `DELETE /api/{resource}/{id}/` - Soft delete

#### 5. Extended Operations
All ModelViewSets automatically provide:
- `GET /api/{resource}/deleted/` - List deleted records
- `POST /api/{resource}/{id}/restore/` - Restore single deleted record

---

### Supplementary Core Constraints
> All development must follow the above standards; any deviation from the mandatory rules (marked with ✅) requires team review and approval.
> The core design concept of the project is **metadata-driven low-code + enterprise-level data isolation**, all business iterations should not break this core architecture.

---

### Report Generation Standards (MUST Follow)
#### 📁 Report Storage Structure
All implementation, verification, and summary reports MUST be stored in the `docs/reports/` directory with the following structure:

```
docs/reports/
├── implementation/   # Phase-by-phase implementation reports
├── compliance/        # Code compliance verification and fix reports
├── quickstart/        # Quick start guides and reference
├── summaries/         # Overall summary reports and manifests
└── README.md          # Report index and navigation
```

#### 📝 Report Naming Conventions

| 报告类型 | 命名格式 | 示例 |
|---------|---------|------|
| 阶段实施报告 | `PHASE{X}_{Y}_{MODULE_NAME}_IMPLEMENTATION_REPORT.md` | `PHASE1_1_ASSET_CATEGORY_IMPLEMENTATION_REPORT.md` |
| 验证报告 | `{MODULE}_CODE_COMPLIANCE_REPORT.md` | `INVENTORY_CODE_COMPLIANCE_REPORT.md` |
| 修复报告 | `{FIX_TYPE}_COMPLETION_REPORT.md` | `ENCODING_FIX_COMPLETION_REPORT.md` |
| 快速入门 | `{MODULE}_QUICK_START.md` | `LOGICFLOW_QUICK_START.md` |
| 文件清单 | `PHASE{X}_{Y}_FILES_MANIFEST.md` | `PHASE2_4_FILES_MANIFEST.md` |
| 快速参考 | `PHASE{X}_{Y}_QUICK_REFERENCE.md` | `PHASE2_4_QUICK_REFERENCE.md` |
| 汇总报告 | `GZEAMS_{REPORT_TYPE}_REPORT.md` | `GZEAMS_FINAL_IMPLEMENTATION_REPORT.md` |

#### ⚠️ Report Generation Rules (MUST Follow)

1. **NEVER generate reports in project root directory** - All reports MUST go into `docs/reports/` subdirectories
2. **Categorize reports correctly** - Choose the appropriate subdirectory based on report type
3. **Use consistent naming** - Follow the naming conventions table above
4. **Update index file** - When adding new reports, update `docs/reports/README.md`
5. **Include metadata** - All reports should include:
   - Document version and date
   - Author/Agent information
   - Scope and coverage summary
   - File list and line count statistics
   - PRD correspondence verification

#### 📋 Report Template (Required Sections)

Every implementation/compliance report MUST include:

```markdown
# [Report Title]

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | YYYY-MM-DD |
| 涉及阶段 | Phase X.Y |
| 作者/Agent | [Name] |

## 一、实施概述
- 完成内容摘要
- 文件清单
- 代码行数统计

## 二、与 PRD 对应关系
| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|

## 三、规范遵循验证
| 规范项 | 状态 | 说明 |

## 四、创建文件清单
## 五、后续建议
```
