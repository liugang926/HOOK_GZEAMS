import { vi } from 'vitest'

export interface RouteMockState {
  params: Record<string, string>
  path?: string
  query?: Record<string, string | string[] | null | undefined>
}

export const createRouteMockContext = (initialRoute: RouteMockState) => {
  return {
    pushMock: vi.fn(),
    routeState: { ...initialRoute } as RouteMockState,
  }
}
