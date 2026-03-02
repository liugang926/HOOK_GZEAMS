# PRD: Dynamic Action Routing & Execution Framework

## 1. Background
The platform currently supports dynamic routing for CRUD and metadata only. Business actions (submit/approve/complete/etc.) are still hardcoded in module-specific routes, which leads to inconsistent endpoints, scattered logic, and high maintenance cost.

## 2. Goals
- Provide a unified action entry: `/api/system/objects/{code}/{id}/{action}/` (instance-level) and `/api/system/objects/{code}/{action}/` (object-level).
- Make actions configurable via an Action Registry.
- Unify permission checks, execution flow, and audit logging for all actions.

## 3. Scope
- Action Registry model and API
- Dynamic action routing in system object router
- Action execution handlers (service/workflow/rule)
- Permission and audit logging
- Frontend dynamic action rendering

## 4. Out of Scope
- Full replacement of all legacy routes (keep compatibility)
- Sandbox script execution (possible future extension)

## 5. User Stories
1. As an admin, I can configure actions for a business object, enable/disable them, and set permissions.
2. As a user, I can see available actions on an object and execute them.
3. As a system, every action execution is logged for audit and traceability.

## 6. Solution Design

### 6.1 Action Registry Model (Example Fields)
- `action_code`
- `action_name`
- `object_code`
- `method` (POST/GET)
- `handler_type` (service/workflow/rule)
- `handler_ref` (service path / workflow key / rule set)
- `enabled`
- `permissions`
- `description`

### 6.2 Dynamic Routing
- Instance-level: `/api/system/objects/{code}/{id}/{action}/`
- Object-level: `/api/system/objects/{code}/{action}/`

### 6.3 Execution Flow
1. Resolve action from Action Registry
2. Permission check
3. Dispatch to handler
4. Execute and return BaseResponse
5. Write audit log

### 6.4 Handler Types
- **Service Handler**: call backend service layer method
- **Workflow Handler**: trigger workflow engine
- **Rule Handler**: evaluate/execute rule engine

## 7. Migration Strategy
- Keep legacy endpoints working
- Enable actions per object gradually
- Support dual mode during migration

## 8. Checkpoints (Acceptance Gates)
1. Action Registry CRUD available
2. Dynamic route resolves and executes actions
3. Permissions enforced for actions
4. Handler execution produces correct results
5. Action audit logs recorded
6. Legacy routes remain usable

## 9. Unit Test Requirements (Minimum Set)
### 9.1 Action Registry
- Create/update/disable actions
- List actions by `object_code`

### 9.2 Routing
- Resolve `{code}/{action}` correctly
- Missing action returns 404

### 9.3 Permissions
- Authorized action succeeds
- Unauthorized action fails

### 9.4 Handlers
- Service handler invoked correctly
- Workflow handler triggers workflow
- Rule handler executes rule set

### 9.5 Audit
- Action execution writes audit log
- Required fields present in log

## 10. Suggested Milestones
1. Registry model + API
2. Router support for actions
3. Handler framework
4. Permission + audit
5. Frontend dynamic actions
6. Migration rollout

## 11. Action Catalog (Initial Scope)

### 11.1 Assets
- AssetPickup: `submit`, `approve`, `complete`, `cancel`
- AssetTransfer: `submit`, `approve`, `reject`
- AssetReturn: `submit`, `approve`, `reject`, `complete`
- AssetLoan: `submit`, `approve`, `reject`, `return`
- Asset: `restore`

### 11.2 Inventory
- InventoryTask: `start`, `complete`, `cancel`, `scan`, `report`, `snapshots.confirm`
- InventoryReconciliation: `submit`, `approve`, `reject`

### 11.3 Consumables
- Consumable: `stock-in`, `stock-out`, `history`

### 11.4 Lifecycle
- PurchaseRequest: `submit`, `approve`, `reject`
- AssetReceipt: `confirm`
- Maintenance: `complete`
- MaintenancePlan: `activate`, `deactivate`
- DisposalRequest: `submit`, `approve`, `confirm`

### 11.5 Workflow
- WorkflowDefinition: `publish`, `unpublish`, `duplicate`
- WorkflowTask: `approve`, `reject`, `return_task`
- WorkflowInstance: `start`, `withdraw`, `terminate`

## 12. Action Registry Initialization Template

```json
[
  {
    "object_code": "AssetPickup",
    "action_code": "submit",
    "action_name": "Submit Pickup",
    "method": "POST",
    "handler_type": "service",
    "handler_ref": "apps.assets.services.operation_service.AssetPickupService.submit_for_approval",
    "enabled": true,
    "permissions": ["assets.pickup.submit"],
    "description": "Submit pickup order for approval"
  }
]
```

## 13. Acceptance Checklist

### 13.1 Platform Behavior
- Dynamic action endpoint available for instance-level and object-level actions
- Action execution returns BaseResponse with `success`, `data`, and `message`
- Action permissions enforced consistently with existing permission system
- Action audit log written for every execution

### 13.2 Backward Compatibility
- Legacy routes remain functional during migration
- New dynamic action returns same business outcome as legacy route

### 13.3 Frontend Integration
- Action list can be fetched by object code
- UI renders actions based on registry output
- UI calls unified action endpoint for execution

## 14. Completion Acceptance Criteria
- All actions in the Action Catalog are registered in the Action Registry with correct handler mappings
- Dynamic action routes work for at least one full business flow per category (Assets, Inventory, Consumables, Lifecycle, Workflow)
- Action execution parity is verified against legacy routes for migrated flows
- Action audit logs are queryable and include actor, timestamp, object, action, result
- Minimum unit test suite in Section 9 passes without failures
