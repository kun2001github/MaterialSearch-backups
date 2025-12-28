# Static Assets Directory

## Overview
This directory contains all static assets for the Material Search Engine frontend.

## Files Structure

### JavaScript Libraries

| File | Size | Description |
|------|-------|-------------|
| `vue.global.prod.js` | 164.91 KB | Vue.js 3.x - Production build |
| `vue-i18n.global.prod.js` | 67.65 KB | Vue I18n - Internationalization plugin |
| `axios.min.js` | 65.36 KB | Axios - HTTP client |
| `index.full.min.js` | 980.6 KB | Element Plus - Full UI component library |
| `index.iife.min.js` | 205 KB | Element Plus - IIFE build |
| `clipboard.min.js` | 8.95 KB | Clipboard.js - Clipboard operations |

### Project Files

| File | Size | Description |
|------|-------|-------------|
| `index.js` | ~2 KB | Custom initialization code (Vue setup, i18n, formatTime) |

### Stylesheets

| File | Size | Description |
|------|-------|-------------|
| `index.css` | 324.96 KB | Element Plus component styles |

## Dependencies

All JavaScript files must be loaded in the correct order in `index.html`:

```html
<!-- 1. Vue Core -->
<script src="static/assets/vue.global.prod.js"></script>

<!-- 2. Vue I18n -->
<script src="static/assets/vue-i18n.global.prod.js"></script>

<!-- 3. Element Plus (UI Library) -->
<script src="static/assets/index.full.min.js"></script>
<script src="static/assets/index.iife.min.js"></script>

<!-- 4. Clipboard Plugin -->
<script src="static/assets/clipboard.min.js"></script>

<!-- 5. HTTP Client -->
<script src="static/assets/axios.min.js"></script>

<!-- 6. Custom Application Code -->
<script src="static/assets/index.js" defer></script>
```

## index.js Structure

The custom `index.js` file handles:

1. **Time Formatting** (`formatTime`)
   - Converts seconds to HH:MM:SS format

2. **Vue Plugin Registration**
   - Registers ElementPlus
   - Registers all ElementPlus icons

3. **Internationalization Setup**
   - Detects browser language
   - Creates VueI18n instance
   - Loads locale messages from `../locales/`

4. **Application Initialization**
   - Loads all locales (en, zh)
   - Mounts Vue app after locales are ready

## Loading Order

Critical: The loading order matters because:
- `index.js` uses global objects defined by loaded libraries
- `formatTime` function is called from Vue app defined in `index.html`
- Vue app mounting must wait for locales to load

## Maintenance Notes

- All third-party files are minified production builds
- Do not modify third-party files unless upgrading versions
- Only `index.js` is custom project code
- Locale files are in `../locales/` directory
