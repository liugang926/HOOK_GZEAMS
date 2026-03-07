import common from './common.json'
import dashboard from './dashboard.json'
import assets from './assets.json'
import menu from './menu.json'
import login from './login.json'
import workflow from './workflow.json'
import system from './system.json'
import inventory from './inventory.json'
import finance from './finance.json'
import itAssets from './itAssets.json'
import softwareLicenses from './softwareLicenses.json'
import form from './form.json'
import mobile from './mobile.json'
import notifications from './notifications.json'
import integration from './integration.json'
import reports from './reports.json'
import sso from './sso.json'
import org from './org.json'
import consumables from './consumables.json'

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
            ...(system.pageLayout || {}),
            sections: {
                ...((system.pageLayout || {}).sections || {}),
                ...pageLayoutSections
            }
        }
    },
    menu: {
        ...menu,
        categories: {
            ...(menu.categories || {}),
            ...menuCategories
        }
    },
    inventory,
    finance,
    itAssets,
    softwareLicenses,
    form,
    mobile,
    notifications,
    integration,
    reports,
    sso,
    org,
    consumables
}
