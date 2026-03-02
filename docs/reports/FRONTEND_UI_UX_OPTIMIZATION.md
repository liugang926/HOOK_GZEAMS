# Frontend UI/UX Optimization Report

## 1. Overview
This report provides actionable suggestions to enhance the frontend user experience, focusing on list management, interactivity, and unified field rendering models. The goal is to align with the "Premium Design" and "Low-code Metadata Driven" requirements of the PRD.

## 2. Analysis of Current State

### 2.1. List Management (`BaseListPage.vue`)
- **Strengths**:
  - Pagination, Search, and Batch Actions are implemented.
  - User-defined column visibility/ordering is supported (`ColumnManager`).
  - Mobile card view fallback is present.
- **Weaknesses**:
  - **Rendering**: Relies heavily on slots or simple text/tag rendering. No built-in support for rich types (Avatars, Progress bars, Links).
  - **Interactivity**: No inline editing. No density control. Standard table view looks "generic".
  - **Loading**: Uses simple spinner instead of skeleton screens.

### 2.2. Field Rendering
- **Fragmentation**:
  - `BaseFormPage` has hardcoded switch-case for standard inputs.
  - `DynamicFieldRenderer` (in `engine`) handles complex types but is isolated.
  - `BaseListPage` implements its own limited rendering logic.
- **Missed Opportunity**: The logic to "Display a User" (Avatar + Name) is not centralized, likely leading to inconsistent display across Lists vs Details vs Forms.

## 3. Optimization Proposals

### 3.1. Unified Field Model & Renderer

**Proposal**: Promote `DynamicFieldRenderer` to a core component `FieldRenderer`.

- **Concept**: A single component that can render any field type in any mode.
- **API**:
  ```typescript
  <FieldRenderer
      :field="fieldConfig"
      :value="value"
      mode="read" | "write" | "table-cell"
  />
  ```
- **Modes**:
  - **Write**: Standard input (Input, Select, DatePicker, UserSelector).
  - **Read**: Formatted text (e.g., "¥1,234.00", "2023-10-01").
  - **Table-Cell**: Optimized for dense display.
    - **User**: Avatar (32px) + Name.
    - **Status**: Colored Badge (Dot or Tag).
    - **File**: File Icon + Filename (Click to preview).
    - **Progress**: Mini progress bar.

### 3.2. List View Enhancements

**A. Visual Polish (Premium Feel)**
- **Skeleton Loading**: Replace `v-loading` with `el-skeleton` matching the table columns during data fetch.
- **Hover Effects**: Add subtle shadow lift or border highlight on row hover.
- **Empty States**: Use rich illustrations for empty states (already partially there with `el-empty`, can be customized).

**B. Advanced Interaction**
- **Inline Editing**: Double-click a cell to switch `FieldRenderer` from `read` to `write` mode temporarily.
- **Density Control**: Add a toolbar toggle for [Compact / Default / Relaxed] row heights.
- **Column Pinning**: Allow users to pin columns to left/right directly from the header (context menu).

**C. Field-Specific Models**

| Field Type | Display Model (Read/Table) | Edit Model (Write) |
| :--- | :--- | :--- |
| **User/Employee** | Avatar + Name (Hover for details card) | `UserSelect` (Searchable dropdown with avatar) |
| **Status/Enum** | `el-tag` with mapped color/icon | `el-select` with Status content |
| **Progress/Percentage** | `el-progress` (Linear or Circle) | Slider or Number Input |
| **Currency** | Monospaced font, localized format | `InputNumber` with prefix |
| **Attachment** | File Icon + Name list (Truncated) | Drag-and-drop Zone |
| **Formula** | Calculated Value (maybe with delta arrow) | *Read-only* |
| **Reference (Asset)** | Link to Asset Detail (Code + Name) | `AssetSelect` (Modal/Dropdown) |

### 3.3. Interaction Logic Improvements
- **Keyboard Navigation**: Support Arrow keys to move selection in Table. Enter to open details.
- **Quick Preview**: Spacebar on a selected row could open a "Drawer" summary view (Side Quest) without leaving the list context.
- **Bulk Edit**: Select multiple rows -> Right Click -> "Batch Edit" -> Opens form with common fields allowed for batch update.

## 4. Implementation Priority

1.  **Refactor Field Renderer**: Extract and standardize `DynamicFieldRenderer` to support `read` vs `write` modes.
2.  **Upgrade BaseListPage**: Integrate the new `FieldRenderer` for cell display.
3.  **Add Visuals**: Implement Skeleton loading and Density control.
