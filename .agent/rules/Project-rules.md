# Claude.md
## Hook Fixed Assets (钩子固定资产) - Project Development Standards & Guidelines
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
- `common`: Base abstract models, unified exception handling, global shared tool functions/utilities
- `organizations`: Multi-org core architecture | company/department tree structure + cross-org data isolation logic
- `accounts`: User core model + org-based RBAC permission control system
- `sso`: Third-party platform integration | SSO login + org structure sync (WeChat Work / DingTalk / Feishu)
- `system`: Low-code core engine | Business Object metadata, Field Definitions, Page Layout configuration
- `workflows`: BPM workflow engine | LogicFlow-based flow definitions + workflow instance state lifecycle management
- `inventory`: Asset inventory core module | asset snapshot generation, scanning operation logs, inventory reconciliation core logic

#### 2. Mandatory Base Model Specification (`apps/common/models.py`)
✅ **Rule: All Django ORM models MUST inherit from `BaseModel`** (non-negotiable)
- ✅ Data Isolation: Built-in `org` ForeignKey field + `TenantManager` auto-filter org-scoped data
- ✅ Soft Delete: Contains `is_deleted`(bool) + `deleted_at`(datetime) fields + `soft_delete()` built-in method (physical delete forbidden)
- ✅ Full Audit Log: Standard fields - `created_at`, `updated_at`, `created_by` (track all data operation sources)
- ✅ Dynamic Extension: `custom_fields` (PostgreSQL JSONB type) for storing low-code defined dynamic field data

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

---

### Frontend Rendering & Interaction Standards (Strict Compliance)
#### 1. Core Dynamic Rendering Engine (`src/components/engine/`)
- `DynamicForm`: Recursively parse metadata-based page layouts, native support for master-detail table structures + real-time formula calculation (powered by `useFormula.js`)
- `FieldRenderer`: Automatic component dispatch based on metadata field type (User Picker, Dept Tree, Scan Input, Reference Selector, etc.)
- `WorkflowDesigner`: Full-featured visual workflow editor encapsulated based on LogicFlow (unified with backend flow definition JSON schema)

#### 2. Mandatory UI/UX Principles (No Exceptions)
- Benchmark Alignment: Strictly follow NIIMBOT official UI style - concise operation area, high-contrast key buttons (prioritize asset scanning & core operation efficiency)
- Global Error Handling: Unified global request/response interceptors for all API calls, standardized error prompt components (✅ `native alert()` is FORBIDDEN completely)
- Interaction Consistency: Unified loading state, empty state, and operation feedback for all business modules

---

### External Integration & ERP Extension Standards (Critical Rules)
#### ✅ Mandatory Development Rules (All Must Comply)
1. **Async First Principle**: All SSO synchronization, ERP data push, complex inventory reconciliation, and batch data processing tasks **MUST** be executed via Celery async tasks (synchronous blocking operations forbidden)
2. **Full Integration Audit Log**: All external third-party API calls are fully recorded in `IntegrationLog` model, including complete request body, response body, request status code, and execution time
3. **Idempotency Guarantee**: All ERP data push operations **MUST** carry a unique `external_id` parameter to prevent duplicate data insertion caused by network retries or repeated requests
4. **Failure Retry Mechanism**: Critical ERP/integration tasks are configured with Celery retry policies (with maximum retry limit) + failure alert notification

---

### Supplementary Core Constraints
> All development must follow the above standards; any deviation from the mandatory rules (marked with ✅) requires team review and approval.
> The core design concept of the project is **metadata-driven low-code + enterprise-level data isolation**, all business iterations should not break this core architecture.
