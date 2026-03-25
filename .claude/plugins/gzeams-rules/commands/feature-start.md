---
description: Start a new feature with proper GZEAMS structure
---

You are helping create a new feature for the GZEAMS project. Follow this workflow:

## Phase 1: Requirements Gathering

1. Ask the user for:
   - Feature name and description
   - User stories / use cases
   - User roles and permissions required

## Phase 2: Architecture Planning

Based on the requirements, design:

### Backend Architecture
- Which module will this belong to? (assets, system, workflows, inventory, etc.)
- What models are needed? (All must inherit BaseModel)
- What serializers, viewsets, services, filters? (All must inherit base classes)
- What are the API endpoints?

### Frontend Architecture
- What pages/components are needed?
- What i18n keys need to be added?
- What are the form layouts required?

## Phase 3: Create PRD

Generate a PRD document following the template at `docs/plans/common_base_features/prd_writing_guide.md`.

The PRD MUST include:
- Public Model Reference Declaration table
- Complete API specifications
- Frontend component design
- Test cases

## Phase 4: Implementation Order

Define the implementation sequence:
1. Backend models and migrations
2. Backend serializers, viewsets, services
3. Backend tests
4. Frontend i18n keys
5. Frontend components
6. Frontend tests
7. Integration tests

## Phase 5: Execute

Ask the user which phase to start with, or if they want to go through all phases sequentially.

---

**Ready to start.** Please describe the feature you want to build, or say "auto" if you want me to guide you through each phase.
