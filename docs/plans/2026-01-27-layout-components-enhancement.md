# Layout Components Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement missing features for frontend common layout components (ColumnManager, DynamicTabs, SectionBlock) and add backend persistence layer for user preferences.

**Architecture:**
- Backend-first approach: Create models and services first to enable persistence
- Field-driven merge strategy: User > Role > Organization > Default (PageLayout)
- Incremental rollout: Enhance components one at a time to minimize breaking changes
- Backward compatibility: Support both `prop` and `field_code` during transition

**Tech Stack:**
- Backend: Django 5.0, DRF, PostgreSQL JSONB, Redis cache
- Frontend: Vue 3 Composition API, Element Plus, TypeScript

---

## Task 1: Add UserColumnPreference Model

**Files:**
- Modify: `backend/apps/system/models.py` (append after line 1527)

**Step 1: Write the failing test**

Create file: `backend/apps/system/tests/test_column_preference.py`

```python
import pytest
from django.core.exceptions import ValidationError
from apps.system.models import UserColumnPreference
from apps.accounts.models import User
from apps.organizations.models import Organization

@pytest.mark.django_db
class TestUserColumnPreference:
    def test_create_column_preference(self):
        """Test creating a user column preference"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        pref = UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={
                'columns': [
                    {'field_code': 'code', 'visible': True, 'width': 120},
                    {'field_code': 'name', 'visible': True, 'width': 200}
                ],
                'columnOrder': ['code', 'name']
            },
            config_name='default',
            is_default=True
        )

        assert pref.user == user
        assert pref.object_code == 'asset'
        assert pref.is_default is True

    def test_unique_constraint(self):
        """Test that user+object_code+config_name is unique"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={},
            config_name='default'
        )

        # Should raise error on duplicate
        with pytest.raises(ValidationError):
            pref2 = UserColumnPreference(
                user=user,
                object_code='asset',
                column_config={},
                config_name='default'
            )
            pref2.full_clean()

    def test_multiple_configs_per_user(self):
        """Test that user can have multiple configs for different objects"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={},
            config_name='default'
        )

        UserColumnPreference.objects.create(
            user=user,
            object_code='procurement',
            column_config={},
            config_name='default'
        )

        assert UserColumnPreference.objects.filter(user=user).count() == 2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && venv/Scripts/python.exe -m pytest apps/system/tests/test_column_preference.py -v`

Expected: `ImportError: cannot import name 'UserColumnPreference'`

**Step 3: Add the model to models.py**

Append to `backend/apps/system/models.py` (after line 1527, before the file ends):

```python
class UserColumnPreference(BaseModel):
    """
    User-level column display preferences.

    Stores user-specific column configurations for list views.
    Inherits from BaseModel for organization isolation and audit trails.
    """

    # === Association ===
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='column_preferences',
        db_comment='User who owns this preference'
    )

    # === Configuration Identifier ===
    object_code = models.CharField(
        max_length=50,
        db_index=True,
        db_comment='Business object code (e.g., asset, procurement_request)'
    )

    # === Configuration Data ===
    column_config = models.JSONField(
        default=dict,
        db_comment='Column configuration (JSON): {columns: [...], columnOrder: [...]}'
    )

    # === Metadata ===
    config_name = models.CharField(
        max_length=50,
        default='default',
        db_comment='Configuration name (allows multiple configs per object)'
    )
    is_default = models.BooleanField(
        default=True,
        db_comment='Is this the default configuration for this object'
    )

    class Meta:
        db_table = 'system_user_column_preference'
        verbose_name = 'User Column Preference'
        verbose_name_plural = 'User Column Preferences'
        unique_together = [['user', 'object_code', 'config_name']]
        indexes = [
            models.Index(fields=['user', 'object_code']),
            models.Index(fields=['user', 'object_code', 'is_default']),
        ]

    def __str__(self):
        return f"{self.user.username}.{self.object_code}.{self.config_name}"


class TabConfig(BaseModel):
    """
    Tab configuration for forms and detail pages.

    Stores tab layout settings with position, style, and behavior options.
    Inherits from BaseModel for organization isolation and audit trails.
    """

    # === Association ===
    business_object = models.ForeignKey(
        BusinessObject,
        on_delete=models.CASCADE,
        related_name='tab_configs',
        db_comment='Business object this config applies to'
    )

    # === Configuration Identifier ===
    name = models.CharField(
        max_length=50,
        db_comment='Configuration name (e.g., form_tabs, detail_tabs)'
    )

    # === Display Options ===
    position = models.CharField(
        max_length=10,
        choices=[
            ('top', 'Top'),
            ('left', 'Left'),
            ('right', 'Right'),
            ('bottom', 'Bottom')
        ],
        default='top',
        db_comment='Tab position'
    )
    type_style = models.CharField(
        max_length=20,
        choices=[
            ('', 'Default'),
            ('card', 'Card'),
            ('border-card', 'Border Card')
        ],
        default='',
        db_comment='Tab style type'
    )
    stretch = models.BooleanField(
        default=False,
        db_comment='Stretch tabs to fill width'
    )

    # === Behavior Options ===
    lazy = models.BooleanField(
        default=True,
        db_comment='Lazy load tab content'
    )
    animated = models.BooleanField(
        default=True,
        db_comment='Animated tab transitions'
    )
    addable = models.BooleanField(
        default=False,
        db_comment='Allow adding new tabs'
    )
    draggable = models.BooleanField(
        default=False,
        db_comment='Allow dragging to reorder tabs'
    )

    # === Tab Configuration ===
    tabs_config = models.JSONField(
        default=list,
        db_comment='Tab definitions: [{id, title, icon, closable, disabled, content, ...}]'
    )

    # === Status ===
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_comment='Is this configuration active'
    )

    class Meta:
        db_table = 'system_tab_config'
        verbose_name = 'Tab Configuration'
        verbose_name_plural = 'Tab Configurations'
        unique_together = [['business_object', 'name', 'organization']]
        indexes = [
            models.Index(fields=['business_object', 'name', 'is_active']),
        ]

    def __str__(self):
        return f"{self.business_object.code}.{self.name}"
```

**Step 4: Run test to verify it passes**

Run: `cd backend && venv/Scripts/python.exe -m pytest apps/system/tests/test_column_preference.py -v`

Expected: PASS

**Step 5: Create migration**

Run: `cd backend && venv/Scripts/python.exe manage.py makemigrations system`

Expected: Creates migration file with `000X_add_column_and_tab_preferences.py`

**Step 6: Run migration**

Run: `cd backend && venv/Scripts/python.exe manage.py migrate system`

Expected: `Running migrations: OK`

**Step 7: Commit**

```bash
git add backend/apps/system/models.py backend/apps/system/tests/test_column_preference.py backend/apps/system/migrations/
git commit -m "feat(system): add UserColumnPreference and TabConfig models"
```

---

## Task 2: Create ColumnConfigService

**Files:**
- Create: `backend/apps/system/services/__init__.py` (if not exists)
- Create: `backend/apps/system/services/column_config_service.py`

**Step 1: Write the failing test**

Create file: `backend/apps/system/tests/test_column_config_service.py`

```python
import pytest
from django.core.cache import cache
from apps.system.services.column_config_service import ColumnConfigService
from apps.system.models import UserColumnPreference, PageLayout, BusinessObject, FieldDefinition
from apps.accounts.models import User
from apps.organizations.models import Organization

@pytest.mark.django_db
class TestColumnConfigService:
    def test_get_column_config_returns_default_when_no_user_pref(self):
        """Test that default config is returned when user has no preference"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)
        bo = BusinessObject.objects.create(code='asset', name='Asset')

        # Create default layout
        PageLayout.objects.create(
            business_object=bo,
            layout_code='asset_list_default',
            layout_name='Asset List Default',
            layout_type='list',
            is_default=True,
            layout_config={
                'columns': [
                    {'field_code': 'code', 'label': '编号', 'width': 120, 'visible': True},
                    {'field_code': 'name', 'label': '名称', 'width': 200, 'visible': True}
                ]
            }
        )

        config = ColumnConfigService.get_column_config(user, 'asset')

        assert 'columns' in config
        assert len(config['columns']) == 2

    def test_get_column_config_merges_user_preferences(self):
        """Test that user config overrides default"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)
        bo = BusinessObject.objects.create(code='asset', name='Asset')

        # Create default layout
        PageLayout.objects.create(
            business_object=bo,
            layout_code='asset_list_default',
            layout_name='Asset List Default',
            layout_type='list',
            is_default=True,
            layout_config={
                'columns': [
                    {'field_code': 'code', 'label': '编号', 'width': 120, 'visible': True},
                    {'field_code': 'name', 'label': '名称', 'width': 200, 'visible': True}
                ]
            }
        )

        # Create user preference (hide 'code', change 'name' width)
        UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={
                'columns': [
                    {'field_code': 'code', 'visible': False},
                    {'field_code': 'name', 'width': 300}
                ]
            }
        )

        config = ColumnConfigService.get_column_config(user, 'asset')

        # User preference should override
        name_col = next(c for c in config['columns'] if c['field_code'] == 'name')
        assert name_col['width'] == 300
        code_col = next(c for c in config['columns'] if c['field_code'] == 'code')
        assert code_col['visible'] is False

    def test_save_user_config(self):
        """Test saving user configuration"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        config = {
            'columns': [
                {'field_code': 'code', 'width': 150}
            ]
        }

        pref = ColumnConfigService.save_user_config(user, 'asset', config)

        assert pref.user == user
        assert pref.object_code == 'asset'
        assert pref.column_config == config

    def test_reset_user_config(self):
        """Test resetting user configuration"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={'columns': []}
        )

        result = ColumnConfigService.reset_user_config(user, 'asset')

        assert result is True
        assert UserColumnPreference.objects.filter(user=user, object_code='asset').count() == 0
```

**Step 2: Run test to verify it fails**

Run: `cd backend && venv/Scripts/python.exe -m pytest apps/system/tests/test_column_config_service.py -v`

Expected: `ModuleNotFoundError: No module named 'apps.system.services.column_config_service'`

**Step 3: Create the service**

Create file: `backend/apps/system/services/column_config_service.py`:

```python
"""
Column configuration service with priority-based merging.

Priority: User > Role > Organization > Default (PageLayout)

This service provides:
- get_column_config(): Get merged column configuration
- save_user_config(): Save user configuration
- reset_user_config(): Reset to default
"""
from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from apps.system.models import UserColumnPreference, PageLayout, BusinessObject


class ColumnConfigService:
    """
    Column configuration service with priority-based merging.

    Cache strategy: Results are cached for 1 hour to reduce database queries.
    Cache invalidation: Automatically cleared when user config is saved/reset.
    """

    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def get_column_config(cls, user, object_code: str) -> Dict[str, Any]:
        """
        Get merged column configuration for a business object.

        Priority: User > Role > Organization > Default (PageLayout)

        Args:
            user: User instance
            object_code: Business object code (e.g., 'asset', 'procurement_request')

        Returns:
            Dict with merged column configuration:
            {
                'columns': [...],      # Merged column definitions
                'columnOrder': [...],   # Column display order
                'source': 'user' | 'default'  # Which config was used
            }
        """
        cache_key = f"column_config:{user.id}:{object_code}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. Get default config from PageLayout
        default_config = cls._get_default_config(object_code)

        # 2. Get user config
        user_config = cls._get_user_config(user, object_code)

        # 3. Merge configs (user overrides default)
        merged_config = cls._merge_configs(default_config, user_config)

        # Determine source for response
        merged_config['source'] = 'user' if user_config else 'default'

        # Cache result
        cache.set(cache_key, merged_config, cls.CACHE_TIMEOUT)

        return merged_config

    @classmethod
    def _get_default_config(cls, object_code: str) -> Dict[str, Any]:
        """Get default configuration from PageLayout."""
        try:
            # Get business object (use all_objects to include global)
            business_object = BusinessObject.all_objects.get(
                code=object_code,
                is_deleted=False
            )

            # Get default list layout
            layout = PageLayout.objects.filter(
                business_object=business_object,
                layout_type='list',
                is_default=True,
                is_active=True,
                is_deleted=False
            ).first()

            if layout:
                config = layout.layout_config or {}
                # Ensure columns key exists
                if 'columns' not in config:
                    config['columns'] = cls._get_columns_from_field_definitions(business_object)
                return config

            # Fallback to field definitions
            return {
                'columns': cls._get_columns_from_field_definitions(business_object)
            }

        except ObjectDoesNotExist:
            # No business object found, return empty config
            return {'columns': [], 'columnOrder': []}

    @classmethod
    def _get_columns_from_field_definitions(cls, business_object: BusinessObject) -> List[Dict]:
        """Generate column config from FieldDefinition or ModelFieldDefinition."""
        columns = []

        # Try FieldDefinition first (for low-code objects)
        if not business_object.is_hardcoded:
            field_defs = business_object.field_definitions.filter(
                show_in_list=True,
                is_deleted=False
            ).order_by('sort_order')

            for field in field_defs:
                columns.append({
                    'field_code': field.code,
                    'label': field.name,
                    'width': field.column_width,
                    'fixed': field.fixed or None,
                    'sortable': field.sortable,
                    'visible': True
                })
        else:
            # For hardcoded objects, use ModelFieldDefinition
            field_defs = business_object.model_fields.filter(
                show_in_list=True
            ).order_by('sort_order')

            for field in field_defs:
                columns.append({
                    'field_code': field.field_name,
                    'label': field.display_name,
                    'width': None,
                    'fixed': None,
                    'sortable': True,
                    'visible': True
                })

        return columns

    @classmethod
    def _get_user_config(cls, user, object_code: str) -> Dict[str, Any]:
        """Get user configuration."""
        try:
            pref = UserColumnPreference.objects.get(
                user=user,
                object_code=object_code,
                is_default=True
            )
            return pref.column_config
        except ObjectDoesNotExist:
            return {}

    @classmethod
    def _merge_configs(cls, default: Dict, user: Dict) -> Dict[str, Any]:
        """
        Merge configurations with user preference taking priority.

        Merge strategy:
        - User columns override default columns by field_code
        - User columnOrder overrides default
        - Default values used for missing user values
        """
        result = default.copy()

        # Build default column map for quick lookup
        default_columns = {col.get('field_code') or col.get('prop'): col for col in default.get('columns', [])}

        # Build user column map
        user_columns = {col.get('field_code') or col.get('prop'): col for col in user.get('columns', [])}

        # Merge columns: user overrides default for matching field_code
        merged_columns = []
        user_column_order = user.get('columnOrder', [])

        # Use user's order if specified, otherwise use default
        if user_column_order:
            for field_code in user_column_order:
                if field_code in user_columns:
                    merged_columns.append({**default_columns.get(field_code, {}), **user_columns[field_code]})
                elif field_code in default_columns:
                    merged_columns.append(default_columns[field_code])
        else:
            # Use default order, apply user overrides
            for field_code, col in default_columns.items():
                if field_code in user_columns:
                    merged_columns.append({**col, **user_columns[field_code]})
                else:
                    merged_columns.append(col)

        result['columns'] = merged_columns
        result['columnOrder'] = user_column_order or default.get('columnOrder', [])

        return result

    @classmethod
    def save_user_config(cls, user, object_code: str, config: Dict) -> UserColumnPreference:
        """
        Save user column configuration.

        Args:
            user: User instance
            object_code: Business object code
            config: Column configuration to save

        Returns:
            UserColumnPreference instance
        """
        pref, created = UserColumnPreference.objects.get_or_create(
            user=user,
            object_code=object_code,
            config_name='default',
            defaults={'column_config': config}
        )

        if not created:
            pref.column_config = config
            pref.save()

        # Clear cache
        cache_key = f"column_config:{user.id}:{object_code}"
        cache.delete(cache_key)

        return pref

    @classmethod
    def reset_user_config(cls, user, object_code: str) -> bool:
        """
        Reset user configuration to default.

        Args:
            user: User instance
            object_code: Business object code

        Returns:
            True if successful, False otherwise
        """
        try:
            UserColumnPreference.objects.filter(
                user=user,
                object_code=object_code
            ).delete()

            # Clear cache
            cache_key = f"column_config:{user.id}:{object_code}"
            cache.delete(cache_key)

            return True
        except Exception:
            return False
```

**Step 4: Run test to verify it passes**

Run: `cd backend && venv/Scripts/python.exe -m pytest apps/system/tests/test_column_config_service.py -v`

Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add backend/apps/system/services/column_config_service.py backend/apps/system/tests/test_column_config_service.py
git commit -m "feat(system): add ColumnConfigService with priority-based merging"
```

---

## Task 3: Create Serializers for New Models

**Files:**
- Modify: `backend/apps/system/serializers.py`

**Step 1: Write the failing test**

Create file: `backend/apps/system/tests/test_column_preference_serializers.py`

```python
import pytest
from apps.system.serializers import UserColumnPreferenceSerializer, TabConfigSerializer
from apps.system.models import UserColumnPreference, TabConfig, BusinessObject
from apps.accounts.models import User
from apps.organizations.models import Organization

@pytest.mark.django_db
class TestColumnPreferenceSerializers:
    def test_serialize_user_column_preference(self):
        """Test serializing user column preference"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        pref = UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={
                'columns': [
                    {'field_code': 'code', 'width': 120, 'visible': True}
                ]
            }
        )

        serializer = UserColumnPreferenceSerializer(pref)
        data = serializer.data

        assert data['object_code'] == 'asset'
        assert 'columns' in data['column_config']
        assert data['user'] == str(user.id)

    def test_deserialize_and_create(self):
        """Test deserializing and creating preference"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        data = {
            'user': str(user.id),
            'object_code': 'asset',
            'column_config': {'columns': []},
            'config_name': 'default'
        }

        serializer = UserColumnPreferenceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        pref = serializer.save()

        assert pref.object_code == 'asset'
        assert pref.user == user


@pytest.mark.django_db
class TestTabConfigSerializers:
    def test_serialize_tab_config(self):
        """Test serializing tab configuration"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        bo = BusinessObject.objects.create(
            code='asset',
            name='Asset',
            organization=org
        )

        tab_config = TabConfig.objects.create(
            business_object=bo,
            name='form_tabs',
            position='top',
            tabs_config=[
                {'id': 'basic', 'title': 'Basic Info', 'content': []}
            ],
            organization=org
        )

        serializer = TabConfigSerializer(tab_config)
        data = serializer.data

        assert data['name'] == 'form_tabs'
        assert data['position'] == 'top'
        assert len(data['tabs_config']) == 1
```

**Step 2: Run test to verify it fails**

Run: `cd backend && venv/Scripts/python.exe -m pytest apps/system/tests/test_column_preference_serializers.py -v`

Expected: `ImportError: cannot import name 'UserColumnPreferenceSerializer'`

**Step 3: Add serializers to serializers.py**

Read current `backend/apps/system/serializers.py` and append at the end (before the file ends):

```python
# === Column Preference Serializers ===

class UserColumnPreferenceSerializer(BaseModelSerializer):
    """Serializer for UserColumnPreference model."""

    user_display = serializers.CharField(source='user.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = UserColumnPreference
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'user_display',
            'object_code',
            'column_config',
            'config_name',
            'is_default'
        ]
        extra_kwargs = {
            'user': {'required': False}  # Set from context in viewset
        }


# === Tab Config Serializers ===

class TabConfigSerializer(BaseModelSerializer):
    """Serializer for TabConfig model."""

    business_object_code = serializers.CharField(source='business_object.code', read_only=True)
    business_object_name = serializers.CharField(source='business_object.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = TabConfig
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'business_object_code',
            'business_object_name',
            'name',
            'position',
            'type_style',
            'stretch',
            'lazy',
            'animated',
            'addable',
            'draggable',
            'tabs_config',
            'is_active'
        ]


class TabConfigDetailSerializer(TabConfigSerializer):
    """Detailed serializer with nested business object info."""

    business_object = BusinessObjectSerializer(read_only=True)

    class Meta(TabConfigSerializer.Meta):
        fields = TabConfigSerializer.Meta.fields
```

**Step 4: Update imports in serializers.py**

At the top of `backend/apps/system/serializers.py`, add to the imports:

```python
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    # ... existing imports ...
    UserColumnPreference,
    TabConfig,
)
```

**Step 5: Run test to verify it passes**

Run: `cd backend && venv/Scripts/python.exe -m pytest apps/system/tests/test_column_preference_serializers.py -v`

Expected: PASS (all 4 tests)

**Step 6: Commit**

```bash
git add backend/apps/system/serializers.py backend/apps/system/tests/test_column_preference_serializers.py
git commit -m "feat(system): add serializers for UserColumnPreference and TabConfig"
```

---

## Task 4: Create ColumnPreference ViewSet

**Files:**
- Modify: `backend/apps/system/viewsets/__init__.py`
- Create: `backend/apps/system/viewsets/column_preference.py`

**Step 1: Write the failing test**

Create file: `backend/apps/system/tests/test_column_preference_viewsets.py`

```python
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.system.models import UserColumnPreference, BusinessObject, PageLayout
from apps.accounts.models import User
from apps.organizations.models import Organization

@pytest.mark.django_db
class TestColumnPreferenceViewSet:
    def setup_method(self):
        self.client = APIClient()
        org = Organization.objects.create(name='Test Org', code='test-org')
        self.user = User.objects.create(username='testuser', organization=org)
        self.client.force_authenticate(user=self.user)

    def test_get_config_returns_default(self):
        """Test GET /api/system/column-config/{object_code}/ returns default config"""
        bo = BusinessObject.objects.create(code='asset', name='Asset')
        PageLayout.objects.create(
            business_object=bo,
            layout_code='asset_list_default',
            layout_name='Asset List',
            layout_type='list',
            is_default=True,
            layout_config={'columns': []}
        )

        url = reverse('system-columnpreference-get-config', kwargs={'object_code': 'asset'})
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data['success'] is True
        assert 'columns' in response.data['data']

    def test_save_config(self):
        """Test POST /api/system/column-config/{object_code}/save/ saves user config"""
        url = reverse('system-columnpreference-save-config', kwargs={'object_code': 'asset'})
        data = {
            'column_config': {
                'columns': [
                    {'field_code': 'code', 'width': 150}
                ]
            }
        }

        response = self.client.post(url, data)

        assert response.status_code == 200
        assert response.data['success'] is True
        assert UserColumnPreference.objects.filter(user=self.user).count() == 1

    def test_reset_config(self):
        """Test POST /api/system/column-config/{object_code}/reset/ deletes user config"""
        UserColumnPreference.objects.create(
            user=self.user,
            object_code='asset',
            column_config={'columns': []}
        )

        url = reverse('system-columnpreference-reset-config', kwargs={'object_code': 'asset'})
        response = self.client.post(url)

        assert response.status_code == 200
        assert response.data['success'] is True
        assert UserColumnPreference.objects.filter(user=self.user, object_code='asset').count() == 0
```

**Step 2: Run test to verify it fails**

Run: `cd backend && venv/Scripts/python.exe -m pytest apps/system/tests/test_column_preference_viewsets.py -v`

Expected: `NoReverseMatch: 'system-columnpreference-get-config'`

**Step 3: Create the ViewSet**

Create file: `backend/apps/system/viewsets/column_preference.py`:

```python
"""
ViewSets for column preference management.

Provides endpoints for:
- Get merged column configuration (default + user preferences)
- Save user column preferences
- Reset to default configuration
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.responses.base import BaseResponse
from apps.system.models import UserColumnPreference
from apps.system.serializers import UserColumnPreferenceSerializer
from apps.system.services.column_config_service import ColumnConfigService


class UserColumnPreferenceViewSet(BaseModelViewSet):
    """
    User Column Preference ViewSet.

    Provides custom actions for column configuration management.
    Standard CRUD actions are also available.
    """

    queryset = UserColumnPreference.objects.all()
    serializer_class = UserColumnPreferenceSerializer

    def get_queryset(self):
        """Filter to current user's preferences only."""
        return UserColumnPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user from request context."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path=r'(?P<object_code>[^/.]+)')
    def get_config(self, request, object_code=None):
        """
        Get merged column configuration for an object.

        GET /api/system/column-config/{object_code}/

        Returns merged configuration from:
        1. Default (PageLayout)
        2. User preferences (overrides default)

        Response:
        {
            "success": true,
            "data": {
                "columns": [...],
                "columnOrder": [...],
                "source": "user" | "default"
            }
        }
        """
        config = ColumnConfigService.get_column_config(
            request.user,
            object_code
        )
        return Response(BaseResponse.success(data=config))

    @action(detail=False, methods=['post'], url_path=r'(?P<object_code>[^/.]+)/save')
    def save_config(self, request, object_code=None):
        """
        Save user column configuration.

        POST /api/system/column-config/{object_code}/save/
        Body: {"column_config": {...}}

        Response:
        {
            "success": true,
            "data": {...preference...},
            "message": "Configuration saved successfully"
        }
        """
        column_config = request.data.get('column_config', {})

        pref = ColumnConfigService.save_user_config(
            request.user,
            object_code,
            column_config
        )

        serializer = UserColumnPreferenceSerializer(pref)
        return Response(BaseResponse.success(
            data=serializer.data,
            message='Configuration saved successfully'
        ))

    @action(detail=False, methods=['post'], url_path=r'(?P<object_code>[^/.]+)/reset')
    def reset_config(self, request, object_code=None):
        """
        Reset column configuration to default.

        POST /api/system/column-config/{object_code}/reset/

        Deletes user preferences for this object.

        Response:
        {
            "success": true,
            "message": "Configuration reset to default"
        }
        """
        success = ColumnConfigService.reset_user_config(
            request.user,
            object_code
        )

        if success:
            return Response(BaseResponse.success(message='Configuration reset to default'))
        else:
            return Response(BaseResponse.error(message='Reset failed'))
```

**Step 4: Update viewsets/__init__.py**

Add to imports and register:

```python
from .column_preference import UserColumnPreferenceViewSet
```

**Step 5: Register URLs in urls.py**

Read `backend/apps/system/urls.py` and add the route:

```python
router.register(r'column-config', viewsets.UserColumnPreferenceViewSet, basename='columnpreference')
```

**Step 6: Run test to verify it passes**

Run: `cd backend && venv/Scripts/python.exe -m pytest apps/system/tests/test_column_preference_viewsets.py -v`

Expected: PASS (all 3 tests)

**Step 7: Commit**

```bash
git add backend/apps/system/viewsets/column_preference.py backend/apps/system/viewsets/__init__.py backend/apps/system/urls.py backend/apps/system/tests/test_column_preference_viewsets.py
git commit -m "feat(system): add UserColumnPreferenceViewSet with get/save/reset endpoints"
```

---

## Task 5: Create Frontend API Service

**Files:**
- Modify: `frontend/src/api/system.ts`

**Step 1: Create the API functions**

Read `frontend/src/api/system.ts` and add these exports:

```typescript
import request from '@/utils/request'

/**
 * Column Configuration API
 */
export const columnConfigApi = {
  /**
   * Get merged column configuration for object
   * GET /api/system/column-config/{objectCode}/
   */
  get: (objectCode: string) =>
    request.get<{ success: boolean; data: ColumnConfig }>(
      `/system/column-config/${objectCode}/`
    ),

  /**
   * Save user column configuration
   * POST /api/system/column-config/{objectCode}/save/
   */
  save: (objectCode: string, config: ColumnConfig) =>
    request.post(`/system/column-config/${objectCode}/save/`, {
      column_config: config
    }),

  /**
   * Reset column configuration to default
   * POST /api/system/column-config/{objectCode}/reset/
   */
  reset: (objectCode: string) =>
    request.post(`/system/column-config/${objectCode}/reset/`)
}

/**
 * Tab Configuration API
 */
export const tabConfigApi = {
  /**
   * Get tab configuration for business object
   * GET /api/system/tab-config/{businessObject}/{name}/
   */
  get: (businessObject: string, name: string = 'form_tabs') =>
    request.get(`/system/tab-config/${businessObject}/${name}/`),

  /**
   * Save tab configuration
   * POST /api/system/tab-config/
   */
  save: (config: TabConfig) =>
    request.post('/system/tab-config/', config),

  /**
   * Update tab configuration
   * PUT /api/system/tab-config/{id}/
   */
  update: (id: string, config: Partial<TabConfig>) =>
    request.put(`/system/tab-config/${id}/`, config)
}

// Type definitions
export interface ColumnItem {
  field_code: string
  label: string
  width?: number
  fixed?: 'left' | 'right' | null
  sortable?: boolean
  visible?: boolean
  required_in_list?: boolean
  label_override?: string
}

export interface ColumnConfig {
  columns: ColumnItem[]
  columnOrder?: string[]
  source?: 'user' | 'default'
}

export interface TabItem {
  id: string
  title: string
  icon?: string
  closable?: boolean
  disabled?: boolean
  content?: any[]
  badge?: string | number
  permission?: string
}

export interface TabConfig {
  business_object?: string
  name: string
  position?: 'top' | 'left' | 'right' | 'bottom'
  type_style?: '' | 'card' | 'border-card'
  stretch?: boolean
  lazy?: boolean
  animated?: boolean
  addable?: boolean
  draggable?: boolean
  tabs_config: TabItem[]
  is_active?: boolean
}
```

**Step 2: Export from index**

Update `frontend/src/api/index.ts` or ensure the exports are available.

**Step 3: Commit**

```bash
git add frontend/src/api/system.ts
git commit -m "feat(frontend): add columnConfigApi and tabConfigApi"
```

---

## Task 6: Enhance ColumnManager Component

**Files:**
- Modify: `frontend/src/components/common/ColumnManager.vue`

**Step 1: Add props and types**

Replace the Props interface to add PRD-compliant fields:

```typescript
interface ColumnItem {
  field_code: string        // PRD standard (snake_case)
  prop?: string             // Legacy support (camelCase)
  label: string
  label_override?: string   // NEW: Custom label support
  width?: number
  defaultWidth?: number
  fixed?: 'left' | 'right' | '' | null
  sortable?: boolean
  visible?: boolean
  defaultVisible?: boolean
  required_in_list?: boolean  // NEW: Prevent hiding
  field_type?: string         // NEW: For type badge
}

interface Props {
  columns: ColumnItem[]
  objectCode?: string
  modelValue?: ColumnItem[]
}
```

**Step 2: Add computed helper for field code**

Add after the internalColumns ref:

```typescript
// Helper to get field_code with backward compatibility
const getFieldCode = (col: ColumnItem): string => {
  return col.field_code || col.prop || ''
}

// Helper to check if column is required (cannot be hidden)
const isRequired = (col: ColumnItem): boolean => {
  return col.required_in_list === true
}
```

**Step 3: Update template to show missing features**

Replace the column-item template section:

```vue
<div
  v-for="(col, index) in internalColumns"
  :key="getFieldCode(col)"
  class="column-item"
  :class="{
    'column-item-dragging': draggingIndex === index,
    'column-item-required': isRequired(col)
  }"
  draggable="true"
  @dragstart="handleDragStart(index, $event)"
  @dragover="handleDragOver(index, $event)"
  @dragend="handleDragEnd"
  @drop="handleDrop(index, $event)"
>
  <div class="column-item-main">
    <el-icon class="drag-handle" :size="16">
      <DCaret />
    </el-icon>

    <!-- Field type badge -->
    <span v-if="col.field_type" class="field-type-badge">
      {{ getFieldTypeLabel(col.field_type) }}
    </span>

    <el-checkbox
      :model-value="col.visible !== false"
      :disabled="isRequired(col)"
      @update:model-value="(val: boolean) => handleToggleVisibility(col, val)"
    >
      <span
        class="column-label"
        :title="col.label_override ? col.label : ''"
      >
        {{ col.label_override || col.label }}
      </span>
      <el-tooltip
        v-if="col.label_override"
        content="Original: " + col.label
        placement="top"
      >
        <el-icon class="override-icon"><InfoFilled /></el-icon>
      </el-tooltip>
    </el-checkbox>

    <div class="column-actions">
      <!-- Column fixed selector -->
      <el-select
        :model-value="col.fixed || ''"
        size="small"
        style="width: 80px"
        @update:model-value="(val) => handleFixedChange(col, val)"
      >
        <el-option label="None" value="" />
        <el-option label="Left" value="left" />
        <el-option label="Right" value="right" />
      </el-select>

      <el-input-number
        :model-value="col.width || col.defaultWidth || 120"
        :min="50"
        :max="500"
        :step="10"
        size="small"
        controls-position="right"
        style="width: 90px"
        @update:model-value="(val: number) => handleWidthChange(col, val)"
      />
    </div>
  </div>
</div>
```

**Step 4: Add handlers for new features**

Add to script setup:

```typescript
import { InfoFilled } from '@element-plus/icons-vue'

// Field type mapping for badges
const getFieldTypeLabel = (type: string): string => {
  const typeMap: Record<string, string> = {
    text: 'T',
    number: '#',
    date: 'D',
    datetime: 'DT',
    boolean: 'B',
    select: 'S',
    user: 'U',
    reference: 'R'
  }
  return typeMap[type] || type[0]?.toUpperCase() || ''
}

// Handle column fixed change
const handleFixedChange = (col: ColumnItem, value: string) => {
  col.fixed = value as 'left' | 'right' | '' | null
  emitChanges()
}
```

**Step 5: Update styles**

Add to scoped styles:

```css
.field-type-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  font-size: 10px;
  background: var(--el-color-info-light-9);
  color: var(--el-color-info);
  border-radius: 2px;
  margin-right: 4px;
}

.column-item-required {
  background: var(--el-color-warning-light-9);
  border-color: var(--el-color-warning-light-5);
}

.override-icon {
  margin-left: 4px;
  font-size: 12px;
  color: var(--el-color-info);
  cursor: help;
}
```

**Step 6: Commit**

```bash
git add frontend/src/components/common/ColumnManager.vue
git commit -m "feat(ColumnManager): add field_code, label_override, fixed, type badge, required"
```

---

## Task 7: Enhance DynamicTabs Component

**Files:**
- Modify: `frontend/src/components/common/DynamicTabs.vue`

**Step 1: Add all PRD props and types**

Replace the script setup section:

```typescript
<script setup lang="ts">
import { ref, computed, watch } from 'vue'

export interface TabItem {
  id: string
  title: string
  icon?: string
  closable?: boolean
  disabled?: boolean
  badge?: string | number
  permission?: string
  visible?: boolean
  lazy?: boolean
  content?: any
  component?: any
  props?: Record<string, any>
}

interface Props {
  modelValue: string
  tabs: TabItem[]
  position?: 'top' | 'left' | 'right' | 'bottom'  // NEW
  typeStyle?: '' | 'card' | 'border-card'          // NEW
  stretch?: boolean                                 // NEW
  animated?: boolean                                // NEW
  addable?: boolean                                 // NEW
  editable?: boolean                                // NEW
  draggable?: boolean                               // NEW
  tabPosition?: 'top' | 'left' | 'right' | 'bottom' // Alias for position
}

const props = withDefaults(defineProps<Props>(), {
  position: 'top',
  typeStyle: 'card',
  stretch: false,
  animated: true,
  addable: false,
  editable: false,
  draggable: false
})

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'remove', name: string): void
  (e: 'add'): void
  (e: 'tab-click', tab: TabItem): void
  (e: 'tab-change', name: string): void
}

const emit = defineEmits<Emits>()

const activeTab = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit('update:modelValue', val)
    emit('tab-change', val)
  }
})

// Filter visible tabs
const visibleTabs = computed(() => {
  return props.tabs.filter(tab => tab.visible !== false)
})

const removeTab = (targetName: string) => {
  emit('remove', targetName)
}

const handleTabClick = (tab: any) => {
  const tabItem = props.tabs.find(t => t.id === tab.paneName || t.name === tab.paneName)
  if (tabItem) {
    emit('tab-click', tabItem)
  }
}

const handleAdd = () => {
  emit('add')
}
</script>
```

**Step 2: Update template with new features**

Replace the template section:

```vue
<template>
  <el-tabs
    v-model="activeTab"
    :position="position"
    :type="typeStyle"
    :stretch="stretch"
    :closable="true"
    :addable="addable"
    :editable="editable"
    @tab-remove="removeTab"
    @tab-click="handleTabClick"
    @tab-add="handleAdd"
  >
    <el-tab-pane
      v-for="item in visibleTabs"
      :key="item.id"
      :label="renderTabLabel(item)"
      :name="item.id"
      :disabled="item.disabled"
      :lazy="item.lazy ?? props.animated"
    >
      <template #label>
        <span class="tab-label">
          <el-icon v-if="item.icon" class="tab-icon">
            <component :is="item.icon" />
          </el-icon>
          <span>{{ item.title }}</span>
          <el-badge
            v-if="item.badge"
            :value="item.badge"
            :type="typeof item.badge === 'number' && item.badge > 0 ? 'danger' : 'info'"
            class="tab-badge"
          />
        </span>
      </template>

      <component
        :is="item.component"
        v-bind="item.props"
        v-if="item.content"
      >
        <template v-for="(slot, name) in item.slots" #[name]="slot">
          <component :is="slot" />
        </template>
      </component>

      <slot v-else :name="item.id" :tab="item" />
    </el-tab-pane>
  </el-tabs>
</template>
```

**Step 3: Add render helper**

Add to script setup:

```typescript
const renderTabLabel = (item: TabItem) => {
  // Return the label as-is, Element Plus will render it
  return item.title
}
```

**Step 4: Add styles**

Add scoped styles:

```css
.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tab-icon {
  font-size: 14px;
}

.tab-badge {
  margin-left: 4px;
}
```

**Step 5: Commit**

```bash
git add frontend/src/components/common/DynamicTabs.vue
git commit -m "feat(DynamicTabs): add position, typeStyle, stretch, animated, badge, icon, addable"
```

---

## Task 8: Enhance SectionBlock Component

**Files:**
- Modify: `frontend/src/components/common/SectionBlock.vue`

**Step 1: Add props for missing features**

Replace the Props interface:

```typescript
interface Props {
  title: string
  description?: string    // NEW: Section description
  collapsed?: boolean
  columns?: 1 | 2 | 3 | 4  // NEW: Multi-column grid layout
  border?: boolean        // NEW: Show/hide border
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
  columns: 1,
  border: true
})
```

**Step 2: Update template**

Replace the template:

```vue
<template>
  <div
    class="section-block"
    :class="{
      'no-border': !border,
      [`columns-${columns}`]: columns > 1
    }"
  >
    <div
      class="section-header"
      @click="toggle"
    >
      <div class="title">
        <el-icon :class="{ 'is-collapsed': isCollapsed }">
          <ArrowDown />
        </el-icon>
        <span class="text">{{ title }}</span>
      </div>
      <div class="actions">
        <slot name="actions" />
      </div>
    </div>

    <el-collapse-transition>
      <div
        v-show="!isCollapsed"
        class="section-body"
      >
        <p v-if="description" class="section-description">
          {{ description }}
        </p>
        <div class="section-content" :class="`grid-${columns}`">
          <slot />
        </div>
      </div>
    </el-collapse-transition>
  </div>
</template>
```

**Step 3: Update styles**

Replace the styles:

```css
<style scoped>
.section-block {
  margin-bottom: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.section-block.no-border {
  border: none;
}

.section-header {
  padding: 10px 15px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.no-border .section-header {
  border-radius: 4px;
}

.title {
  display: flex;
  align-items: center;
  font-weight: bold;
}

.text {
  margin-left: 5px;
}

.is-collapsed {
  transform: rotate(-90deg);
}

.section-body {
  padding: 15px;
}

.section-description {
  margin: 0 0 12px 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.section-content {
  display: grid;
  gap: 16px;
}

.grid-1 {
  grid-template-columns: repeat(1, 1fr);
}

.grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.grid-3 {
  grid-template-columns: repeat(3, 1fr);
}

.grid-4 {
  grid-template-columns: repeat(4, 1fr);
}

@media (max-width: 768px) {
  .grid-2, .grid-3, .grid-4 {
    grid-template-columns: 1fr;
  }
}
</style>
```

**Step 4: Commit**

```bash
git add frontend/src/components/common/SectionBlock.vue
git commit -m "feat(SectionBlock): add description, columns grid layout, border option"
```

---

## Task 9: Update Types and Exports

**Files:**
- Modify: `frontend/src/types/common.ts`
- Modify: `frontend/src/components/common/index.ts`

**Step 1: Add common type exports**

Update `frontend/src/types/common.ts`:

```typescript
// Common layout component types

export interface FieldReference {
  field_code: string
  label_override?: string
  help_text_override?: string
}

export interface VisibilityRule {
  logic?: 'and' | 'or'
  conditions: Array<{
    field_code: string
    operator: 'eq' | 'neq' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'not_in' | 'contains' | 'empty' | 'not_empty'
    value?: any
  }>
}

export interface SectionConfig {
  id: string
  title: string
  description?: string
  collapsible?: boolean
  default_collapsed?: boolean
  columns?: 1 | 2 | 3 | 4
  items: Array<FieldReference | SectionConfig>
  visibility_rules?: VisibilityRule[]
}

export interface TabConfig {
  id: string
  title: string
  icon?: string
  closable?: boolean
  disabled?: boolean
  badge?: string | number
  permission?: string
  visible?: boolean
  lazy?: boolean
  content: SectionConfig[]
  visibility_rules?: VisibilityRule[]
}

export interface ActionConfig {
  key: string
  label: string
  type: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default' | 'text'
  icon?: string
  permission?: string
  confirm_message?: string
  web_action?: {
    target: 'api' | 'route' | 'modal' | 'download'
    uri: string
  }
}

// Column configuration types
export interface ColumnItem {
  field_code: string
  prop?: string  // Legacy support
  label: string
  label_override?: string
  width?: number
  defaultWidth?: number
  fixed?: 'left' | 'right' | '' | null
  sortable?: boolean
  visible?: boolean
  defaultVisible?: boolean
  required_in_list?: boolean
  field_type?: string
}

export interface ColumnConfig {
  columns: ColumnItem[]
  columnOrder?: string[]
  source?: 'user' | 'default'
}
```

**Step 2: Update component exports**

Update `frontend/src/components/common/index.ts`:

```typescript
export { default as ColumnManager } from './ColumnManager.vue'
export { default as DynamicTabs } from './DynamicTabs.vue'
export { default as SectionBlock } from './SectionBlock.vue'
export { default as BaseListPage } from './BaseListPage.vue'
export { default as BaseDetailPage } from './BaseDetailPage.vue'
// ... other exports
```

**Step 3: Commit**

```bash
git add frontend/src/types/common.ts frontend/src/components/common/index.ts
git commit -m "feat(types): add common layout type definitions"
```

---

## Task 10: Integration Testing

**Files:**
- Create: `frontend/e2e/layout-components.spec.ts`

**Step 1: Write E2E test**

Create file: `frontend/e2e/layout-components.spec.ts`:

```typescript
import { test, expect } from '@playwright/test'

test.describe('Layout Components Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:5173/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard')
  })

  test('ColumnManager saves and loads user preferences', async ({ page }) => {
    await page.goto('http://localhost:5173/assets')

    // Open column manager
    await page.click('[data-testid="column-settings-button"]')

    // Wait for popover
    await page.waitForSelector('.column-manager')

    // Change column width
    await page.fill('.column-item:first-child input[type="number"]', '200')

    // Save configuration
    await page.click('button:has-text("Save")')

    // Wait for success message
    await page.waitForSelector('.el-message--success')

    // Refresh page
    await page.reload()

    // Open column manager again
    await page.click('[data-testid="column-settings-button"]')

    // Verify width was saved
    const widthInput = await page.inputValue('.column-item:first-child input[type="number"]')
    expect(widthInput).toBe('200')
  })

  test('DynamicTabs renders with all features', async ({ page }) => {
    await page.goto('http://localhost:5173/assets/create')

    // Check tabs are rendered
    await expect(page.locator('.el-tabs__item').first()).toBeVisible()

    // Check active tab
    const activeTab = page.locator('.el-tabs__item.is-active')
    await expect(activeTab).toBeVisible()

    // Click a different tab
    await page.locator('.el-tabs__item').nth(1).click()

    // Verify tab changed
    await expect(page.locator('.el-tabs__item.is-active')).toHaveText(/Basic|Details/)
  })

  test('SectionBlock collapses and expands', async ({ page }) => {
    await page.goto('http://localhost:5173/assets/create')

    // Find first section block
    const section = page.locator('.section-block').first()

    // Click header to collapse
    await section.locator('.section-header').click()

    // Verify content is hidden
    await expect(section.locator('.section-body')).not.toBeVisible()

    // Click again to expand
    await section.locator('.section-header').click()

    // Verify content is visible
    await expect(section.locator('.section-body')).toBeVisible()
  })

  test('SectionBlock multi-column layout', async ({ page }) => {
    await page.goto('http://localhost:5173/assets/create')

    // Find a section with columns=2
    const section = page.locator('.section-block.columns-2')

    if (await section.count() > 0) {
      // Verify grid layout
      const grid = section.locator('.section-content.grid-2')
      await expect(grid).toHaveCSS('grid-template-columns', /repeat\(2/)
    }
  })
})
```

**Step 2: Run E2E test**

Run: `cd frontend && npx playwright test layout-components.spec.ts`

Expected: All tests pass

**Step 3: Commit**

```bash
git add frontend/e2e/layout-components.spec.ts
git commit -m "test(e2e): add integration tests for layout components"
```

---

## Execution Checklist

After completing all tasks, verify:

- [ ] All backend models have migrations applied
- [ ] All API endpoints return correct response format
- [ ] Frontend components render without errors
- [ ] ColumnManager persists user preferences
- [ ] DynamicTabs supports position, lazy loading, badges
- [ ] SectionBlock supports multi-column layout
- [ ] E2E tests pass
- [ ] No console errors in browser

---

## Estimated Total Time

| Phase | Tasks | Time |
|-------|-------|------|
| Backend Models | Tasks 1-3 | 2 hours |
| Backend APIs | Task 4 | 1 hour |
| Frontend API | Task 5 | 30 min |
| ColumnManager | Task 6 | 1 hour |
| DynamicTabs | Task 7 | 1 hour |
| SectionBlock | Task 8 | 30 min |
| Types & Exports | Task 9 | 30 min |
| Testing | Task 10 | 1 hour |
| **Total** | | **7-8 hours** |
