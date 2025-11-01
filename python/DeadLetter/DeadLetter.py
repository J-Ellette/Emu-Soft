"""
DeadLetter - Dead Letter Queue Analyzer

Analyzes and manages dead letter queue messages, providing insights
into failures and retry strategies.
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict


class FailureReason(Enum):
    """Common failure reasons"""
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class DeadLetterMessage:
    """Represents a message in dead letter queue"""
    id: str
    original_queue: str
    message_body: Any
    failure_reason: FailureReason
    failure_count: int
    first_failed_at: str
    last_failed_at: str
    error_details: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeadLetter:
    """Dead Letter Queue Analyzer"""
    
    def __init__(self):
        """Initialize analyzer"""
        self.messages: Dict[str, DeadLetterMessage] = {}
        self.failure_patterns: Dict[str, int] = defaultdict(int)
        self.queue_failures: Dict[str, int] = defaultdict(int)
    
    def add_message(
        self,
        message_id: str,
        original_queue: str,
        message_body: Any,
        failure_reason: FailureReason,
        error_details: Optional[str] = None
    ) -> None:
        """Add a message to dead letter queue"""
        now = datetime.utcnow().isoformat()
        
        if message_id in self.messages:
            # Update existing message
            msg = self.messages[message_id]
            msg.failure_count += 1
            msg.last_failed_at = now
            msg.failure_reason = failure_reason
            msg.error_details = error_details
        else:
            # New message
            msg = DeadLetterMessage(
                id=message_id,
                original_queue=original_queue,
                message_body=message_body,
                failure_reason=failure_reason,
                failure_count=1,
                first_failed_at=now,
                last_failed_at=now,
                error_details=error_details
            )
            self.messages[message_id] = msg
        
        # Track patterns
        self.failure_patterns[failure_reason.value] += 1
        self.queue_failures[original_queue] += 1
    
    def get_message(self, message_id: str) -> Optional[DeadLetterMessage]:
        """Get a specific message"""
        return self.messages.get(message_id)
    
    def list_messages(
        self,
        queue: Optional[str] = None,
        reason: Optional[FailureReason] = None
    ) -> List[DeadLetterMessage]:
        """List messages with optional filters"""
        result = list(self.messages.values())
        
        if queue:
            result = [m for m in result if m.original_queue == queue]
        
        if reason:
            result = [m for m in result if m.failure_reason == reason]
        
        return result
    
    def retry_message(self, message_id: str) -> bool:
        """Mark message for retry"""
        if message_id in self.messages:
            del self.messages[message_id]
            return True
        return False
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a message from DLQ"""
        if message_id in self.messages:
            del self.messages[message_id]
            return True
        return False
    
    def get_failure_analysis(self) -> Dict[str, Any]:
        """Analyze failure patterns"""
        total_messages = len(self.messages)
        
        # Most common failure reasons
        sorted_reasons = sorted(
            self.failure_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Queues with most failures
        sorted_queues = sorted(
            self.queue_failures.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Messages by failure count
        high_retry_messages = [
            m for m in self.messages.values()
            if m.failure_count > 3
        ]
        
        return {
            'total_messages': total_messages,
            'failure_reasons': dict(sorted_reasons),
            'queues_with_failures': dict(sorted_queues[:10]),
            'high_retry_count': len(high_retry_messages),
            'messages_by_reason': {
                reason.value: len([m for m in self.messages.values() if m.failure_reason == reason])
                for reason in FailureReason
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get DLQ statistics"""
        return {
            'total_messages': len(self.messages),
            'unique_queues': len(self.queue_failures),
            'failure_types': len(self.failure_patterns),
            'avg_retries': sum(m.failure_count for m in self.messages.values()) / len(self.messages) if self.messages else 0
        }
    
    def clear(self) -> None:
        """Clear all messages"""
        self.messages.clear()
        self.failure_patterns.clear()
        self.queue_failures.clear()
