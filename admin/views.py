"""Admin views for handling HTTP requests.

This module provides view functions for the admin interface,
including login, dashboard, and CRUD operations.
"""

from typing import Any, Dict, Optional, Type
from mycms.core.framework.request import Request
from mycms.core.framework.response import Response, HTMLResponse
from mycms.core.database.orm import Model
from mycms.admin.interface import AdminSite
from mycms.admin.forms import ModelForm
from mycms.admin.dashboard import Dashboard
from mycms.admin.config_manager import config_manager
from mycms.auth.authentication import authenticate, login, logout
from mycms.auth.session import SessionManager


class AdminViews:
    """Collection of admin view handlers."""

    def __init__(self, admin_site: AdminSite, session_manager: SessionManager) -> None:
        """Initialize admin views.

        Args:
            admin_site: AdminSite instance
            session_manager: Session manager for authentication
        """
        self.admin_site = admin_site
        self.session_manager = session_manager
        self.dashboard = Dashboard(admin_site)

    async def login_view(self, request: Request) -> Response:
        """Handle admin login.

        Args:
            request: HTTP request

        Returns:
            Login page or redirect to dashboard
        """
        if request.method == "POST":
            # Handle login form submission
            data = await request.form()

            username = data.get("username")
            password = data.get("password")

            if username and password:
                user = await authenticate(username, password)
                if user and user.is_staff:
                    # Login successful
                    session = await login(user, self.session_manager)
                    response = Response(
                        content="",
                        status_code=302,
                        headers={"Location": f"/{self.admin_site.name}/"},
                    )
                    response.set_cookie("session_id", session.session_id, max_age=604800)
                    return response
                else:
                    error = "Invalid credentials or insufficient permissions"
            else:
                error = "Please provide username and password"

            return self._render_login_page(error=error)

        # Show login form
        return self._render_login_page()

    async def logout_view(self, request: Request) -> Response:
        """Handle admin logout.

        Args:
            request: HTTP request

        Returns:
            Redirect to login page
        """
        # Get session from cookie
        cookies = request.cookies
        session_id = cookies.get("session_id")

        if session_id:
            session = await self.session_manager.get_session(session_id)
            if session:
                await logout(session, self.session_manager)

        response = Response(
            content="", status_code=302, headers={"Location": f"/{self.admin_site.name}/login"}
        )
        response.set_cookie("session_id", "", max_age=0)  # Clear cookie
        return response

    async def dashboard_view(self, request: Request) -> Response:
        """Display admin dashboard.

        Args:
            request: HTTP request

        Returns:
            Dashboard page
        """
        app_list = self.admin_site.get_app_list()
        dashboard_html = await self.dashboard.render()
        return self._render_dashboard(app_list, dashboard_html)

    async def model_list_view(self, request: Request, model_name: str) -> Response:
        """Display list of model instances.

        Args:
            request: HTTP request
            model_name: URL-safe model name

        Returns:
            Model list page
        """
        model = self._get_model_by_name(model_name)
        if not model:
            return Response(content="Model not found", status_code=404)

        admin = self.admin_site.get_model_admin(model)
        if not admin:
            return Response(content="Model not registered", status_code=404)

        # Get query parameters
        query_params = request.query_params
        search = query_params.get("search")

        # Get all instances
        instances = await admin.get_queryset(search=search)

        return self._render_model_list(model, admin, instances, search)

    async def model_add_view(self, request: Request, model_name: str) -> Response:
        """Display form to add a new model instance.

        Args:
            request: HTTP request
            model_name: URL-safe model name

        Returns:
            Add form page or redirect on success
        """
        model = self._get_model_by_name(model_name)
        if not model:
            return Response(content="Model not found", status_code=404)

        admin = self.admin_site.get_model_admin(model)
        if not admin or not admin.has_add_permission():
            return Response(content="Permission denied", status_code=403)

        if request.method == "POST":
            # Handle form submission
            data = await request.form()
            form_class = admin.get_form_class()
            form = form_class(data=data)

            if form.is_valid():
                try:
                    await form.save()
                    # Redirect to model list
                    return Response(
                        content="",
                        status_code=302,
                        headers={"Location": f"/{self.admin_site.name}/{model_name}/"},
                    )
                except Exception as e:
                    return self._render_model_form(model, admin, form, action="add", error=str(e))

            return self._render_model_form(model, admin, form, action="add")

        # Show empty form
        form_class = admin.get_form_class()
        form = form_class()
        return self._render_model_form(model, admin, form, action="add")

    async def model_change_view(self, request: Request, model_name: str, pk: str) -> Response:
        """Display form to edit a model instance.

        Args:
            request: HTTP request
            model_name: URL-safe model name
            pk: Primary key of instance

        Returns:
            Edit form page or redirect on success
        """
        model = self._get_model_by_name(model_name)
        if not model:
            return Response(content="Model not found", status_code=404)

        admin = self.admin_site.get_model_admin(model)
        if not admin or not admin.has_change_permission():
            return Response(content="Permission denied", status_code=403)

        # Get the instance
        try:
            pk_int = int(pk)
        except ValueError:
            return Response(content="Invalid primary key", status_code=400)

        instance = await admin.get_object(pk_int)
        if not instance:
            return Response(content="Object not found", status_code=404)

        if request.method == "POST":
            # Handle form submission
            data = await request.form()
            form_class = admin.get_form_class()
            form = form_class(data=data, instance=instance)

            if form.is_valid():
                try:
                    await form.save()
                    # Redirect to model list
                    return Response(
                        content="",
                        status_code=302,
                        headers={"Location": f"/{self.admin_site.name}/{model_name}/"},
                    )
                except Exception as e:
                    return self._render_model_form(
                        model, admin, form, action="change", error=str(e), pk=pk
                    )

            return self._render_model_form(model, admin, form, action="change", pk=pk)

        # Show form with instance data
        form_class = admin.get_form_class()
        form = form_class(instance=instance)
        return self._render_model_form(model, admin, form, action="change", pk=pk)

    async def model_delete_view(self, request: Request, model_name: str, pk: str) -> Response:
        """Delete a model instance.

        Args:
            request: HTTP request
            model_name: URL-safe model name
            pk: Primary key of instance

        Returns:
            Delete confirmation page or redirect on success
        """
        model = self._get_model_by_name(model_name)
        if not model:
            return Response(content="Model not found", status_code=404)

        admin = self.admin_site.get_model_admin(model)
        if not admin or not admin.has_delete_permission():
            return Response(content="Permission denied", status_code=403)

        # Get the instance
        try:
            pk_int = int(pk)
        except ValueError:
            return Response(content="Invalid primary key", status_code=400)

        instance = await admin.get_object(pk_int)
        if not instance:
            return Response(content="Object not found", status_code=404)

        if request.method == "POST":
            # Confirm deletion
            await instance.delete()
            # Redirect to model list
            return Response(
                content="",
                status_code=302,
                headers={"Location": f"/{self.admin_site.name}/{model_name}/"},
            )

        # Show confirmation page
        return self._render_delete_confirmation(model, admin, instance, pk)

    async def config_view(self, request: Request) -> Response:
        """Display configuration management interface.

        Args:
            request: HTTP request

        Returns:
            Configuration page
        """
        if request.method == "POST":
            # Handle configuration form submission
            data = await request.form()
            errors = {}

            for key, value in data.items():
                success, error = config_manager.set_value(key, value)
                if not success:
                    errors[key] = error

            if not errors:
                # Redirect to config page with success message
                return Response(
                    content="",
                    status_code=302,
                    headers={"Location": f"/{self.admin_site.name}/config/?success=1"},
                )

            return self._render_config_page(errors=errors, success=False)

        # Check for success message
        query_params = request.query_params
        success = query_params.get("success") == "1"

        # Show configuration form
        return self._render_config_page(success=success)

    def _get_model_by_name(self, model_name: str) -> Optional[Type[Model]]:
        """Get a model class by its URL-safe name.

        Args:
            model_name: URL-safe model name

        Returns:
            Model class or None
        """
        for model in self.admin_site.get_registered_models():
            if self.admin_site.get_model_name(model) == model_name:
                return model
        return None

    def _render_login_page(self, error: Optional[str] = None) -> Response:
        """Render the login page.

        Args:
            error: Error message to display

        Returns:
            HTML response
        """
        error_html = f'<div class="error">{error}</div>' if error else ""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Admin Login</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .login-container {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    width: 100%;
                    max-width: 400px;
                }}
                h1 {{
                    color: #333;
                    margin-top: 0;
                }}
                .form-field {{
                    margin-bottom: 20px;
                }}
                label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #555;
                }}
                input[type="text"],
                input[type="password"] {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }}
                button {{
                    background-color: #007bff;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    width: 100%;
                    font-size: 16px;
                }}
                button:hover {{
                    background-color: #0056b3;
                }}
                .error {{
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <h1>Admin Login</h1>
                {error_html}
                <form method="post">
                    <div class="form-field">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-field">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)

    def _render_dashboard(self, app_list: list, dashboard_html: str = "") -> Response:
        """Render the dashboard page.

        Args:
            app_list: List of apps and models
            dashboard_html: HTML from dashboard widgets

        Returns:
            HTML response
        """
        models_html = ""
        for app in app_list:
            models_html += f'<h2>{app["name"]}</h2><ul class="model-list">'
            for model_info in app["models"]:
                name = model_info["name"]
                url_name = model_info["url_name"]
                models_html += f"""
                <li>
                    <a href="/{self.admin_site.name}/{url_name}/">{name}</a>
                    <span class="actions">
                        <a href="/{self.admin_site.name}/{url_name}/add/" class="add-link">+ Add</a>
                    </span>
                </li>
                """
            models_html += "</ul>"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Admin Dashboard</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 30px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .header a {{
                    color: white;
                    text-decoration: none;
                    margin-left: 20px;
                }}
                .header a:hover {{
                    text-decoration: underline;
                }}
                .content {{
                    max-width: 1200px;
                    margin: 30px auto;
                    padding: 0 20px;
                }}
                .model-list {{
                    list-style: none;
                    padding: 0;
                }}
                .model-list li {{
                    background: white;
                    padding: 15px;
                    margin-bottom: 10px;
                    border-radius: 4px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .model-list a {{
                    text-decoration: none;
                    color: #007bff;
                }}
                .model-list a:hover {{
                    text-decoration: underline;
                }}
                .add-link {{
                    color: #28a745 !important;
                    font-weight: bold;
                }}
                .dashboard {{
                    margin-bottom: 30px;
                }}
                .dashboard-widgets {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .dashboard-widget {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .dashboard-widget h3 {{
                    margin-top: 0;
                    color: #2c3e50;
                    border-bottom: 2px solid #007bff;
                    padding-bottom: 10px;
                }}
                .widget-content {{
                    margin-top: 15px;
                }}
                .stat-item {{
                    padding: 10px 0;
                    border-bottom: 1px solid #eee;
                }}
                .stat-item:last-child {{
                    border-bottom: none;
                }}
                .stat-item a {{
                    display: flex;
                    justify-content: space-between;
                    text-decoration: none;
                    color: #333;
                }}
                .stat-item a:hover {{
                    color: #007bff;
                }}
                .stat-value {{
                    font-weight: bold;
                    color: #007bff;
                    font-size: 18px;
                }}
                .activity-item {{
                    padding: 10px 0;
                    border-bottom: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .activity-item:last-child {{
                    border-bottom: none;
                }}
                .activity-time {{
                    color: #666;
                    font-size: 12px;
                }}
                .activity-model {{
                    color: #007bff;
                    font-weight: bold;
                }}
                .action-item {{
                    padding: 8px 0;
                }}
                .action-link {{
                    color: #28a745;
                    text-decoration: none;
                    font-weight: bold;
                }}
                .action-link:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Admin Dashboard</h1>
                <div>
                    <a href="/{self.admin_site.name}/config/">Configuration</a>
                    <a href="/{self.admin_site.name}/logout">Logout</a>
                </div>
            </div>
            <div class="content">
                <h1>Welcome to the Admin Interface</h1>
                {dashboard_html}
                <h2>Content Management</h2>
                {models_html}
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)

    def _render_model_list(
        self, model: Type[Model], admin: Any, instances: list, search: Optional[str]
    ) -> Response:
        """Render the model list page.

        Args:
            model: Model class
            admin: ModelAdmin instance
            instances: List of model instances
            search: Search query

        Returns:
            HTML response
        """
        model_name = self.admin_site.get_model_name(model)
        list_display = admin.get_list_display()

        # Build table headers
        headers_html = "".join([f"<th>{field}</th>" for field in list_display])

        # Build no items row
        no_items_row = f'<tr><td colspan="{len(list_display)}">No items found</td></tr>'

        # Build table rows
        rows_html = ""
        for instance in instances:
            pk_field = admin._get_primary_key_field()
            pk_value = getattr(instance, pk_field)

            cells = []
            for field_name in list_display:
                value = getattr(instance, field_name, "")
                # First column links to detail page
                if field_name == list_display[0]:
                    link = f"/{self.admin_site.name}/{model_name}/{pk_value}/"
                    cells.append(f'<td><a href="{link}">{value}</a></td>')
                else:
                    cells.append(f"<td>{value}</td>")

            rows_html += f"<tr>{''.join(cells)}</tr>"

        search_value = search or ""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{model.__name__} List</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 30px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .header a {{
                    color: white;
                    text-decoration: none;
                }}
                .content {{
                    max-width: 1200px;
                    margin: 30px auto;
                    padding: 0 20px;
                }}
                .actions {{
                    margin-bottom: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .add-button {{
                    background-color: #28a745;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 4px;
                }}
                .add-button:hover {{
                    background-color: #218838;
                }}
                .search-form {{
                    display: flex;
                    gap: 10px;
                }}
                .search-form input {{
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }}
                .search-form button {{
                    padding: 8px 16px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }}
                table {{
                    width: 100%;
                    background: white;
                    border-collapse: collapse;
                    border-radius: 4px;
                    overflow: hidden;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f8f9fa;
                    font-weight: bold;
                }}
                tr:hover {{
                    background-color: #f8f9fa;
                }}
                a {{
                    color: #007bff;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .back-link {{
                    color: white;
                    margin-right: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{model.__name__} List</h1>
                <div>
                    <a href="/{self.admin_site.name}/" class="back-link">← Dashboard</a>
                    <a href="/{self.admin_site.name}/logout">Logout</a>
                </div>
            </div>
            <div class="content">
                <div class="actions">
                    <a href="/{self.admin_site.name}/{model_name}/add/" class="add-button">
                        + Add {model.__name__}
                    </a>
                    <form class="search-form" method="get">
                        <input type="text" name="search" placeholder="Search..."
                               value="{search_value}">
                        <button type="submit">Search</button>
                    </form>
                </div>
                <table>
                    <thead>
                        <tr>{headers_html}</tr>
                    </thead>
                    <tbody>
                        {rows_html if rows_html else no_items_row}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)

    def _render_model_form(
        self,
        model: Type[Model],
        admin: Any,
        form: ModelForm,
        action: str,
        error: Optional[str] = None,
        pk: Optional[str] = None,
    ) -> Response:
        """Render the model add/edit form page.

        Args:
            model: Model class
            admin: ModelAdmin instance
            form: Form instance
            action: 'add' or 'change'
            error: Error message
            pk: Primary key (for edit)

        Returns:
            HTML response
        """
        model_name = self.admin_site.get_model_name(model)
        title = f"Add {model.__name__}" if action == "add" else f"Edit {model.__name__}"

        error_html = f'<div class="error">{error}</div>' if error else ""
        form_html = form.render()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 30px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .header a {{
                    color: white;
                    text-decoration: none;
                }}
                .content {{
                    max-width: 800px;
                    margin: 30px auto;
                    padding: 0 20px;
                }}
                .form-container {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                }}
                .form-field {{
                    margin-bottom: 20px;
                }}
                label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #555;
                }}
                input[type="text"],
                input[type="number"],
                input[type="password"],
                input[type="email"],
                textarea {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }}
                textarea {{
                    min-height: 100px;
                }}
                .buttons {{
                    display: flex;
                    gap: 10px;
                    margin-top: 20px;
                }}
                button {{
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                }}
                .save-button {{
                    background-color: #007bff;
                    color: white;
                }}
                .save-button:hover {{
                    background-color: #0056b3;
                }}
                .cancel-button {{
                    background-color: #6c757d;
                    color: white;
                    text-decoration: none;
                    display: inline-block;
                    text-align: center;
                    line-height: 20px;
                }}
                .cancel-button:hover {{
                    background-color: #5a6268;
                }}
                .error {{
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}
                .help-text {{
                    font-size: 12px;
                    color: #6c757d;
                    margin-top: 5px;
                }}
                .back-link {{
                    color: white;
                    margin-right: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <div>
                    <a href="/{self.admin_site.name}/{model_name}/"
                       class="back-link">← Back to list</a>
                    <a href="/{self.admin_site.name}/logout">Logout</a>
                </div>
            </div>
            <div class="content">
                <div class="form-container">
                    {error_html}
                    <form method="post">
                        {form_html}
                        <div class="buttons">
                            <button type="submit" class="save-button">Save</button>
                            <a href="/{self.admin_site.name}/{model_name}/"
                               class="cancel-button">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)

    def _render_delete_confirmation(
        self, model: Type[Model], admin: Any, instance: Model, pk: str
    ) -> Response:
        """Render the delete confirmation page.

        Args:
            model: Model class
            admin: ModelAdmin instance
            instance: Model instance to delete
            pk: Primary key

        Returns:
            HTML response
        """
        model_name = self.admin_site.get_model_name(model)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Delete {model.__name__}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    max-width: 800px;
                    margin: 30px auto;
                    padding: 0 20px;
                }}
                .warning {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    border-left: 4px solid #dc3545;
                }}
                .buttons {{
                    display: flex;
                    gap: 10px;
                    margin-top: 20px;
                }}
                button {{
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }}
                .delete-button {{
                    background-color: #dc3545;
                    color: white;
                }}
                .cancel-button {{
                    background-color: #6c757d;
                    color: white;
                    text-decoration: none;
                    display: inline-block;
                    text-align: center;
                    line-height: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Delete {model.__name__}</h1>
            </div>
            <div class="content">
                <div class="warning">
                    <h2>Are you sure?</h2>
                    <p>Are you sure you want to delete this {model.__name__}?</p>
                    <p><strong>This action cannot be undone.</strong></p>
                    <form method="post">
                        <div class="buttons">
                            <button type="submit" class="delete-button">
                                Yes, delete it
                            </button>
                            <a href="/{self.admin_site.name}/{model_name}/"
                               class="cancel-button">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)

    def _render_config_page(
        self, errors: Optional[Dict[str, str]] = None, success: bool = False
    ) -> Response:
        """Render the configuration management page.

        Args:
            errors: Dictionary of field errors
            success: Whether to show success message

        Returns:
            HTML response
        """
        errors = errors or {}

        # Get all categories
        categories = config_manager.get_categories()

        # Build category tabs and forms
        category_tabs = ""
        category_content = ""

        for i, category in enumerate(categories):
            active_class = "active" if i == 0 else ""
            category_tabs += f"""
            <button class="tab-button {active_class}"
                    onclick="showCategory('{category.value}')"
                    id="tab-{category.value}">
                {category.value.replace('_', ' ').title()}
            </button>
            """

            settings = config_manager.get_settings_by_category(category)
            settings_html = ""

            for setting in settings:
                error_html = ""
                if setting.key in errors:
                    error_html = f'<div class="field-error">{errors[setting.key]}</div>'

                input_html = self._render_config_field(setting)

                settings_html += f"""
                <div class="form-field">
                    <label for="{setting.key}">
                        {setting.label}
                        {'<span class="required">*</span>' if setting.required else ''}
                    </label>
                    {input_html}
                    {f'<div class="help-text">{setting.description}</div>' if setting.description else ''}
                    {error_html}
                </div>
                """

            category_content += f"""
            <div class="category-content {active_class}" id="category-{category.value}">
                {settings_html}
            </div>
            """

        success_html = ""
        if success:
            success_html = '<div class="success">Configuration saved successfully!</div>'

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Configuration Management</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 30px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .header a {{
                    color: white;
                    text-decoration: none;
                    margin-left: 20px;
                }}
                .content {{
                    max-width: 1200px;
                    margin: 30px auto;
                    padding: 0 20px;
                }}
                .config-container {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                }}
                .tabs {{
                    display: flex;
                    border-bottom: 2px solid #ddd;
                    margin-bottom: 20px;
                }}
                .tab-button {{
                    padding: 10px 20px;
                    border: none;
                    background: none;
                    cursor: pointer;
                    font-size: 14px;
                    color: #666;
                    border-bottom: 2px solid transparent;
                    margin-bottom: -2px;
                }}
                .tab-button.active {{
                    color: #007bff;
                    border-bottom-color: #007bff;
                }}
                .tab-button:hover {{
                    color: #007bff;
                }}
                .category-content {{
                    display: none;
                }}
                .category-content.active {{
                    display: block;
                }}
                .form-field {{
                    margin-bottom: 20px;
                }}
                label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #555;
                }}
                .required {{
                    color: #dc3545;
                }}
                input[type="text"],
                input[type="number"],
                input[type="password"],
                select {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }}
                input[type="checkbox"] {{
                    width: auto;
                    margin-right: 5px;
                }}
                .help-text {{
                    font-size: 12px;
                    color: #6c757d;
                    margin-top: 5px;
                }}
                .field-error {{
                    color: #dc3545;
                    font-size: 12px;
                    margin-top: 5px;
                }}
                .success {{
                    background-color: #d4edda;
                    color: #155724;
                    padding: 10px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}
                .buttons {{
                    display: flex;
                    gap: 10px;
                    margin-top: 30px;
                }}
                button[type="submit"] {{
                    padding: 10px 20px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }}
                button[type="submit"]:hover {{
                    background-color: #0056b3;
                }}
                .cancel-link {{
                    padding: 10px 20px;
                    background-color: #6c757d;
                    color: white;
                    border-radius: 4px;
                    text-decoration: none;
                    display: inline-block;
                }}
            </style>
            <script>
                function showCategory(categoryId) {{
                    // Hide all category contents
                    var contents = document.getElementsByClassName('category-content');
                    for (var i = 0; i < contents.length; i++) {{
                        contents[i].classList.remove('active');
                    }}

                    // Hide all tab buttons
                    var tabs = document.getElementsByClassName('tab-button');
                    for (var i = 0; i < tabs.length; i++) {{
                        tabs[i].classList.remove('active');
                    }}

                    // Show selected category
                    document.getElementById('category-' + categoryId).classList.add('active');
                    document.getElementById('tab-' + categoryId).classList.add('active');
                }}
            </script>
        </head>
        <body>
            <div class="header">
                <h1>Configuration Management</h1>
                <div>
                    <a href="/{self.admin_site.name}/">← Dashboard</a>
                    <a href="/{self.admin_site.name}/logout">Logout</a>
                </div>
            </div>
            <div class="content">
                <div class="config-container">
                    <h2>Site Configuration</h2>
                    {success_html}
                    <form method="post">
                        <div class="tabs">
                            {category_tabs}
                        </div>
                        {category_content}
                        <div class="buttons">
                            <button type="submit">Save Configuration</button>
                            <a href="/{self.admin_site.name}/" class="cancel-link">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)

    def _render_config_field(self, setting: Any) -> str:
        """Render a configuration field based on its type.

        Args:
            setting: ConfigSetting instance

        Returns:
            HTML string for the field
        """
        disabled = "" if setting.editable else "disabled"
        value = setting.value if setting.value is not None else ""

        if setting.choices:
            # Render as select
            options = ""
            for choice in setting.choices:
                selected = "selected" if choice == setting.value else ""
                options += f'<option value="{choice}" {selected}>{choice}</option>'
            return f'<select name="{setting.key}" id="{setting.key}" {disabled}>{options}</select>'

        if setting.config_type.value == "boolean":
            checked = "checked" if setting.value else ""
            return f'<input type="checkbox" name="{setting.key}" id="{setting.key}" {checked} {disabled} value="true">'

        if setting.config_type.value == "integer":
            return f'<input type="number" name="{setting.key}" id="{setting.key}" value="{value}" {disabled}>'

        # Default to text input
        return f'<input type="text" name="{setting.key}" id="{setting.key}" value="{value}" {disabled}>'
