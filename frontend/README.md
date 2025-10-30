# Frontend System

Frontend framework integration with USWDS (United States Web Design System).

## What This Provides

**Purpose:** Frontend development with federal design standards
**Emulates:** Theme management systems, USWDS integration tools

## Features

- USWDS (United States Web Design System) integration
- Theme management and switching
- Frontend view rendering
- URL routing for frontend pages
- Template directory management
- Federal-compliant accessibility

## Components

### USWDS Integration
- **uswds_integration.py** - USWDS integration utilities
  - USWDS component utilities
  - CDN asset management
  - Theme color configuration
  - Federal design patterns
  - Accessibility-compliant components

### Theme Management
- **themes.py** - Theme system
  - Theme registration and loading
  - Theme switching
  - Theme customization
  - Template overrides

### Frontend Views
- **views.py** - Frontend page views
  - Page rendering
  - Template context building
  - Dynamic content loading

### URL Routing
- **urls.py** - Frontend URL routing
  - Route definitions for pages
  - URL pattern matching
  - Frontend-specific routing

### Templates
- **templates/** - Frontend template files
  - Base templates
  - Component templates
  - Page templates

## Usage Examples

### USWDS Integration
```python
from frontend.uswds_integration import USWDSConfig, USWDSHelper

# Get USWDS assets
config = USWDSConfig()
css_url = config.CSS_CDN
js_url = config.JS_CDN

# Generate USWDS components
helper = USWDSHelper()
button = helper.create_button("Click Me", style="primary")
alert = helper.create_alert("Success!", type="success")
```

### Theme Management
```python
from frontend.themes import ThemeManager

manager = ThemeManager()

# Register theme
manager.register_theme("custom_theme", {
    "name": "Custom Theme",
    "template_dir": "themes/custom/templates",
    "static_dir": "themes/custom/static",
})

# Activate theme
manager.set_active_theme("custom_theme")

# Get theme info
theme = manager.get_active_theme()
```

### Frontend Views
```python
from frontend.views import render_page
from framework.request import Request

async def homepage(request: Request):
    context = {
        "title": "Welcome",
        "content": get_homepage_content(),
        "navigation": get_navigation_items(),
    }
    return await render_page("home.html", context)
```

## USWDS Components

Integrated USWDS components include:
- Buttons (primary, secondary, accent)
- Alerts (info, warning, error, success)
- Forms and inputs
- Navigation (header, footer, breadcrumbs)
- Cards and layouts
- Tables
- Modals
- Icons

## Theme Structure

```
themes/
└── custom_theme/
    ├── theme.json
    ├── templates/
    │   ├── base.html
    │   ├── home.html
    │   └── components/
    └── static/
        ├── css/
        ├── js/
        └── images/
```

## Federal Compliance

USWDS integration ensures:
- Section 508 compliance
- WCAG 2.1 AA accessibility
- Mobile-first responsive design
- Federal design standards
- Consistent user experience

## Accessibility Features

- Keyboard navigation
- Screen reader support
- Color contrast compliance
- Focus indicators
- ARIA attributes
- Semantic HTML

## Theme Configuration

```json
{
  "name": "Custom Theme",
  "version": "1.0.0",
  "description": "A custom USWDS theme",
  "template_dir": "templates",
  "static_dir": "static",
  "settings": {
    "primary_color": "#005ea2",
    "font_family": "Source Sans Pro",
    "logo": "/static/images/logo.png"
  }
}
```

## Integration

Works with:
- Template engine (templates/ module)
- Web components (web/ module)
- Admin interface (admin/ module)
- Web framework (framework/ module)

## Why This Was Created

Part of the CIV-ARCOS project to provide federal-compliant frontend capabilities with USWDS integration, ensuring accessibility and design consistency while maintaining self-containment.
