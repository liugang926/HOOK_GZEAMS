import 'axios'

declare module 'axios' {
  export interface AxiosRequestConfig {
    /**
     * When true, suppress global error toasts in `handleApiError`.
     * The request still rejects and callers can handle it explicitly.
     */
    silent?: boolean

    /**
     * When true, do not attach Authorization / organization headers.
     * Use for third-party absolute URLs to avoid leaking credentials.
     */
    noAuth?: boolean

    /**
     * Response unwrapping behavior for `{ success, data }` API envelope.
     * - `auto` (default): unwrap only when `data` is present, otherwise return raw payload
     * - `data`: always return `data` (may be undefined)
     * - `none`: never unwrap (always return raw payload)
     */
    unwrap?: 'auto' | 'data' | 'none'
  }
}
