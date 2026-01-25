import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// Layouts
const MainLayout = () => import('@/layouts/MainLayout.vue')
const AuthLayout = () => import('@/layouts/AuthLayout.vue')

// Pages
const Dashboard = () => import('@/views/Dashboard.vue')
const Login = () => import('@/views/auth/Login.vue')
const AssetList = () => import('@/views/assets/AssetList.vue')
const TaskList = () => import('@/views/inventory/TaskList.vue')
const ConsumableList = () => import('@/views/consumables/ConsumableList.vue')
const DepartmentList = () => import('@/views/system/DepartmentList.vue')
const TaskCenter = () => import('@/views/workflow/TaskCenter.vue')
const TaskDetail = () => import('@/views/workflow/TaskDetail.vue')

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
      {
        path: 'assets',
        name: 'AssetList',
        component: AssetList
      },
      {
        path: 'assets/create',
        name: 'AssetCreate',
        component: () => import('@/views/assets/AssetForm.vue')
      },
      {
        path: 'assets/edit/:id',
        name: 'AssetEdit',
        component: () => import('@/views/assets/AssetForm.vue')
      },
      {
        path: 'assets/:id',
        name: 'AssetDetail',
        component: () => import('@/views/assets/AssetDetail.vue')
      },
      // Asset Operations
      {
        path: 'assets/settings/categories',
        name: 'AssetCategories',
        component: () => import('@/views/assets/settings/CategoryManagement.vue'),
        meta: { title: '分类管理' }
      },
      // Suppliers
      {
        path: 'assets/settings/suppliers',
        name: 'SupplierList',
        component: () => import('@/views/assets/settings/SupplierList.vue'),
        meta: { title: '供应商管理' }
      },
      {
        path: 'assets/settings/suppliers/create',
        name: 'SupplierCreate',
        component: () => import('@/views/assets/settings/SupplierForm.vue'),
        meta: { title: '新建供应商' }
      },
      {
        path: 'assets/settings/suppliers/:id',
        name: 'SupplierDetail',
        component: () => import('@/views/assets/settings/SupplierForm.vue'),
        meta: { title: '供应商详情' }
      },
      {
        path: 'assets/settings/suppliers/:id/edit',
        name: 'SupplierEdit',
        component: () => import('@/views/assets/settings/SupplierForm.vue'),
        meta: { title: '编辑供应商' }
      },
      // Locations
      {
        path: 'assets/settings/locations',
        name: 'LocationList',
        component: () => import('@/views/assets/settings/LocationList.vue'),
        meta: { title: '存放位置管理' }
      },
      {
        path: 'assets/settings/locations/create',
        name: 'LocationCreate',
        component: () => import('@/views/assets/settings/LocationForm.vue'),
        meta: { title: '新建存放位置' }
      },
      {
        path: 'assets/settings/locations/:id',
        name: 'LocationDetail',
        component: () => import('@/views/assets/settings/LocationForm.vue'),
        meta: { title: '位置详情' }
      },
      {
        path: 'assets/settings/locations/:id/edit',
        name: 'LocationEdit',
        component: () => import('@/views/assets/settings/LocationForm.vue'),
        meta: { title: '编辑存放位置' }
      },
      // Status Logs
      {
        path: 'assets/status-logs',
        name: 'AssetStatusLogs',
        component: () => import('@/views/assets/StatusLogList.vue'),
        meta: { title: '资产状态日志' }
      },
      {
        path: 'assets/operations/pickup',
        name: 'PickupList',
        component: () => import('@/views/assets/operations/PickupList.vue')
      },
      {
        path: 'assets/operations/pickup/create',
        name: 'PickupCreate',
        component: () => import('@/views/assets/operations/PickupForm.vue')
      },
      {
        path: 'assets/operations/pickup/:id',
        name: 'PickupDetail', // Re-using form for read-only view logic if needed, or create separate Detail
        component: () => import('@/views/assets/operations/PickupForm.vue')
      },
      {
        path: 'assets/operations/pickup/:id/edit',
        name: 'PickupEdit',
        component: () => import('@/views/assets/operations/PickupForm.vue')
      },
      // Transfer Operations
      {
        path: 'assets/operations/transfer',
        name: 'TransferList',
        component: () => import('@/views/assets/operations/TransferList.vue')
      },
      {
        path: 'assets/operations/transfer/create',
        name: 'TransferCreate',
        component: () => import('@/views/assets/operations/TransferForm.vue')
      },
      // Return Operations
      {
        path: 'assets/operations/return',
        name: 'ReturnList',
        component: () => import('@/views/assets/operations/ReturnList.vue')
      },
      {
        path: 'assets/operations/return/create',
        name: 'ReturnCreate',
        component: () => import('@/views/assets/operations/ReturnForm.vue')
      },
      // Loan Operations
      {
        path: 'assets/operations/loans',
        name: 'LoanList',
        component: () => import('@/views/assets/operations/LoanList.vue')
      },
      {
        path: 'assets/operations/loans/create',
        name: 'LoanCreate',
        component: () => import('@/views/assets/operations/LoanForm.vue')
      },
      {
        path: 'assets/operations/loans/:id',
        name: 'LoanDetail',
        component: () => import('@/views/assets/operations/LoanForm.vue')
      },
      {
        path: 'assets/operations/loans/:id/edit',
        name: 'LoanEdit',
        component: () => import('@/views/assets/operations/LoanForm.vue')
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
      // Permission Management
      {
        path: 'admin/permissions',
        name: 'PermissionManagement',
        component: () => import('@/views/admin/PermissionManagement.vue'),
        meta: { title: '权限管理' }
      },
      {
        path: 'inventory',
        name: 'InventoryTaskList',
        component: TaskList
      },
      {
        path: 'inventory/task/:id/execute',
        name: 'TaskExecute',
        component: () => import('@/views/inventory/TaskExecute.vue'),
        meta: { title: '执行盘点', hideMenu: true }
      },
      {
        path: 'consumables',
        name: 'ConsumableList',
        component: ConsumableList
      },
      // Finance
      {
        path: 'finance/vouchers',
        name: 'VoucherList',
        component: () => import('@/views/finance/VoucherList.vue'),
        meta: { title: '财务凭证' }
      },
      {
        path: 'finance/depreciation',
        name: 'DepreciationList',
        component: () => import('@/views/finance/DepreciationList.vue'),
        meta: { title: '折旧管理' }
      },
      // System
      {
        path: 'system/departments',
        name: 'DepartmentList',
        component: DepartmentList
      },
      // System - Business Objects
      {
        path: 'system/business-objects',
        name: 'BusinessObjectList',
        component: () => import('@/views/system/BusinessObjectList.vue'),
        meta: { title: '业务对象管理' }
      },
      // System - Field Definitions
      {
        path: 'system/field-definitions',
        name: 'FieldDefinitionList',
        component: () => import('@/views/system/FieldDefinitionList.vue'),
        meta: { title: '字段定义管理' }
      },
      // System - Page Layouts
      {
        path: 'system/page-layouts',
        name: 'PageLayoutList',
        component: () => import('@/views/system/PageLayoutList.vue'),
        meta: { title: '页面布局管理' }
      },
      // System - Dictionary Types
      {
        path: 'system/dictionary-types',
        name: 'DictionaryTypeList',
        component: () => import('@/views/system/DictionaryTypeList.vue'),
        meta: { title: '数据字典管理' }
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
      // Software Licenses
      {
        path: 'software-licenses',
        children: [
          {
            path: 'software',
            name: 'SoftwareCatalog',
            component: () => import('@/views/softwareLicenses/SoftwareCatalog.vue'),
            meta: { title: '软件目录' }
          },
          {
            path: 'software/create',
            name: 'SoftwareCreate',
            component: () => import('@/views/softwareLicenses/SoftwareForm.vue'),
            meta: { title: '新建软件' }
          },
          {
            path: 'software/:id/edit',
            name: 'SoftwareEdit',
            component: () => import('@/views/softwareLicenses/SoftwareForm.vue'),
            meta: { title: '编辑软件' }
          },
          {
            path: 'licenses',
            name: 'SoftwareLicenseList',
            component: () => import('@/views/softwareLicenses/SoftwareLicenseList.vue'),
            meta: { title: '软件许可证' }
          },
          {
            path: 'licenses/create',
            name: 'SoftwareLicenseCreate',
            component: () => import('@/views/softwareLicenses/SoftwareLicenseForm.vue'),
            meta: { title: '新建许可证' }
          },
          {
            path: 'licenses/:id/edit',
            name: 'SoftwareLicenseEdit',
            component: () => import('@/views/softwareLicenses/SoftwareLicenseForm.vue'),
            meta: { title: '编辑许可证' }
          },
          {
            path: 'allocations',
            name: 'LicenseAllocations',
            component: () => import('@/views/softwareLicenses/AllocationList.vue'),
            meta: { title: '分配记录' }
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

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
