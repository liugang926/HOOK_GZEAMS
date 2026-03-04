import { createRouter, createWebHistory } from 'vue-router'

import type { RouteRecordRaw } from 'vue-router'

// Layouts
const MainLayout = () => import('@/layouts/MainLayout.vue')
const AuthLayout = () => import('@/layouts/AuthLayout.vue')

// Pages
const Dashboard = () => import('@/views/Dashboard.vue')
const Login = () => import('@/views/auth/Login.vue')
const TaskCenter = () => import('@/views/workflow/TaskCenter.vue')
const TaskDetail = () => import('@/views/workflow/TaskDetail.vue')
const MyApprovals = () => import('@/views/workflow/MyApprovals.vue')
const NotificationCenter = () => import('@/views/notifications/NotificationCenter.vue')
const NotificationPreferences = () => import('@/views/notifications/NotificationPreferences.vue')

// Dynamic Pages (Unified routing for all business objects)
const DynamicListPage = () => import('@/views/dynamic/DynamicListPage.vue')
const DynamicFormPage = () => import('@/views/dynamic/DynamicFormPage.vue')
const DynamicDetailPage = () => import('@/views/dynamic/DynamicDetailPage.vue')

type LegacyRouteMap = Record<string, string>

const toObjectListPath = (objectCode: string): string => `/objects/${objectCode}`
const toObjectCreatePath = (objectCode: string): string => `/objects/${objectCode}/create`
const toObjectDetailPath = (objectCode: string, id: string): string => `/objects/${objectCode}/${id}`
const toObjectEditPath = (objectCode: string, id: string): string => `/objects/${objectCode}/${id}/edit`

// Additional legacy module routes that now resolve through the metadata-driven object engine.
// These modules exist on backend but may still expose legacy menu URLs or bookmarks.
export const ADDITIONAL_BUSINESS_OBJECT_ROUTES: LegacyRouteMap = {
  // Inventory
  'inventory/items': 'InventoryItem',
  // Insurance
  'insurance/companies': 'InsuranceCompany',
  'insurance/policies': 'InsurancePolicy',
  'insurance/insured-assets': 'InsuredAsset',
  'insurance/payments': 'PremiumPayment',
  'insurance/claims': 'ClaimRecord',
  'insurance/renewals': 'PolicyRenewal',
  // Leasing
  'leasing/contracts': 'LeasingContract',
  'leasing/items': 'LeaseItem',
  'leasing/rent-payments': 'RentPayment',
  'leasing/returns': 'LeaseReturn',
  'leasing/extensions': 'LeaseExtension',
}

const LEGACY_OBJECT_FULL_CRUD_ROUTES: LegacyRouteMap = {
  assets: 'Asset',
  'assets/settings/suppliers': 'Supplier',
  'assets/settings/locations': 'Location',
  'assets/operations/pickup': 'AssetPickup',
  'assets/operations/transfer': 'AssetTransfer',
  'assets/operations/return': 'AssetReturn',
  'assets/operations/loans': 'AssetLoan'
}

const LEGACY_OBJECT_LIST_CREATE_ROUTES: LegacyRouteMap = {
  'assets/settings/categories': 'AssetCategory',
  consumables: 'Consumable'
}

const LEGACY_OBJECT_LIST_ONLY_ROUTES: LegacyRouteMap = {
  'assets/status-logs': 'AssetStatusLog',
  'consumables/categories': 'ConsumableCategory',
  'consumables/stock': 'ConsumableStock',
  inventory: 'InventoryTask',
  'system/departments': 'Department'
}

export const buildLegacyObjectAliasRoutes = (routeMap: LegacyRouteMap): RouteRecordRaw[] => {
  return Object.entries(routeMap).flatMap(([legacyPath, objectCode]) => ([
    { path: legacyPath, redirect: toObjectListPath(objectCode) },
    { path: `${legacyPath}/create`, redirect: toObjectCreatePath(objectCode) },
    { path: `${legacyPath}/:id`, redirect: (to) => toObjectDetailPath(objectCode, String(to.params.id)) },
    { path: `${legacyPath}/:id/edit`, redirect: (to) => toObjectEditPath(objectCode, String(to.params.id)) },
  ]))
}

const buildLegacyObjectListCreateAliasRoutes = (routeMap: LegacyRouteMap): RouteRecordRaw[] => {
  return Object.entries(routeMap).flatMap(([legacyPath, objectCode]) => ([
    { path: legacyPath, redirect: toObjectListPath(objectCode) },
    { path: `${legacyPath}/create`, redirect: toObjectCreatePath(objectCode) }
  ]))
}

const buildLegacyObjectListAliasRoutes = (routeMap: LegacyRouteMap): RouteRecordRaw[] => {
  return Object.entries(routeMap).map(([legacyPath, objectCode]) => ({
    path: legacyPath,
    redirect: toObjectListPath(objectCode)
  }))
}

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    component: AuthLayout,
    children: [
      {
        path: '',
        name: 'Login',
        component: Login
      }
    ]
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard
      },

      // ============================================================
      // UNIFIED DYNAMIC OBJECT ROUTES (Primary routing pattern)
      // ============================================================
      // All business objects now use /objects/{code} pattern
      {
        path: 'objects/:code',
        name: 'DynamicObjectList',
        component: DynamicListPage,
        meta: { title: 'menu.routes.objectList' }
      },
      {
        path: 'objects/:code/create',
        name: 'DynamicObjectCreate',
        component: DynamicFormPage,
        meta: { title: 'menu.routes.objectCreate' }
      },
      {
        path: 'objects/:code/:id',
        name: 'DynamicObjectDetail',
        component: DynamicDetailPage,
        meta: { title: 'menu.routes.objectDetail' }
      },
      {
        path: 'objects/:code/:id/edit',
        name: 'DynamicObjectEdit',
        redirect: (to) => ({
          name: 'DynamicObjectDetail',
          params: { code: to.params.code, id: to.params.id },
          query: { ...to.query, action: 'edit' }
        }),
        meta: { title: 'menu.routes.objectEdit' }
      },

      // ============================================================
      // LEGACY ROUTE ALIASES (Backward compatibility)
      // ============================================================
      // These routes redirect to the unified /objects/{code} pattern
      // They are kept for backward compatibility with existing bookmarks/links

      ...buildLegacyObjectAliasRoutes(LEGACY_OBJECT_FULL_CRUD_ROUTES),
      ...buildLegacyObjectListCreateAliasRoutes(LEGACY_OBJECT_LIST_CREATE_ROUTES),
      ...buildLegacyObjectListAliasRoutes(LEGACY_OBJECT_LIST_ONLY_ROUTES),

      // ============================================================
      // LIFECYCLE ROUTES (Purchase Request / Maintenance / Disposal)
      // ============================================================
      {
        path: 'assets/lifecycle/purchase-requests',
        name: 'PurchaseRequestList',
        component: () => import('@/views/lifecycle/PurchaseRequestList.vue'),
        meta: { title: 'assets.lifecycle.purchaseRequest.title' }
      },
      {
        path: 'assets/lifecycle/purchase-requests/create',
        name: 'PurchaseRequestCreate',
        component: () => import('@/views/lifecycle/PurchaseRequestDetail.vue'),
        meta: { title: 'assets.lifecycle.purchaseRequest.createTitle' }
      },
      {
        path: 'assets/lifecycle/purchase-requests/:id',
        name: 'PurchaseRequestDetail',
        component: () => import('@/views/lifecycle/PurchaseRequestDetail.vue'),
        meta: { title: 'assets.lifecycle.purchaseRequest.detailTitle' }
      },
      {
        path: 'assets/lifecycle/maintenance',
        name: 'MaintenanceList',
        component: () => import('@/views/lifecycle/MaintenanceList.vue'),
        meta: { title: 'assets.lifecycle.maintenance.title' }
      },
      {
        path: 'assets/lifecycle/maintenance/create',
        name: 'MaintenanceCreate',
        component: () => import('@/views/lifecycle/MaintenanceDetail.vue'),
        meta: { title: 'assets.lifecycle.maintenance.createTitle' }
      },
      {
        path: 'assets/lifecycle/maintenance/:id',
        name: 'MaintenanceDetail',
        component: () => import('@/views/lifecycle/MaintenanceDetail.vue'),
        meta: { title: 'assets.lifecycle.maintenance.detailTitle' }
      },
      {
        path: 'assets/lifecycle/disposal-requests',
        name: 'DisposalRequestList',
        component: () => import('@/views/lifecycle/DisposalRequestList.vue'),
        meta: { title: 'assets.lifecycle.disposalRequest.title' }
      },
      {
        path: 'assets/lifecycle/disposal-requests/create',
        name: 'DisposalRequestCreate',
        component: () => import('@/views/lifecycle/DisposalRequestDetail.vue'),
        meta: { title: 'assets.lifecycle.disposalRequest.createTitle' }
      },
      {
        path: 'assets/lifecycle/disposal-requests/:id',
        name: 'DisposalRequestDetail',
        component: () => import('@/views/lifecycle/DisposalRequestDetail.vue'),
        meta: { title: 'assets.lifecycle.disposalRequest.detailTitle' }
      },

      // ── P3 Lifecycle Routes ──────────────────────────────────────────────
      {
        path: 'assets/lifecycle/asset-receipts',
        name: 'AssetReceiptList',
        component: () => import('@/views/lifecycle/AssetReceiptList.vue'),
        meta: { title: 'assets.lifecycle.assetReceipt.title' }
      },
      {
        path: 'assets/lifecycle/asset-receipts/create',
        name: 'AssetReceiptCreate',
        component: () => import('@/views/lifecycle/AssetReceiptDetail.vue'),
        meta: { title: 'assets.lifecycle.assetReceipt.createTitle' }
      },
      {
        path: 'assets/lifecycle/asset-receipts/:id',
        name: 'AssetReceiptDetail',
        component: () => import('@/views/lifecycle/AssetReceiptDetail.vue'),
        meta: { title: 'assets.lifecycle.assetReceipt.detailTitle' }
      },
      {
        path: 'assets/lifecycle/maintenance-plans',
        name: 'MaintenancePlanList',
        component: () => import('@/views/lifecycle/MaintenancePlanList.vue'),
        meta: { title: 'assets.lifecycle.maintenancePlan.title' }
      },
      {
        path: 'assets/lifecycle/maintenance-plans/create',
        name: 'MaintenancePlanCreate',
        component: () => import('@/views/lifecycle/MaintenancePlanDetail.vue'),
        meta: { title: 'assets.lifecycle.maintenancePlan.createTitle' }
      },
      {
        path: 'assets/lifecycle/maintenance-plans/:id',
        name: 'MaintenancePlanDetail',
        component: () => import('@/views/lifecycle/MaintenancePlanDetail.vue'),
        meta: { title: 'assets.lifecycle.maintenancePlan.detailTitle' }
      },
      {
        path: 'assets/lifecycle/maintenance-tasks',
        name: 'MaintenanceTaskList',
        component: () => import('@/views/lifecycle/MaintenanceTaskList.vue'),
        meta: { title: 'assets.lifecycle.maintenanceTask.title' }
      },
      {
        path: 'assets/lifecycle/maintenance-tasks/create',
        name: 'MaintenanceTaskCreate',
        component: () => import('@/views/lifecycle/MaintenanceTaskDetail.vue'),
        meta: { title: 'assets.lifecycle.maintenanceTask.createTitle' }
      },
      {
        path: 'assets/lifecycle/maintenance-tasks/:id',
        name: 'MaintenanceTaskDetail',
        component: () => import('@/views/lifecycle/MaintenanceTaskDetail.vue'),
        meta: { title: 'assets.lifecycle.maintenanceTask.detailTitle' }
      },

      // Inventory Routes
      {
        path: 'inventory/task/:id/execute',
        name: 'TaskExecute',
        component: () => import('@/views/inventory/TaskExecute.vue'),
        meta: { title: 'menu.routes.taskExecute', hideMenu: true }
      },

      // Finance Routes (keep as-is for now, not migrated to dynamic routing)
      {
        path: 'finance/vouchers',
        name: 'VoucherList',
        component: () => import('@/views/finance/VoucherList.vue'),
        meta: { title: 'menu.routes.vouchers' }
      },
      {
        path: 'finance/vouchers/:id',
        name: 'VoucherDetail',
        component: () => import('@/views/finance/VoucherDetail.vue'),
        meta: { title: 'menu.routes.vouchers', hideMenu: true }
      },
      {
        path: 'finance/depreciation',
        name: 'DepreciationList',
        component: () => import('@/views/finance/DepreciationList.vue'),
        meta: { title: 'menu.routes.depreciation' }
      },

      // Insurance Routes  (specialized pages beyond dynamic object engine)
      {
        path: 'insurance/dashboard',
        name: 'InsuranceDashboard',
        component: () => import('@/views/insurance/InsuranceDashboard.vue'),
        meta: { title: 'menu.routes.insuranceDashboard' }
      },
      {
        path: 'insurance/claims',
        name: 'ClaimList',
        component: () => import('@/views/insurance/ClaimList.vue'),
        meta: { title: 'menu.routes.claimList' }
      },

      // Leasing Routes (specialized pages beyond dynamic object engine)
      {
        path: 'leasing/dashboard',
        name: 'LeasingDashboard',
        component: () => import('@/views/leasing/LeasingDashboard.vue'),
        meta: { title: 'menu.routes.leasingDashboard' }
      },
      {
        path: 'leasing/payments',
        name: 'RentPaymentList',
        component: () => import('@/views/leasing/RentPaymentList.vue'),
        meta: { title: 'menu.routes.rentPayments' }
      },

      // Reports
      {
        path: 'reports/center',
        name: 'ReportCenter',
        component: () => import('@/views/reports/ReportCenter.vue'),
        meta: { title: 'menu.routes.reportCenter' }
      },

      // System Routes (Special system pages that are not business objects)

      {
        path: 'system/business-objects',
        name: 'BusinessObjectList',
        component: () => import('@/views/system/BusinessObjectList.vue'),
        meta: { title: 'menu.routes.businessObjects' }
      },
      {
        path: 'system/field-definitions',
        name: 'FieldDefinitionList',
        component: () => import('@/views/system/FieldDefinitionList.vue'),
        meta: { title: 'menu.routes.fieldDefinitions' }
      },
      {
        path: 'system/page-layouts',
        name: 'PageLayoutList',
        component: () => import('@/views/system/PageLayoutList.vue'),
        meta: { title: 'menu.routes.pageLayouts' }
      },
      {
        path: 'system/languages',
        name: 'LanguageList',
        component: () => import('@/views/system/LanguageList.vue'),
        meta: { title: 'menu.routes.languages' }
      },
      {
        path: 'system/translations',
        name: 'TranslationList',
        component: () => import('@/views/system/TranslationList.vue'),
        meta: { title: 'menu.routes.translations' }
      },
      {
        path: 'system/page-layouts/designer',
        name: 'PageLayoutDesigner',
        component: () => import('@/views/system/PageLayoutDesigner.vue'),
        meta: { title: 'menu.routes.layoutDesigner', hideMenu: true }
      },
      {
        path: 'system/business-rules/:objectCode?',
        name: 'BusinessRuleList',
        component: () => import('@/views/system/BusinessRuleList.vue'),
        meta: { title: 'menu.routes.businessRules' }
      },
      {
        path: 'system/config-packages',
        name: 'ConfigPackageList',
        component: () => import('@/views/system/ConfigPackageList.vue'),
        meta: { title: 'menu.routes.configPackages' }
      },
      {
        path: 'system/dictionary-types',
        name: 'DictionaryTypeList',
        component: () => import('@/views/system/DictionaryTypeList.vue'),
        meta: { title: 'menu.routes.dictionaryTypes' }
      },
      {
        path: 'system/sequence-rules',
        name: 'SequenceRuleList',
        component: () => import('@/views/system/SequenceRuleList.vue'),
        meta: { title: 'menu.routes.sequenceRules' }
      },
      {
        path: 'system/config',
        name: 'SystemConfigList',
        component: () => import('@/views/system/SystemConfigList.vue'),
        meta: { title: 'menu.routes.systemConfig' }
      },
      {
        path: 'system/files',
        name: 'SystemFileList',
        component: () => import('@/views/system/SystemFileList.vue'),
        meta: { title: 'menu.routes.systemFiles' }
      },
      {
        path: 'system/module-workbench',
        name: 'ModuleWorkbench',
        component: () => import('@/views/system/ModuleWorkbench.vue'),
        meta: { title: 'menu.routes.moduleWorkbench' }
      },

      // Workflow Management
      {
        path: 'admin/workflows',
        name: 'WorkflowList',
        component: () => import('@/views/admin/WorkflowList.vue')
      },
      {
        path: 'admin/workflows/create',
        name: 'WorkflowCreate',
        component: () => import('@/views/admin/WorkflowEdit.vue')
      },
      {
        path: 'admin/workflows/:id/edit',
        name: 'WorkflowEdit',
        component: () => import('@/views/admin/WorkflowEdit.vue')
      },
      {
        path: 'admin/permissions',
        name: 'PermissionManagement',
        component: () => import('@/views/admin/PermissionManagement.vue'),
        meta: { title: 'menu.routes.permissions' }
      },

      // Workflow
      {
        path: 'workflow/tasks',
        name: 'TaskCenter',
        component: TaskCenter
      },
      {
        path: 'workflow/task/:id',
        name: 'TaskDetail',
        component: TaskDetail
      },
      {
        path: 'workflow/my-approvals',
        name: 'MyApprovals',
        component: MyApprovals,
        meta: { title: 'menu.routes.myApprovals' }
      },
      {
        path: 'notifications/center',
        name: 'NotificationCenter',
        component: NotificationCenter,
        meta: { title: 'menu.routes.notificationCenter' }
      },
      {
        path: 'notifications/preferences',
        name: 'NotificationPreferences',
        component: NotificationPreferences,
        meta: { title: 'menu.routes.notificationPreferences' }
      },

      // Integration
      {
        path: 'integration/configs',
        name: 'IntegrationConfigList',
        component: () => import('@/views/integration/IntegrationConfigList.vue'),
        meta: { title: 'menu.routes.integrationConfigs' }
      },

      // IT Assets
      {
        path: 'it-assets',
        name: 'ITAssetList',
        component: () => import('@/views/it-assets/ITAssetList.vue'),
        meta: { title: 'menu.routes.itAssets' }
      },
      {
        path: 'it-assets/maintenance',
        name: 'ITMaintenanceList',
        component: () => import('@/views/it-assets/MaintenanceList.vue'),
        meta: { title: 'menu.routes.itMaintenance' }
      },
      {
        path: 'it-assets/configuration-changes',
        name: 'ConfigurationChangeList',
        component: () => import('@/views/it-assets/ConfigurationChangeList.vue'),
        meta: { title: 'menu.routes.configChanges' }
      },

      // Software Licenses
      {
        path: 'software-licenses',
        children: [
          {
            path: 'software',
            name: 'SoftwareCatalog',
            component: () => import('@/views/softwareLicenses/SoftwareCatalog.vue'),
            meta: { title: 'menu.routes.softwareCatalog' }
          },
          {
            path: 'software/create',
            name: 'SoftwareCreate',
            component: () => import('@/views/softwareLicenses/SoftwareForm.vue'),
            meta: { title: 'menu.routes.softwareCreate' }
          },
          {
            path: 'software/:id/edit',
            name: 'SoftwareEdit',
            component: () => import('@/views/softwareLicenses/SoftwareForm.vue'),
            meta: { title: 'menu.routes.softwareEdit' }
          },
          {
            path: 'licenses',
            name: 'SoftwareLicenseList',
            component: () => import('@/views/softwareLicenses/SoftwareLicenseList.vue'),
            meta: { title: 'menu.routes.softwareLicenses' }
          },
          {
            path: 'licenses/create',
            name: 'SoftwareLicenseCreate',
            component: () => import('@/views/softwareLicenses/SoftwareLicenseForm.vue'),
            meta: { title: 'menu.routes.softwareLicenseCreate' }
          },
          {
            path: 'licenses/:id/edit',
            name: 'SoftwareLicenseEdit',
            component: () => import('@/views/softwareLicenses/SoftwareLicenseForm.vue'),
            meta: { title: 'menu.routes.softwareLicenseEdit' }
          },
          {
            path: 'allocations',
            name: 'LicenseAllocations',
            component: () => import('@/views/softwareLicenses/AllocationList.vue'),
            meta: { title: 'menu.routes.licenseAllocations' }
          }
        ]
      },

      // Additional legacy routes mapped to unified dynamic object pages.
      ...buildLegacyObjectAliasRoutes(ADDITIONAL_BUSINESS_OBJECT_ROUTES)
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

export default createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})
