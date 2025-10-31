#!/usr/bin/env python3
"""
Test suite for Fluentd Emulator

Tests core functionality including:
- Log collection
- Filtering
- Routing
- Output plugins
"""

import unittest
import json
from datetime import datetime
from AlertRoute import (
    AlertRoute, Source, Filter, Output, LogRecord,
    create_source, create_filter, create_output
)


class TestAlertRoute(unittest.TestCase):
    """Test Fluentd emulator basic functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.fluentd = AlertRoute()
    
    def test_create_source(self):
        """Test source creation"""
        source = self.fluentd.add_source("tail", "app.log", path="/var/log/app.log")
        
        self.assertEqual(source.source_type, "tail")
        self.assertEqual(source.tag, "app.log")
        self.assertEqual(source.config["path"], "/var/log/app.log")
    
    def test_add_filter(self):
        """Test filter creation"""
        filter_obj = self.fluentd.add_filter("grep", "app.*", regexp="ERROR")
        
        self.assertEqual(filter_obj.filter_type, "grep")
        self.assertEqual(filter_obj.tag_pattern, "app.*")
    
    def test_add_output(self):
        """Test output creation"""
        output = self.fluentd.add_output("stdout", "**")
        
        self.assertEqual(output.output_type, "stdout")
        self.assertEqual(output.tag_pattern, "**")
    
    def test_emit_log(self):
        """Test log emission"""
        output = self.fluentd.add_output("file", "**")
        
        self.fluentd.emit("app.access", {"method": "GET", "status": 200})
        
        buffered = output.flush()
        self.assertEqual(len(buffered), 1)
        self.assertEqual(buffered[0].tag, "app.access")
        self.assertEqual(buffered[0].record["method"], "GET")


class TestFilter(unittest.TestCase):
    """Test filter functionality"""
    
    def test_grep_filter(self):
        """Test grep filter"""
        filter_obj = Filter("grep", "app.*", regexp="ERROR", key="level")
        
        record1 = LogRecord("app.log", datetime.now(), {"level": "ERROR", "msg": "Test"})
        record2 = LogRecord("app.log", datetime.now(), {"level": "INFO", "msg": "Test"})
        
        result1 = filter_obj.process(record1)
        result2 = filter_obj.process(record2)
        
        self.assertIsNotNone(result1)
        self.assertIsNone(result2)
    
    def test_record_transformer(self):
        """Test record transformer"""
        filter_obj = Filter("record_transformer", "app.*", 
                           add={"env": "prod"}, remove=["temp"])
        
        record = LogRecord("app.log", datetime.now(), {"msg": "Test", "temp": "x"})
        result = filter_obj.process(record)
        
        self.assertEqual(result.record["env"], "prod")
        self.assertNotIn("temp", result.record)
    
    def test_tag_matching(self):
        """Test tag pattern matching"""
        filter_obj = Filter("grep", "app.*", regexp="test")
        
        self.assertTrue(filter_obj.matches("app.log"))
        self.assertTrue(filter_obj.matches("app.access"))
        self.assertFalse(filter_obj.matches("system.log"))


class TestOutput(unittest.TestCase):
    """Test output functionality"""
    
    def test_stdout_output(self):
        """Test stdout output"""
        output = Output("stdout", "**")
        record = LogRecord("app.log", datetime.now(), {"msg": "test"})
        
        # Should not raise exception
        output.write(record)
    
    def test_file_output(self):
        """Test file output buffering"""
        output = Output("file", "app.*", path="/tmp/logs.txt")
        
        record1 = LogRecord("app.log", datetime.now(), {"msg": "log1"})
        record2 = LogRecord("app.log", datetime.now(), {"msg": "log2"})
        
        output.write(record1)
        output.write(record2)
        
        buffered = output.flush()
        self.assertEqual(len(buffered), 2)
    
    def test_output_tag_matching(self):
        """Test output tag pattern matching"""
        output = Output("file", "app.access.*")
        
        self.assertTrue(output.matches("app.access.log"))
        self.assertTrue(output.matches("app.access.json"))
        self.assertFalse(output.matches("app.error.log"))


class TestEndToEnd(unittest.TestCase):
    """Test end-to-end scenarios"""
    
    def test_full_pipeline(self):
        """Test complete log pipeline"""
        fluentd = AlertRoute()
        
        # Add filter to add hostname
        fluentd.add_filter("record_transformer", "app.*", add={"host": "server1"})
        
        # Add output
        output = fluentd.add_output("file", "app.**")
        
        # Emit logs
        fluentd.emit("app.access", {"method": "GET"})
        fluentd.emit("app.error", {"error": "404"})
        
        # Check buffered logs
        buffered = output.flush()
        self.assertEqual(len(buffered), 2)
        self.assertEqual(buffered[0].record["host"], "server1")
        self.assertEqual(buffered[1].record["host"], "server1")
    
    def test_filtering_pipeline(self):
        """Test filtering unwanted logs"""
        fluentd = AlertRoute()
        
        # Filter only ERROR logs
        fluentd.add_filter("grep", "app.*", regexp="ERROR", key="level")
        
        # Add output
        output = fluentd.add_output("file", "**")
        
        # Emit logs
        fluentd.emit("app.log", {"level": "ERROR", "msg": "Error occurred"})
        fluentd.emit("app.log", {"level": "INFO", "msg": "Info message"})
        fluentd.emit("app.log", {"level": "ERROR", "msg": "Another error"})
        
        # Only ERROR logs should be buffered
        buffered = output.flush()
        self.assertEqual(len(buffered), 2)
    
    def test_multiple_outputs(self):
        """Test routing to multiple outputs"""
        fluentd = AlertRoute()
        
        # Two outputs with different patterns
        output1 = fluentd.add_output("file", "app.access.*")
        output2 = fluentd.add_output("file", "app.error.*")
        
        # Emit logs
        fluentd.emit("app.access.log", {"msg": "access"})
        fluentd.emit("app.error.log", {"msg": "error"})
        
        # Check each output
        buffered1 = output1.flush()
        buffered2 = output2.flush()
        
        self.assertEqual(len(buffered1), 1)
        self.assertEqual(len(buffered2), 1)


if __name__ == "__main__":
    unittest.main()
