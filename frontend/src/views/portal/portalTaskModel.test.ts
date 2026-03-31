import { describe, expect, it } from 'vitest'

import {
  getPortalTaskInitiator,
  getPortalTaskPath,
  getPortalTaskTime,
  getPortalTaskTitle,
  getPortalTaskTypeLabel,
} from './portalTaskModel'

describe('portalTaskModel', () => {
  it('builds stable task display fields', () => {
    const task = {
      id: 'task-1',
      businessTitle: 'Approve Purchase Request',
      createdBy: 'Alex',
      assignedAt: '2026-03-19 10:00:00'
    }

    expect(getPortalTaskTitle(task)).toBe('Approve Purchase Request')
    expect(getPortalTaskInitiator(task)).toBe('Alex')
    expect(getPortalTaskTime(task)).toBe('2026-03-19 10:00:00')
    expect(getPortalTaskPath(task.id)).toBe('/workflow/approvals/task-1')
    expect(getPortalTaskTypeLabel({} as any, (key) => key)).toBe('portal.tasks.approvalTask')
  })
})
