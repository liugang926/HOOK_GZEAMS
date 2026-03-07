export interface LookupUserRecord {
  id: string
  fullName: string
  username: string
  name: string
  code: string
  email: string
  mobile: string
}

export interface LookupBatchGetRequest {
  ids?: string[]
}

export interface LookupTraceWindow extends Window {
  __lookupGetKeys?: string[]
}

export const LOOKUP_USER_POOL: LookupUserRecord[] = [
  {
    id: 'user-alice',
    fullName: 'Alice Stone',
    username: 'alice',
    name: 'Alice Stone',
    code: 'U-ALICE',
    email: 'alice@example.com',
    mobile: '13800000001'
  },
  {
    id: 'user-john',
    fullName: 'John Carter',
    username: 'john',
    name: 'John Carter',
    code: 'U-JOHN',
    email: 'john@example.com',
    mobile: '13800000002'
  },
  {
    id: 'user-zoe',
    fullName: 'Zoe Green',
    username: 'zoe',
    name: 'Zoe Green',
    code: 'U-ZOE',
    email: 'zoe@example.com',
    mobile: '13800000003'
  }
]

export const pickLookupUsersBySearch = (
  keyword: string,
  keys: Array<keyof LookupUserRecord>
): LookupUserRecord[] => {
  const query = keyword.trim().toLowerCase()
  if (!query) return LOOKUP_USER_POOL

  return LOOKUP_USER_POOL.filter((user) => {
    return keys.some((key) => String(user[key] || '').toLowerCase().includes(query))
  })
}
