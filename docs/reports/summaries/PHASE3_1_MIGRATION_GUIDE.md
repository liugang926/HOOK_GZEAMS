# LogicFlow Backend - Migration & Setup Guide

## Overview

This guide provides step-by-step instructions for setting up the LogicFlow workflow engine backend in your GZEAMS project.

---

## Prerequisites

### Required Dependencies

Ensure your `requirements.txt` includes these packages:

```txt
# Core Django
Django==5.0.*
djangorestframework==3.14.*
django-filter==23.5*

# Database
psycopg2-binary==2.9.*

# Pinyin for code generation
pypinyin==0.51.*

# Optional: For production
gunicorn==21.2.*
```

### Install Dependencies

```bash
cd C:\Users\ND\Desktop\Notting_Project\GZEAMS\backend
pip install -r requirements.txt
```

---

## Step 1: Create Database Migrations

### Generate Migration Files

```bash
# Navigate to backend directory
cd C:\Users\ND\Desktop\Notting_Project\GZEAMS\backend

# Create migrations for workflows app
python manage.py makemigrations workflows
```

**Expected Output**:
```
Migrations for 'workflows':
  backend/apps/workflows/migrations/0001_initial.py
    - Create model FlowDefinition
    - Create model FlowInstance
    - Create model FlowNodeInstance
    - Create model FlowOperationLog
```

### Review Generated Migration

Check the generated migration file:

```bash
# Windows
type backend\apps\workflows\migrations\0001_initial.py

# Linux/Mac
cat backend/apps/workflows/migrations/0001_initial.py
```

Ensure it includes:
- FlowDefinition model
- FlowInstance model
- FlowNodeInstance model
- FlowOperationLog model
- All indexes and constraints

---

## Step 2: Apply Migrations

### Apply to Database

```bash
# Run migrations
python manage.py migrate workflows
```

**Expected Output**:
```
Running migrations:
  Applying workflows.0001_initial... OK
```

### Verify Tables Created

```bash
# Open Django shell
python manage.py shell

# Run verification
from django.db import connection
cursor = connection.cursor()
cursor.execute("""
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename LIKE 'workflow_%'
    ORDER BY tablename;
""")
print(cursor.fetchall())
```

**Expected Tables**:
```
workflow_flow_definitions
workflow_flow_instances
workflow_flow_node_instances
workflow_flow_operation_logs
```

---

## Step 3: Create Superuser (if not exists)

```bash
python manage.py createsuperuser
```

Follow prompts to create:
- Username
- Email
- Password

---

## Step 4: Verify Installation

### Test Django Admin

1. Start development server:
```bash
python manage.py runserver
```

2. Open browser:
```
http://localhost:8000/admin/
```

3. Login with superuser credentials

4. Verify workflow models appear:
   - Workflow definitions
   - Workflow instances
   - Flow node instances
   - Flow operation logs

### Test API Endpoints

```bash
# Test flow definitions list
curl http://localhost:8000/api/process-definitions/

# Expected response (empty list):
# {"success": true, "data": {"count": 0, ...}}
```

---

## Step 5: Load Sample Data (Optional)

### Create Sample Workflow

```python
# Save as load_sample_workflow.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.workflows.models import FlowDefinition
from django.contrib.auth import get_user_model

User = get_user_model()

# Get or create a test user
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)
if created:
    user.set_password('testpass123')
    user.save()

# Create sample workflow definition
workflow = FlowDefinition.objects.create(
    code='SAMPLE_APPROVAL',
    name='示例审批流程',
    definition={
        'nodes': [
            {
                'id': 'start',
                'type': 'start',
                'name': '开始',
                'properties': {},
                'x': 100,
                'y': 100
            },
            {
                'id': 'task_review',
                'type': 'task',
                'name': '审批',
                'properties': {
                    'assigneeType': 'role',
                    'assigneeId': 'manager'
                },
                'x': 300,
                'y': 100
            },
            {
                'id': 'end',
                'type': 'end',
                'name': '结束',
                'properties': {},
                'x': 500,
                'y': 100
            }
        ],
        'edges': [
            {
                'id': 'e1',
                'sourceNodeId': 'start',
                'targetNodeId': 'task_review',
                'type': 'default',
                'properties': {}
            },
            {
                'id': 'e2',
                'sourceNodeId': 'task_review',
                'targetNodeId': 'end',
                'type': 'default',
                'properties': {}
            }
        ]
    },
    description='这是一个示例审批流程',
    status='draft',
    version='1.0',
    category='sample',
    tags=['示例', '测试'],
    created_by=user
)

print(f"Created workflow: {workflow.name} (ID: {workflow.id})")
```

Run the script:
```bash
python load_sample_workflow.py
```

---

## Step 6: Update URL Configuration

### Include Workflow URLs

Ensure `backend/config/urls.py` includes workflow URLs:

```python
# backend/config/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Workflow URLs
    path('', include('apps.workflows.urls')),

    # Other app URLs
    # path('api/', include(...)),
]
```

---

## Step 7: Configure Settings

### Update INSTALLED_APPS

Ensure `backend/config/settings.py` includes workflows:

```python
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'django_filters',
    'corsheaders',

    # GZEAMS apps
    'apps.common',
    'apps.organizations',
    'apps.accounts',
    'apps.workflows',  # Add this line
    # ... other apps
]
```

### Configure REST Framework

```python
# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
```

---

## Step 8: Run Tests

### Create Test File

```python
# backend/apps/workflows/tests.py
from django.test import TestCase
from apps.workflows.models import FlowDefinition, FlowInstance, FlowNodeInstance
from django.contrib.auth import get_user_model

User = get_user_model()


class FlowDefinitionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_flow_definition(self):
        """Test creating a flow definition"""
        flow = FlowDefinition.objects.create(
            code='TEST_FLOW',
            name='Test Flow',
            definition={
                'nodes': [
                    {'id': 'start', 'type': 'start', 'name': 'Start'},
                    {'id': 'end', 'type': 'end', 'name': 'End'}
                ],
                'edges': [
                    {'id': 'e1', 'sourceNodeId': 'start', 'targetNodeId': 'end'}
                ]
            },
            created_by=self.user
        )
        self.assertEqual(flow.code, 'TEST_FLOW')
        self.assertEqual(flow.status, 'draft')
        self.assertTrue(flow.is_active())

    def test_invalid_definition(self):
        """Test validation fails for invalid definition"""
        with self.assertRaises(Exception):
            flow = FlowDefinition(
                code='INVALID_FLOW',
                name='Invalid Flow',
                definition={'nodes': []},  # Missing edges
                created_by=self.user
            )
            flow.full_clean()


class FlowExecutionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.flow = FlowDefinition.objects.create(
            code='TEST_FLOW',
            name='Test Flow',
            definition={
                'nodes': [
                    {'id': 'start', 'type': 'start', 'name': 'Start'},
                    {'id': 'end', 'type': 'end', 'name': 'End'}
                ],
                'edges': [
                    {'id': 'e1', 'sourceNodeId': 'start', 'targetNodeId': 'end'}
                ]
            },
            status='published',
            created_by=self.user
        )

    def test_create_and_start_instance(self):
        """Test creating and starting a flow instance"""
        from apps.workflows.services.flow_service import FlowService

        service = FlowService()

        # Create instance
        instance = service.create_flow(
            flow_definition_id=self.flow.id,
            business_key='TEST-001',
            business_type='test',
            business_data={'test': 'data'},
            user=self.user
        )

        self.assertEqual(instance.status, 'pending')

        # Start instance
        started = service.start_instance(instance.id, self.user)
        self.assertEqual(started.status, 'running')
```

### Run Tests

```bash
# Run all workflow tests
python manage.py test apps.workflows

# Run with verbosity
python manage.py test apps.workflows --verbosity=2

# Run specific test
python manage.py test apps.workflows.tests.FlowDefinitionModelTest
```

---

## Step 9: Troubleshooting

### Issue: Migration Fails

**Error**: `django.db.utils.ProgrammingError: relation "organizations_organization" does not exist`

**Solution**:
1. Ensure organizations app is migrated first:
```bash
python manage.py migrate organizations
python manage.py migrate workflows
```

### Issue: Import Error

**Error**: `ModuleNotFoundError: No module named 'pypinyin'`

**Solution**:
```bash
pip install pypinyin
```

### Issue: Permission Denied

**Error**: `Permission denied when creating flow instance`

**Solution**:
1. Ensure user is authenticated
2. Check organization context is set
3. Verify user has permissions

### Issue: Validation Error

**Error**: `Flow definition validation failed`

**Solution**:
1. Check LogicFlow JSON structure
2. Ensure nodes array has at least one node
3. Ensure edges array is present
4. Verify node IDs are unique
5. Check for start and end nodes

---

## Step 10: Production Deployment

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Database Backup

```bash
# Backup database before migration
pg_dump -U postgres -d gzeams > backup_before_workflow.sql

# Backup after migration
pg_dump -U postgres -d gzeams > backup_after_workflow.sql
```

### Performance Tuning

```sql
-- Create indexes for better query performance
CREATE INDEX idx_flow_def_org_status ON workflow_flow_definitions(organization_id, status);
CREATE INDEX idx_flow_inst_business ON workflow_flow_instances(business_type, business_key);
CREATE INDEX idx_flow_node_assignee_status ON workflow_flow_node_instances(assignee_id, status);
```

### Monitoring

```python
# Add to settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/gzeams/workflows.log',
        },
    },
    'loggers': {
        'apps.workflows': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## Checklist

- [x] Install dependencies
- [x] Create migrations
- [x] Apply migrations
- [x] Verify tables created
- [x] Create superuser
- [x] Test Django admin
- [x] Test API endpoints
- [x] Load sample data
- [x] Update URL configuration
- [x] Configure settings
- [x] Run tests
- [ ] Configure CORS (if using frontend)
- [ ] Set up authentication
- [ ] Configure permissions
- [ ] Deploy to production

---

## Next Steps

1. **Frontend Integration**
   - Implement LogicFlow designer component
   - Connect to workflow API endpoints
   - Build task management interface

2. **Business Workflows**
   - Create procurement approval workflow
   - Create asset transfer workflow
   - Create inventory reconciliation workflow

3. **Testing**
   - Write comprehensive API tests
   - Perform integration testing
   - Load testing for concurrent workflows

4. **Documentation**
   - API documentation
   - User guide for workflow designers
   - Admin guide for workflow monitoring

---

**Migration Completed**: 2026-01-16
**Database Version**: PostgreSQL 15+
**Django Version**: 5.0+
**Python Version**: 3.11+
