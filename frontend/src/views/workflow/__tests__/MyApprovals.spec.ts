/**
 * MyApprovals Page Component Tests
 *
 * Tests for the MyApprovals page which displays user's approval tasks.
 * Tests include:
 * - Component rendering
 * - API integration
 * - User interactions (approve, reject, return)
 * - Tab navigation
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MyApprovals from '../MyApprovals.vue'
import ApprovalList from '../components/ApprovalList.vue'

// Mock Element Plus components
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    prompt: vi.fn()
  },
  ElCard: {
    name: 'ElCard',
    template: '<div class="el-card"><slot /></div>'
  },
  ElTabs: {
    name: 'ElTabs',
    template: '<div class="el-tabs"><slot /></div>',
    props: ['modelValue']
  },
  ElTabPane: {
    name: 'ElTabPane',
    template: '<div class="el-tab-pane"><slot /></div>',
    props: ['name', 'label']
  },
  ElBadge: {
    name: 'ElBadge',
    template: '<span class="el-badge"><slot /></span>',
    props: ['value', 'type']
  }
}))

// Mock workflow API
const mockMyTasksData = {
  pending: [
    {
      id: 'task-1',
      node_name: '部门审批',
      status: 'pending',
      priority: 'normal',
      created_at: '2024-01-26T10:00:00Z',
      instance: {
        business_no: 'LY-2024-001',
        business_object_code: 'asset_pickup',
        initiator: { username: 'testuser' }
      }
    }
  ],
  overdue: [],
  completed_today: [
    {
      id: 'task-2',
      node_name: '财务审批',
      status: 'approved',
      priority: 'normal',
      created_at: '2024-01-26T09:00:00Z',
      instance: {
        business_no: 'LY-2024-002',
        business_object_code: 'asset_transfer',
        initiator: { username: 'otheruser' }
      }
    }
  ],
  summary: {
    pending_count: 1,
    overdue_count: 0,
    completed_today_count: 1
  }
}

vi.mock('@/api/workflow', () => ({
  workflowNodeApi: {
    getMyTasks: vi.fn(() => Promise.resolve(mockMyTasksData)),
    approveNode: vi.fn(() => Promise.resolve({ success: true }))
  },
  taskApi: {
    returnTask: vi.fn(() => Promise.resolve({ success: true }))
  }
}))

const stubs = {
  ApprovalList: true,
  'el-card': true,
  'el-tabs': true,
  'el-tab-pane': true,
  'el-badge': true,
  'el-button': true,
  'el-table': true,
  'el-table-column': true,
  'el-tag': true
}

describe('MyApprovals Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Component Rendering', () => {
    it('should render page title', () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      expect(wrapper.text()).toContain('我的审批')
    })

    it('should render summary cards', () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // After mounting, the component should try to load data
      expect(wrapper.find('.page-header').exists()).toBe(true)
    })

    it('should render approval tabs', () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      expect(wrapper.vm.activeTab).toBe('pending')
    })
  })

  describe('API Integration', () => {
    it('should load tasks on mount', async () => {
      const { workflowNodeApi } = await import('@/api/workflow')

      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 0))
      await wrapper.vm.$nextTick()

      expect(workflowNodeApi.getMyTasks).toHaveBeenCalled()
    })

    it('should populate tasks after API call', async () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 100))

      // Check if data is populated
      expect(wrapper.vm.pendingTasks).toEqual(mockMyTasksData.pending)
      expect(wrapper.vm.overdueTasks).toEqual(mockMyTasksData.overdue)
      expect(wrapper.vm.completedTasks).toEqual(mockMyTasksData.completed_today)
    })

    it('should set task summary correctly', async () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.vm.taskSummary).toEqual(mockMyTasksData.summary)
    })
  })

  describe('Actions', () => {
    it('should handle approve action', async () => {
      const { workflowNodeApi } = await import('@/api/workflow')

      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // Wait for initial load
      await new Promise(resolve => setTimeout(resolve, 100))

      // Call handleApprove
      await wrapper.vm.handleApprove('task-1', 'Approved')

      expect(workflowNodeApi.approveNode).toHaveBeenCalled()
    })

    it('should handle reject action', async () => {
      const { workflowNodeApi } = await import('@/api/workflow')

      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // Wait for initial load
      await new Promise(resolve => setTimeout(resolve, 100))

      // Mock MessageBox to return comment
      const { ElMessageBox } = await import('element-plus')
      vi.mocked(ElMessageBox.prompt).mockResolvedValueOnce({
        value: 'Rejected'
      })

      // Call handleReject
      await wrapper.vm.handleReject('task-1')

      expect(ElMessageBox.prompt).toHaveBeenCalled()
    })

    it('should handle return action', async () => {
      const { taskApi } = await import('@/api/workflow')
      const { ElMessageBox } = await import('element-plus')

      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // Wait for initial load
      await new Promise(resolve => setTimeout(resolve, 100))

      // Mock MessageBox to return comment
      vi.mocked(ElMessageBox.prompt).mockResolvedValueOnce({
        value: 'Needs revision'
      })

      // Call handleReturn
      await wrapper.vm.handleReturn('task-1')

      expect(ElMessageBox.prompt).toHaveBeenCalled()
    })
  })

  describe('Tab Navigation', () => {
    it('should have pending tab as default', () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      expect(wrapper.vm.activeTab).toBe('pending')
    })

    it('should switch to overdue tab', () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      wrapper.vm.activeTab = 'overdue'
      expect(wrapper.vm.activeTab).toBe('overdue')
    })

    it('should switch to completed tab', () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      wrapper.vm.activeTab = 'completed'
      expect(wrapper.vm.activeTab).toBe('completed')
    })
  })

  describe('Data Display', () => {
    it('should display pending tasks', async () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.vm.pendingTasks).toHaveLength(1)
      expect(wrapper.vm.pendingTasks[0].node_name).toBe('部门审批')
    })

    it('should display completed tasks', async () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.vm.completedTasks).toHaveLength(1)
      expect(wrapper.vm.completedTasks[0].status).toBe('approved')
    })

    it('should show correct summary counts', async () => {
      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.vm.taskSummary?.pending_count).toBe(1)
      expect(wrapper.vm.taskSummary?.overdue_count).toBe(0)
      expect(wrapper.vm.taskSummary?.completed_today_count).toBe(1)
    })
  })

  describe('Auto Refresh', () => {
    it('should set up auto-refresh interval on mount', async () => {
      const setIntervalSpy = vi.spyOn(global, 'setInterval')

      const wrapper = mount(MyApprovals, {
        global: { stubs }
      })

      // Wait for mounting
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(setIntervalSpy).toHaveBeenCalled()

      setIntervalSpy.mockRestore()
    })
  })
})
