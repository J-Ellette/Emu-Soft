# Template Engine

Custom template engine with Jinja2/Django-like syntax.

## What This Emulates

**Emulates:** Jinja2, Django Templates
**Purpose:** Dynamic HTML generation with template syntax

## Features

- Variable substitution with {{ variable }}
- Template control structures (if, for, while)
- Template inheritance (extends, include)
- Template filters
- Template context management
- Component system
- Template optimization
- AI-powered template generation
- Collaboration features

## Components

### Template Engine Core
- **engine.py** - Template rendering engine
  - Variable substitution
  - Control structures (if/else, for loops)
  - Template inheritance
  - Include support
  - Comment handling
  - Filter application

### Template Loading
- **loader.py** - Template loading system
  - File system template loading
  - Template caching
  - Template path resolution
  - Multiple template directories
  - Template reloading in development

### Template Filters
- **filters.py** - Built-in and custom filters
  - String filters (upper, lower, capitalize, title)
  - Date/time filters (date, time, datetime)
  - Number filters (round, abs, format)
  - List filters (join, length, first, last)
  - Custom filter registration

### Context Management
- **context.py** - Template context
  - Context variable management
  - Context processors
  - Global context variables
  - Context inheritance
  - Request context

### Components
- **components.py** - Reusable template components
  - Component library
  - Component composition
  - Component parameters
  - Slot-based composition

### Optimization
- **optimizer.py** - Template optimization
  - Template compilation
  - Caching strategies
  - Performance optimization
  - Minification

### AI Generation
- **ai_generator.py** - AI-powered template generation
  - Template generation from descriptions
  - Smart component suggestions
  - Layout recommendations

### Collaboration
- **collaboration.py** - Template collaboration features
  - Version control for templates
  - Template sharing
  - Change tracking
  - Conflict resolution

## Usage Examples

### Basic Template Rendering
```python
from templates.engine import TemplateEngine
from templates.loader import TemplateLoader

# Create engine with loader
loader = TemplateLoader(template_dir="templates/")
engine = TemplateEngine(loader)

# Render template
context = {
    "title": "My Page",
    "user": {"name": "John", "age": 30},
    "items": ["apple", "banana", "orange"]
}

html = engine.render("page.html", context)
```

### Template Syntax

#### Variables
```html
<h1>{{ title }}</h1>
<p>Hello, {{ user.name }}!</p>
<p>Age: {{ user.age }}</p>
```

#### Filters
```html
<h1>{{ title|upper }}</h1>
<p>{{ text|truncate:100 }}</p>
<p>{{ date|date:"Y-m-d" }}</p>
<p>{{ items|join:", " }}</p>
```

#### If Statements
```html
{% if user.is_authenticated %}
    <p>Welcome, {{ user.name }}!</p>
{% else %}
    <p>Please log in.</p>
{% endif %}
```

#### For Loops
```html
<ul>
{% for item in items %}
    <li>{{ item }}</li>
{% endfor %}
</ul>
```

#### Template Inheritance
```html
<!-- base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Default Title{% endblock %}</title>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>

<!-- page.html -->
{% extends "base.html" %}

{% block title %}My Page{% endblock %}

{% block content %}
    <h1>Welcome to My Page</h1>
{% endblock %}
```

#### Include
```html
{% include "header.html" %}
<main>
    {{ content }}
</main>
{% include "footer.html" %}
```

#### Comments
```html
{# This is a comment and won't be rendered #}
```

### Custom Filters
```python
from templates.filters import TemplateFilters

filters = TemplateFilters()

@filters.register("reverse")
def reverse_filter(value):
    return value[::-1]

# Use in template: {{ text|reverse }}
```

### Context Processors
```python
from templates.context import Context

def add_site_info(context):
    context["site_name"] = "My Site"
    context["year"] = 2024
    return context

context = Context()
context.add_processor(add_site_info)
```

### Components
```python
from templates.components import Component

class ButtonComponent(Component):
    template = '<button class="{{ class }}">{{ text }}</button>'
    
    def get_context(self, text, style="primary"):
        return {
            "text": text,
            "class": f"btn btn-{style}"
        }

# Use in template: {% component "button" text="Click Me" style="primary" %}
```

## Built-in Filters

### String Filters
- `upper` - Convert to uppercase
- `lower` - Convert to lowercase
- `capitalize` - Capitalize first letter
- `title` - Title case
- `truncate` - Truncate to length
- `strip` - Remove whitespace
- `reverse` - Reverse string

### Number Filters
- `round` - Round number
- `abs` - Absolute value
- `format` - Number formatting

### List Filters
- `join` - Join list items
- `length` - Get list length
- `first` - First item
- `last` - Last item
- `sort` - Sort list

### Date/Time Filters
- `date` - Format date
- `time` - Format time
- `datetime` - Format datetime
- `timesince` - Time since date
- `timeuntil` - Time until date

## Template Optimization

- **Compilation**: Pre-compile templates for faster rendering
- **Caching**: Cache rendered templates
- **Minification**: Remove whitespace and comments
- **Lazy Loading**: Load templates on demand

## Integration

Works with:
- Web framework (framework/ module)
- Frontend system (frontend/ module)
- Admin interface (admin/ module)
- API documentation

## Why This Was Created

Part of the CIV-ARCOS project to provide template engine capabilities without external template libraries, enabling dynamic HTML generation with familiar syntax while maintaining self-containment.
