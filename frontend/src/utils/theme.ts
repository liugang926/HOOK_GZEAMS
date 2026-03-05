/**
 * ThemeInjector Utility
 * Manages SaaS Whitelabeling tokens such as brand colors, radiuses, and dynamic dark mode toggles.
 * Calculations run dynamically on `:root` to adjust the frontend appearance in real-time.
 */

export interface ThemeConfig {
    primaryColor?: string;
    borderRadius?: number;
    darkMode?: boolean;
}

/**
 * Calculates a lighter or darker shade of a hex color.
 * A lightweight alternative to pulling in chroma.js.
 * @param hex Original hex color
 * @param percent Positive for lighter, negative for darker (-1 to 1)
 */
export function adjustBrightness(hex: string, percent: number): string {
    // Strip '#'
    hex = hex.replace(/^#/, '');
    if (hex.length === 3) {
        hex = hex.split('').map(char => char + char).join('');
    }

    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);

    const adjust = (val: number, isDarken: boolean) => {
        // If darkening, move toward 0; if lightening, move toward 255
        const diff = isDarken ? val : (255 - val);
        const amount = diff * Math.abs(percent);
        const adjusted = isDarken ? (val - amount) : (val + amount);
        return Math.min(255, Math.max(0, Math.round(adjusted))).toString(16).padStart(2, '0');
    };

    const isDarkening = percent < 0;
    return `#${adjust(r, isDarkening)}${adjust(g, isDarkening)}${adjust(b, isDarkening)}`;
}

/**
 * Inject dynamic theme variables into the document `:root`.
 * Handles the mapping between the raw settings and the system context variables (--sys-*).
 * Changes natively propagate back up to Element Plus due to `tokens.scss` mappings.
 * @param config ThemeConfig object
 */
export function injectTheme(config: ThemeConfig) {
    const root = document.documentElement;

    if (config.primaryColor) {
        root.style.setProperty('--sys-color-primary', config.primaryColor);

        // Generate Element Plus internal shades for active/hover states
        root.style.setProperty('--el-color-primary-light-3', adjustBrightness(config.primaryColor, 0.3));
        root.style.setProperty('--el-color-primary-light-5', adjustBrightness(config.primaryColor, 0.5));
        root.style.setProperty('--el-color-primary-light-7', adjustBrightness(config.primaryColor, 0.7));
        root.style.setProperty('--el-color-primary-light-9', adjustBrightness(config.primaryColor, 0.9));
        root.style.setProperty('--el-color-primary-dark-2', adjustBrightness(config.primaryColor, -0.2));
    }

    if (config.borderRadius !== undefined) {
        root.style.setProperty('--sys-radius-base', `${config.borderRadius}px`);
        // Scale up the larger radius based on the base radius
        const largeRadius = Math.max(config.borderRadius + 4, 10);
        root.style.setProperty('--sys-radius-large', `${largeRadius}px`);
    }

    if (config.darkMode !== undefined) {
        if (config.darkMode) {
            document.documentElement.classList.add('dark');
            // Set some dark mode structural overrides
            // These overwrite the --sys-* tokens
            root.style.setProperty('--sys-color-bg-base', '#0f172a'); // slate-900
            root.style.setProperty('--sys-color-bg-card', '#1e293b'); // slate-800
            root.style.setProperty('--sys-color-text-main', '#f8fafc');
            root.style.setProperty('--sys-color-text-regular', '#e2e8f0');
            root.style.setProperty('--sys-color-text-secondary', '#94a3b8');
            root.style.setProperty('--sys-border-color', '#334155');
            root.style.setProperty('--sys-border-light', 'rgba(255, 255, 255, 0.06)');
            root.style.setProperty('--sys-color-bg-hover', '#334155');

            // Update element plus table theme specifically for dark mode
            root.style.setProperty('--el-table-header-bg-color', '#1e293b');
            root.style.setProperty('--el-table-header-text-color', '#cbd5e1');
        } else {
            document.documentElement.classList.remove('dark');
            // Reset to light mode defaults declared in tokens.scss by removing inline properties
            root.style.removeProperty('--sys-color-bg-base');
            root.style.removeProperty('--sys-color-bg-card');
            root.style.removeProperty('--sys-color-text-main');
            root.style.removeProperty('--sys-color-text-regular');
            root.style.removeProperty('--sys-color-text-secondary');
            root.style.removeProperty('--sys-border-color');
            root.style.removeProperty('--sys-border-light');
            root.style.removeProperty('--sys-color-bg-hover');

            root.style.removeProperty('--el-table-header-bg-color');
            root.style.removeProperty('--el-table-header-text-color');
        }
    }
}
