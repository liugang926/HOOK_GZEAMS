# GZEAMS Frontend Architecture Optimization PRD (Phase 5)

## 1. Introduction
This Product Requirements Document (PRD) outlines the next phase of frontend architecture optimization for the GZEAMS (Hook Fixed Assets Management System) project. Building upon the successful implementation of UI consistency, resilience, designer ergonomics, and basic A11y features (Phases 1-4), Phase 5 focuses on deep systemic optimizations. The goal is to ensure the platform remains performant, resilient, and highly usable as it scales to handle enterprise-level data volumes and complex multi-tenant environments.

## 2. Objectives
*   **Enhance I/O Performance:** Eliminate main-thread blocking caused by synchronous `localStorage` operations, especially during high-frequency events like auto-saving complex layout configurations.
*   **Advance Caching Strategy:** Upgrade the existing in-memory SWR (Stale-While-Revalidate) cache to support persistent storage, enabling "zero-network cold boots" and robust offline capabilities.
*   **Refine Global Interactions:** Implement context-aware hotkey scoping to prevent accidental cross-component triggers and improve keyboard navigation efficiency.
*   **Elevate UX & A11y Resilience:** Provide actionable recovery mechanisms for component failures and ensure smooth navigation through massive datasets using virtual scrolling and trapped focus.

## 3. Scope of Work

### 3.1. Storage & I/O Performance Optimization
**Current State:** `WysiwygLayoutDesigner` uses synchronous `localStorage.setItem` for auto-saving.
**Problem:** Serializing large JSON objects synchronously on the main thread during high-frequency drag-and-drop operations causes UI stutter (frame drops).
**Requirements:**
1.  **Migrate to IndexedDB:** Replace `localStorage` with `IndexedDB` for layout drafts and other heavy payloads. Use a lightweight wrapper library like `localforage` or `idb-keyval` to simplify the asynchronous API.
2.  **Debounce Auto-Save:** Implement a debounce mechanism (e.g., 500ms - 1000ms) for the auto-save trigger in `WysiwygLayoutDesigner`. This ensures that rapid, successive changes (like dragging an element across the canvas) only result in a single write operation after the interaction settles.
3.  **Storage Quota Management:** Implement logic to handle `QuotaExceededError` gracefully, falling back to in-memory state and notifying the user if the browser's storage limit is reached.

### 3.2. SWR Caching Evolution
**Current State:** `cacheWrapper.ts` provides a solid in-memory SWR implementation.
**Problem:** Cache is lost on page reload. High-value, infrequent-change data (like multi-megabyte dictionaries or deep organizational trees) must be re-fetched on every cold start.
**Requirements:**
1.  **Persistent Adapter:** Extend `withSWR` to optionally accept a persistent storage adapter (pointing to IndexedDB).
2.  **Zero-Network Cold Boot:** When a user opens a new tab, `withSWR` should immediately return the stale data from IndexedDB while triggering the background fetch.
3.  **Resilient Fetching:** Implement Exponential Backoff for failed background revalidation requests. If the API is unreachable, the system must retain the stale data instead of clearing the cache, ensuring partial offline functionality.
4.  **Cache Invalidation Tiers:** Provide mechanics to invalidate cache by namespace (e.g., `invalidate('dict:*')`) or specific keys when the user explicitly triggers a "Refresh" semantic action.

### 3.3. Hotkey Scoping & Context Management
**Current State:** `useHotkeys.ts` binds listeners globally to the `window` object.
**Problem:** In a Single Page Application with overlapping contexts (e.g., a detail page open, with a drawer sliding out, containing a dialog box), pressing `Ctrl+S` might trigger save actions on all three layers simultaneously.
**Requirements:**
1.  **Priority or Z-Index Context:** Refactor `useHotkeys` to support an active context stack.
2.  **Event Consumption:** When a hotkey combination is detected, it should only be dispatched to the listener currently at the top of the stack (the most recently opened, active context).
3.  **Context Registration:** Developers should be able to register a new hotkey context when a Dialog or Drawer mounts, and automatically unregister it when it descends.

### 3.4. Error Boundary UX Enhancement
**Current State:** `<ErrorBoundary>` catches render errors and displays a generic fallback string.
**Problem:** Lack of user agency to recover from transient errors, and inability for specific business components to define their own polite failure states.
**Requirements:**
1.  **Fallback Slots:** Update `ErrorBoundary.vue` to expose a `fallback` scoped slot. This allows consuming components to provide contextual error UI (e.g., a "Chart Data Unavailable" card instead of a full-page red box).
2.  **Self-Recovery Mechanism:** Implement a `resetBoundary` method inside `ErrorBoundary`. This method should reset the internal `hasError` state and force a re-render of the default slot (potentially using the `key` resetting technique). Expose this method to the fallback UI to render a "Retry" button.

### 3.5. Accessibility (A11y) & Virtualization Deepening
**Current State:** Basic A11y tokens are present, but deep data entry contexts lack polish.
**Problem:** Left-hand field palettes with thousands of items will crash the DOM. Keyboard navigation inside data-entry drawers can easily escape the modal context.
**Requirements:**
1.  **Virtualization for Designer Palette:** Replace the standard `v-for` rendering in the `WysiwygLayoutDesigner` left-hand field palette with a robust virtual scrolling solution (e.g., `vue-virtual-scroller` or `el-tree-v2` if hierarchical).
2.  **Strict Focus Trapping:** Implement a `v-focus-trap` directive (or integrate an existing robust library like `focus-trap-vue`). Apply this to all side-drawers (e.g., `ContextDrawer.vue`, `DetailRelatedManager.vue` drawers, `ITAssetList.vue` drawers) to ensure the `Tab` key cycles only within the drawer content.
3.  **Deterministic `tabindex` flows:** For high-volume data entry forms (e.g., `DynamicFormPage.vue`, aggregate document editors, `VoucherList.vue` forms), explicitly sequence the `tabindex` to follow the visual layout (Left-to-Right, Top-to-Bottom), overriding default browser DOM order if necessary to match the semantic grid.

## 4. Acceptance Criteria
*   **Performance:** Dragging elements in the Layout Designer at 60Hz does not drop frames due to auto-save I/O.
*   **Caching:** Reloading the app while disconnected from the network instantly paints UI shells using stale data from IndexedDB for dictionaries and org charts.
*   **Hotkeys:** Pressing `Ctrl+S` while a Drawer is open only triggers the Drawer's save action, not the underlying Page's save action.
*   **Resilience:** Clicking "Retry" on a component that failed due to a mock simulated error successfully re-renders the component.
*   **A11y:** Focus cannot leave an open Drawer using the `Tab` key.

## 5. Technical Stack Considerations
*   **IndexedDB Wrapper:** `localforage` (recommended for Promise-based API and cross-browser fallback) or `idb`.
*   **Virtual Scrolling:** `vue-virtual-scroller` (widely used in Vue ecosystem) or native Element Plus virtualized components if they meet the drag-and-drop requirements.
*   **Focus Trapping:** `focus-trap-vue` or custom composable using `document.activeElement` and DOM querying.
