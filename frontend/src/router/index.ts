import { createRouter, createWebHistory } from 'vue-router'

import type { LocationQueryRaw, RouteRecordRaw } from 'vue-router'

// Layouts
const MainLayout = () => import('@/layouts/MainLayout.vue')
const AuthLayout = () => import('@/layouts/AuthLayout.vue')

// Pages
const Dashboard = () => import('@/views/Dashboard.vue')
const Login = () => import('@/views/auth/Login.vue')
const TaskCenter = () => import('@/views/workflow/TaskCenter.vue')
const TaskDetail = () => import('@/views/workflow/TaskDetail.vue')
const MyApprovals = () => import('@/views/workflow/MyApprovals.vue')
const ApprovalDetail = () => import('@/views/workflow/ApprovalDetail.vue')
const NotificationCenter = () => import('@/views/notifications/NotificationCenter.vue')
const NotificationPreferences = () => import('@/views/notifications/NotificationPreferences.vue')

// Dynamic Pages (Unified routing for all business objects)
const DynamicListPage = () => import('@/views/dynamic/DynamicListPage.vue')
const DynamicFormPage = () => import('@/views/dynamic/DynamicFormPage.vue')
const DynamicDetailPage = () => import('@/views/dynamic/DynamicDetailPage.vue')

type LegacyRouteMap = Record<string, string>
type LegacyLifecycleAliasRouteDefinition = {
  legacyPath: string
  objectCode: string
  titleKey: string
  createTitleKey: string
  detailTitleKey: string
}

const toObjectListPath = (objectCode: string): string => `/objects/${objectCode}`
const toObjectListLocation = (objectCode: string, query?: LocationQueryRaw) => ({
  path: toObjectListPath(objectCode),
  query: { ...(query || {}) }
})
const toObjectCreatePath = (objectCode: string): string => `/objects/${objectCode}/create`
const toObjectCreateLocation = (objectCode: string, query?: LocationQueryRaw) => ({
  path: toObjectCreatePath(objectCode),
  query: { ...(query || {}) }
})
const toObjectDetailPath = (objectCode: string, id: string): string => `/objects/${objectCode}/${id}`
const toObjectEditPath = (objectCode: string, id: string): string => `/objects/${objectCode}/${id}/edit`
const toObjectDetailLocation = (objectCode: string, id: string, query?: LocationQueryRaw) => ({
  path: toObjectDetailPath(objectCode, id),
  query: { ...(query || {}) }
})
const toObjectEditLocation = (objectCode: string, id: string, query?: LocationQueryRaw) => ({
  path: toObjectEditPath(objectCode, id),
  query: { ...(query || {}) }
})
const AGGREGATE_DOCUMENT_EDIT_OBJECT_CODES = new Set([
  'AssetPickup',
  'AssetTransfer',
  'AssetReturn',
  'AssetLoan',
  'PurchaseRequest',
  'AssetReceipt',
  'DisposalRequest',
])

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
  'assets/operations/loans': 'AssetLoan',
  'finance/vouchers': 'FinanceVoucher'
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

const LEGACY_LIFECYCLE_ALIAS_ROUTES: LegacyLifecycleAliasRouteDefinition[] = [
  {
    legacyPath: 'assets/lifecycle/purchase-requests',
    objectCode: 'PurchaseRequest',
    titleKey: 'assets.lifecycle.purchaseRequest.title',
    createTitleKey: 'assets.lifecycle.purchaseRequest.createTitle',
    detailTitleKey: 'assets.lifecycle.purchaseRequest.detailTitle'
  },
  {
    legacyPath: 'assets/lifecycle/maintenance',
    objectCode: 'Maintenance',
    titleKey: 'assets.lifecycle.maintenance.title',
    createTitleKey: 'assets.lifecycle.maintenance.createTitle',
    detailTitleKey: 'assets.lifecycle.maintenance.detailTitle'
  },
  {
    legacyPath: 'assets/lifecycle/disposal-requests',
    objectCode: 'DisposalRequest',
    titleKey: 'assets.lifecycle.disposalRequest.title',
    createTitleKey: 'assets.lifecycle.disposalRequest.createTitle',
    detailTitleKey: 'assets.lifecycle.disposalRequest.detailTitle'
  },
  {
    legacyPath: 'assets/lifecycle/asset-receipts',
    objectCode: 'AssetReceipt',
    titleKey: 'assets.lifecycle.assetReceipt.title',
    createTitleKey: 'assets.lifecycle.assetReceipt.createTitle',
    detailTitleKey: 'assets.lifecycle.assetReceipt.detailTitle'
  },
  {
    legacyPath: 'assets/lifecycle/maintenance-plans',
    objectCode: 'MaintenancePlan',
    titleKey: 'assets.lifecycle.maintenancePlan.title',
    createTitleKey: 'assets.lifecycle.maintenancePlan.createTitle',
    detailTitleKey: 'assets.lifecycle.maintenancePlan.detailTitle'
  },
  {
    legacyPath: 'assets/lifecycle/maintenance-tasks',
    objectCode: 'MaintenanceTask',
    titleKey: 'assets.lifecycle.maintenanceTask.title',
    createTitleKey: 'assets.lifecycle.maintenanceTask.createTitle',
    detailTitleKey: 'assets.lifecycle.maintenanceTask.detailTitle'
  },
  {
    legacyPath: 'assets/lifecycle/asset-warranties',
    objectCode: 'AssetWarranty',
    titleKey: 'assets.lifecycle.assetWarranty.title',
    createTitleKey: 'assets.lifecycle.assetWarranty.createTitle',
    detailTitleKey: 'assets.lifecycle.assetWarranty.detailTitle'
  }
]

export const buildLegacyObjectAliasRoutes = (routeMap: LegacyRouteMap): RouteRecordRaw[] => {
  return Object.entries(routeMap).flatMap(([legacyPath, objectCode]) => ([
    {
      path: legacyPath,
      redirect: (to) => toObjectListLocation(objectCode, to.query as LocationQueryRaw)
    },
    {
      path: `${legacyPath}/create`,
      redirect: (to) => toObjectCreateLocation(objectCode, to.query as LocationQueryRaw)
    },
    { path: `${legacyPath}/:id`, redirect: (to) => toObjectDetailLocation(objectCode, String(to.params.id), to.query as LocationQueryRaw) },
    { path: `${legacyPath}/:id/edit`, redirect: (to) => toObjectEditLocation(objectCode, String(to.params.id), to.query as LocationQueryRaw) },
  ]))
}

const buildLegacyObjectListCreateAliasRoutes = (routeMap: LegacyRouteMap): RouteRecordRaw[] => {
  return Object.entries(routeMap).flatMap(([legacyPath, objectCode]) => ([
    {
      path: legacyPath,
      redirect: (to) => toObjectListLocation(objectCode, to.query as LocationQueryRaw)
    },
    {
      path: `${legacyPath}/create`,
      redirect: (to) => toObjectCreateLocation(objectCode, to.query as LocationQueryRaw)
    }
  ]))
}

const buildLegacyObjectListAliasRoutes = (routeMap: LegacyRouteMap): RouteRecordRaw[] => {
  return Object.entries(routeMap).map(([legacyPath, objectCode]) => ({
    path: legacyPath,
    redirect: (to) => toObjectListLocation(objectCode, to.query as LocationQueryRaw)
  }))
}

const buildLegacyLifecycleAliasRoutes = (
  routeDefinitions: LegacyLifecycleAliasRouteDefinition[]
): RouteRecordRaw[] => {
  return routeDefinitions.flatMap(({
    legacyPath,
    objectCode,
    titleKey,
    createTitleKey,
    detailTitleKey
  }) => ([
    {
      path: legacyPath,
      redirect: (to) => toObjectListLocation(objectCode, to.query as LocationQueryRaw),
      meta: { title: titleKey }
    },
    {
      path: `${legacyPath}/create`,
      redirect: (to) => toObjectCreateLocation(objectCode, to.query as LocationQueryRaw),
      meta: { title: createTitleKey }
    },
    {
      path: `${legacyPath}/:id`,
      redirect: (to) => toObjectDetailLocation(objectCode, String(to.params.id), to.query as LocationQueryRaw),
      meta: { title: detailTitleKey }
    }
  ]))
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
        path: 'objects/:code/:id/edit-form',
        name: 'DynamicObjectEditForm',
        component: DynamicFormPage,
        meta: { title: 'menu.routes.objectEdit', hideMenu: true }
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
        redirect: (to) => {
          const objectCode = String(to.params.code || '').trim()
          if (AGGREGATE_DOCUMENT_EDIT_OBJECT_CODES.has(objectCode)) {
            return {
              name: 'DynamicObjectEditForm',
              params: { code: to.params.code, id: to.params.id },
              query: { ...to.query }
            }
          }
          return {
            name: 'DynamicObjectDetail',
            params: { code: to.params.code, id: to.params.id },
            query: { ...to.query, action: 'edit' }
          }
        },
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
      // LEGACY LIFECYCLE ROUTE ALIASES
      // ============================================================
      // Lifecycle pages now resolve through the unified /objects/{code} routes.
      // Keep these redirects only for existing bookmarks and legacy menu URLs.
      ...buildLegacyLifecycleAliasRoutes(LEGACY_LIFECYCLE_ALIAS_ROUTES),

      // Inventory Routes
      {
        path: 'inventory/task/:id/execute',
        name: 'TaskExecute',
        component: () => import('@/views/inventory/TaskExecute.vue'),
        meta: { title: 'menu.routes.taskExecute', hideMenu: true }
      },

      // Finance Routes
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
        path: 'system/menu-management',
        name: 'MenuManagement',
        component: () => import('@/views/system/SystemMenuManagement.vue'),
        meta: { title: 'menu.routes.menuManagement' }
      },
      {
        path: 'system/menu-layout-management',
        name: 'MenuLayoutManagement',
        component: () => import('@/views/system/SystemMenuLayoutManagement.vue'),
        meta: { title: 'menu.routes.menuLayoutManagement' }
      },
      {
        path: 'system/branding',
        name: 'SystemBranding',
        component: () => import('@/views/system/SystemBranding.vue'),
        meta: { title: 'menu.routes.systemBranding' }
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
      {
        path: 'system/sso',
        name: 'SSOConfigPage',
        component: () => import('@/views/system/SSOConfigPage.vue'),
        meta: { title: 'menu.routes.ssoConfig' }
      },
      {
        path: 'system/organization-tree',
        name: 'OrganizationTree',
        component: () => import('@/views/system/OrganizationTree.vue'),
        meta: { title: 'menu.routes.organizationTree' }
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
        alias: ['/workflows/tasks'],
        component: TaskCenter
      },
      {
        path: 'workflow/task/:id',
        name: 'TaskDetail',
        alias: ['/workflows/task/:id'],
        component: TaskDetail
      },
      {
        path: 'workflow/my-approvals',
        name: 'MyApprovals',
        alias: ['/workflows/my-approvals'],
        component: MyApprovals,
        meta: { title: 'menu.routes.myApprovals' }
      },
      {
        path: 'workflow/dashboard',
        name: 'WorkflowDashboard',
        alias: ['/workflows/dashboard'],
        component: () => import('@/views/workflow/WorkflowDashboard.vue'),
        meta: { title: 'menu.routes.workflowDashboard' }
      },
      {
        path: 'workflow/approvals/:taskId',
        name: 'ApprovalDetail',
        alias: ['/workflows/approvals/:taskId'],
        component: ApprovalDetail,
        meta: { title: 'menu.routes.approvalDetail', hideMenu: true }
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
