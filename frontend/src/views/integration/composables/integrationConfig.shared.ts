export type IntegrationTranslate = (key: string) => string

export interface IntegrationPageRequest {
  page: number
  pageSize: number
}

export interface IntegrationPaginationState extends IntegrationPageRequest {
  total: number
}

export const createIntegrationPaginationState = (pageSize = 20): IntegrationPaginationState => ({
  page: 1,
  pageSize,
  total: 0
})

export interface LatestRequestGuard {
  begin: () => number
  isActive: (requestId: number) => boolean
}

export const createLatestRequestGuard = (): LatestRequestGuard => {
  let activeRequestId = 0

  return {
    begin: () => {
      activeRequestId += 1
      return activeRequestId
    },
    isActive: (requestId: number) => requestId === activeRequestId
  }
}
