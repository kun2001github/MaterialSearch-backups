/**
 * Material Search Engine - Frontend Initialization
 *
 * This script initializes the Vue application with:
 * - Time formatting utilities
 * - ElementPlus UI framework
 * - VueI18n internationalization
 * - Locale loading from JSON files
 *
 * IMPORTANT: This file must be loaded after all Vue libraries
 */

// ============================================================================
// SECTION 1: Utility Functions
// ============================================================================

/**
 * Convert seconds to HH:MM:SS format
 * @param {number} seconds - Time in seconds
 * @returns {string} Formatted time string
 *
 * Examples:
 *   formatTime(0)      => "00:00"
 *   formatTime(3661)   => "1:01:01"
 *   formatTime(86400)  => "24:00:00"
 */
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    seconds -= hours * 3600;
    const minutes = Math.floor(seconds / 60);
    seconds -= minutes * 60;
    seconds = Math.floor(seconds);

    const hoursStr = hours > 0 ? hours + ':' : '';
    const minutesStr = minutes.toString().padStart(2, '0') + ':';
    const secondsStr = seconds.toString().padStart(2, '0');

    return hoursStr + minutesStr + secondsStr;
}

// ============================================================================
// SECTION 2: Vue Plugin Registration
// ============================================================================

/**
 * Register ElementPlus UI framework
 * This provides the component library for the application
 */
app.use(ElementPlus);

/**
 * Register all ElementPlus icons
 * Makes all icons available as Vue components
 */
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
}

// ============================================================================
// SECTION 3: Internationalization Setup
// ============================================================================

/**
 * Detect browser language
 * Falls back to 'en' if detection fails
 */
const browserLanguage = navigator.language || navigator.userLanguage;
const languageTag = browserLanguage.split('-')[0];

/**
 * Create VueI18n instance
 * Configures internationalization with:
 * - Legacy mode disabled (Composition API)
 * - Auto-detected locale
 * - Fallback to English
 */
const i18n = VueI18n.createI18n({
    legacy: false,
    locale: languageTag,
    fallbackLocale: 'en',
    messages: {}
});

/**
 * Register i18n plugin with Vue app
 */
app.use(i18n);

// ============================================================================
// SECTION 4: Locale Loading
// ============================================================================

/**
 * Load locale messages from JSON file
 * @param {string} locale - Locale code (e.g., 'en', 'zh')
 * @returns {Promise<Object>} Locale messages
 */
function loadLocaleMessages(locale) {
    return axios.get('/static/locales/' + locale + '.json')
        .then(response => {
            return response.data;
        });
}

/**
 * Load all available locales and mount the application
 * This ensures all translations are available before rendering
 */
async function loadLocales() {
    // Define available locales
    const locales = ['en', 'zh'];

    try {
        // Load all locales in parallel
        await Promise.all(locales.map(async locale => {
            const messages = await loadLocaleMessages(locale);
            i18n.global.setLocaleMessage(locale, messages);
        }));

        // Mount app only after locales are loaded
        app.mount('#app');
    } catch (error) {
        console.error('Failed to load locales:', error);
        // Mount anyway even if loading fails to prevent blank page
        app.mount('#app');
    }
}

// ============================================================================
// SECTION 5: Application Bootstrap
// ============================================================================

/**
 * Start loading locales and initialize application
 */
loadLocales();
