# Fluentd Emulator - Unified Logging Layer

A lightweight emulation of **Fluentd**, the open-source data collector for building a unified logging layer.

## Features

This emulator implements core Fluentd functionality:

### Log Collection
- **Multiple Sources**: Tail files, HTTP, forward protocol
- **Tag-based Routing**: Route logs based on tags
- **Flexible Input**: Accept logs from various sources

### Log Processing
- **Filtering**: Filter logs based on patterns
- **Transformation**: Add, remove, or modify fields
- **Parsing**: Parse log formats (JSON, regex, etc.)
- **Buffering**: Buffer logs before output

### Log Output
- **Multiple Outputs**: stdout, file, forward, Elasticsearch, Kafka
- **Pattern Matching**: Route logs to outputs based on tags
- **Buffering**: Buffer output for batch processing
- **Flushing**: Flush buffers on demand

## What It Emulates

This tool emulates core functionality of [Fluentd](https://www.fluentd.org/), a popular log collector.

## Usage

### Basic Log Collection

```python
from fluentd_emulator import FluentdEmulator

# Create Fluentd instance
fluentd = FluentdEmulator()

# Add output
fluentd.add_output("stdout", "**")

# Start collecting
fluentd.start()

# Emit logs
fluentd.emit("app.access", {"method": "GET", "path": "/api", "status": 200})
fluentd.emit("app.error", {"error": "Connection timeout", "code": 500})

# Stop
fluentd.stop()
```

### Filtering Logs

```python
from fluentd_emulator import FluentdEmulator

fluentd = FluentdEmulator()

# Filter only ERROR logs
fluentd.add_filter("grep", "app.*", regexp="ERROR", key="level")

# Output to file
fluentd.add_output("file", "app.**", path="/var/log/filtered.log")

# Emit logs
fluentd.emit("app.log", {"level": "INFO", "msg": "Normal operation"})
fluentd.emit("app.log", {"level": "ERROR", "msg": "Something went wrong"})

# Only ERROR logs will be in output
```

### Transforming Records

```python
from fluentd_emulator import FluentdEmulator

fluentd = FluentdEmulator()

# Add hostname to all logs
fluentd.add_filter(
    "record_transformer",
    "app.*",
    add={"hostname": "server1", "env": "production"}
)

fluentd.add_output("stdout", "**")

fluentd.emit("app.log", {"msg": "Test"})
# Output will include hostname and env fields
```

### Multiple Outputs

```python
from fluentd_emulator import FluentdEmulator

fluentd = FluentdEmulator()

# Route access logs to one output
fluentd.add_output("file", "app.access.*", path="/logs/access.log")

# Route error logs to another
fluentd.add_output("file", "app.error.*", path="/logs/error.log")

# All logs to stdout
fluentd.add_output("stdout", "**")

fluentd.emit("app.access.web", {"method": "GET"})
fluentd.emit("app.error.web", {"error": "404"})
```

## API Reference

### Main Classes

#### `FluentdEmulator`
**Methods:**
- `add_source(source_type, tag, **config)` - Add input source
- `add_filter(filter_type, tag_pattern, **config)` - Add filter
- `add_output(output_type, tag_pattern, **config)` - Add output
- `emit(tag, record)` - Emit log record
- `start()` - Start collecting
- `stop()` - Stop collecting
- `flush_all()` - Flush all buffers

#### `Source`
**Attributes:**
- `source_type` - Type of source (tail, http, forward)
- `tag` - Tag for logs from this source
- `config` - Source configuration

#### `Filter`
**Attributes:**
- `filter_type` - Type of filter (grep, record_transformer, parser)
- `tag_pattern` - Pattern to match tags
- `config` - Filter configuration

**Methods:**
- `matches(tag)` - Check if tag matches
- `process(record)` - Process log record

#### `Output`
**Attributes:**
- `output_type` - Type of output (stdout, file, elasticsearch, kafka)
- `tag_pattern` - Pattern to match tags
- `buffer` - Buffered logs

**Methods:**
- `matches(tag)` - Check if tag matches
- `write(record)` - Write log record
- `flush()` - Flush buffer

## Testing

Run the test suite:

```bash
python test_fluentd_emulator.py
```

## Limitations

- Simplified filtering and parsing
- In-memory buffering only
- No actual file I/O
- Basic pattern matching

## Dependencies

- Python 3.7+
- No external dependencies required

## License

Part of the Emu-Soft project - see main repository LICENSE.
