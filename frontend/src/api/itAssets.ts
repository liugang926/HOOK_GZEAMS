import request from '@/utils/request'

// =============================================================================
// IT Asset Info API
// =============================================================================

export interface ITAssetInfo {
    id: string
    asset: string
    asset_code: string
    asset_name: string
    cpu_model?: string
    cpu_cores?: number
    cpu_threads?: number
    ram_capacity?: number
    ram_type?: string
    ram_slots?: number
    disk_type?: 'HDD' | 'SSD' | 'NVMe' | 'SATA'
    disk_type_display?: string
    disk_capacity?: number
    disk_count?: number
    gpu_model?: string
    gpu_memory?: number
    mac_address?: string
    ip_address?: string
    hostname?: string
    os_name?: string
    os_version?: string
    os_architecture?: string
    os_license_key?: string
    disk_encrypted?: boolean
    antivirus_software?: string
    antivirus_enabled?: boolean
    ad_domain?: string
    ad_computer_name?: string
    full_config?: string
    created_at: string
    updated_at: string
}

export const itAssetInfoApi = {
    list(params?: any) {
        return request({
            url: '/it-assets/it-assets/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/it-assets/it-assets/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<ITAssetInfo>) {
        return request({
            url: '/it-assets/it-assets/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<ITAssetInfo>) {
        return request({
            url: `/it-assets/it-assets/${id}/`,
            method: 'put',
            data
        })
    },

    partialUpdate(id: string, data: Partial<ITAssetInfo>) {
        return request({
            url: `/it-assets/it-assets/${id}/`,
            method: 'patch',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/it-assets/it-assets/${id}/`,
            method: 'delete'
        })
    }
}

// =============================================================================
// Software Catalog API
// =============================================================================

export interface Software {
    id: string
    name: string
    vendor?: string
    version?: string
    category?: string
    license_type: 'open_source' | 'freeware' | 'commercial' | 'enterprise' | 'subscription' | 'oem'
    license_type_display?: string
    description?: string
    website_url?: string
    licenses_count?: number
    created_at: string
    updated_at: string
}

export const softwareApi = {
    list(params?: any) {
        return request({
            url: '/it-assets/software/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/it-assets/software/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<Software>) {
        return request({
            url: '/it-assets/software/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<Software>) {
        return request({
            url: `/it-assets/software/${id}/`,
            method: 'put',
            data
        })
    },

    partialUpdate(id: string, data: Partial<Software>) {
        return request({
            url: `/it-assets/software/${id}/`,
            method: 'patch',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/it-assets/software/${id}/`,
            method: 'delete'
        })
    }
}

// =============================================================================
// Software License API
// =============================================================================

export interface SoftwareLicense {
    id: string
    software: string
    software_name: string
    software_vendor?: string
    license_key?: string
    seats: number
    seats_used: number
    available_seats?: number
    purchase_date?: string
    expiry_date?: string
    cost?: number
    currency: string
    status: 'active' | 'expired' | 'suspended' | 'terminated'
    status_display?: string
    is_expired?: boolean
    vendor_reference?: string
    notes?: string
    created_at: string
    updated_at: string
}

export const softwareLicenseApi = {
    list(params?: any) {
        return request({
            url: '/it-assets/licenses/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/it-assets/licenses/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<SoftwareLicense>) {
        return request({
            url: '/it-assets/licenses/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<SoftwareLicense>) {
        return request({
            url: `/it-assets/licenses/${id}/`,
            method: 'put',
            data
        })
    },

    partialUpdate(id: string, data: Partial<SoftwareLicense>) {
        return request({
            url: `/it-assets/licenses/${id}/`,
            method: 'patch',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/it-assets/licenses/${id}/`,
            method: 'delete'
        })
    },

    expiring() {
        return request({
            url: '/it-assets/licenses/expiring/',
            method: 'get'
        })
    }
}

// =============================================================================
// License Allocation API
// =============================================================================

export interface LicenseAllocation {
    id: string
    license: string
    software_name: string
    asset: string
    asset_code: string
    asset_name: string
    allocated_by?: string
    allocated_by_username?: string
    allocated_date: string
    deallocated_by?: string
    deallocated_by_username?: string
    deallocated_date?: string
    notes?: string
    is_active?: boolean
    created_at: string
}

export const licenseAllocationApi = {
    list(params?: any) {
        return request({
            url: '/it-assets/license-allocations/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/it-assets/license-allocations/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<LicenseAllocation>) {
        return request({
            url: '/it-assets/license-allocations/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<LicenseAllocation>) {
        return request({
            url: `/it-assets/license-allocations/${id}/`,
            method: 'put',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/it-assets/license-allocations/${id}/`,
            method: 'delete'
        })
    },

    deallocate(id: string, notes?: string) {
        return request({
            url: `/it-assets/license-allocations/${id}/deallocate/`,
            method: 'post',
            data: { notes }
        })
    }
}

// =============================================================================
// IT Maintenance Record API
// =============================================================================

export interface ITMaintenanceRecord {
    id: string
    asset: string
    asset_code: string
    asset_name: string
    maintenance_type: 'preventive' | 'corrective' | 'upgrade' | 'replacement' | 'inspection' | 'cleaning' | 'other'
    maintenance_type_display?: string
    title: string
    description?: string
    performed_by?: string
    performed_by_username?: string
    maintenance_date: string
    cost?: number
    vendor?: string
    notes?: string
    created_at: string
    updated_at: string
}

export const itMaintenanceApi = {
    list(params?: any) {
        return request({
            url: '/it-assets/maintenance/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/it-assets/maintenance/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<ITMaintenanceRecord>) {
        return request({
            url: '/it-assets/maintenance/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<ITMaintenanceRecord>) {
        return request({
            url: `/it-assets/maintenance/${id}/`,
            method: 'put',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/it-assets/maintenance/${id}/`,
            method: 'delete'
        })
    }
}

// =============================================================================
// Configuration Change API
// =============================================================================

export interface ConfigurationChange {
    id: string
    asset: string
    asset_code: string
    asset_name: string
    field_name: string
    old_value?: string
    new_value?: string
    change_reason?: string
    changed_by?: string
    changed_by_username?: string
    change_date: string
    created_at: string
}

export const configurationChangeApi = {
    list(params?: any) {
        return request({
            url: '/it-assets/configuration-changes/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/it-assets/configuration-changes/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<ConfigurationChange>) {
        return request({
            url: '/it-assets/configuration-changes/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<ConfigurationChange>) {
        return request({
            url: `/it-assets/configuration-changes/${id}/`,
            method: 'put',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/it-assets/configuration-changes/${id}/`,
            method: 'delete'
        })
    }
}
