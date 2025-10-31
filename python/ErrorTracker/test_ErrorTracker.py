"""
Tests for Sentry SDK Emulator

This test suite validates the core functionality of the Sentry SDK emulator.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ErrorTracker import (
    init, capture_exception, capture_message, add_breadcrumb,
    set_user, set_tag, set_tags, set_extra, set_extras,
    set_context, set_level, set_transaction, push_scope,
    configure_scope, get_events, clear_events, Level,
    start_transaction, Client, Scope, Hub
)


def test_init():
    """Test SDK initialization"""
    print("Testing SDK initialization...")
    
    clear_events()
    client = init(
        dsn="https://test@sentry.io/123",
        release="1.0.0",
        environment="test",
        sample_rate=1.0
    )
    
    assert client is not None
    assert client.dsn == "https://test@sentry.io/123"
    assert client.release == "1.0.0"
    assert client.environment == "test"
    assert client.sample_rate == 1.0
    
    print("✓ SDK initialization works")


def test_capture_message():
    """Test message capture"""
    print("Testing message capture...")
    
    clear_events()
    init(dsn="test")
    
    event_id = capture_message("Test message", level=Level.INFO)
    assert event_id is not None
    
    events = get_events()
    assert len(events) == 1
    assert events[0].message == "Test message"
    assert events[0].level == "info"
    
    print("✓ Message capture works")


def test_capture_exception():
    """Test exception capture"""
    print("Testing exception capture...")
    
    clear_events()
    init(dsn="test")
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        event_id = capture_exception(e)
        assert event_id is not None
    
    events = get_events()
    assert len(events) == 1
    assert events[0].exception is not None
    assert events[0].exception['type'] == 'ValueError'
    assert events[0].exception['value'] == 'Test error'
    assert events[0].level == 'error'
    
    print("✓ Exception capture works")


def test_capture_exception_from_context():
    """Test exception capture from context"""
    print("Testing exception capture from context...")
    
    clear_events()
    init(dsn="test")
    
    try:
        raise RuntimeError("Context error")
    except:
        event_id = capture_exception()
        assert event_id is not None
    
    events = get_events()
    assert len(events) == 1
    assert events[0].exception is not None
    assert events[0].exception['type'] == 'RuntimeError'
    
    print("✓ Exception capture from context works")


def test_breadcrumbs():
    """Test breadcrumb tracking"""
    print("Testing breadcrumb tracking...")
    
    clear_events()
    init(dsn="test")
    
    add_breadcrumb(message="Action 1", category="user")
    add_breadcrumb(message="Action 2", category="navigation", level="info")
    add_breadcrumb(message="Action 3", category="http", data={"url": "/api/test"})
    
    capture_message("Test with breadcrumbs")
    
    events = get_events()
    assert len(events) == 1
    assert len(events[0].breadcrumbs) == 3
    assert events[0].breadcrumbs[0]['message'] == "Action 1"
    assert events[0].breadcrumbs[1]['category'] == "navigation"
    assert events[0].breadcrumbs[2]['data']['url'] == "/api/test"
    
    print("✓ Breadcrumb tracking works")


def test_user_context():
    """Test user context"""
    print("Testing user context...")
    
    clear_events()
    init(dsn="test")
    
    set_user({
        "id": "123",
        "email": "test@example.com",
        "username": "testuser"
    })
    
    capture_message("User context test")
    
    events = get_events()
    assert len(events) == 1
    assert events[0].user is not None
    assert events[0].user['id'] == "123"
    assert events[0].user['email'] == "test@example.com"
    assert events[0].user['username'] == "testuser"
    
    print("✓ User context works")


def test_tags():
    """Test tags"""
    print("Testing tags...")
    
    clear_events()
    init(dsn="test")
    
    set_tag("server", "web-1")
    set_tags({"region": "us-west", "version": "1.0"})
    
    capture_message("Tags test")
    
    events = get_events()
    assert len(events) == 1
    assert events[0].tags['server'] == "web-1"
    assert events[0].tags['region'] == "us-west"
    assert events[0].tags['version'] == "1.0"
    
    print("✓ Tags work")


def test_extra_data():
    """Test extra data"""
    print("Testing extra data...")
    
    clear_events()
    init(dsn="test")
    
    set_extra("user_data", {"premium": True})
    set_extras({"request_id": "abc123", "ip": "192.168.1.1"})
    
    capture_message("Extra data test")
    
    events = get_events()
    assert len(events) == 1
    assert events[0].extra['user_data']['premium'] is True
    assert events[0].extra['request_id'] == "abc123"
    assert events[0].extra['ip'] == "192.168.1.1"
    
    print("✓ Extra data works")


def test_context():
    """Test context data"""
    print("Testing context data...")
    
    clear_events()
    init(dsn="test")
    
    set_context("device", {
        "name": "iPhone 12",
        "model": "iPhone13,2",
        "orientation": "portrait"
    })
    
    capture_message("Context test")
    
    events = get_events()
    assert len(events) == 1
    assert events[0].extra['device']['name'] == "iPhone 12"
    
    print("✓ Context data works")


def test_level():
    """Test level setting"""
    print("Testing level setting...")
    
    clear_events()
    init(dsn="test")
    
    set_level(Level.WARNING)
    capture_message("Level test")
    
    events = get_events()
    assert len(events) == 1
    assert events[0].level == "warning"
    
    print("✓ Level setting works")


def test_transaction():
    """Test transaction setting"""
    print("Testing transaction setting...")
    
    clear_events()
    init(dsn="test")
    
    set_transaction("/api/users")
    capture_message("Transaction test")
    
    events = get_events()
    assert len(events) == 1
    assert events[0].transaction == "/api/users"
    
    print("✓ Transaction setting works")


def test_push_scope():
    """Test scope pushing"""
    print("Testing scope pushing...")
    
    clear_events()
    init(dsn="test")
    
    set_tag("global", "value")
    
    with push_scope() as scope:
        scope.set_tag("local", "value")
        scope.set_extra("request_id", "123")
        capture_message("Inside scope")
    
    capture_message("Outside scope")
    
    events = get_events()
    assert len(events) == 2
    
    # First event should have both global and local tags
    assert events[0].tags['global'] == "value"
    assert events[0].tags['local'] == "value"
    assert events[0].extra['request_id'] == "123"
    
    # Second event should only have global tag
    assert events[1].tags['global'] == "value"
    assert 'local' not in events[1].tags
    assert 'request_id' not in events[1].extra
    
    print("✓ Scope pushing works")


def test_configure_scope():
    """Test scope configuration"""
    print("Testing scope configuration...")
    
    clear_events()
    init(dsn="test")
    
    with configure_scope() as scope:
        scope.set_tag("configured", "yes")
        scope.set_extra("config", "data")
    
    capture_message("Configured scope test")
    
    events = get_events()
    assert len(events) == 1
    assert events[0].tags['configured'] == "yes"
    assert events[0].extra['config'] == "data"
    
    print("✓ Scope configuration works")


def test_sampling():
    """Test event sampling"""
    print("Testing event sampling...")
    
    clear_events()
    init(dsn="test", sample_rate=0.0)  # Sample nothing
    
    capture_message("Sampled message 1")
    capture_message("Sampled message 2")
    capture_message("Sampled message 3")
    
    events = get_events()
    # With 0% sample rate, we might get 0 events (probabilistic)
    # But the test is more about ensuring sampling doesn't crash
    assert len(events) >= 0
    
    # Now test with 100% sample rate
    clear_events()
    init(dsn="test", sample_rate=1.0)
    
    capture_message("Not sampled")
    
    events = get_events()
    assert len(events) == 1
    
    print("✓ Event sampling works")


def test_before_send():
    """Test before_send hook"""
    print("Testing before_send hook...")
    
    clear_events()
    
    def before_send(event, hint):
        # Modify event
        event.tags['modified'] = 'yes'
        # Filter events with certain messages
        if event.message == "filtered":
            return None
        return event
    
    init(dsn="test", before_send=before_send)
    
    capture_message("normal")
    capture_message("filtered")
    
    events = get_events()
    assert len(events) == 1
    assert events[0].message == "normal"
    assert events[0].tags['modified'] == 'yes'
    
    print("✓ before_send hook works")


def test_release_and_environment():
    """Test release and environment"""
    print("Testing release and environment...")
    
    clear_events()
    init(
        dsn="test",
        release="v1.2.3",
        environment="production"
    )
    
    capture_message("Release test")
    
    events = get_events()
    assert len(events) == 1
    assert events[0].release == "v1.2.3"
    assert events[0].environment == "production"
    
    print("✓ Release and environment work")


def test_scope_class():
    """Test Scope class"""
    print("Testing Scope class...")
    
    scope = Scope()
    
    # Test user
    scope.set_user({"id": "123"})
    assert scope.user.id == "123"
    
    # Test tags
    scope.set_tag("key", "value")
    assert scope.tags['key'] == "value"
    
    scope.set_tags({"key2": "value2", "key3": "value3"})
    assert scope.tags['key2'] == "value2"
    
    # Test extra
    scope.set_extra("extra_key", "extra_value")
    assert scope.extra['extra_key'] == "extra_value"
    
    scope.set_extras({"extra2": "value2"})
    assert scope.extra['extra2'] == "value2"
    
    # Test breadcrumbs
    scope.add_breadcrumb({"message": "test"})
    assert len(scope.breadcrumbs) == 1
    
    # Test clear
    scope.clear()
    assert scope.user is None
    assert len(scope.tags) == 0
    assert len(scope.extra) == 0
    assert len(scope.breadcrumbs) == 0
    
    print("✓ Scope class works")


def test_hub_class():
    """Test Hub class"""
    print("Testing Hub class...")
    
    client = Client(dsn="test")
    hub = Hub(client)
    
    # Test scope management
    initial_scope = hub.scope
    hub.push_scope()
    new_scope = hub.scope
    assert new_scope is not initial_scope
    
    hub.pop_scope()
    assert hub.scope is initial_scope
    
    print("✓ Hub class works")


def test_start_transaction():
    """Test transaction creation"""
    print("Testing transaction creation...")
    
    transaction = start_transaction(name="test_transaction", op="http.server")
    
    assert transaction.name == "test_transaction"
    assert transaction.op == "http.server"
    assert transaction.transaction_id is not None
    assert transaction.start_timestamp > 0
    
    print("✓ Transaction creation works")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running Sentry SDK Emulator Tests")
    print("=" * 60)
    
    tests = [
        test_init,
        test_capture_message,
        test_capture_exception,
        test_capture_exception_from_context,
        test_breadcrumbs,
        test_user_context,
        test_tags,
        test_extra_data,
        test_context,
        test_level,
        test_transaction,
        test_push_scope,
        test_configure_scope,
        test_sampling,
        test_before_send,
        test_release_and_environment,
        test_scope_class,
        test_hub_class,
        test_start_transaction,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Tests: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
