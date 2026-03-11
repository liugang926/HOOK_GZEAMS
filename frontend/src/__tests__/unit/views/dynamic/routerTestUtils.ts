import { vi } from 'vitest'

export interface RouteMockState {
  params: Record<string, string>
  path?: string
}

export const createRouteMockContext = (initialRoute: RouteMockState) => {
  return {
    pushMock: vi.fn(),
    routeState: { ...initialRoute } as RouteMockState,
  }
}
