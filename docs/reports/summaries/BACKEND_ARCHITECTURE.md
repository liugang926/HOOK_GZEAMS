# GZEAMS Backend Architecture Overview

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vue3)                         │
│                  Vite + Element Plus                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Django REST Framework (DRF)                    │
│              JWT Authentication + CORS                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Django 5.0 Apps                          │
├─────────────────────────────────────────────────────────────┤
│  common     │  Base models, serializers, viewsets, services │
│  accounts   │  User authentication, authorization           │
│  orgs       │  Multi-organization hierarchy (MPTT)          │
│  assets     │  Fixed asset management                       │
│  system     │  Low-code metadata engine                     │
│  workflows  │  BPM workflow engine (LogicFlow)              │
│  inventory  │  Asset inventory & reconciliation             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL │  Primary DB (JSONB for custom_fields)        │
│  Redis      │  Cache, Session, Celery Broker               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Background Tasks (Celery)                      │
│              SSO Sync, ERP Integration, Reports             │
└─────────────────────────────────────────────────────────────┘
```

## Core Models Hierarchy

```
BaseModel (Abstract)
├── id: UUID (primary key)
├── organization: ForeignKey (for multi-tenancy)
├── is_deleted: Boolean (soft delete)
├── deleted_at: DateTime
├── created_at: DateTime
├── updated_at: DateTime
├── created_by: ForeignKey (User)
└── custom_fields: JSONB (dynamic metadata)

Organization (BaseModel)
├── name: CharField
├── code: CharField (unique)
├── type: ChoiceField (company/subsidiary/branch)
├── parent: ForeignKey (self, tree structure)
├── is_active: Boolean
└── contact information...

Department (MPTTModel, BaseModel)
├── name: CharField
├── code: CharField (unique per org)
├── organization: ForeignKey (Organization)
├── parent: TreeForeignKey (self, MPTT)
├── type: ChoiceField (functional/business/support)
├── manager: ForeignKey (User)
└── contact information...

User (AbstractUser, BaseModel)
├── username: CharField (unique)
├── email: EmailField
├── phone/mobile: CharField
├── organization: ForeignKey (Organization)
├── department: ForeignKey (Department)
├── employee_no: CharField
├── avatar: ImageField
├── real_name/nickname: CharField
├── position/title: CharField
├── SSO fields: wechat_userid, dingtalk_userid, feishu_userid
└── Django auth fields (is_active, is_staff, is_superuser)
```

## Multi-Organization Data Isolation

```
┌─────────────────────────────────────────────┐
│         Organization A (总公司)              │
│  ├─ Department A1 (财务部)                  │
│  │   └─ Assets [scoped to A-A1]            │
│  └─ Department A2 (IT部)                   │
│      └─ Assets [scoped to A-A2]            │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         Organization B (子公司)             │
│  ├─ Department B1 (人力资源)               │
│  │   └─ Assets [scoped to B-B1]            │
│  └─ Department B2 (市场部)                 │
│      └─ Assets [scoped to B-B2]            │
└─────────────────────────────────────────────┘
```

## API Endpoint Structure

```
/api/v1/
├── auth/          (accounts app)
│   ├── login/     (JWT token generation)
│   ├── logout/
│   └── me/        (current user info)
├── organizations/ (organizations app)
│   ├── /          (list/create orgs)
│   ├── {id}/      (retrieve/update/delete)
│   └── departments/ (nested dept endpoints)
├── assets/        (assets app)
│   ├── /          (list/create assets)
│   ├── {id}/
│   ├── categories/
│   └── transfers/
├── system/        (system app - low-code engine)
│   ├── business-objects/
│   ├── field-definitions/
│   └── page-layouts/
└── common/        (common app)
    └── batch-operations/ (shared endpoints)
```

## Request/Response Flow

```
1. Frontend Request (with JWT token)
   ↓
2. CORS Middleware (validate origin)
   ↓
3. Authentication Middleware (validate JWT)
   ↓
4. Organization Middleware (extract org from token/user)
   ↓
5. ViewSet (BaseModelViewSet)
   ├── get_queryset() - auto-filter by org
   ├── perform_create() - auto-set org and created_by
   └── perform_destroy() - soft delete
   ↓
6. Service Layer (BaseCRUDService)
   ├── CRUD operations with org isolation
   └── Business logic
   ↓
7. Response (standardized format)
   {
     "success": true,
     "message": "操作成功",
     "data": {...}
   }
```

## Celery Task Architecture

```
Celery Beat (Scheduler)
├── Sync org structure from WeChat Work (every 1 hour)
├── Sync user data from DingTalk (every 30 minutes)
├── Generate depreciation reports (monthly)
└── Cleanup soft-deleted records (daily)

Celery Workers
├── Queue: default (general tasks)
├── Queue: sso_sync (SSO synchronization)
├── Queue: erp_integration (ERP data push)
└── Queue: reports (report generation)
```

## Environment Variables

Required environment variables in .env:

```bash
# Database
DB_NAME=gzeams
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis123
REDIS_DB=0

# Django
SECRET_KEY=<generate with openssl rand -hex 32>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
SITE_URL=http://localhost:8000

# SSO (optional)
WECHAT_WORK_CORP_ID=
WECHAT_WORK_AGENT_ID=
WECHAT_WORK_SECRET=
```

## Development Workflow

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# Start Celery worker (separate terminal)
celery -A config worker -l info

# Start Celery beat (separate terminal)
celery -A config beat -l info

# Access API documentation
# Swagger UI: http://localhost:8000/swagger/
# Admin: http://localhost:8000/admin/
```

## Key Design Principles

1. **Convention over Configuration**: Inherit base classes to get default behaviors
2. **Multi-Tenancy First**: All data scoped to organization
3. **Soft Delete**: No physical data deletion (audit trail)
4. **Audit Everything**: Track who created/modified all records
5. **Async for Heavy Tasks**: Use Celery for SSO sync, ERP integration
6. **Low-Code Metadata**: JSONB custom_fields for dynamic schema evolution
7. **API Standards**: Unified response format, error codes, pagination
