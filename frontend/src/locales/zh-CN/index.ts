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
    asset_master: '\u8d44\u4ea7\u4e3b\u6570\u636e',
    asset_operation: '\u8d44\u4ea7\u4e1a\u52a1',
    lifecycle: '\u8d44\u4ea7\u751f\u547d\u5468\u671f',
    consumable: '\u8017\u6750\u7ba1\u7406',
    inventory: '\u76d8\u70b9\u7ba1\u7406',
    finance: '\u8d22\u52a1\u7ba1\u7406',
    organization: '\u7ec4\u7ec7\u7ba1\u7406',
    workflow: '\u5de5\u4f5c\u6d41',
    system: '\u7cfb\u7edf\u7ba1\u7406',
    reports: '\u62a5\u8868\u4e2d\u5fc3',
    other: '\u5176\u4ed6'
}

const pageLayoutSections = {
    basic: '\u57fa\u672c\u4fe1\u606f',
    financial: '\u8d22\u52a1\u4fe1\u606f',
    depreciation: '\u6298\u65e7\u4fe1\u606f',
    supplier: '\u4f9b\u5e94\u5546\u4fe1\u606f',
    usage: '\u4f7f\u7528\u4fe1\u606f',
    status: '\u72b6\u6001\u4fe1\u606f',
    details: '\u8be6\u7ec6\u4fe1\u606f',
    system: '\u7cfb\u7edf\u4fe1\u606f'
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
