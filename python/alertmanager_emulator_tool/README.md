# AlertManager Emulator - Alert Routing and Management

A lightweight emulation of **Prometheus AlertManager**, the alert handling and routing component of the Prometheus monitoring system.

## Features

This emulator implements core AlertManager functionality:

### Alert Management
- **Alert Reception**: Receive alerts from Prometheus or other sources
- **Alert Storage**: Store active and resolved alerts
- **Alert Resolution**: Mark alerts as resolved
- **Alert Fingerprinting**: Unique identification of alerts

### Routing
- **Route Configuration**: Define routing rules
- **Label Matching**: Route based on label matchers
- **Receiver Assignment**: Send alerts to appropriate receivers
- **Nested Routes**: Support for route hierarchies

### Silences
- **Silence Creation**: Temporarily mute alerts
- **Silence Matching**: Match alerts based on labels
- **Active Silences**: Track currently active silences
- **Silence Expiration**: Time-based silence management

### Receivers
- **Multiple Receivers**: Support various notification channels
- **Webhook**: Send to webhook URLs
- **Email**: Email notifications
- **Slack**: Slack notifications
- **PagerDuty**: PagerDuty integration

## What It Emulates

This tool emulates core functionality of [Prometheus AlertManager](https://prometheus.io/docs/alerting/latest/alertmanager/).

## Usage

### Basic Alert Handling

```python
from alertmanager_emulator import AlertManagerEmulator

# Create AlertManager instance
am = AlertManagerEmulator()

# Add receiver
am.add_receiver("default", webhook_configs=[{"url": "http://localhost:9000"}])

# Post alerts
am.post_alerts([
    {
        "labels": {"alertname": "HighCPU", "severity": "warning"},
        "annotations": {"summary": "CPU usage above 80%"},
        "status": "firing"
    }
])

# Get all alerts
alerts = am.get_alerts()
print(f"Total alerts: {len(alerts)}")
```

### Alert Routing

```python
from alertmanager_emulator import AlertManagerEmulator

am = AlertManagerEmulator()

# Add receivers
am.add_receiver("default")
am.add_receiver("critical", pagerduty_configs=[{"service_key": "xxx"}])
am.add_receiver("warning", email_configs=[{"to": "team@example.com"}])

# Add routes
am.add_route("critical", match={"severity": "critical"})
am.add_route("warning", match={"severity": "warning"})

# Post alerts - will be routed based on severity
am.post_alerts([
    {"labels": {"alertname": "DiskFull", "severity": "critical"}, "status": "firing"},
    {"labels": {"alertname": "HighMemory", "severity": "warning"}, "status": "firing"}
])
```

### Silences

```python
from alertmanager_emulator import AlertManagerEmulator

am = AlertManagerEmulator()

# Add silence for maintenance window
silence = am.add_silence(
    matchers={"alertname": "HighCPU", "instance": "server1"},
    duration_hours=2,
    created_by="admin@example.com",
    comment="Scheduled maintenance"
)

print(f"Silence ID: {silence.id}")

# Get active silences
active = am.get_active_silences()
print(f"Active silences: {len(active)}")

# Delete silence
am.delete_silence(silence.id)
```

## API Reference

### Main Classes

#### `AlertManagerEmulator`
**Methods:**
- `add_receiver(name, **configs)` - Add receiver
- `add_route(receiver, **config)` - Add routing rule
- `post_alerts(alerts)` - Receive alerts
- `get_alerts(status)` - Get alerts
- `resolve_alert(fingerprint)` - Resolve alert
- `add_silence(matchers, duration_hours, created_by, comment)` - Create silence
- `delete_silence(silence_id)` - Delete silence
- `get_silences()` - Get all silences
- `get_active_silences()` - Get active silences

#### `Alert`
**Attributes:**
- `labels` - Alert labels
- `annotations` - Alert annotations
- `status` - Alert status (firing/resolved)
- `fingerprint` - Unique identifier

#### `Silence`
**Attributes:**
- `matchers` - Label matchers
- `starts_at` - Silence start time
- `ends_at` - Silence end time
- `created_by` - Creator
- `id` - Unique identifier

**Methods:**
- `is_active()` - Check if silence is active
- `matches(alert)` - Check if silence matches alert

## Testing

```bash
python test_alertmanager_emulator.py
```

## Limitations

- Simplified routing logic
- No grouping/aggregation
- No inhibition rules
- In-memory storage only

## Dependencies

- Python 3.7+
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
