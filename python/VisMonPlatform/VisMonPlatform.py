#!/usr/bin/env python3
"""
Grafana Emulator - Visualization and Monitoring

This module emulates core Grafana functionality including:
- Dashboard creation and management
- Panel types (graph, stat, table, etc.)
- Data source configuration
- Query building
- Alerting
- User and organization management
- Templating variables
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import secrets


class PanelType(Enum):
    """Types of visualization panels"""
    GRAPH = "graph"
    STAT = "stat"
    TABLE = "table"
    GAUGE = "gauge"
    BAR_GAUGE = "bar-gauge"
    HEATMAP = "heatmap"
    PIE_CHART = "pie-chart"
    TEXT = "text"


class DataSourceType(Enum):
    """Types of data sources"""
    PROMETHEUS = "prometheus"
    INFLUXDB = "influxdb"
    ELASTICSEARCH = "elasticsearch"
    MYSQL = "mysql"
    POSTGRES = "postgres"
    GRAPHITE = "graphite"
    CLOUDWATCH = "cloudwatch"


class AlertState(Enum):
    """Alert states"""
    OK = "ok"
    PENDING = "pending"
    ALERTING = "alerting"
    NO_DATA = "no_data"


@dataclass
class DataSource:
    """Data source configuration"""
    id: int
    name: str
    type: DataSourceType
    url: str
    access: str = "proxy"  # proxy or direct
    basic_auth: bool = False
    database: Optional[str] = None
    user: Optional[str] = None
    is_default: bool = False
    json_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Target:
    """Query target for a panel"""
    ref_id: str
    datasource: str
    expr: str  # Query expression
    legend_format: Optional[str] = None
    interval: Optional[str] = None
    format: str = "time_series"


@dataclass
class Panel:
    """Dashboard panel"""
    id: int
    title: str
    type: PanelType
    datasource: Optional[str] = None
    targets: List[Target] = field(default_factory=list)
    grid_pos: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0, "w": 12, "h": 8})
    options: Dict[str, Any] = field(default_factory=dict)
    field_config: Dict[str, Any] = field(default_factory=dict)
    transparent: bool = False
    description: Optional[str] = None


@dataclass
class TemplateVariable:
    """Dashboard template variable"""
    name: str
    type: str  # query, custom, interval, datasource, etc.
    query: Optional[str] = None
    datasource: Optional[str] = None
    current: Optional[str] = None
    options: List[Dict[str, str]] = field(default_factory=list)
    multi: bool = False
    include_all: bool = False


@dataclass
class Dashboard:
    """Grafana dashboard"""
    id: Optional[int] = None
    uid: Optional[str] = None
    title: str = "New Dashboard"
    tags: List[str] = field(default_factory=list)
    panels: List[Panel] = field(default_factory=list)
    templating: List[TemplateVariable] = field(default_factory=list)
    timezone: str = "browser"
    editable: bool = True
    version: int = 0
    created: Optional[str] = None
    updated: Optional[str] = None
    created_by: Optional[str] = None


@dataclass
class AlertRule:
    """Alert rule configuration"""
    id: int
    dashboard_id: int
    panel_id: int
    name: str
    conditions: List[Dict[str, Any]]
    frequency: str = "60s"  # How often to evaluate
    for_duration: str = "5m"  # How long condition must be true
    state: AlertState = AlertState.OK
    notifications: List[str] = field(default_factory=list)
    message: Optional[str] = None
    last_state_change: Optional[str] = None


@dataclass
class User:
    """Grafana user"""
    id: int
    login: str
    email: str
    name: str
    is_admin: bool = False
    org_id: int = 1
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Organization:
    """Grafana organization"""
    id: int
    name: str
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class VisMonPlatform:
    """Main Grafana emulator class"""
    
    def __init__(self):
        self.dashboards: Dict[int, Dashboard] = {}
        self.datasources: Dict[int, DataSource] = {}
        self.users: Dict[int, User] = {}
        self.organizations: Dict[int, Organization] = {}
        self.alert_rules: Dict[int, AlertRule] = {}
        
        self._next_dashboard_id = 1
        self._next_datasource_id = 1
        self._next_user_id = 1
        self._next_org_id = 1
        self._next_alert_id = 1
        self._next_panel_id = 1
        
        # Create default organization
        default_org = Organization(id=1, name="Main Org.")
        self.organizations[1] = default_org
        
        # Create admin user
        admin = User(
            id=1,
            login="admin",
            email="admin@localhost",
            name="Admin",
            is_admin=True,
            org_id=1
        )
        self.users[1] = admin
    
    # Dashboard Management
    
    def create_dashboard(self, title: str, tags: List[str] = None) -> Dashboard:
        """Create a new dashboard"""
        if tags is None:
            tags = []
        
        dashboard = Dashboard(
            id=self._next_dashboard_id,
            uid=secrets.token_urlsafe(9),
            title=title,
            tags=tags,
            created=datetime.utcnow().isoformat(),
            updated=datetime.utcnow().isoformat()
        )
        
        self.dashboards[self._next_dashboard_id] = dashboard
        self._next_dashboard_id += 1
        
        return dashboard
    
    def get_dashboard(self, dashboard_id: int) -> Optional[Dashboard]:
        """Get dashboard by ID"""
        return self.dashboards.get(dashboard_id)
    
    def get_dashboard_by_uid(self, uid: str) -> Optional[Dashboard]:
        """Get dashboard by UID"""
        for dashboard in self.dashboards.values():
            if dashboard.uid == uid:
                return dashboard
        return None
    
    def update_dashboard(self, dashboard_id: int, **kwargs) -> Optional[Dashboard]:
        """Update dashboard properties"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        for key, value in kwargs.items():
            if hasattr(dashboard, key):
                setattr(dashboard, key, value)
        
        dashboard.updated = datetime.utcnow().isoformat()
        dashboard.version += 1
        
        return dashboard
    
    def delete_dashboard(self, dashboard_id: int) -> bool:
        """Delete a dashboard"""
        if dashboard_id in self.dashboards:
            del self.dashboards[dashboard_id]
            return True
        return False
    
    def search_dashboards(self, query: str = "", tags: List[str] = None) -> List[Dashboard]:
        """Search dashboards"""
        results = []
        
        for dashboard in self.dashboards.values():
            # Match by title
            if query and query.lower() not in dashboard.title.lower():
                continue
            
            # Match by tags
            if tags:
                if not any(tag in dashboard.tags for tag in tags):
                    continue
            
            results.append(dashboard)
        
        return results
    
    # Panel Management
    
    def add_panel(self, dashboard_id: int, title: str, panel_type: PanelType, 
                  x: int = 0, y: int = 0, w: int = 12, h: int = 8) -> Optional[Panel]:
        """Add panel to dashboard"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        panel = Panel(
            id=self._next_panel_id,
            title=title,
            type=panel_type,
            grid_pos={"x": x, "y": y, "w": w, "h": h}
        )
        
        dashboard.panels.append(panel)
        self._next_panel_id += 1
        
        dashboard.updated = datetime.utcnow().isoformat()
        dashboard.version += 1
        
        return panel
    
    def add_target_to_panel(self, dashboard_id: int, panel_id: int, 
                            datasource: str, expr: str, ref_id: str = "A") -> bool:
        """Add query target to panel"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return False
        
        panel = next((p for p in dashboard.panels if p.id == panel_id), None)
        if not panel:
            return False
        
        target = Target(
            ref_id=ref_id,
            datasource=datasource,
            expr=expr
        )
        
        panel.targets.append(target)
        return True
    
    def remove_panel(self, dashboard_id: int, panel_id: int) -> bool:
        """Remove panel from dashboard"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return False
        
        dashboard.panels = [p for p in dashboard.panels if p.id != panel_id]
        dashboard.updated = datetime.utcnow().isoformat()
        dashboard.version += 1
        
        return True
    
    # Data Source Management
    
    def create_datasource(self, name: str, ds_type: DataSourceType, 
                         url: str, **kwargs) -> DataSource:
        """Create a data source"""
        datasource = DataSource(
            id=self._next_datasource_id,
            name=name,
            type=ds_type,
            url=url,
            **kwargs
        )
        
        self.datasources[self._next_datasource_id] = datasource
        self._next_datasource_id += 1
        
        return datasource
    
    def get_datasource(self, datasource_id: int) -> Optional[DataSource]:
        """Get data source by ID"""
        return self.datasources.get(datasource_id)
    
    def get_datasource_by_name(self, name: str) -> Optional[DataSource]:
        """Get data source by name"""
        for ds in self.datasources.values():
            if ds.name == name:
                return ds
        return None
    
    def list_datasources(self) -> List[DataSource]:
        """List all data sources"""
        return list(self.datasources.values())
    
    def delete_datasource(self, datasource_id: int) -> bool:
        """Delete a data source"""
        if datasource_id in self.datasources:
            del self.datasources[datasource_id]
            return True
        return False
    
    # Template Variables
    
    def add_template_variable(self, dashboard_id: int, name: str, 
                             var_type: str, **kwargs) -> Optional[TemplateVariable]:
        """Add template variable to dashboard"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        variable = TemplateVariable(name=name, type=var_type, **kwargs)
        dashboard.templating.append(variable)
        
        return variable
    
    # Alert Management
    
    def create_alert(self, dashboard_id: int, panel_id: int, name: str,
                    conditions: List[Dict[str, Any]]) -> AlertRule:
        """Create an alert rule"""
        alert = AlertRule(
            id=self._next_alert_id,
            dashboard_id=dashboard_id,
            panel_id=panel_id,
            name=name,
            conditions=conditions,
            state=AlertState.OK
        )
        
        self.alert_rules[self._next_alert_id] = alert
        self._next_alert_id += 1
        
        return alert
    
    def get_alert(self, alert_id: int) -> Optional[AlertRule]:
        """Get alert by ID"""
        return self.alert_rules.get(alert_id)
    
    def update_alert_state(self, alert_id: int, state: AlertState) -> bool:
        """Update alert state"""
        alert = self.alert_rules.get(alert_id)
        if not alert:
            return False
        
        alert.state = state
        alert.last_state_change = datetime.utcnow().isoformat()
        return True
    
    def list_alerts(self, dashboard_id: Optional[int] = None) -> List[AlertRule]:
        """List alerts, optionally filtered by dashboard"""
        alerts = list(self.alert_rules.values())
        
        if dashboard_id is not None:
            alerts = [a for a in alerts if a.dashboard_id == dashboard_id]
        
        return alerts
    
    # User Management
    
    def create_user(self, login: str, email: str, name: str, 
                   is_admin: bool = False, org_id: int = 1) -> User:
        """Create a user"""
        user = User(
            id=self._next_user_id,
            login=login,
            email=email,
            name=name,
            is_admin=is_admin,
            org_id=org_id
        )
        
        self.users[self._next_user_id] = user
        self._next_user_id += 1
        
        return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_login(self, login: str) -> Optional[User]:
        """Get user by login"""
        for user in self.users.values():
            if user.login == login:
                return user
        return None
    
    def list_users(self) -> List[User]:
        """List all users"""
        return list(self.users.values())
    
    # Organization Management
    
    def create_organization(self, name: str) -> Organization:
        """Create an organization"""
        org = Organization(id=self._next_org_id, name=name)
        self.organizations[self._next_org_id] = org
        self._next_org_id += 1
        return org
    
    def get_organization(self, org_id: int) -> Optional[Organization]:
        """Get organization by ID"""
        return self.organizations.get(org_id)
    
    # Export/Import
    
    def export_dashboard(self, dashboard_id: int) -> Optional[str]:
        """Export dashboard as JSON"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        data = {
            "dashboard": {
                "id": dashboard.id,
                "uid": dashboard.uid,
                "title": dashboard.title,
                "tags": dashboard.tags,
                "timezone": dashboard.timezone,
                "panels": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "type": p.type.value,
                        "datasource": p.datasource,
                        "gridPos": p.grid_pos,
                        "targets": [
                            {
                                "refId": t.ref_id,
                                "datasource": t.datasource,
                                "expr": t.expr
                            }
                            for t in p.targets
                        ]
                    }
                    for p in dashboard.panels
                ],
                "templating": {
                    "list": [
                        {
                            "name": v.name,
                            "type": v.type,
                            "query": v.query,
                            "datasource": v.datasource
                        }
                        for v in dashboard.templating
                    ]
                }
            }
        }
        
        return json.dumps(data, indent=2)
    
    def import_dashboard(self, json_data: str, overwrite: bool = False) -> Optional[Dashboard]:
        """Import dashboard from JSON"""
        try:
            data = json.loads(json_data)
            dashboard_data = data.get("dashboard", {})
            
            # Create new dashboard
            dashboard = self.create_dashboard(
                title=dashboard_data.get("title", "Imported Dashboard"),
                tags=dashboard_data.get("tags", [])
            )
            
            # Import panels
            for panel_data in dashboard_data.get("panels", []):
                panel_type = PanelType(panel_data.get("type", "graph"))
                grid_pos = panel_data.get("gridPos", {})
                
                panel = self.add_panel(
                    dashboard.id,
                    panel_data.get("title", "Panel"),
                    panel_type,
                    x=grid_pos.get("x", 0),
                    y=grid_pos.get("y", 0),
                    w=grid_pos.get("w", 12),
                    h=grid_pos.get("h", 8)
                )
                
                # Import targets
                for target_data in panel_data.get("targets", []):
                    self.add_target_to_panel(
                        dashboard.id,
                        panel.id,
                        target_data.get("datasource", ""),
                        target_data.get("expr", ""),
                        target_data.get("refId", "A")
                    )
            
            return dashboard
        
        except Exception as e:
            print(f"Error importing dashboard: {e}")
            return None


if __name__ == "__main__":
    # Example usage
    grafana = VisMonPlatform()
    
    # Create a data source
    prometheus_ds = grafana.create_datasource(
        "Prometheus",
        DataSourceType.PROMETHEUS,
        "http://localhost:9090",
        is_default=True
    )
    print(f"Created datasource: {prometheus_ds.name}")
    
    # Create a dashboard
    dashboard = grafana.create_dashboard("System Metrics", tags=["monitoring", "system"])
    print(f"Created dashboard: {dashboard.title} (UID: {dashboard.uid})")
    
    # Add panels
    cpu_panel = grafana.add_panel(
        dashboard.id,
        "CPU Usage",
        PanelType.GRAPH,
        x=0, y=0, w=12, h=8
    )
    
    # Add query to panel
    grafana.add_target_to_panel(
        dashboard.id,
        cpu_panel.id,
        "Prometheus",
        "rate(cpu_usage[5m])",
        ref_id="A"
    )
    
    memory_panel = grafana.add_panel(
        dashboard.id,
        "Memory Usage",
        PanelType.STAT,
        x=0, y=8, w=6, h=4
    )
    
    # Create alert
    alert = grafana.create_alert(
        dashboard.id,
        cpu_panel.id,
        "High CPU Alert",
        conditions=[{"type": "query", "query": {"params": ["A", "5m", "now"]}}]
    )
    print(f"Created alert: {alert.name}")
    
    # Export dashboard
    exported = grafana.export_dashboard(dashboard.id)
    print(f"Exported dashboard JSON:\n{exported[:200]}...")
