# Menu Loading Fix Report

## Document Information
| Project | Description |
|---------|-------------|
| Report Version | v1.0 |
| Created Date | 2026-01-28 |
| Issue Type | Menu not displaying after login |
| Status | RESOLVED |

---

## Issue Description

**User Report:** "为何我登录之后看不到前端页面的任何功能的菜单栏？"

After login, the frontend menu bar was completely empty except for the "工作台" (Workspace) menu item. No business object menu items were visible.

---

## Root Cause Analysis

### The Problem

The `MenuViewSet.list()` endpoint was returning empty menu data:
```json
{"success":true,"message":"Operation successful","data":{"groups":[],"items":[]}}
```

### Root Cause

**TenantManager Organization Filtering**

The `BusinessObject` model inherits from `BaseModel`, which uses `TenantManager` for automatic organization filtering:

```python
class TenantManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = get_current_organization()
        if org_id:
            queryset = queryset.filter(organization_id=org_id)  # <-- Filter applied here
        queryset = queryset.filter(is_deleted=False)
        return queryset
```

**The Issue:**
- `BusinessObject` records had `organization_id=None` (system-level metadata)
- User login had `organization_id='0227b052-daf5-408a-aacb-b6668aa69e14'`
- `TenantManager` filtered out all records where `organization_id != user_org_id`
- Result: Empty queryset, no menu items

### Evidence from Database Query

```
Admin user org: 0227b052-daf5-408a-aacb-b6668aa69e14
Asset: org_id=None, menu_config={'show_in_menu': True, ...}
AssetCategory: org_id=None, menu_config={'show_in_menu': True, ...}
...
```

All 28 BusinessObjects configured for menu display had `org_id=None`.

---

## Solution

### Code Changes

**File:** `backend/apps/system/viewsets/menu.py`

**Before:**
```python
def get_queryset(self):
    return BusinessObject.objects.filter(
        is_deleted=False,
        menu_config__show_in_menu=True
    ).order_by(...)
```

**After:**
```python
def get_queryset(self):
    """
    Get BusinessObjects that should appear in menu.

    Uses all_objects to bypass organization filtering since BusinessObject
    is system-level metadata that should be available to all organizations.
    """
    return BusinessObject.all_objects.filter(
        is_deleted=False,
        menu_config__show_in_menu=True
    ).order_by(...)
```

### Explanation

- Changed from `objects` manager to `all_objects` manager
- `all_objects` is defined in `BaseModel` as `models.Manager()` (bypasses organization filtering)
- BusinessObject is system-level metadata that should be globally available
- This allows all organizations to see the same menu structure

---

## Verification Results

### Before Fix

```
Menu Items: 1 found (only "工作台")
Sub menus found: 0
Menu API response: {groups: Array(0), items: Array(0)}
```

### After Fix

```
Menu Items: 29 found (including "工作台" + 28 business objects)
Sub menus found: 5 (groups with multiple items)
Menu API response: {groups: Array(10), items: Array(28)}
```

### Menu Groups Verified

| Group | Order | Items |
|-------|-------|-------|
| 资产管理 | 10 | 9 items (资产卡片, 领用单, 调拨单, 归还单, 借用单, 分类, 供应商, 地点, 状态日志) |
| 库存管理 | 20 | 1 item (盘点任务) |
| 耗材管理 | 30 | 5 items (耗材, 分类, 库存, 采购, 领用) |
| 维护管理 | 40 | 3 items (维修记录, 维修计划, 维修任务) |
| 财务管理 | 50 | 5 items (采购申请, 入库单, 处置申请, 财务凭证, 折旧记录) |
| IT资产管理 | 60 | 1 item (IT设备) |
| 软件许可 | 70 | 1 item (软件许可) |
| 租赁管理 | 80 | 1 item (租赁合同) |
| 保险管理 | 85 | 1 item (保险单) |
| 组织管理 | 90 | 1 item (部门) |

---

## Additional Fix

### Vue Key Warning Fix

**File:** `frontend/src/layouts/MainLayout.vue`

Added missing `:key` attribute to single-item menu groups:

```vue
<el-menu-item v-else-if="group.items.length === 1" :key="group.items[0].code" :index="group.items[0].url">
```

This resolved Vue warnings about duplicate keys during menu rendering.

---

## Test Methodology

Used Playwright browser automation to:
1. Navigate to login page
2. Fill credentials and submit
3. Capture localStorage contents (access_token verification)
4. Monitor network requests for `/api/system/menu/`
5. Verify menu elements are rendered in DOM
6. Count menu items and sub-menus
7. Take screenshots for visual verification

---

## Files Modified

| File | Change |
|------|--------|
| `backend/apps/system/viewsets/menu.py` | Use `all_objects` instead of `objects` |
| `frontend/src/layouts/MainLayout.vue` | Add `:key` to single-item menu groups |

---

## Lessons Learned

1. **System-level metadata should bypass organization filtering**
   - BusinessObject, FieldDefinition, PageLayout are system-wide configurations
   - They should use `all_objects` or have a separate query path

2. **TenantManager affects all BaseModel inheritors**
   - Any model using `objects` manager will be filtered by organization
   - Always check if the model should be organization-scoped or global

3. **Consider adding `is_global` flag to BaseModel**
   - Could mark certain models as global (bypass org filtering)
   - This would be more explicit than using different managers

---

## Related Issues

None currently. This fix resolves the menu loading issue completely.

---

**Report Generated:** 2026-01-28
**Tested By:** Claude Code (Playwright Browser Automation)
