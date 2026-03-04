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

  export interface AxiosInstance {
    <T = any, D = any>(config: AxiosRequestConfig<D>): Promise<T>
    <T = any, D = any>(url: string, config?: AxiosRequestConfig<D>): Promise<T>
    request<T = any, D = any>(config: AxiosRequestConfig<D>): Promise<T>
    get<T = any, D = any>(url: string, config?: AxiosRequestConfig<D>): Promise<T>
    delete<T = any, D = any>(url: string, config?: AxiosRequestConfig<D>): Promise<T>
    head<T = any, D = any>(url: string, config?: AxiosRequestConfig<D>): Promise<T>
    options<T = any, D = any>(url: string, config?: AxiosRequestConfig<D>): Promise<T>
    post<T = any, D = any>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<T>
    put<T = any, D = any>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<T>
    patch<T = any, D = any>(url: string, data?: D, config?: AxiosRequestConfig<D>): Promise<T>
  }
}
