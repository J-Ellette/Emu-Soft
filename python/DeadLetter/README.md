# DeadLetter - Dead Letter Queue Analyzer

Analyzes and manages dead letter queue messages.

## Features

- Message tracking with failure counts
- Failure pattern analysis
- Queue-specific failure analysis
- Retry management

## Usage

```python
from DeadLetter import DeadLetter, FailureReason

dlq = DeadLetter()

# Add failed message
dlq.add_message(
    'msg123',
    'orders-queue',
    {'order_id': 456},
    FailureReason.TIMEOUT,
    error_details='Connection timeout after 30s'
)

# Analyze failures
analysis = dlq.get_failure_analysis()
print(f"Total messages: {analysis['total_messages']}")
print(f"By reason: {analysis['failure_reasons']}")

# Retry message
dlq.retry_message('msg123')
```

## API Reference

- `add_message(message_id, queue, body, reason, details)` - Add message
- `get_message(message_id)` - Get message
- `list_messages(queue, reason)` - List messages
- `retry_message(message_id)` - Retry message
- `get_failure_analysis()` - Analyze failures
- `get_statistics()` - Get statistics

## Testing

```bash
python test_DeadLetter.py
```

## License

Part of the Emu-Soft project.
