"""
Developed by PowerShield, as an alternative to Fluentd
"""

#!/usr/bin/env python3
"""
Fluentd Emulator - Unified Logging Layer

This module emulates core Fluentd functionality including:
- Log collection from multiple sources
- Log parsing and filtering
- Log routing and tagging
- Output plugins
- Buffer management
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from collections import deque


@dataclass
class LogRecord:
    """A log record"""
    tag: str
    time: Optional[datetime]
    record: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tag": self.tag,
            "time": self.time.isoformat() if self.time else datetime.now().isoformat(),
            "record": self.record
        }


class Source:
    """Input source for logs"""
    
    def __init__(self, source_type: str, tag: str, **config):
        self.source_type = source_type
        self.tag = tag
        self.config = config
        self.running = False
    
    def start(self):
        """Start collecting logs"""
        self.running = True
    
    def stop(self):
        """Stop collecting logs"""
        self.running = False
    
    def emit(self, record: Dict[str, Any]) -> LogRecord:
        """Emit a log record"""
        return LogRecord(
            tag=self.tag,
            time=datetime.now(),
            record=record
        )


class Filter:
    """Log filter/transformer"""
    
    def __init__(self, filter_type: str, tag_pattern: str, **config):
        self.filter_type = filter_type
        self.tag_pattern = tag_pattern
        self.config = config
    
    def matches(self, tag: str) -> bool:
        """Check if tag matches filter pattern"""
        pattern = self.tag_pattern.replace("*", ".*").replace(".", "\\.")
        return re.match(pattern, tag) is not None
    
    def process(self, record: LogRecord) -> Optional[LogRecord]:
        """Process log record"""
        if not self.matches(record.tag):
            return record
        
        if self.filter_type == "grep":
            # Filter based on pattern
            pattern = self.config.get("regexp", "")
            key = self.config.get("key", "message")
            if key in record.record:
                if re.search(pattern, str(record.record[key])):
                    return record
            return None
        
        elif self.filter_type == "record_transformer":
            # Transform record
            new_record = record.record.copy()
            for key, value in self.config.get("add", {}).items():
                new_record[key] = value
            for key in self.config.get("remove", []):
                new_record.pop(key, None)
            record.record = new_record
            return record
        
        elif self.filter_type == "parser":
            # Parse log format
            parser = self.config.get("format", "json")
            key = self.config.get("key", "message")
            if parser == "json" and key in record.record:
                try:
                    parsed = json.loads(record.record[key])
                    record.record.update(parsed)
                except:
                    pass
            return record
        
        return record


class Output:
    """Output destination for logs"""
    
    def __init__(self, output_type: str, tag_pattern: str = "**", **config):
        self.output_type = output_type
        self.tag_pattern = tag_pattern
        self.config = config
        self.buffer: deque = deque(maxlen=config.get("buffer_size", 1000))
    
    def matches(self, tag: str) -> bool:
        """Check if tag matches output pattern"""
        if self.tag_pattern == "**":
            return True
        # Simple pattern matching: * matches any sequence within a segment, ** matches everything
        pattern = self.tag_pattern
        pattern = pattern.replace(".", r"\.")
        pattern = pattern.replace("**", "DOUBLESTAR")
        pattern = pattern.replace("*", "[^.]*")
        pattern = pattern.replace("DOUBLESTAR", ".*")
        try:
            return re.match(f"^{pattern}$", tag) is not None
        except:
            return False
    
    def write(self, record: LogRecord):
        """Write log record"""
        if not self.matches(record.tag):
            return
        
        if self.output_type == "stdout":
            print(f"[{record.time}] {record.tag}: {json.dumps(record.record)}")
        
        elif self.output_type == "file":
            # Simulate file writing
            self.buffer.append(record)
        
        elif self.output_type == "forward":
            # Simulate forwarding to another Fluentd
            self.buffer.append(record)
        
        elif self.output_type == "elasticsearch":
            # Simulate sending to Elasticsearch
            self.buffer.append(record)
        
        elif self.output_type == "kafka":
            # Simulate sending to Kafka
            self.buffer.append(record)
        
        else:
            # Default: buffer it
            self.buffer.append(record)
    
    def flush(self) -> List[LogRecord]:
        """Flush buffered records"""
        records = list(self.buffer)
        self.buffer.clear()
        return records


class AlertRoute:
    """Main Fluentd emulator class"""
    
    def __init__(self):
        self.sources: List[Source] = []
        self.filters: List[Filter] = []
        self.outputs: List[Output] = []
        self.running = False
    
    def add_source(self, source_type: str, tag: str, **config) -> Source:
        """Add input source"""
        source = Source(source_type, tag, **config)
        self.sources.append(source)
        return source
    
    def add_filter(self, filter_type: str, tag_pattern: str, **config) -> Filter:
        """Add filter"""
        filter_obj = Filter(filter_type, tag_pattern, **config)
        self.filters.append(filter_obj)
        return filter_obj
    
    def add_output(self, output_type: str, tag_pattern: str = "**", **config) -> Output:
        """Add output destination"""
        output = Output(output_type, tag_pattern, **config)
        self.outputs.append(output)
        return output
    
    def emit(self, tag: str, record: Dict[str, Any]):
        """Emit a log record"""
        log_record = LogRecord(tag=tag, time=datetime.now(), record=record)
        self.process(log_record)
    
    def process(self, record: LogRecord):
        """Process a log record through filters and outputs"""
        # Apply filters
        for filter_obj in self.filters:
            if record is None:
                break
            record = filter_obj.process(record)
        
        # Send to outputs
        if record is not None:
            for output in self.outputs:
                output.write(record)
    
    def start(self):
        """Start Fluentd"""
        self.running = True
        for source in self.sources:
            source.start()
    
    def stop(self):
        """Stop Fluentd"""
        self.running = False
        for source in self.sources:
            source.stop()
    
    def flush_all(self) -> Dict[str, List[LogRecord]]:
        """Flush all output buffers"""
        result = {}
        for i, output in enumerate(self.outputs):
            result[f"output_{i}_{output.output_type}"] = output.flush()
        return result


# Helper functions
def create_source(fluentd: AlertRoute, source_type: str, tag: str, **config) -> Source:
    """Helper to create a source"""
    return fluentd.add_source(source_type, tag, **config)


def create_filter(fluentd: AlertRoute, filter_type: str, tag_pattern: str, **config) -> Filter:
    """Helper to create a filter"""
    return fluentd.add_filter(filter_type, tag_pattern, **config)


def create_output(fluentd: AlertRoute, output_type: str, tag_pattern: str = "**", **config) -> Output:
    """Helper to create an output"""
    return fluentd.add_output(output_type, tag_pattern, **config)


if __name__ == "__main__":
    # Example usage
    fluentd = AlertRoute()
    
    # Add source
    fluentd.add_source("tail", "app.access", path="/var/log/app/access.log")
    
    # Add filter
    fluentd.add_filter("record_transformer", "app.*", add={"hostname": "server1"})
    
    # Add output
    fluentd.add_output("stdout", "app.**")
    
    # Start
    fluentd.start()
    
    # Emit logs
    fluentd.emit("app.access", {"method": "GET", "path": "/api", "status": 200})
    fluentd.emit("app.access", {"method": "POST", "path": "/users", "status": 201})
    
    # Stop
    fluentd.stop()
