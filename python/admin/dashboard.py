"""
Developed by PowerShield, as an alternative to Django Admin
"""

"""Dashboard functionality for the admin interface.

This module provides dashboard widgets and statistics for the admin interface.
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta
from admin.interface import AdminSite


class DashboardWidget:
    """Base class for dashboard widgets."""

    def __init__(self, title: str, template: str = "default") -> None:
        """Initialize the widget.

        Args:
            title: Widget title
            template: Template style for the widget
        """
        self.title = title
        self.template = template

    async def get_content(self) -> Dict[str, Any]:
        """Get widget content.

        Returns:
            Dictionary containing widget data
        """
        return {"title": self.title}

    def render(self, content: Dict[str, Any]) -> str:
        """Render the widget as HTML.

        Args:
            content: Widget content data

        Returns:
            HTML string
        """
        return f"""
        <div class="dashboard-widget">
            <h3>{content['title']}</h3>
            <div class="widget-content">
                {self._render_content(content)}
            </div>
        </div>
        """

    def _render_content(self, content: Dict[str, Any]) -> str:
        """Render the widget content body.

        Args:
            content: Widget content data

        Returns:
            HTML string
        """
        return ""


class StatisticsWidget(DashboardWidget):
    """Widget for displaying site statistics."""

    def __init__(self, admin_site: AdminSite) -> None:
        """Initialize statistics widget.

        Args:
            admin_site: Admin site instance
        """
        super().__init__("Site Statistics")
        self.admin_site = admin_site

    async def get_content(self) -> Dict[str, Any]:
        """Get statistics content.

        Returns:
            Dictionary with statistics data
        """
        content = await super().get_content()

        # Get statistics for each registered model
        stats = []
        for model in self.admin_site.get_registered_models():
            try:
                count = await self._get_model_count(model)
                stats.append(
                    {
                        "model_name": model.__name__,
                        "url_name": self.admin_site.get_model_name(model),
                        "count": count,
                    }
                )
            except Exception:
                # If we can't get the count, skip this model
                continue

        content["stats"] = stats
        return content

    async def _get_model_count(self, model: Any) -> int:
        """Get count of instances for a model.

        Args:
            model: Model class

        Returns:
            Number of instances
        """
        try:
            instances = await model.all()
            return len(instances)
        except Exception:
            return 0

    def _render_content(self, content: Dict[str, Any]) -> str:
        """Render statistics content.

        Args:
            content: Widget content data

        Returns:
            HTML string
        """
        stats_html = ""
        for stat in content.get("stats", []):
            stats_html += f"""
            <div class="stat-item">
                <a href="/admin/{stat['url_name']}/">
                    <span class="stat-label">{stat['model_name']}</span>
                    <span class="stat-value">{stat['count']}</span>
                </a>
            </div>
            """

        return stats_html or "<p>No statistics available</p>"


class RecentActivityWidget(DashboardWidget):
    """Widget for displaying recent activity."""

    def __init__(self, admin_site: AdminSite, limit: int = 10) -> None:
        """Initialize recent activity widget.

        Args:
            admin_site: Admin site instance
            limit: Maximum number of recent items to show
        """
        super().__init__("Recent Activity")
        self.admin_site = admin_site
        self.limit = limit

    async def get_content(self) -> Dict[str, Any]:
        """Get recent activity content.

        Returns:
            Dictionary with recent activity data
        """
        content = await super().get_content()

        # Get recent items from each model
        recent_items = []
        for model in self.admin_site.get_registered_models():
            try:
                items = await self._get_recent_items(model)
                recent_items.extend(items)
            except Exception:
                # If we can't get items, skip this model
                continue

        # Sort by timestamp (most recent first) and limit
        recent_items.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        content["items"] = recent_items[: self.limit]

        return content

    async def _get_recent_items(self, model: Any) -> List[Dict[str, Any]]:
        """Get recent items for a model.

        Args:
            model: Model class

        Returns:
            List of recent item dictionaries
        """
        items = []
        try:
            instances = await model.all()

            # Get the last few instances (assumes they have created_at or similar)
            for instance in instances[-self.limit :]:
                timestamp = None
                # Try to get a timestamp field
                for field_name in ["created_at", "updated_at", "timestamp"]:
                    if hasattr(instance, field_name):
                        timestamp = getattr(instance, field_name)
                        if timestamp:
                            break

                if timestamp is None:
                    timestamp = datetime.now()

                # Get primary key
                pk_field = self._get_primary_key_field(model)
                pk_value = getattr(instance, pk_field, None)

                # Get display name (try common fields)
                display_name = None
                for field_name in ["title", "name", "username", pk_field]:
                    if hasattr(instance, field_name):
                        display_name = str(getattr(instance, field_name))
                        break

                if display_name and pk_value:
                    items.append(
                        {
                            "model_name": model.__name__,
                            "url_name": self.admin_site.get_model_name(model),
                            "display_name": display_name,
                            "pk": pk_value,
                            "timestamp": timestamp,
                        }
                    )
        except Exception:
            pass

        return items

    def _get_primary_key_field(self, model: Any) -> str:
        """Get the primary key field name.

        Args:
            model: Model class

        Returns:
            Primary key field name
        """
        for field_name, field in model._fields.items():
            if field.primary_key:
                return field_name
        return "id"

    def _render_content(self, content: Dict[str, Any]) -> str:
        """Render recent activity content.

        Args:
            content: Widget content data

        Returns:
            HTML string
        """
        items_html = ""
        for item in content.get("items", []):
            timestamp = item.get("timestamp", datetime.now())
            time_str = self._format_timestamp(timestamp)

            items_html += f"""
            <div class="activity-item">
                <a href="/admin/{item['url_name']}/{item['pk']}/">
                    <span class="activity-model">{item['model_name']}</span>:
                    <span class="activity-name">{item['display_name']}</span>
                </a>
                <span class="activity-time">{time_str}</span>
            </div>
            """

        return items_html or "<p>No recent activity</p>"

    def _format_timestamp(self, timestamp: datetime) -> str:
        """Format a timestamp for display.

        Args:
            timestamp: Timestamp to format

        Returns:
            Formatted string
        """
        if not isinstance(timestamp, datetime):
            return "Unknown"

        now = datetime.now()
        diff = now - timestamp

        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return timestamp.strftime("%Y-%m-%d %H:%M")


class QuickActionsWidget(DashboardWidget):
    """Widget for displaying quick action links."""

    def __init__(self, admin_site: AdminSite) -> None:
        """Initialize quick actions widget.

        Args:
            admin_site: Admin site instance
        """
        super().__init__("Quick Actions")
        self.admin_site = admin_site

    async def get_content(self) -> Dict[str, Any]:
        """Get quick actions content.

        Returns:
            Dictionary with quick actions data
        """
        content = await super().get_content()

        # Build quick actions for each model
        actions = []
        for model in self.admin_site.get_registered_models():
            admin = self.admin_site.get_model_admin(model)
            if admin and admin.has_add_permission():
                actions.append(
                    {
                        "model_name": model.__name__,
                        "url_name": self.admin_site.get_model_name(model),
                        "label": f"Add {model.__name__}",
                    }
                )

        content["actions"] = actions
        return content

    def _render_content(self, content: Dict[str, Any]) -> str:
        """Render quick actions content.

        Args:
            content: Widget content data

        Returns:
            HTML string
        """
        actions_html = ""
        for action in content.get("actions", []):
            actions_html += f"""
            <div class="action-item">
                <a href="/admin/{action['url_name']}/add/" class="action-link">
                    + {action['label']}
                </a>
            </div>
            """

        return actions_html or "<p>No actions available</p>"


class Dashboard:
    """Main dashboard class that aggregates widgets."""

    def __init__(self, admin_site: AdminSite) -> None:
        """Initialize dashboard.

        Args:
            admin_site: Admin site instance
        """
        self.admin_site = admin_site
        self.widgets: List[DashboardWidget] = []

        # Register default widgets
        self.add_widget(StatisticsWidget(admin_site))
        self.add_widget(RecentActivityWidget(admin_site))
        self.add_widget(QuickActionsWidget(admin_site))

    def add_widget(self, widget: DashboardWidget) -> None:
        """Add a widget to the dashboard.

        Args:
            widget: Widget to add
        """
        self.widgets.append(widget)

    def remove_widget(self, widget: DashboardWidget) -> None:
        """Remove a widget from the dashboard.

        Args:
            widget: Widget to remove
        """
        if widget in self.widgets:
            self.widgets.remove(widget)

    async def render(self) -> str:
        """Render the entire dashboard.

        Returns:
            HTML string
        """
        widgets_html = ""

        for widget in self.widgets:
            content = await widget.get_content()
            widgets_html += widget.render(content)

        return f"""
        <div class="dashboard">
            <div class="dashboard-widgets">
                {widgets_html}
            </div>
        </div>
        """
