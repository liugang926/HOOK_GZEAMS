# PRD: Salesforce-like Layout Architecture & Menu Automation
**Document Version:** 1.0
**Date:** 2026-03-06
**Target Phase:** Phase 6 Architecture Optimization

## 1. Executive Summary
To elevate the system's frontend architecture to an enterprise level comparable to Salesforce, we need to restructure how UI Layouts and Menus are administered. 

Currently, the `WysiwygLayoutDesigner` acts as a monolithic editor for a single "form" state. In contrast, enterprise CRM systems distinguish between **Full Detail Layouts** (comprehensive viewing and deep editing) and **Compact/Mini Layouts** (rapid creation, hover-cards, and inline summary edits).

Furthermore, as the number of polymorphic objects grows (Assets, Approvals, Software, etc.), manually configuring routing and sidebar menus becomes a bottleneck. We need an automated **Object-to-Menu Registry** that scans the system's metadata and automatically generates a logical, categorised navigation tree without duplicate entries.

## 2. Layout Designer Restructuring (Dual-Mode Design)

### 2.1 The Problem
The current layout designer attempts to do too much in one canvas. When users want to configure what shows up when "Creating a new Asset" vs "Viewing an existing Asset detail page", they are forced into the same rigid schema.

### 2.2 Salesforce Architecture Reference
Salesforce splits object layouts into:
1. **Page Layouts (Full View):** Defines the massive layout for viewing an existing record. Contains Tabs, Accordions, Related Lists, and Sidebar components.
2. **Compact Layouts (Mini View):** A highly condensed set of 5-8 fields. Used for the "Create New" modal, highlight panels at the top of detail pages, and hover-cards.

### 2.3 Proposed Solution: Dual-Mode Layout Designer
We will split the `WysiwygLayoutDesigner` into two distinct configuration streams governed by a segmented switch at the top of the designer.

#### Mode A: Full Detail Layout (Default)
- **Use Case:** Replaces the current designer logic. Used exclusively for `BaseDetailPage` and deep editing.
- **Features:**
  - Allows grouping fields into complex `Tabs` and `Collapses`.
  - Supports sidebars (`position: sidebar`).
  - Supports embedding `RelatedObjectTable` components directly into the layout.
  - Interactive Preview mimics `BaseDetailPage.vue`.

#### Mode B: Compact/Quick Action Layout
- **Use Case:** Used for standalone "Create New" dialogs, quick-edit drawers, and summary highlight ribbons.
- **Features:**
  - **Flat Structure:** Disables Tabs and Accordions. Only allows a simple 1 or 2-column grid.
  - **Field Limit:** Encourages or enforces a maximum number of fields (e.g., top 10 most important).
  - **No Related Lists:** Cannot embed child tables (since the record doesn't exist yet during creation).
  - Interactive Preview mimics a Modal/Drawer (`el-dialog` / `el-drawer`).

### 2.4 Data Schema Changes
The Layout Config schema in the database will need to support layout "Types":
```json
{
  "layout_type": "Detail" | "Compact",
  "object_code": "asset",
  "config": { ... }
}
```

---

## 3. Automated Object-to-Menu Registry

### 3.1 The Problem
Currently, adding a new standard or custom object requires jumping into `menu.json` or database routing tables to manually configure the sidebar navigation. This is error-prone and leads to orphaned objects that users cannot access.

### 3.2 Proposed Solution: Recursive Menu Generator
We will implement an automated registry system that recursively scans the existing system objects (Asset, Location, User, Software, etc.) and auto-generates the menu structure.

#### Key Mechanisms
1. **Object Classification:** 
   - Every object metadata definition will have a `menuCategory` property (e.g., `Core`, `Lifecycle`, `Financial`, `System`).
2. **Menu Visibility Control:**
   - Add an `isMenuHidden` boolean property to the Object Metadata.
   - Objects like internal junction tables or deep child records should have this set to `true` so they don't clutter the sidebar but remain strictly accessible via Related Lists or API.
3. **Strict Singularity:**
   - The generator will keep a Set of mapped `object_codes`. 
   - An object definition can only be mapped to the menu **once**. This prevents the chaotic duplicate routing seen in poorly managed CRMs.
4. **Global Menu Search:**
   - Introduce a fast, client-side search bar at the top of the Sidebar/App Menu.
   - Allows users to quickly filter the generated menu tree by `displayName` or `code`, instantly traversing categories to find specific object list pages.
5. **The Registry Function:**
   - We will encapsulate this in a utility hook/class: `MenuRegistryManager`.
   - It will fetch all active objects from the backend metadata API.
   - It will filter out objects where `isMenuHidden === true`.
   - It will group them by `menuCategory` and hydrate the Vue Router and the Sidebar component dynamically.

### 3.3 Menu Generation Strategy
```typescript
interface MenuCategory {
  id: string;
  label: string;
  icon: string;
  children: MenuItem[];
}

class MenuRegistryManager {
  private registeredObjects = new Set<string>();

  public async generateMenuTree(objects: SystemObject[]): Promise<MenuCategory[]> {
    const tree = this.initializeEmptyCategories(); // Core, Lifecycle, etc.

    for (const obj of objects) {
      if (obj.isMenuHidden) continue; // Respect visibility guard

      if (this.registeredObjects.has(obj.code)) {
         console.warn(`Object ${obj.code} is already registered in the menu. Skipping duplicate.`);
         continue; 
      }

      const category = classifyObjectCategory(obj);
      tree[category].children.push({
         path: `/${obj.namespace}/${obj.code}/list`,
         title: obj.displayName,
         icon: obj.icon
      });

      this.registeredObjects.add(obj.code);
    }

    return tree;
  }
}
```

## 4. Implementation Phasing

### Step 1: Menu Registry Expansion
1. Implement the `MenuRegistryManager` logic.
2. Hook it into the global application initialization (`main.ts` or Vue Router `beforeEach` boot sequence).
3. Replace hardcoded menu lists in the Sidebar component with the generated tree.

### Step 2: Layout Type Schema Update
1. Update frontend TS interfaces (`LayoutConfig`) to explicitly type `layoutType` as `Detail | Compact`.
2. Ensure the layout fetching API `pageLayoutApi.getLayout` accepts `layoutType` filtering.

### Step 3: Dual-Mode Layout Designer UI
1. Add a Segmented Control to `WysiwygLayoutDesigner` header: `[ Detail View | Compact View ]`.
2. When toggled to Compact View:
   - Hide the "Add Tab" and "Add Collapse" buttons.
   - Restrict the Preview container width to 600px (Modal size).
3. Update the save payload to include the specific `layoutType`.

### Step 4: UI Application
1. Update `BaseListPage.vue` "New" button to fetch and render the `Compact` layout inside a Dialog.
2. Update `BaseDetailPage.vue` "Edit" inline mode to fetch and render the `Compact` layout (or explicitly fallback to Detail layout if no compact exists).
