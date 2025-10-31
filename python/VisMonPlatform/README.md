# Grafana Emulator - Visualization and Monitoring

A lightweight emulation of **Grafana**, the leading open source platform for metrics visualization and monitoring.

## Features

### Dashboard Management
- **Create/Edit/Delete**: Full dashboard lifecycle
- **Search**: Find dashboards by title and tags
- **Versioning**: Track dashboard changes
- **UID-based**: Unique identifiers for dashboards

### Panels
- **Multiple Types**: Graph, Stat, Table, Gauge, Heatmap, Pie Chart
- **Flexible Layout**: Grid-based positioning (x, y, width, height)
- **Query Targets**: Multiple queries per panel
- **Customization**: Panel options and field configuration

### Data Sources
- **Multiple Types**: Prometheus, InfluxDB, Elasticsearch, MySQL, PostgreSQL
- **Configuration**: URL, authentication, database settings
- **Default Source**: Mark a data source as default

### Templating
- **Variables**: Query, custom, interval, datasource types
- **Dynamic Dashboards**: Use variables in queries
- **Multi-select**: Select multiple values

### Alerting
- **Alert Rules**: Define conditions and thresholds
- **States**: OK, Pending, Alerting, No Data
- **Notifications**: Configure alert channels
- **Dashboard Integration**: Alerts tied to panels

### Users & Organizations
- **User Management**: Create and manage users
- **Organizations**: Multi-tenant support
- **Admin Users**: Elevated permissions
- **Default Admin**: Pre-configured admin user

### Export/Import
- **JSON Export**: Export dashboards as JSON
- **JSON Import**: Import dashboards from JSON
- **Sharing**: Easy dashboard sharing between instances

## What It Emulates

This tool emulates core functionality of [Grafana](https://grafana.com/), the analytics and monitoring solution used by thousands of companies worldwide.

### Core Components Implemented

1. **Dashboard System**
   - Dashboard CRUD operations
   - Panel management
   - Layout configuration

2. **Data Source Integration**
   - Multiple data source types
   - Connection configuration
   - Query execution (simulated)

3. **Visualization**
   - Panel types and configuration
   - Query targets
   - Display options

4. **Alerting**
   - Alert rule definition
   - State management
   - Notification configuration

5. **Multi-Tenancy**
   - Organizations
   - Users and permissions
   - Access control

## Usage

### Basic Setup

```python
from grafana_emulator import GrafanaEmulator, PanelType, DataSourceType

# Create Grafana instance
grafana = GrafanaEmulator()

# Create a data source
prometheus = grafana.create_datasource(
    "Prometheus",
    DataSourceType.PROMETHEUS,
    "http://localhost:9090",
    is_default=True
)
```

### Create Dashboard

```python
# Create dashboard
dashboard = grafana.create_dashboard(
    "System Metrics",
    tags=["system", "monitoring"]
)

print(f"Dashboard UID: {dashboard.uid}")
```

### Add Panels

```python
# Add CPU panel
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
    'rate(node_cpu_seconds_total{mode="idle"}[5m])',
    ref_id="A"
)

# Add memory panel
memory_panel = grafana.add_panel(
    dashboard.id,
    "Memory Usage",
    PanelType.STAT,
    x=12, y=0, w=6, h=4
)

grafana.add_target_to_panel(
    dashboard.id,
    memory_panel.id,
    "Prometheus",
    'node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100',
    ref_id="A"
)
```

### Template Variables

```python
# Add hostname variable
grafana.add_template_variable(
    dashboard.id,
    "hostname",
    "query",
    query="label_values(node_cpu_seconds_total, instance)",
    datasource="Prometheus",
    multi=True,
    include_all=True
)

# Use in query: node_cpu_seconds_total{instance="$hostname"}
```

### Create Alerts

```python
# Create alert for high CPU
alert = grafana.create_alert(
    dashboard.id,
    cpu_panel.id,
    "High CPU Alert",
    conditions=[
        {
            "type": "query",
            "query": {"params": ["A", "5m", "now"]},
            "evaluator": {"type": "gt", "params": [80]}
        }
    ],
    frequency="1m",
    for_duration="5m"
)

# Update alert state (simulated)
grafana.update_alert_state(alert.id, AlertState.ALERTING)
```

### Export and Import

```python
# Export dashboard
exported_json = grafana.export_dashboard(dashboard.id)

# Save to file
with open("dashboard.json", "w") as f:
    f.write(exported_json)

# Import dashboard
with open("dashboard.json", "r") as f:
    imported = grafana.import_dashboard(f.read())

print(f"Imported: {imported.title}")
```

### User Management

```python
# Create user
user = grafana.create_user(
    "analyst",
    "analyst@company.com",
    "Data Analyst",
    is_admin=False
)

# List all users
users = grafana.list_users()
for user in users:
    print(f"{user.login} - {user.email}")
```

### Search Dashboards

```python
# Create multiple dashboards
grafana.create_dashboard("App Performance", tags=["application"])
grafana.create_dashboard("Database Metrics", tags=["database"])
grafana.create_dashboard("Application Logs", tags=["application", "logs"])

# Search by title
results = grafana.search_dashboards(query="app")
print(f"Found {len(results)} dashboards")

# Search by tags
results = grafana.search_dashboards(tags=["application"])
print(f"Found {len(results)} with 'application' tag")
```

## API Reference

### GrafanaEmulator

**Dashboard Methods:**
- `create_dashboard(title, tags)` - Create dashboard
- `get_dashboard(dashboard_id)` - Get by ID
- `get_dashboard_by_uid(uid)` - Get by UID
- `update_dashboard(dashboard_id, **kwargs)` - Update dashboard
- `delete_dashboard(dashboard_id)` - Delete dashboard
- `search_dashboards(query, tags)` - Search dashboards

**Panel Methods:**
- `add_panel(dashboard_id, title, panel_type, x, y, w, h)` - Add panel
- `add_target_to_panel(dashboard_id, panel_id, datasource, expr, ref_id)` - Add query
- `remove_panel(dashboard_id, panel_id)` - Remove panel

**Data Source Methods:**
- `create_datasource(name, ds_type, url, **kwargs)` - Create data source
- `get_datasource(datasource_id)` - Get by ID
- `get_datasource_by_name(name)` - Get by name
- `list_datasources()` - List all
- `delete_datasource(datasource_id)` - Delete data source

**Template Methods:**
- `add_template_variable(dashboard_id, name, var_type, **kwargs)` - Add variable

**Alert Methods:**
- `create_alert(dashboard_id, panel_id, name, conditions)` - Create alert
- `get_alert(alert_id)` - Get alert
- `update_alert_state(alert_id, state)` - Update state
- `list_alerts(dashboard_id)` - List alerts

**User Methods:**
- `create_user(login, email, name, is_admin, org_id)` - Create user
- `get_user(user_id)` - Get user
- `get_user_by_login(login)` - Get by login
- `list_users()` - List all users

**Organization Methods:**
- `create_organization(name)` - Create org
- `get_organization(org_id)` - Get org

**Export/Import Methods:**
- `export_dashboard(dashboard_id)` - Export as JSON
- `import_dashboard(json_data, overwrite)` - Import from JSON

### Enums

**PanelType:**
- `GRAPH`, `STAT`, `TABLE`, `GAUGE`, `BAR_GAUGE`, `HEATMAP`, `PIE_CHART`, `TEXT`

**DataSourceType:**
- `PROMETHEUS`, `INFLUXDB`, `ELASTICSEARCH`, `MYSQL`, `POSTGRES`, `GRAPHITE`, `CLOUDWATCH`

**AlertState:**
- `OK`, `PENDING`, `ALERTING`, `NO_DATA`

## Testing

Run the test suite:

```bash
python test_grafana_emulator.py
```

Tests cover:
- Dashboard CRUD
- Panel management
- Data source configuration
- Template variables
- Alert management
- User management
- Export/import

## Limitations

This is an educational emulation with limitations:

1. **No Actual Queries**: Query execution is simulated
2. **No Rendering**: No actual graph rendering
3. **In-Memory Only**: No persistence
4. **Simplified Alerts**: Basic alert evaluation
5. **No Plugins**: No plugin system
6. **No API Server**: Direct function calls only
7. **Limited Panel Types**: Basic panel types only
8. **No Annotations**: Annotation system not implemented
9. **No Playlists**: Playlist feature not included
10. **No Snapshots**: Snapshot sharing not implemented

## Real-World Grafana

To use real Grafana, see [grafana.com](https://grafana.com/).

### Installation
```bash
# Docker
docker run -d -p 3000:3000 grafana/grafana

# Access at http://localhost:3000
# Default credentials: admin/admin
```

## Use Cases

- Learning dashboard design
- Understanding monitoring concepts
- Prototyping dashboard layouts
- Testing alert configurations
- Educational purposes
- Development environments

## Complexity

**Implementation Complexity**: Medium

This emulator involves:
- Dashboard data structures
- Panel configuration
- Data source management
- Query handling
- Alert system
- User management
- JSON serialization

## Comparison with Real Grafana

### Similarities
- Dashboard structure
- Panel types
- Data source concept
- Templating variables
- Alert rules
- User/org model

### Differences
- Real Grafana renders actual visualizations
- Real Grafana executes real queries
- Real Grafana has extensive plugin ecosystem
- Real Grafana has production-grade features
- Real Grafana has web UI
- Real Grafana supports many more features

## Dependencies

- Python 3.6+
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
