import { describe, expect, it } from 'vitest'

import {
  buildPortalHeaderStats,
  getPortalDisplayName,
  getPortalUserInitial,
} from './portalHeaderModel'

const t = (key: string) => key

describe('portalHeaderModel', () => {
  it('derives display name and initial from user info', () => {
    expect(getPortalDisplayName({ fullName: 'Alice Chen', username: 'alice' })).toBe('Alice Chen')
    expect(getPortalDisplayName({ username: 'alice' })).toBe('alice')
    expect(getPortalUserInitial('alice')).toBe('A')
    expect(getPortalUserInitial('')).toBe('U')
  })

  it('builds header stats in display order', () => {
    expect(buildPortalHeaderStats({
      assets: 3,
      pendingRequests: 2,
      pendingTasks: 1,
    }, t)).toEqual([
      { id: 'assets', label: 'portal.stats.assets', value: 3 },
      { id: 'pendingRequests', label: 'portal.stats.pendingRequests', value: 2 },
      { id: 'pendingTasks', label: 'portal.stats.pendingTasks', tone: 'danger', value: 1 },
    ])
  })
})
