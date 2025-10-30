# Admin Interface

This  Admin Interface is a web-based control panel for managing CMS content. It provides CRUD (Create, Read, Update, Delete) operations for registered models with a clean, intuitive interface.

## Quick Start

### 1. Register Your Models

```python
from admin import site
from auth.models import User

# Simple registration
site.register(User)
```

### 2. Set Up Admin Routes

```python
from framework.application import Application
from admin.views import AdminViews
from auth.session import SessionManager

app = Application()
session_manager = SessionManager()
admin_views = AdminViews(site, session_manager)

# Add authentication middleware
from auth.middleware import AuthMiddleware
app.add_middleware(AuthMiddleware(session_manager))

# Add admin routes
@app.get("/admin/login")
async def admin_login(request):
    return await admin_views.login_view(request)

@app.post("/admin/login")
async def admin_login_post(request):
    return await admin_views.login_view(request)

@app.get("/admin/")
async def admin_dashboard(request):
    if not request.user or not request.user.is_staff:
        return Response(content="", status_code=302, 
                       headers={"Location": "/admin/login"})
    return await admin_views.dashboard_view(request)

# Add more routes... (see examples/admin_app.py for complete example)
```

### 3. Access the Admin

Navigate to `http://localhost:8000/admin/` and log in with a staff user account.

## Features

- **Model Registration**: Register any model with the admin interface
- **CRUD Operations**: Create, read, update, and delete model instances
- **Search**: Search through model instances
- **List Display**: Customize which fields to display in list views
- **Form Validation**: Server-side validation with error messages
- **Authentication**: Staff-only access with session-based authentication
- **Permissions**: Per-action permission checking
- **Clean UI**: Professional, responsive interface

## Customization

### Custom ModelAdmin

```python
from admin import ModelAdmin

class MyModelAdmin(ModelAdmin):
    # Fields to display in list view
    list_display = ['id', 'title', 'created_at']
    
    # Fields to enable search on
    search_fields = ['title', 'content']
    
    # Fields to filter by
    list_filter = ['status', 'category']
    
    # Number of items per page
    list_per_page = 50
    
    # Fields to show in form
    fields = ['title', 'content', 'status']
    
    # Or exclude specific fields
    exclude = ['internal_id']

site.register(MyModel, MyModelAdmin)
```

### Custom Forms

```python
from admin.forms import ModelForm, CharField, EmailField

class CustomForm(ModelForm):
    title = CharField(
        label="Title",
        max_length=200,
        help_text="Enter a descriptive title"
    )
    email = EmailField(
        label="Contact Email",
        required=True
    )
```

## Available Field Types

- `CharField`: Text input with length validation
- `IntegerField`: Numeric input with range validation
- `BooleanField`: Checkbox input
- `EmailField`: Email input with format validation
- `PasswordField`: Masked password input
- `TextAreaField`: Multi-line text input

## Admin Routes

The admin interface uses these URL patterns:

```
GET  /admin/login                    # Login page
POST /admin/login                    # Login submission
GET  /admin/logout                   # Logout
GET  /admin/                         # Dashboard
GET  /admin/{model}/                 # Model list
GET  /admin/{model}/add/             # Add form
POST /admin/{model}/add/             # Add submission
GET  /admin/{model}/{pk}/            # Edit form
POST /admin/{model}/{pk}/            # Edit submission
GET  /admin/{model}/{pk}/delete/     # Delete confirmation
POST /admin/{model}/{pk}/delete/     # Delete submission
```

## Documentation

- **User Guide**: See `docs/admin-user-guide.md` for end-user documentation
- **Example App**: See `examples/admin_app.py` for a complete working example

## Testing

Run the admin tests:

```bash
pytest tests/test_admin.py -v
```

## Requirements

- Staff user account (`is_staff=True`)
- Session manager configured
- Authentication middleware enabled
- Models registered with the admin site

## Examples

See `examples/admin_app.py` for a complete working example with:
- Model registration
- Route setup
- Authentication integration
- All CRUD operations
