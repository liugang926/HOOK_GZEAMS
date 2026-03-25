/**
 * Mock user and authentication data for testing
 */

export const mockCurrentUser = {
  id: 'user-001',
  username: 'admin',
  email: 'admin@example.com',
  first_name: 'System',
  last_name: 'Administrator',
  is_active: true,
  organization: {
    id: 'org-001',
    code: 'org-001',
    name: '测试组织',
    is_active: true
  },
  role: {
    id: 'role-001',
    code: 'admin',
    name: 'Administrator',
    permissions: ['*']
  }
}

export const mockAuthState = {
  isAuthenticated: true,
  token: 'mock-jwt-token',
  user: mockCurrentUser
}

export const mockUsers = [
  mockCurrentUser,
  {
    id: 'user-002',
    username: 'user1',
    email: 'user1@example.com',
    first_name: 'Test',
    last_name: 'User',
    is_active: true,
    organization: { id: 'org-001', code: 'org-001', name: '测试组织' },
    role: { id: 'role-002', code: 'user', name: 'User', permissions: ['view'] }
  }
]
