import common from './common.json'
import dashboard from './dashboard.json'
import assets from './assets.json'
import menu from './menu.json'
import login from './login.json'
import workflow from './workflow.json'
import system from './system.json'
import inventory from './inventory.json'
import finance from './finance.json'
import insurance from './insurance.json'
import itAssets from './itAssets.json'
import leasing from './leasing.json'
import softwareLicenses from './softwareLicenses.json'
import form from './form.json'
import mobile from './mobile.json'
import notifications from './notifications.json'
import integration from './integration.json'
import reports from './reports.json'
import sso from './sso.json'
import org from './org.json'
import consumables from './consumables.json'
import projects from './projects.json'
import portal from './portal.json'

const financeMessages = ((finance as Record<string, unknown>).finance || finance) as Record<string, unknown>
const insuranceMessages = ((insurance as Record<string, unknown>).insurance || insurance) as Record<string, unknown>
const leasingMessages = ((leasing as Record<string, unknown>).leasing || leasing) as Record<string, unknown>
const systemPageLayout = (system.pageLayout || {}) as Record<string, unknown>
const systemPageLayoutSections = (systemPageLayout.sections || {}) as Record<string, string>
const menuMessages = menu as Record<string, unknown>
const menuCategoryMessages = (menuMessages.categories || {}) as Record<string, string>

const menuCategories = {
    asset_master: 'Asset Master',
    asset_operation: 'Asset Operations',
    lifecycle: 'Lifecycle',
    consumable: 'Consumables',
    inventory: 'Inventory',
    finance: 'Finance',
    organization: 'Organization',
    workflow: 'Workflow',
    system: 'System',
    reports: 'Reports',
    other: 'Other'
}

const pageLayoutSections = {
    basic: 'Basic Information',
    financial: 'Financial Information',
    depreciation: 'Depreciation Information',
    supplier: 'Supplier Information',
    usage: 'Usage Information',
    status: 'Status Information',
    details: 'Detailed Information',
    system: 'System Information'
}

export default {
    common,
    login,
    dashboard,
    assets,
    workflow,
    system: {
        ...system,
        pageLayout: {
            ...systemPageLayout,
            sections: {
                ...systemPageLayoutSections,
                ...pageLayoutSections
            }
        }
    },
    menu: {
        ...menu,
        categories: {
            ...menuCategoryMessages,
            ...menuCategories
        }
    },
    inventory,
    finance: financeMessages,
    insurance: insuranceMessages,
    itAssets,
    leasing: leasingMessages,
    softwareLicenses,
    form,
    mobile,
    notifications,
    integration,
    reports,
    sso,
    org,
    consumables,
    projects,
    portal
}
