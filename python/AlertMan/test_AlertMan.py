"""
Developed by PowerShield, as an alternative to AlertManager
"""

#!/usr/bin/env python3
"""Test suite for AlertManager Emulator"""

import unittest
from datetime import datetime, timedelta
from AlertMan import (
    AlertMan, Alert, Silence, Route, Receiver, AlertStatus
)


class TestAlertManager(unittest.TestCase):
    """Test AlertManager functionality"""
    
    def setUp(self):
        self.am = AlertMan()
    
    def test_add_receiver(self):
        """Test adding receiver"""
        receiver = self.am.add_receiver("test", webhook_configs=[{"url": "http://test"}])
        self.assertEqual(receiver.name, "test")
        self.assertIn("test", self.am.receivers)
    
    def test_post_alerts(self):
        """Test posting alerts"""
        self.am.post_alerts([
            {
                "labels": {"alertname": "TestAlert", "severity": "warning"},
                "annotations": {"summary": "Test alert"},
                "status": "firing"
            }
        ])
        
        alerts = self.am.get_alerts()
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].labels["alertname"], "TestAlert")
    
    def test_alert_routing(self):
        """Test alert routing"""
        receiver = self.am.add_receiver("critical")
        self.am.add_route("critical", match={"severity": "critical"})
        
        self.am.post_alerts([
            {"labels": {"alertname": "Test", "severity": "critical"}, "status": "firing"}
        ])
        
        # Alert should be routed (notification printed)
        alerts = self.am.get_alerts()
        self.assertEqual(len(alerts), 1)
    
    def test_silence(self):
        """Test silence creation"""
        silence = self.am.add_silence(
            matchers={"alertname": "TestAlert"},
            duration_hours=1,
            created_by="admin",
            comment="Maintenance"
        )
        
        self.assertEqual(len(self.am.get_silences()), 1)
        self.assertTrue(silence.is_active())
    
    def test_silence_matching(self):
        """Test silence matches alert"""
        silence = self.am.add_silence(
            matchers={"alertname": "CPU"},
            duration_hours=1,
            created_by="admin"
        )
        
        alert = Alert(labels={"alertname": "CPU", "severity": "warning"})
        self.assertTrue(silence.matches(alert))
        
        alert2 = Alert(labels={"alertname": "Memory", "severity": "warning"})
        self.assertFalse(silence.matches(alert2))
    
    def test_resolve_alert(self):
        """Test resolving alert"""
        self.am.post_alerts([
            {"labels": {"alertname": "Test"}, "status": "firing"}
        ])
        
        alert = self.am.get_alerts()[0]
        self.am.resolve_alert(alert.fingerprint)
        
        self.assertEqual(alert.status, AlertStatus.RESOLVED)
    
    def test_get_alerts_by_status(self):
        """Test filtering alerts by status"""
        self.am.post_alerts([
            {"labels": {"alertname": "Alert1"}, "status": "firing"},
            {"labels": {"alertname": "Alert2"}, "status": "resolved"}
        ])
        
        firing = self.am.get_alerts(status="firing")
        resolved = self.am.get_alerts(status="resolved")
        
        self.assertEqual(len(firing), 1)
        self.assertEqual(len(resolved), 1)


if __name__ == "__main__":
    unittest.main()
