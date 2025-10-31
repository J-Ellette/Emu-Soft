#!/usr/bin/env python3
"""
AlertManager Emulator - Alert Routing and Management

This module emulates core AlertManager functionality including:
- Alert reception and storage
- Alert grouping and routing
- Silence management
- Notification routing
- Inhibition rules
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class AlertStatus(Enum):
    """Alert status"""
    FIRING = "firing"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """An alert instance"""
    labels: Dict[str, str]
    annotations: Dict[str, str] = field(default_factory=dict)
    status: AlertStatus = AlertStatus.FIRING
    starts_at: datetime = field(default_factory=datetime.now)
    ends_at: Optional[datetime] = None
    generator_url: str = ""
    fingerprint: str = ""
    
    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()
    
    def _generate_fingerprint(self) -> str:
        """Generate unique fingerprint from labels"""
        label_str = ",".join(f"{k}={v}" for k, v in sorted(self.labels.items()))
        return str(hash(label_str))
    
    def is_firing(self) -> bool:
        """Check if alert is firing"""
        return self.status == AlertStatus.FIRING
    
    def resolve(self):
        """Resolve the alert"""
        self.status = AlertStatus.RESOLVED
        self.ends_at = datetime.now()


@dataclass
class Silence:
    """Alert silence rule"""
    matchers: Dict[str, str]
    starts_at: datetime
    ends_at: datetime
    created_by: str
    comment: str = ""
    id: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(hash(f"{self.matchers}{self.starts_at}"))
    
    def is_active(self) -> bool:
        """Check if silence is currently active"""
        now = datetime.now()
        return self.starts_at <= now <= self.ends_at
    
    def matches(self, alert: Alert) -> bool:
        """Check if silence matches alert"""
        if not self.is_active():
            return False
        
        for key, value in self.matchers.items():
            if alert.labels.get(key) != value:
                return False
        return True


@dataclass
class Route:
    """Routing configuration"""
    receiver: str
    match: Dict[str, str] = field(default_factory=dict)
    match_re: Dict[str, str] = field(default_factory=dict)
    group_by: List[str] = field(default_factory=list)
    group_wait: int = 30  # seconds
    group_interval: int = 300  # seconds
    repeat_interval: int = 3600  # seconds
    continue_routing: bool = False
    routes: List['Route'] = field(default_factory=list)
    
    def matches(self, alert: Alert) -> bool:
        """Check if route matches alert"""
        # Check exact matches
        for key, value in self.match.items():
            if alert.labels.get(key) != value:
                return False
        
        # Check regex matches (simplified)
        import re
        for key, pattern in self.match_re.items():
            if key not in alert.labels:
                return False
            if not re.match(pattern, alert.labels[key]):
                return False
        
        return True


@dataclass
class Receiver:
    """Notification receiver"""
    name: str
    webhook_configs: List[Dict[str, str]] = field(default_factory=list)
    email_configs: List[Dict[str, str]] = field(default_factory=list)
    slack_configs: List[Dict[str, str]] = field(default_factory=list)
    pagerduty_configs: List[Dict[str, str]] = field(default_factory=list)
    
    def send_notification(self, alerts: List[Alert]):
        """Send notification for alerts"""
        # Simulate sending notification
        print(f"[{self.name}] Sending notification for {len(alerts)} alert(s)")
        for alert in alerts:
            print(f"  - {alert.labels.get('alertname', 'unknown')}: {alert.status.value}")


class AlertMan:
    """Main AlertManager emulator class"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}  # fingerprint -> Alert
        self.silences: Dict[str, Silence] = {}  # id -> Silence
        self.receivers: Dict[str, Receiver] = {}  # name -> Receiver
        self.routes: List[Route] = []
        self.default_receiver: str = "default"
    
    def add_receiver(self, name: str, **configs) -> Receiver:
        """Add a notification receiver"""
        receiver = Receiver(name=name, **configs)
        self.receivers[name] = receiver
        return receiver
    
    def add_route(self, receiver: str, **config) -> Route:
        """Add a routing rule"""
        route = Route(receiver=receiver, **config)
        self.routes.append(route)
        return route
    
    def post_alerts(self, alerts: List[Dict[str, Any]]):
        """Receive alerts from Prometheus or other sources"""
        for alert_data in alerts:
            alert = Alert(
                labels=alert_data.get("labels", {}),
                annotations=alert_data.get("annotations", {}),
                status=AlertStatus(alert_data.get("status", "firing")),
                generator_url=alert_data.get("generatorURL", "")
            )
            
            self.alerts[alert.fingerprint] = alert
            self._route_alert(alert)
    
    def _route_alert(self, alert: Alert):
        """Route alert to appropriate receiver"""
        # Check if alert is silenced
        for silence in self.silences.values():
            if silence.matches(alert):
                print(f"Alert {alert.labels.get('alertname')} is silenced")
                return
        
        # Find matching route
        for route in self.routes:
            if route.matches(alert):
                receiver = self.receivers.get(route.receiver)
                if receiver:
                    receiver.send_notification([alert])
                if not route.continue_routing:
                    return
        
        # Use default receiver
        default = self.receivers.get(self.default_receiver)
        if default:
            default.send_notification([alert])
    
    def get_alerts(self, status: Optional[str] = None) -> List[Alert]:
        """Get all alerts, optionally filtered by status"""
        alerts = list(self.alerts.values())
        if status:
            alerts = [a for a in alerts if a.status.value == status]
        return alerts
    
    def resolve_alert(self, fingerprint: str):
        """Resolve an alert"""
        if fingerprint in self.alerts:
            self.alerts[fingerprint].resolve()
    
    def add_silence(self, matchers: Dict[str, str], duration_hours: int,
                    created_by: str, comment: str = "") -> Silence:
        """Add a silence rule"""
        silence = Silence(
            matchers=matchers,
            starts_at=datetime.now(),
            ends_at=datetime.now() + timedelta(hours=duration_hours),
            created_by=created_by,
            comment=comment
        )
        self.silences[silence.id] = silence
        return silence
    
    def delete_silence(self, silence_id: str) -> bool:
        """Delete a silence"""
        if silence_id in self.silences:
            del self.silences[silence_id]
            return True
        return False
    
    def get_silences(self) -> List[Silence]:
        """Get all silences"""
        return list(self.silences.values())
    
    def get_active_silences(self) -> List[Silence]:
        """Get active silences"""
        return [s for s in self.silences.values() if s.is_active()]


# Helper functions
def create_receiver(am: AlertMan, name: str, **configs) -> Receiver:
    """Helper to create a receiver"""
    return am.add_receiver(name, **configs)


def create_route(am: AlertMan, receiver: str, **config) -> Route:
    """Helper to create a route"""
    return am.add_route(receiver, **config)


if __name__ == "__main__":
    # Example usage
    am = AlertMan()
    
    # Add receivers
    am.add_receiver("default", webhook_configs=[{"url": "http://localhost:9000"}])
    am.add_receiver("critical", pagerduty_configs=[{"service_key": "xxx"}])
    
    # Add routes
    am.add_route("critical", match={"severity": "critical"})
    
    # Post alerts
    am.post_alerts([
        {
            "labels": {"alertname": "HighCPU", "severity": "warning"},
            "annotations": {"summary": "CPU usage high"},
            "status": "firing"
        }
    ])
