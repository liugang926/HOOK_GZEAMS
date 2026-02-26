import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// Layouts
const MainLayout = () => import('@/layouts/MainLayout.vue')
const AuthLayout = () => import('@/layouts/AuthLayout.vue')

// Pages
const Dashboard = () => import('@/views/Dashboard.vue')
const Login = () => import('@/views/auth/Login.vue')
const TaskList = () => import('@/views/inventory/TaskList.vue')
const DepartmentList = () => import('@/views/system/DepartmentList.vue')
const TaskCenter = () => import('@/views/workflow/TaskCenter.vue')
const TaskDetail = () => import('@/views/workflow/TaskDetail.vue')
const MyApprovals = () => import('@/views/workflow/MyApprovals.vue')

// Dynamic Pages (Unified routing for all business objects)
const DynamicListPage = () => import('@/views/dynamic/DynamicListPage.vue')
const DynamicFormPage = () => import('@/views/dynamic/DynamicFormPage.vue')
const DynamicDetailPage = () => import('@/views/dynamic/DynamicDetailPage.vue')

// Business Object Codes mapping for route aliases
// This maps old route paths to new object codes
const BUSINESS_OBJECT_ROUTES: Record<string, string> = {
  // Assets
  'assets': 'Asset',
  'assets/operations/pickup': 'AssetPickup',
  'assets/operations/transfer': 'AssetTransfer',
  'assets/operations/return': 'AssetReturn',
  'assets/operations/loans': 'AssetLoan',
  'assets/settings/categories': 'AssetCategory',
  'assets/settings/suppliers': 'Supplier',
  'assets/settings/locations': 'Location',
  'assets/status-logs': 'AssetStatusLog',
  // Consumables
  'consumables': 'Consumable',
  'consumables/categories': 'ConsumableCategory',
  'consumables/stock': 'ConsumableStock',
  // Inventory
  'inventory': 'InventoryTask',
  // System
  'system/departments': 'Department',
  'system/business-objects': 'BusinessObject',
  'system/field-definitions': 'FieldDefinition',
  'system/page-layouts': 'PageLayout',
}

const routes: RouteRecordRaw[] = [
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
        component: DynamicFormPage,
        meta: { title: 'menu.routes.objectEdit' }
      },

      // ============================================================
      // LEGACY ROUTE ALIASES (Backward compatibility)
      // ============================================================
      // These routes redirect to the unified /objects/{code} pattern
      // They are kept for backward compatibility with existing bookmarks/links

      // Asset Routes
      {
        path: 'assets',
        redirect: '/objects/Asset'
      },
      {
        path: 'assets/create',
        redirect: '/objects/Asset/create'
      },
      {
        path: 'assets/:id/edit',
        redirect: to => `/objects/Asset/${to.params.id}/edit`
      },
      {
        path: 'assets/:id',
        redirect: to => `/objects/Asset/${to.params.id}`
      },
      {
        path: 'assets/settings/categories',
        redirect: '/objects/AssetCategory'
      },
      {
        path: 'assets/settings/categories/create',
        redirect: '/objects/AssetCategory/create'
      },
      {
        path: 'assets/settings/suppliers',
        redirect: '/objects/Supplier'
      },
      {
        path: 'assets/settings/suppliers/create',
        redirect: '/objects/Supplier/create'
      },
      {
        path: 'assets/settings/suppliers/:id',
        redirect: to => `/objects/Supplier/${to.params.id}`
      },
      {
        path: 'assets/settings/suppliers/:id/edit',
        redirect: to => `/objects/Supplier/${to.params.id}/edit`
      },
      {
        path: 'assets/settings/locations',
        redirect: '/objects/Location'
      },
      {
        path: 'assets/settings/locations/create',
        redirect: '/objects/Location/create'
      },
      {
        path: 'assets/settings/locations/:id',
        redirect: to => `/objects/Location/${to.params.id}`
      },
      {
        path: 'assets/settings/locations/:id/edit',
        redirect: to => `/objects/Location/${to.params.id}/edit`
      },
      {
        path: 'assets/status-logs',
        redirect: '/objects/AssetStatusLog'
      },
      {
        path: 'assets/operations/pickup',
        redirect: '/objects/AssetPickup'
      },
      {
        path: 'assets/operations/pickup/create',
        redirect: '/objects/AssetPickup/create'
      },
      {
        path: 'assets/operations/pickup/:id',
        redirect: to => `/objects/AssetPickup/${to.params.id}`
      },
      {
        path: 'assets/operations/pickup/:id/edit',
        redirect: to => `/objects/AssetPickup/${to.params.id}/edit`
      },
      {
        path: 'assets/operations/transfer',
        redirect: '/objects/AssetTransfer'
      },
      {
        path: 'assets/operations/transfer/create',
        redirect: '/objects/AssetTransfer/create'
      },
      {
        path: 'assets/operations/transfer/:id',
        redirect: to => `/objects/AssetTransfer/${to.params.id}`
      },
      {
        path: 'assets/operations/transfer/:id/edit',
        redirect: to => `/objects/AssetTransfer/${to.params.id}/edit`
      },
      {
        path: 'assets/operations/return',
        redirect: '/objects/AssetReturn'
      },
      {
        path: 'assets/operations/return/create',
        redirect: '/objects/AssetReturn/create'
      },
      {
        path: 'assets/operations/return/:id',
        redirect: to => `/objects/AssetReturn/${to.params.id}`
      },
      {
        path: 'assets/operations/return/:id/edit',
        redirect: to => `/objects/AssetReturn/${to.params.id}/edit`
      },
      {
        path: 'assets/operations/loans',
        redirect: '/objects/AssetLoan'
      },
      {
        path: 'assets/operations/loans/create',
        redirect: '/objects/AssetLoan/create'
      },
      {
        path: 'assets/operations/loans/:id',
        redirect: to => `/objects/AssetLoan/${to.params.id}`
      },
      {
        path: 'assets/operations/loans/:id/edit',
        redirect: to => `/objects/AssetLoan/${to.params.id}/edit`
      },

      // Consumable Routes
      {
        path: 'consumables',
        redirect: '/objects/Consumable'
      },
      {
        path: 'consumables/create',
        redirect: '/objects/Consumable/create'
      },
      {
        path: 'consumables/categories',
        redirect: '/objects/ConsumableCategory'
      },
      {
        path: 'consumables/stock',
        redirect: '/objects/ConsumableStock'
      },

      // Inventory Routes
      {
        path: 'inventory',
        redirect: '/objects/InventoryTask'
      },
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

      // System Routes (Special system pages that are not business objects)
      {
        path: 'system/departments',
        redirect: '/objects/Department'
      },
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
      }
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
