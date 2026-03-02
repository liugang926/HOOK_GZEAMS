/**
 * Lazy loading utilities for frontend performance optimization.
 * Provides dynamic imports and progressive loading patterns.
 */

import { defineAsyncComponent, h, type Component, type AsyncComponentLoader } from 'vue'
import { ElSkeleton } from 'element-plus'
import request from '@/utils/request'

/**
 * Default loading component shown while lazy component loads
 */
const DefaultLoading = {
    render() {
        return h(ElSkeleton, { rows: 5, animated: true })
    }
}

/**
 * Default error component shown when lazy load fails
 */
const DefaultError = {
    props: ['error'],
    render() {
        return h('div', { class: 'lazy-error' }, [
            h('p', '加载组件失败'),
            h('button', { onClick: () => window.location.reload() }, '重新加载')
        ])
    }
}

/**
 * Create a lazy-loaded component with loading and error states.
 * 
 * @param loader - Async component loader (e.g., () => import('./Component.vue'))
 * @param options - Configuration options
 */
export function createLazyComponent(
    loader: AsyncComponentLoader,
    options: {
        loadingComponent?: Component
        errorComponent?: Component
        delay?: number
        timeout?: number
        onError?: (error: Error) => void
    } = {}
): Component {
    return defineAsyncComponent({
        loader,
        loadingComponent: options.loadingComponent || DefaultLoading,
        errorComponent: options.errorComponent || DefaultError,
        delay: options.delay ?? 200,        // Show loading after 200ms
        timeout: options.timeout ?? 30000,  // Timeout after 30s
        onError(error, retry, fail) {
            if (options.onError) {
                options.onError(error)
            }
            // Auto-retry once
            if (!error.message.includes('retry')) {
                error.message += ' (retry)'
                retry()
            } else {
                fail()
            }
        }
    })
}

/**
 * Prefetch a component to warm the cache.
 * Call this on hover or when you anticipate the user will navigate soon.
 */
export function prefetchComponent(loader: () => Promise<any>): void {
    // Start loading the component in the background
    loader().catch(() => {
        // Silently fail - will retry when actually needed
    })
}

/**
 * Lazy load configuration components
 */
export const LazyComponents = {
    // WYSIWYG Layout Designer - real-time preview layout designer
    WysiwygLayoutDesigner: createLazyComponent(
        () => import('@/components/designer/WysiwygLayoutDesigner.vue')
    ),

    // Rule Designer - heavy component with JSON Logic builder
    RuleDesigner: createLazyComponent(
        () => import('@/components/designer/RuleDesigner.vue')
    ),

    // Config Package Manager
    ConfigPackageList: createLazyComponent(
        () => import('@/views/system/ConfigPackageList.vue')
    ),

    // Business Rule List
    BusinessRuleList: createLazyComponent(
        () => import('@/views/system/BusinessRuleList.vue')
    )
}

/**
 * Data prefetch utilities for optimistic loading
 */
export const DataPrefetch = {
    /**
     * Prefetch business object metadata
     * Uses /api/system/objects/{code}/metadata/ endpoint
     */
    async prefetchMetadata(objectCode: string): Promise<void> {
        try {
            await request.get(`/system/objects/${objectCode}/metadata/`, { silent: true })
        } catch {
            // Silently fail
        }
    },

    /**
     * Prefetch field definitions
     */
    async prefetchFields(objectCode: string): Promise<void> {
        try {
            await request.get('/system/field-definitions/', {
                params: { business_object__code: objectCode },
                silent: true
            })
        } catch {
            // Silently fail
        }
    },

    /**
     * Prefetch multiple resources in parallel
     */
    async prefetchAll(objectCode: string): Promise<void> {
        await Promise.all([
            this.prefetchMetadata(objectCode),
            this.prefetchFields(objectCode)
        ])
    }
}

/**
 * Intersection Observer based lazy loading for components
 */
export function useLazyLoad(callback: () => void, options?: IntersectionObserverInit) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                callback()
                observer.disconnect()
            }
        })
    }, {
        rootMargin: '100px',
        threshold: 0.1,
        ...options
    })

    return {
        observe: (el: Element) => observer.observe(el),
        disconnect: () => observer.disconnect()
    }
}

export default {
    createLazyComponent,
    prefetchComponent,
    LazyComponents,
    DataPrefetch,
    useLazyLoad
}
