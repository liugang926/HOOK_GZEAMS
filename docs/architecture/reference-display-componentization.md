# Reference Display Componentization

## Goal
- Unify reference-value display across detail/read-only views.
- Keep lookup/edit behavior unchanged while reducing duplicated UI logic.
- Align to a professional CRM-style reference presentation pattern.

## Core Component
- `src/components/common/ReferenceRecordPill.vue`
  - Single reusable presenter for reference values.
  - Supports:
    - primary label
    - secondary text
    - object code tag
    - id footer
    - optional open action
    - hover popover with skeleton + compact meta items

## Applied Entry Points
- `src/components/common/FieldDisplay.vue`
  - Reference rendering now uses `ReferenceRecordPill`.
- `src/components/engine/fields/ReferenceField.vue`
  - Read-mode single/multiple rendering now uses `ReferenceRecordPill`.
  - Existing deep hover fetch logic is preserved and passed as compact meta items.

## Lookup Interaction Upgrade
- `src/components/engine/fields/ReferenceLookupDialog.vue`
  - Added single-select quick action: `Open` selected record in new tab.

## Benefits
- Less duplicated reference hover-card markup/styles.
- Consistent visual language between generic field display and engine reference field.
- Easier future upgrades (e.g., pinned actions, SLA badges, ownership chip) in one place.
