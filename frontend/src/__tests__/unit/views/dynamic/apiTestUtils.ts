import { vi } from 'vitest'

export const createListApiMockContext = () => ({
  listMock: vi.fn(),
  getMetadataMock: vi.fn(),
  batchDeleteMock: vi.fn(),
  deleteMock: vi.fn(),
})

export const createCrudApiMockContext = () => ({
  getMetadataMock: vi.fn(),
  getRecordMock: vi.fn(),
  createMock: vi.fn(),
  updateMock: vi.fn(),
})

export const createMetadataApiMockContext = () => ({
  getMetadataMock: vi.fn(),
  getSlaMock: vi.fn(),
})

export const createRuntimeLayoutMockContext = () => ({
  resolveRuntimeLayoutMock: vi.fn(),
})
