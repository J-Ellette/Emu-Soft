#!/usr/bin/env python3
"""
Test suite for Grafana Emulator

Tests core functionality including:
- Dashboard management
- Panel creation
- Data source configuration
- Template variables
- Alert rules
- User management
- Export/import
"""

import unittest
import json
from grafana_emulator import (
    GrafanaEmulator, PanelType, DataSourceType, AlertState,
    Dashboard, Panel, DataSource
)


class TestDashboardManagement(unittest.TestCase):
    """Test dashboard CRUD operations"""
    
    def setUp(self):
        """Set up Grafana for testing"""
        self.grafana = GrafanaEmulator()
    
    def test_create_dashboard(self):
        """Test creating a dashboard"""
        dashboard = self.grafana.create_dashboard("Test Dashboard", tags=["test"])
        
        self.assertEqual(dashboard.title, "Test Dashboard")
        self.assertIn("test", dashboard.tags)
        self.assertIsNotNone(dashboard.uid)
    
    def test_get_dashboard(self):
        """Test retrieving a dashboard"""
        dashboard = self.grafana.create_dashboard("My Dashboard")
        
        retrieved = self.grafana.get_dashboard(dashboard.id)
        self.assertEqual(retrieved.title, "My Dashboard")
    
    def test_get_dashboard_by_uid(self):
        """Test retrieving dashboard by UID"""
        dashboard = self.grafana.create_dashboard("UID Test")
        
        retrieved = self.grafana.get_dashboard_by_uid(dashboard.uid)
        self.assertEqual(retrieved.id, dashboard.id)
    
    def test_update_dashboard(self):
        """Test updating dashboard"""
        dashboard = self.grafana.create_dashboard("Old Title")
        
        updated = self.grafana.update_dashboard(dashboard.id, title="New Title")
        
        self.assertEqual(updated.title, "New Title")
        self.assertGreater(updated.version, 0)
    
    def test_delete_dashboard(self):
        """Test deleting dashboard"""
        dashboard = self.grafana.create_dashboard("To Delete")
        
        result = self.grafana.delete_dashboard(dashboard.id)
        self.assertTrue(result)
        
        retrieved = self.grafana.get_dashboard(dashboard.id)
        self.assertIsNone(retrieved)
    
    def test_search_dashboards(self):
        """Test searching dashboards"""
        self.grafana.create_dashboard("System Metrics", tags=["system"])
        self.grafana.create_dashboard("App Metrics", tags=["application"])
        self.grafana.create_dashboard("System Logs", tags=["system", "logs"])
        
        # Search by title
        results = self.grafana.search_dashboards(query="system")
        self.assertEqual(len(results), 2)
        
        # Search by tags
        results = self.grafana.search_dashboards(tags=["system"])
        self.assertEqual(len(results), 2)


class TestPanelManagement(unittest.TestCase):
    """Test panel operations"""
    
    def setUp(self):
        """Set up Grafana for testing"""
        self.grafana = GrafanaEmulator()
        self.dashboard = self.grafana.create_dashboard("Test Dashboard")
    
    def test_add_panel(self):
        """Test adding a panel"""
        panel = self.grafana.add_panel(
            self.dashboard.id,
            "CPU Usage",
            PanelType.GRAPH,
            x=0, y=0, w=12, h=8
        )
        
        self.assertIsNotNone(panel)
        self.assertEqual(panel.title, "CPU Usage")
        self.assertEqual(panel.type, PanelType.GRAPH)
    
    def test_add_target_to_panel(self):
        """Test adding query target to panel"""
        panel = self.grafana.add_panel(
            self.dashboard.id,
            "Metrics",
            PanelType.GRAPH
        )
        
        result = self.grafana.add_target_to_panel(
            self.dashboard.id,
            panel.id,
            "Prometheus",
            "rate(cpu[5m])",
            ref_id="A"
        )
        
        self.assertTrue(result)
        self.assertEqual(len(panel.targets), 1)
        self.assertEqual(panel.targets[0].expr, "rate(cpu[5m])")
    
    def test_remove_panel(self):
        """Test removing a panel"""
        panel = self.grafana.add_panel(self.dashboard.id, "Test", PanelType.STAT)
        
        result = self.grafana.remove_panel(self.dashboard.id, panel.id)
        self.assertTrue(result)
        
        dashboard = self.grafana.get_dashboard(self.dashboard.id)
        self.assertEqual(len(dashboard.panels), 0)


class TestDataSourceManagement(unittest.TestCase):
    """Test data source operations"""
    
    def setUp(self):
        """Set up Grafana for testing"""
        self.grafana = GrafanaEmulator()
    
    def test_create_datasource(self):
        """Test creating a data source"""
        ds = self.grafana.create_datasource(
            "Prometheus",
            DataSourceType.PROMETHEUS,
            "http://localhost:9090"
        )
        
        self.assertEqual(ds.name, "Prometheus")
        self.assertEqual(ds.type, DataSourceType.PROMETHEUS)
    
    def test_get_datasource(self):
        """Test retrieving data source"""
        ds = self.grafana.create_datasource(
            "InfluxDB",
            DataSourceType.INFLUXDB,
            "http://localhost:8086"
        )
        
        retrieved = self.grafana.get_datasource(ds.id)
        self.assertEqual(retrieved.name, "InfluxDB")
    
    def test_get_datasource_by_name(self):
        """Test retrieving data source by name"""
        self.grafana.create_datasource(
            "MySQL",
            DataSourceType.MYSQL,
            "localhost:3306"
        )
        
        ds = self.grafana.get_datasource_by_name("MySQL")
        self.assertIsNotNone(ds)
        self.assertEqual(ds.type, DataSourceType.MYSQL)
    
    def test_list_datasources(self):
        """Test listing all data sources"""
        self.grafana.create_datasource("DS1", DataSourceType.PROMETHEUS, "url1")
        self.grafana.create_datasource("DS2", DataSourceType.INFLUXDB, "url2")
        
        datasources = self.grafana.list_datasources()
        self.assertEqual(len(datasources), 2)
    
    def test_delete_datasource(self):
        """Test deleting data source"""
        ds = self.grafana.create_datasource("ToDelete", DataSourceType.MYSQL, "url")
        
        result = self.grafana.delete_datasource(ds.id)
        self.assertTrue(result)
        
        retrieved = self.grafana.get_datasource(ds.id)
        self.assertIsNone(retrieved)


class TestTemplateVariables(unittest.TestCase):
    """Test template variable functionality"""
    
    def setUp(self):
        """Set up Grafana for testing"""
        self.grafana = GrafanaEmulator()
        self.dashboard = self.grafana.create_dashboard("Test Dashboard")
    
    def test_add_template_variable(self):
        """Test adding template variable"""
        variable = self.grafana.add_template_variable(
            self.dashboard.id,
            "hostname",
            "query",
            query="label_values(hostname)",
            datasource="Prometheus"
        )
        
        self.assertIsNotNone(variable)
        self.assertEqual(variable.name, "hostname")
        
        dashboard = self.grafana.get_dashboard(self.dashboard.id)
        self.assertEqual(len(dashboard.templating), 1)


class TestAlertManagement(unittest.TestCase):
    """Test alert functionality"""
    
    def setUp(self):
        """Set up Grafana for testing"""
        self.grafana = GrafanaEmulator()
        self.dashboard = self.grafana.create_dashboard("Test Dashboard")
        self.panel = self.grafana.add_panel(
            self.dashboard.id,
            "CPU",
            PanelType.GRAPH
        )
    
    def test_create_alert(self):
        """Test creating an alert"""
        alert = self.grafana.create_alert(
            self.dashboard.id,
            self.panel.id,
            "High CPU",
            conditions=[{"type": "query"}]
        )
        
        self.assertEqual(alert.name, "High CPU")
        self.assertEqual(alert.state, AlertState.OK)
    
    def test_update_alert_state(self):
        """Test updating alert state"""
        alert = self.grafana.create_alert(
            self.dashboard.id,
            self.panel.id,
            "Test Alert",
            conditions=[]
        )
        
        result = self.grafana.update_alert_state(alert.id, AlertState.ALERTING)
        self.assertTrue(result)
        
        updated = self.grafana.get_alert(alert.id)
        self.assertEqual(updated.state, AlertState.ALERTING)
        self.assertIsNotNone(updated.last_state_change)
    
    def test_list_alerts(self):
        """Test listing alerts"""
        alert1 = self.grafana.create_alert(
            self.dashboard.id,
            self.panel.id,
            "Alert 1",
            conditions=[]
        )
        
        dashboard2 = self.grafana.create_dashboard("Dashboard 2")
        panel2 = self.grafana.add_panel(dashboard2.id, "Panel 2", PanelType.STAT)
        alert2 = self.grafana.create_alert(
            dashboard2.id,
            panel2.id,
            "Alert 2",
            conditions=[]
        )
        
        # List all alerts
        all_alerts = self.grafana.list_alerts()
        self.assertEqual(len(all_alerts), 2)
        
        # List dashboard-specific alerts
        dashboard_alerts = self.grafana.list_alerts(dashboard_id=self.dashboard.id)
        self.assertEqual(len(dashboard_alerts), 1)
        self.assertEqual(dashboard_alerts[0].name, "Alert 1")


class TestUserManagement(unittest.TestCase):
    """Test user management"""
    
    def setUp(self):
        """Set up Grafana for testing"""
        self.grafana = GrafanaEmulator()
    
    def test_create_user(self):
        """Test creating a user"""
        user = self.grafana.create_user(
            "testuser",
            "test@example.com",
            "Test User"
        )
        
        self.assertEqual(user.login, "testuser")
        self.assertFalse(user.is_admin)
    
    def test_get_user(self):
        """Test retrieving user"""
        user = self.grafana.create_user("john", "john@example.com", "John Doe")
        
        retrieved = self.grafana.get_user(user.id)
        self.assertEqual(retrieved.name, "John Doe")
    
    def test_get_user_by_login(self):
        """Test retrieving user by login"""
        self.grafana.create_user("jane", "jane@example.com", "Jane Doe")
        
        user = self.grafana.get_user_by_login("jane")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "jane@example.com")
    
    def test_default_admin_user(self):
        """Test that admin user exists by default"""
        admin = self.grafana.get_user_by_login("admin")
        
        self.assertIsNotNone(admin)
        self.assertTrue(admin.is_admin)


class TestOrganizations(unittest.TestCase):
    """Test organization management"""
    
    def setUp(self):
        """Set up Grafana for testing"""
        self.grafana = GrafanaEmulator()
    
    def test_default_organization(self):
        """Test that default organization exists"""
        org = self.grafana.get_organization(1)
        
        self.assertIsNotNone(org)
        self.assertEqual(org.name, "Main Org.")
    
    def test_create_organization(self):
        """Test creating an organization"""
        org = self.grafana.create_organization("Test Org")
        
        self.assertEqual(org.name, "Test Org")
        self.assertIsNotNone(org.created)


class TestExportImport(unittest.TestCase):
    """Test dashboard export/import"""
    
    def setUp(self):
        """Set up Grafana for testing"""
        self.grafana = GrafanaEmulator()
    
    def test_export_dashboard(self):
        """Test exporting dashboard"""
        dashboard = self.grafana.create_dashboard("Export Test")
        panel = self.grafana.add_panel(dashboard.id, "Panel 1", PanelType.GRAPH)
        self.grafana.add_target_to_panel(
            dashboard.id,
            panel.id,
            "Prometheus",
            "up",
            ref_id="A"
        )
        
        exported = self.grafana.export_dashboard(dashboard.id)
        
        self.assertIsNotNone(exported)
        self.assertIn("Export Test", exported)
        
        # Verify it's valid JSON
        data = json.loads(exported)
        self.assertIn("dashboard", data)
    
    def test_import_dashboard(self):
        """Test importing dashboard"""
        json_data = json.dumps({
            "dashboard": {
                "title": "Imported Dashboard",
                "tags": ["imported"],
                "panels": [
                    {
                        "id": 1,
                        "title": "Imported Panel",
                        "type": "graph",
                        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
                        "targets": [
                            {
                                "refId": "A",
                                "datasource": "Prometheus",
                                "expr": "metric"
                            }
                        ]
                    }
                ]
            }
        })
        
        dashboard = self.grafana.import_dashboard(json_data)
        
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.title, "Imported Dashboard")
        self.assertEqual(len(dashboard.panels), 1)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
