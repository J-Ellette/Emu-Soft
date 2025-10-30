"""
Test suite for structlog emulator

Tests structured logging functionality including:
- Logger creation and configuration
- Context binding and unbinding
- Log levels
- Processors and renderers
- Output formats (JSON, key-value, console)
"""

import io
import json
import os
import sys
import unittest
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from structlog_emulator_tool.structlog_emulator import (
    BoundLogger, get_logger, configure,
    add_timestamp, add_log_level, filter_by_level,
    JSONRenderer, KeyValueRenderer, ConsoleRenderer,
    PrintLogger, create_console_logger, create_json_logger,
    threadlocal_context, clear_threadlocal_context,
    merge_threadlocal_context, unbind_threadlocal_context
)


class TestBoundLogger(unittest.TestCase):
    """Test BoundLogger class"""
    
    def test_logger_creation(self):
        """Test creating a bound logger"""
        log = BoundLogger("test", {"key": "value"})
        self.assertEqual(log._logger_name, "test")
        self.assertEqual(log._context, {"key": "value"})
    
    def test_bind(self):
        """Test binding context to logger"""
        log = BoundLogger("test")
        log2 = log.bind(user_id=123, request_id="abc")
        
        # Original logger unchanged
        self.assertEqual(log._context, {})
        
        # New logger has bound values
        self.assertEqual(log2._context, {"user_id": 123, "request_id": "abc"})
    
    def test_bind_multiple(self):
        """Test binding multiple times"""
        log = BoundLogger("test")
        log2 = log.bind(user_id=123)
        log3 = log2.bind(request_id="abc")
        
        self.assertEqual(log3._context, {"user_id": 123, "request_id": "abc"})
    
    def test_unbind(self):
        """Test unbinding context from logger"""
        log = BoundLogger("test", {"user_id": 123, "request_id": "abc"})
        log2 = log.unbind("request_id")
        
        self.assertEqual(log2._context, {"user_id": 123})
    
    def test_unbind_multiple(self):
        """Test unbinding multiple keys"""
        log = BoundLogger("test", {"a": 1, "b": 2, "c": 3})
        log2 = log.unbind("a", "c")
        
        self.assertEqual(log2._context, {"b": 2})
    
    def test_new(self):
        """Test creating logger with new context"""
        log = BoundLogger("test", {"old": "value"})
        log2 = log.new(new="data")
        
        self.assertEqual(log2._context, {"new": "data"})
    
    def test_log_levels(self):
        """Test different log levels"""
        log = BoundLogger("test")
        
        # Test each level returns event dict
        result = log.debug("debug message")
        self.assertEqual(result['event'], "debug message")
        self.assertEqual(result['level'], "debug")
        
        result = log.info("info message")
        self.assertEqual(result['level'], "info")
        
        result = log.warning("warning message")
        self.assertEqual(result['level'], "warning")
        
        result = log.error("error message")
        self.assertEqual(result['level'], "error")
        
        result = log.critical("critical message")
        self.assertEqual(result['level'], "critical")
    
    def test_log_with_extra_data(self):
        """Test logging with extra key-value data"""
        log = BoundLogger("test")
        result = log.info("user login", user_id=456, username="john")
        
        self.assertEqual(result['event'], "user login")
        self.assertEqual(result['user_id'], 456)
        self.assertEqual(result['username'], "john")
    
    def test_warn_alias(self):
        """Test that warn is an alias for warning"""
        log = BoundLogger("test")
        result = log.warn("warning message")
        self.assertEqual(result['level'], "warning")


class TestProcessors(unittest.TestCase):
    """Test processor functions"""
    
    def test_add_timestamp(self):
        """Test timestamp processor"""
        event_dict = {"event": "test"}
        result = add_timestamp(event_dict)
        
        self.assertIn('timestamp', result)
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
    
    def test_add_log_level(self):
        """Test log level processor"""
        event_dict = {"event": "test"}
        result = add_log_level(event_dict)
        
        self.assertEqual(result['level'], 'info')
    
    def test_filter_by_level_debug(self):
        """Test level filtering with debug"""
        processor = filter_by_level('debug')
        
        # All levels should pass
        self.assertIsNotNone(processor({"level": "debug"}))
        self.assertIsNotNone(processor({"level": "info"}))
        self.assertIsNotNone(processor({"level": "error"}))
    
    def test_filter_by_level_warning(self):
        """Test level filtering with warning"""
        processor = filter_by_level('warning')
        
        # Debug and info should be filtered
        self.assertIsNone(processor({"level": "debug"}))
        self.assertIsNone(processor({"level": "info"}))
        
        # Warning and above should pass
        self.assertIsNotNone(processor({"level": "warning"}))
        self.assertIsNotNone(processor({"level": "error"}))
        self.assertIsNotNone(processor({"level": "critical"}))
    
    def test_filter_by_level_error(self):
        """Test level filtering with error"""
        processor = filter_by_level('error')
        
        self.assertIsNone(processor({"level": "info"}))
        self.assertIsNone(processor({"level": "warning"}))
        self.assertIsNotNone(processor({"level": "error"}))
        self.assertIsNotNone(processor({"level": "critical"}))


class TestRenderers(unittest.TestCase):
    """Test renderer classes"""
    
    def test_json_renderer(self):
        """Test JSON renderer"""
        renderer = JSONRenderer()
        event_dict = {
            "event": "test event",
            "level": "info",
            "user_id": 123
        }
        
        result = renderer(event_dict)
        
        # Should be valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed['event'], "test event")
        self.assertEqual(parsed['level'], "info")
        self.assertEqual(parsed['user_id'], 123)
    
    def test_json_renderer_sorted(self):
        """Test JSON renderer with sorted keys"""
        renderer = JSONRenderer(sort_keys=True)
        event_dict = {"z": 1, "a": 2, "m": 3}
        
        result = renderer(event_dict)
        
        # Keys should be sorted
        self.assertTrue(result.index('"a"') < result.index('"m"'))
        self.assertTrue(result.index('"m"') < result.index('"z"'))
    
    def test_keyvalue_renderer(self):
        """Test key-value renderer"""
        renderer = KeyValueRenderer()
        event_dict = {
            "event": "test",
            "level": "info",
            "count": 42
        }
        
        result = renderer(event_dict)
        
        # Should contain key=value pairs
        self.assertIn("event=test", result)
        self.assertIn("level=info", result)
        self.assertIn("count=42", result)
    
    def test_keyvalue_renderer_with_spaces(self):
        """Test key-value renderer with spaces in values"""
        renderer = KeyValueRenderer()
        event_dict = {"message": "hello world"}
        
        result = renderer(event_dict)
        
        # Values with spaces should be quoted
        self.assertIn('message="hello world"', result)
    
    def test_keyvalue_renderer_key_order(self):
        """Test key-value renderer with custom key order"""
        renderer = KeyValueRenderer(key_order=["level", "event"])
        event_dict = {"event": "test", "level": "info", "other": "data"}
        
        result = renderer(event_dict)
        
        # Ordered keys should come first
        level_pos = result.index("level=")
        event_pos = result.index("event=")
        other_pos = result.index("other=")
        
        self.assertTrue(level_pos < event_pos < other_pos)
    
    def test_console_renderer(self):
        """Test console renderer"""
        renderer = ConsoleRenderer(colors=False)
        event_dict = {
            "event": "test event",
            "level": "info",
            "timestamp": "2024-01-01T12:00:00"
        }
        
        result = renderer(event_dict)
        
        # Should contain formatted output
        self.assertIn("INFO", result)
        self.assertIn("test event", result)
        self.assertIn("2024-01-01", result)
    
    def test_console_renderer_different_levels(self):
        """Test console renderer with different levels"""
        renderer = ConsoleRenderer(colors=False)
        
        for level in ['debug', 'info', 'warning', 'error', 'critical']:
            event_dict = {"event": "test", "level": level}
            result = renderer(event_dict)
            self.assertIn(level.upper(), result)


class TestConfiguration(unittest.TestCase):
    """Test logger configuration"""
    
    def test_configure_processors(self):
        """Test configuring processors"""
        custom_processors = [add_timestamp, add_log_level]
        configure(processors=custom_processors)
        
        log = get_logger()
        self.assertEqual(log._processors, custom_processors)
    
    def test_get_logger_with_name(self):
        """Test getting logger with specific name"""
        log = get_logger("myapp")
        self.assertEqual(log._logger_name, "myapp")
    
    def test_get_logger_with_initial_values(self):
        """Test getting logger with initial context"""
        log = get_logger("test", app_version="1.0.0", env="prod")
        
        self.assertEqual(log._context['app_version'], "1.0.0")
        self.assertEqual(log._context['env'], "prod")


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    def test_create_console_logger(self):
        """Test creating console logger"""
        log = create_console_logger(level='info')
        
        self.assertIsInstance(log, BoundLogger)
        # Should have processors configured
        self.assertTrue(len(log._processors) > 0)
    
    def test_create_json_logger(self):
        """Test creating JSON logger"""
        output = io.StringIO()
        log = create_json_logger(file=output, level='info')
        
        self.assertIsInstance(log, BoundLogger)
    
    def test_json_logger_output(self):
        """Test JSON logger produces valid JSON output"""
        output = io.StringIO()
        
        # Configure with JSON output
        processors = [
            add_timestamp,
            add_log_level,
            JSONRenderer(),
            PrintLogger(file=output),
        ]
        configure(processors=processors)
        
        log = get_logger()
        log.info("test message", key="value")
        
        # Get output
        output.seek(0)
        result = output.read().strip()
        
        # Should be valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed['event'], "test message")
        self.assertEqual(parsed['key'], "value")


class TestThreadLocalContext(unittest.TestCase):
    """Test thread-local context management"""
    
    def setUp(self):
        """Clear context before each test"""
        clear_threadlocal_context()
    
    def tearDown(self):
        """Clear context after each test"""
        clear_threadlocal_context()
    
    def test_threadlocal_context_manager(self):
        """Test thread-local context manager"""
        with threadlocal_context(request_id="123", user_id=456):
            # Context should be available here
            from structlog_emulator_tool.structlog_emulator import _get_context
            context = _get_context()
            self.assertEqual(context['request_id'], "123")
            self.assertEqual(context['user_id'], 456)
        
        # Context should be cleared after
        context = _get_context()
        self.assertEqual(context, {})
    
    def test_merge_threadlocal_context(self):
        """Test merging into thread-local context"""
        merge_threadlocal_context(key1="value1")
        merge_threadlocal_context(key2="value2")
        
        from structlog_emulator_tool.structlog_emulator import _get_context
        context = _get_context()
        
        self.assertEqual(context['key1'], "value1")
        self.assertEqual(context['key2'], "value2")
    
    def test_unbind_threadlocal_context(self):
        """Test unbinding from thread-local context"""
        merge_threadlocal_context(key1="value1", key2="value2", key3="value3")
        unbind_threadlocal_context("key2")
        
        from structlog_emulator_tool.structlog_emulator import _get_context
        context = _get_context()
        
        self.assertIn('key1', context)
        self.assertNotIn('key2', context)
        self.assertIn('key3', context)
    
    def test_clear_threadlocal_context(self):
        """Test clearing thread-local context"""
        merge_threadlocal_context(key1="value1", key2="value2")
        
        from structlog_emulator_tool.structlog_emulator import _get_context
        context = _get_context()
        self.assertEqual(len(context), 2)
        
        clear_threadlocal_context()
        context = _get_context()
        self.assertEqual(context, {})


class TestProcessorPipeline(unittest.TestCase):
    """Test processor pipeline functionality"""
    
    def test_processor_chain(self):
        """Test that processors are called in order"""
        results = []
        
        def processor1(event_dict):
            results.append(1)
            event_dict['proc1'] = True
            return event_dict
        
        def processor2(event_dict):
            results.append(2)
            event_dict['proc2'] = True
            return event_dict
        
        log = BoundLogger("test", processors=[processor1, processor2])
        result = log.info("test")
        
        # Processors should be called in order
        self.assertEqual(results, [1, 2])
        self.assertTrue(result['proc1'])
        self.assertTrue(result['proc2'])
    
    def test_processor_can_filter(self):
        """Test that processors can filter events by returning None"""
        def filter_processor(event_dict):
            if event_dict.get('level') == 'debug':
                return None
            return event_dict
        
        log = BoundLogger("test", processors=[filter_processor])
        
        # Debug should be filtered
        result = log.debug("debug message")
        self.assertIsNone(result)
        
        # Info should pass
        result = log.info("info message")
        self.assertIsNotNone(result)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestBoundLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessors))
    suite.addTests(loader.loadTestsFromTestCase(TestRenderers))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestThreadLocalContext))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessorPipeline))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
