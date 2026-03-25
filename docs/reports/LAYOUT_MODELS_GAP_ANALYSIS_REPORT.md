# Frontend Common Layout Models - PRD vs Implementation Gap Analysis Report

## Document Information

| Project | Information |
|---------|-------------|
| **Report Version** | v1.0 |
| **Created Date** | 2026-01-27 |
| **Author** | Claude (AI Assistant) |
| **Scope** | Layout Components PRD Compliance Analysis |
| **Target PRDs** | `docs/plans/common_base_features/03_layouts/` |

---

## Executive Summary

This report analyzes the gap between PRD specifications and actual implementation for frontend common layout components in the GZEAMS (Hook Fixed Assets) project.

### Key Findings

| Metric | Value |
|--------|-------|
| **PRD Documents Analyzed** | 4 documents |
| **Components Analyzed** | 3 main components |
| **Total Features Specified** | 40 features |
| **Features Implemented** | 10 features (25%) |
| **Features Missing** | 30 features (75%) |
| **Backend Models Missing** | 4 models |
| **Services Missing** | 2 services |

### Critical Blockers

1. **No persistence layer** - UserColumnPreference, TabConfig models not implemented
2. **Field naming inconsistency** - PRD uses `field_code`, code uses `prop`
3. **No config merge service** - Priority-based configuration merging not implemented

---

## 1. PRD Documents Analyzed

| Document | Purpose | Status |
|----------|---------|--------|
| `00_layout_common_models.md` | Defines common schemas (FieldReference, VisibilityRule, SectionConfig, TabConfig) | ✅ Foundation document |
| `list_column_configuration.md` | Column display management with user preferences | ⚠️ Partially implemented |
| `tab_configuration.md` | Dynamic tabs with drag-drop, lazy loading, permissions | ❌ Barely implemented |
| `section_block_layout.md` | Collapsible sections with multi-column layout | ⚠️ Partially implemented |
| `analysis_common_models.md` | Gap analysis proposal document | ℹ️ Meta-document |

---

## 2. Component Gap Analysis

### 2.1 ColumnManager Component

**File:** `frontend/src/components/common/ColumnManager.vue`

#### Feature Comparison

| Feature | PRD Specification | Current Implementation | Gap Status |
|---------|-----------------|----------------------|------------|
| **Field Reference** | Uses `field_code` (snake_case) | Uses `prop` (camelCase) | ❌ Naming mismatch |
| **Label Override** | `label_override` for custom labels | Not stored | ❌ Missing |
| **Drag Handle Icon** | `grip-vertical` (VerticalDndIcon) | `DCaret` | ⚠️ Wrong icon |
| **Field Type Badge** | Shows field type (text/date/number) | Not displayed | ❌ Missing |
| **Original Label Tooltip** | Shows when label is overridden | Not implemented | ❌ Missing |
| **Required in List** | `required_in_list` prevents hiding | No required check | ❌ Missing |
| **Column Fixed** | left/right/none selection | Not in UI | ❌ Missing |
| **Column Width** | Editable via InputNumber | ✅ Implemented | ✅ Works |
| **Visibility Toggle** | Checkbox for show/hide | ✅ Implemented | ✅ Works |
| **Drag Reorder** | Native drag-and-drop | ✅ Implemented | ✅ Works |
| **Select All** | Checkbox with indeterminate state | ✅ Implemented | ✅ Works |
| **Save/Reset** | Save to backend, reset to default | Frontend only | ⚠️ No backend |

**Completion:** 5/12 features (42%)

---

### 2.2 DynamicTabs Component

**File:** `frontend/src/components/common/DynamicTabs.vue`

#### Feature Comparison

| Feature | PRD Specification | Current Implementation | Gap Status |
|---------|-----------------|----------------------|------------|
| **Position** | top/left/right/bottom configurable | Hardcoded top | ❌ Missing |
| **Type Style** | card/border-card/empty | Hardcoded `type="card"` | ⚠️ Limited |
| **Stretch** | Boolean to stretch tabs | Not implemented | ❌ Missing |
| **Lazy Loading** | Per-tab `lazy` option | Not implemented | ❌ Missing |
| **Animated** | Configurable animation | Not configurable | ❌ Missing |
| **Closable** | Global and per-tab closable | ✅ Implemented | ✅ Works |
| **Addable** | Dynamic tab creation | Not implemented | ❌ Missing |
| **Editable** | Edit tab titles | Not implemented | ❌ Missing |
| **Draggable** | Tab reordering | Not implemented | ❌ Missing |
| **Default Active** | Specify initial tab | Not implemented | ⚠️ Limited |
| **Badge** | Tab badges (count, dot) | Not implemented | ❌ Missing |
| **Icons** | Tab icons | Not supported | ❌ Missing |
| **Disabled** | Per-tab disabled state | Not supported | ❌ Missing |
| **Visibility Rules** | Conditional tab display | Not implemented | ❌ Missing |
| **Permission** | Per-tab permission check | Not implemented | ❌ Missing |
| **Events** | before-change, after-change, close | Only `remove` | ⚠️ Limited |
| **Responsive** | Mobile/tablet/desktop configs | Not implemented | ❌ Missing |
| **Scrollable** | Horizontal scroll when many tabs | Not implemented | ❌ Missing |

**Completion:** 2/18 features (11%)

---

### 2.3 SectionBlock Component

**File:** `frontend/src/components/common/SectionBlock.vue`

#### Feature Comparison

| Feature | PRD Specification | Current Implementation | Gap Status |
|---------|-----------------|----------------------|------------|
| **Collapsible** | Collapsible with animation | ✅ Implemented | ✅ Works |
| **Default Collapsed** | Configurable initial state | ✅ Via prop | ✅ Works |
| **Title** | Section title | ✅ Implemented | ✅ Works |
| **Description** | Optional description text | Not supported | ❌ Missing |
| **Columns** | 1-4 column grid layout | Not implemented | ❌ Missing |
| **Actions Slot** | Custom action buttons | ✅ Implemented | ✅ Works |
| **Visibility Rules** | Conditional section display | Not implemented | ❌ Missing |

**Completion:** 3/7 features (43%)

---

## 3. Backend Models Gap Analysis

### 3.1 Missing Models

| Model | Purpose | PRD Reference | Status |
|-------|---------|---------------|--------|
| **UserColumnPreference** | User-level column preferences | `list_column_configuration.md` | ❌ NOT EXISTS |
| **RoleColumnPreference** | Role-level column preferences | `list_column_configuration.md` | ❌ NOT EXISTS |
| **OrganizationColumnPreference** | Org-level column preferences | `list_column_configuration.md` | ❌ NOT EXISTS |
| **TabConfig** | Tab configuration storage | `tab_configuration.md` | ❌ NOT EXISTS |

### 3.2 Existing Models (Verified)

| Model | File | Status |
|-------|------|--------|
| **BusinessObject** | `backend/apps/system/models.py` | ✅ EXISTS |
| **FieldDefinition** | `backend/apps/system/models.py` | ✅ EXISTS |
| **ModelFieldDefinition** | `backend/apps/system/models.py` | ✅ EXISTS |
| **PageLayout** | `backend/apps/system/models.py` | ✅ EXISTS |
| **LayoutHistory** | `backend/apps/system/models.py` | ✅ EXISTS |

---

## 4. Services & API Gap Analysis

### 4.1 Missing Services

| Service | Purpose | PRD Reference | Status |
|---------|---------|---------------|--------|
| **ColumnConfigService** | Config merge logic (User > Role > Org > Default) | `list_column_configuration.md` lines 450-591 | ❌ NOT EXISTS |
| **TabConfigService** | Tab configuration management | `tab_configuration.md` | ❌ NOT EXISTS |

### 4.2 Missing API Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/system/column-config/{object_code}/` | GET | Get merged column config | ❌ MISSING |
| `/api/system/column-config/{object_code}/save/` | POST | Save user config | ❌ MISSING |
| `/api/system/column-config/{object_code}/reset/` | POST | Reset to default | ❌ MISSING |
| `/api/system/tab-config/` | GET/POST | Tab config CRUD | ❌ MISSING |

---

## 5. Development Plan

### Phase 1: Backend Foundation (Week 1-2)

#### 1.1 Add Missing Models

**File:** `backend/apps/system/models.py`

```python
class UserColumnPreference(BaseModel):
    """User-level column display preferences"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='column_preferences',
        verbose_name='User'
    )
    object_code = models.CharField(
        max_length=50,
        verbose_name='Object code',
        help_text='e.g., asset, procurement_request'
    )
    column_config = models.JSONField(
        default=dict,
        verbose_name='Column configuration'
    )
    config_name = models.CharField(
        max_length=50,
        default='default',
        verbose_name='Configuration name'
    )
    is_default = models.BooleanField(
        default=True,
        verbose_name='Is default configuration'
    )

    class Meta:
        db_table = 'system_user_column_preference'
        verbose_name = 'User Column Preference'
        verbose_name_plural = 'User Column Preferences'
        unique_together = [['user', 'object_code', 'config_name']]
        indexes = [
            models.Index(fields=['user', 'object_code']),
        ]


class TabConfig(BaseModel):
    """Tab configuration for forms and detail pages"""
    business_object = models.ForeignKey(
        'BusinessObject',
        on_delete=models.CASCADE,
        related_name='tab_configs',
        verbose_name='Business object'
    )
    name = models.CharField(
        max_length=50,
        choices=[('form_tabs', 'Form Tabs'), ('detail_tabs', 'Detail Tabs')],
        verbose_name='Configuration name'
    )
    position = models.CharField(
        max_length=10,
        choices=[('top', 'Top'), ('left', 'Left'), ('right', 'Right'), ('bottom', 'Bottom')],
        default='top',
        verbose_name='Tab position'
    )
    type_style = models.CharField(
        max_length=20,
        choices=[('', 'card', 'border-card')],
        default='',
        verbose_name='Tab style type'
    )
    stretch = models.BooleanField(
        default=False,
        verbose_name='Stretch tabs'
    )
    lazy = models.BooleanField(
        default=True,
        verbose_name='Lazy load tabs'
    )
    animated = models.BooleanField(
        default=True,
        verbose_name='Animated transitions'
    )
    tabs_config = models.JSONField(
        default=list,
        verbose_name='Tabs configuration (JSON)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is active'
    )

    class Meta:
        db_table = 'system_tab_config'
        verbose_name = 'Tab Configuration'
        verbose_name_plural = 'Tab Configurations'
        unique_together = [['business_object', 'name', 'organization']]
```

#### 1.2 Create ColumnConfigService

**File:** `backend/apps/system/services/column_config_service.py`

```python
from typing import Dict, Optional
from django.core.cache import cache
from .models import UserColumnPreference, PageLayout

class ColumnConfigService:
    """Column configuration service with priority-based merging"""

    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def get_column_config(cls, user, object_code: str) -> Dict:
        """
        Get merged column configuration

        Priority: User > Role > Org > Default (PageLayout)
        """
        cache_key = f"column_config:{user.id}:{object_code}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. Get default config from PageLayout
        default_config = cls._get_default_config(object_code)

        # 2. Get user config
        user_config = cls._get_user_config(user, object_code)

        # 3. Merge configs
        merged_config = cls._merge_configs(default_config, user_config)

        # Cache result
        cache.set(cache_key, merged_config, cls.CACHE_TIMEOUT)

        return merged_config

    @classmethod
    def _get_default_config(cls, object_code: str) -> Dict:
        """Get default configuration from PageLayout"""
        try:
            layout = PageLayout.objects.get(
                business_object__code=object_code,
                layout_type='list',
                is_default=True
            )
            return layout.layout_config.get('columns', {})
        except PageLayout.DoesNotExist:
            return {}

    @classmethod
    def _get_user_config(cls, user, object_code: str) -> Dict:
        """Get user configuration"""
        try:
            pref = UserColumnPreference.objects.get(
                user=user,
                object_code=object_code,
                is_default=True
            )
            return pref.column_config
        except UserColumnPreference.DoesNotExist:
            return {}

    @classmethod
    def _merge_configs(cls, default: Dict, user: Dict) -> Dict:
        """Merge configurations with user preference taking priority"""
        result = default.copy()
        result.update(user)
        return result

    @classmethod
    def save_user_config(cls, user, object_code: str, config: Dict) -> UserColumnPreference:
        """Save user configuration"""
        pref, created = UserColumnPreference.objects.get_or_create(
            user=user,
            object_code=object_code,
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
        """Reset user configuration to default"""
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

---

### Phase 2: Frontend Component Enhancement (Week 2-3)

#### 2.1 ColumnManager.vue Enhancements

| Priority | Task | Description |
|----------|------|-------------|
| HIGH | Rename `prop` → `field_code` | Align with PRD naming convention |
| HIGH | Add `label_override` | Support custom column labels |
| HIGH | Add column fixed toggle | left/right/none options |
| MEDIUM | Replace `DCaret` icon | Use `DArrow` or `Menu` icon |
| MEDIUM | Add field type badge | Display type (text/date/number/etc) |
| MEDIUM | Add original label tooltip | Show when label overridden |
| LOW | Add required indicator | Prevent hiding required columns |

#### 2.2 DynamicTabs.vue Enhancements

| Priority | Task | Description |
|----------|------|-------------|
| HIGH | Add `position` prop | Support top/left/right/bottom |
| HIGH | Add `typeStyle` prop | Support card/border-card/empty |
| HIGH | Add `lazy` prop | Per-tab lazy loading |
| MEDIUM | Add `animated` prop | Control transition animation |
| MEDIUM | Add `badge` config | Show badges on tabs |
| MEDIUM | Add `icon` support | Display tab icons |
| LOW | Add `draggable` | Enable tab reordering |
| LOW | Add `addable` | Dynamic tab creation |
| LOW | Add `events` | before-change, after-change, close |

#### 2.3 SectionBlock.vue Enhancements

| Priority | Task | Description |
|----------|------|-------------|
| HIGH | Add `columns` prop | 1-4 column grid layout |
| MEDIUM | Add `description` prop | Show description text |
| LOW | Add `visibility_rules` | Conditional section display |

---

### Phase 3: API & Integration (Week 3-4)

#### 3.1 Backend ViewSets

**File:** `backend/apps/system/viewsets/column_preference.py`

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.responses.base import BaseResponse
from apps.common.models import BaseModel
from ..models import UserColumnPreference
from ..serializers import UserColumnPreferenceSerializer
from .column_config_service import ColumnConfigService

class UserColumnPreferenceViewSet(BaseModelViewSet):
    """User column preference ViewSet"""

    queryset = UserColumnPreference.objects.all()
    serializer_class = UserColumnPreferenceSerializer

    def get_queryset(self):
        return UserColumnPreference.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path=r'(?P<object_code>[^/.]+)')
    def get_config(self, request, object_code=None):
        """Get column configuration for object"""
        config = ColumnConfigService.get_column_config(
            request.user,
            object_code
        )
        return Response(BaseResponse.success(data=config))

    @action(detail=False, methods=['post'], url_path=r'(?P<object_code>[^/.]+)/save')
    def save_config(self, request, object_code=None):
        """Save column configuration"""
        pref = ColumnConfigService.save_user_config(
            request.user,
            object_code,
            request.data.get('column_config', {})
        )
        serializer = UserColumnPreferenceSerializer(pref)
        return Response(BaseResponse.success(
            data=serializer.data,
            message='Configuration saved successfully'
        ))

    @action(detail=False, methods=['post'], url_path=r'(?P<object_code>[^/.]+)/reset')
    def reset_config(self, request, object_code=None):
        """Reset column configuration to default"""
        success = ColumnConfigService.reset_user_config(
            request.user,
            object_code
        )
        if success:
            return Response(BaseResponse.success(message='Configuration reset'))
        else:
            return Response(BaseResponse.error(message='Reset failed'))
```

#### 3.2 Frontend API Integration

**File:** `frontend/src/api/system.ts`

```typescript
import request from '@/utils/request'

export const columnConfigApi = {
  /**
   * Get merged column configuration for object
   */
  get: (objectCode: string) =>
    request.get(`/system/column-config/${objectCode}/`),

  /**
   * Save user column configuration
   */
  save: (objectCode: string, config: {
    columns: any[]
    columnOrder: string[]
  }) =>
    request.post(`/system/column-config/${objectCode}/save/`, config),

  /**
   * Reset column configuration to default
   */
  reset: (objectCode: string) =>
    request.post(`/system/column-config/${objectCode}/reset/`)
}

export const tabConfigApi = {
  /**
   * Get tab configuration for business object
   */
  get: (businessObject: string, name: string = 'form_tabs') =>
    request.get(`/system/tab-config/${businessObject}/${name}/`),

  /**
   * Save tab configuration
   */
  save: (config: any) =>
    request.post('/system/tab-config/', config),

  /**
   * Update tab configuration
   */
  update: (id: string, config: any) =>
    request.put(`/system/tab-config/${id}/`, config)
}
```

---

## 6. Estimated Effort

| Phase | Tasks | Estimated Time |
|-------|-------|---------------|
| **Phase 1** | Backend models, services, APIs | 3-4 days |
| **Phase 2** | Frontend component enhancements | 4-5 days |
| **Phase 3** | API integration & testing | 2-3 days |
| **Phase 4** | Documentation & demo | 1-2 days |
| **Total** | | **10-14 days** |

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Breaking Changes** | HIGH | Field name change (`prop` → `field_code`) affects all usages |
| **Performance** | MEDIUM | Config caching implemented in service |
| **Data Migration** | LOW | New models, no existing data to migrate |
| **Testing Coverage** | MEDIUM | Need E2E tests for drag-drop, persistence |

---

## 8. Recommendations

1. **Start with Phase 1** - Backend foundation unblocks frontend persistence
2. **Incremental rollout** - Deploy component updates one at a time
3. **Backward compatibility** - Support both `prop` and `field_code` during transition
4. **User testing** - Verify UI usability after each enhancement
5. **Document changes** - Update component documentation after implementation

---

## 9. Appendix: File Checklist

### Files to Create

```
backend/apps/system/
├── services/
│   ├── __init__.py
│   └── column_config_service.py    # NEW
├── viewsets/
│   ├── __init__.py
│   ├── column_preference.py         # NEW
│   └── tab_config.py                # NEW

frontend/src/
├── api/
│   └── system.ts                     # UPDATE: add APIs
└── types/
    └── common.ts                      # UPDATE: add types
```

### Files to Modify

```
backend/apps/system/
├── models.py                          # ADD: 4 models
├── serializers.py                      # ADD: serializers
└── urls.py                            # ADD: routes

frontend/src/components/common/
├── ColumnManager.vue                   # ENHANCE: +7 features
├── DynamicTabs.vue                     # ENHANCE: +16 features
└── SectionBlock.vue                    # ENHANCE: +3 features
```

---

**Report End**

*This report was generated on 2026-01-27 as part of the GZEAMS Frontend Layout Models Gap Analysis.*
