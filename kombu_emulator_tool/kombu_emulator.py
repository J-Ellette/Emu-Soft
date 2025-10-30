"""
Kombu Emulator - Messaging library for Python.

Kombu is a messaging library for Python that provides a simple, uniform API
for interacting with message brokers (RabbitMQ, Redis, Amazon SQS, etc.).
It's used by Celery as the messaging backbone.

This emulator provides Kombu's core functionality without external broker dependencies.
"""

import uuid
import time
import json
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime
from threading import Thread, Lock, Event
from queue import Queue as ThreadQueue, Empty
from enum import Enum


class ExchangeType(Enum):
    """Exchange types for message routing."""
    DIRECT = "direct"
    TOPIC = "topic"
    FANOUT = "fanout"
    HEADERS = "headers"


class Message:
    """
    Represents a message in the queue.
    """

    def __init__(
        self,
        body: Any,
        content_type: str = "application/json",
        content_encoding: str = "utf-8",
        headers: Optional[Dict[str, Any]] = None,
        properties: Optional[Dict[str, Any]] = None,
        delivery_info: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a message.

        Args:
            body: Message body (will be serialized)
            content_type: Content type
            content_encoding: Content encoding
            headers: Message headers
            properties: Message properties
            delivery_info: Delivery information
        """
        self.body = body
        self.content_type = content_type
        self.content_encoding = content_encoding
        self.headers = headers or {}
        self.properties = properties or {}
        self.delivery_info = delivery_info or {}
        self.channel = None
        self.delivery_tag = None

    def ack(self):
        """Acknowledge the message."""
        if self.channel and self.delivery_tag:
            self.channel.basic_ack(self.delivery_tag)

    def reject(self, requeue: bool = True):
        """
        Reject the message.

        Args:
            requeue: Whether to requeue the message
        """
        if self.channel and self.delivery_tag:
            self.channel.basic_reject(self.delivery_tag, requeue)

    def requeue(self):
        """Requeue the message."""
        self.reject(requeue=True)


class Exchange:
    """
    Represents a message exchange.
    """

    def __init__(
        self,
        name: str = "",
        type: str = "direct",
        durable: bool = True,
        auto_delete: bool = False,
        channel=None,
    ):
        """
        Initialize an exchange.

        Args:
            name: Exchange name
            type: Exchange type (direct, topic, fanout, headers)
            durable: Whether exchange survives broker restart
            auto_delete: Whether exchange is deleted when not in use
            channel: Channel for operations
        """
        self.name = name
        self.type = type
        self.durable = durable
        self.auto_delete = auto_delete
        self.channel = channel
        self._bindings: Dict[str, List[str]] = {}  # routing_key -> [queue_names]

    def bind_to(self, queue_name: str, routing_key: str = ""):
        """
        Bind a queue to this exchange.

        Args:
            queue_name: Name of the queue to bind
            routing_key: Routing key for binding
        """
        if routing_key not in self._bindings:
            self._bindings[routing_key] = []
        if queue_name not in self._bindings[routing_key]:
            self._bindings[routing_key].append(queue_name)

    def get_bound_queues(self, routing_key: str) -> List[str]:
        """
        Get queues bound to a routing key.

        Args:
            routing_key: Routing key

        Returns:
            List of queue names
        """
        if self.type == ExchangeType.FANOUT.value:
            # Fanout sends to all bound queues regardless of routing key
            all_queues = []
            for queues in self._bindings.values():
                all_queues.extend(queues)
            return list(set(all_queues))
        elif self.type == ExchangeType.TOPIC.value:
            # Topic matching (simplified - just exact match for now)
            return self._bindings.get(routing_key, [])
        else:  # direct
            return self._bindings.get(routing_key, [])


class Queue:
    """
    Represents a message queue.
    """

    def __init__(
        self,
        name: str = "",
        exchange: Optional[Exchange] = None,
        routing_key: str = "",
        durable: bool = True,
        exclusive: bool = False,
        auto_delete: bool = False,
        channel=None,
    ):
        """
        Initialize a queue.

        Args:
            name: Queue name
            exchange: Exchange to bind to
            routing_key: Routing key for binding
            durable: Whether queue survives broker restart
            exclusive: Whether queue is exclusive to one connection
            auto_delete: Whether queue is deleted when not in use
            channel: Channel for operations
        """
        self.name = name or f"queue-{uuid.uuid4()}"
        self.exchange = exchange
        self.routing_key = routing_key
        self.durable = durable
        self.exclusive = exclusive
        self.auto_delete = auto_delete
        self.channel = channel
        self._messages: ThreadQueue = ThreadQueue()

    def put(self, message: Message):
        """
        Put a message in the queue.

        Args:
            message: Message to add
        """
        self._messages.put(message)

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Message]:
        """
        Get a message from the queue.

        Args:
            block: Whether to block waiting for a message
            timeout: Timeout for blocking

        Returns:
            Message or None
        """
        try:
            return self._messages.get(block=block, timeout=timeout)
        except Empty:
            return None

    def qsize(self) -> int:
        """Get the queue size."""
        return self._messages.qsize()

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._messages.empty()


class Connection:
    """
    Represents a connection to a message broker.
    """

    def __init__(
        self,
        hostname: str = "localhost",
        port: int = 5672,
        userid: str = "guest",
        password: str = "guest",
        virtual_host: str = "/",
        transport: Optional[str] = None,
    ):
        """
        Initialize a connection.

        Args:
            hostname: Broker hostname
            port: Broker port
            userid: User ID
            password: Password
            virtual_host: Virtual host
            transport: Transport type
        """
        self.hostname = hostname
        self.port = port
        self.userid = userid
        self.password = password
        self.virtual_host = virtual_host
        self.transport = transport
        self._connected = False
        self._channels: List['Channel'] = []

    def connect(self):
        """Establish connection to broker."""
        self._connected = True

    def disconnect(self):
        """Disconnect from broker."""
        self._connected = False
        for channel in self._channels:
            channel.close()

    def channel(self) -> 'Channel':
        """
        Create a new channel.

        Returns:
            Channel instance
        """
        channel = Channel(self)
        self._channels.append(channel)
        return channel

    def release(self):
        """Release connection resources."""
        self.disconnect()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class Channel:
    """
    Represents a communication channel.
    """

    def __init__(self, connection: Connection):
        """
        Initialize a channel.

        Args:
            connection: Parent connection
        """
        self.connection = connection
        self._exchanges: Dict[str, Exchange] = {}
        self._queues: Dict[str, Queue] = {}
        self._closed = False
        self._delivery_tag_counter = 0
        self._lock = Lock()

    def exchange_declare(
        self,
        exchange: str,
        type: str = "direct",
        durable: bool = True,
        auto_delete: bool = False,
    ) -> Exchange:
        """
        Declare an exchange.

        Args:
            exchange: Exchange name
            type: Exchange type
            durable: Durability
            auto_delete: Auto-delete

        Returns:
            Exchange instance
        """
        if exchange not in self._exchanges:
            self._exchanges[exchange] = Exchange(
                name=exchange,
                type=type,
                durable=durable,
                auto_delete=auto_delete,
                channel=self,
            )
        return self._exchanges[exchange]

    def queue_declare(
        self,
        queue: str = "",
        durable: bool = True,
        exclusive: bool = False,
        auto_delete: bool = False,
    ) -> Queue:
        """
        Declare a queue.

        Args:
            queue: Queue name
            durable: Durability
            exclusive: Exclusive to connection
            auto_delete: Auto-delete

        Returns:
            Queue instance
        """
        if not queue:
            queue = f"queue-{uuid.uuid4()}"

        if queue not in self._queues:
            self._queues[queue] = Queue(
                name=queue,
                durable=durable,
                exclusive=exclusive,
                auto_delete=auto_delete,
                channel=self,
            )
        return self._queues[queue]

    def queue_bind(
        self,
        queue: str,
        exchange: str = "",
        routing_key: str = "",
    ):
        """
        Bind a queue to an exchange.

        Args:
            queue: Queue name
            exchange: Exchange name
            routing_key: Routing key
        """
        if exchange in self._exchanges:
            exch = self._exchanges[exchange]
            exch.bind_to(queue, routing_key)

    def basic_publish(
        self,
        message: Union[Message, Any],
        exchange: str = "",
        routing_key: str = "",
        mandatory: bool = False,
        immediate: bool = False,
    ):
        """
        Publish a message.

        Args:
            message: Message to publish
            exchange: Exchange name
            routing_key: Routing key
            mandatory: Message must be routable
            immediate: Message must be immediately consumable
        """
        # Convert to Message if needed
        if not isinstance(message, Message):
            message = Message(body=message)

        message.delivery_info = {
            "exchange": exchange,
            "routing_key": routing_key,
        }

        # Route message to appropriate queues
        if exchange and exchange in self._exchanges:
            exch = self._exchanges[exchange]
            target_queues = exch.get_bound_queues(routing_key)
        else:
            # Default exchange - route directly to queue named by routing_key
            target_queues = [routing_key] if routing_key else []

        # Put message in all target queues
        for queue_name in target_queues:
            if queue_name in self._queues:
                queue = self._queues[queue_name]
                queue.put(message)

    def basic_consume(
        self,
        queue: str,
        callback: Callable[[Message], None],
        no_ack: bool = False,
        consumer_tag: Optional[str] = None,
    ) -> str:
        """
        Start consuming messages from a queue.

        Args:
            queue: Queue name
            callback: Callback function for messages
            no_ack: Auto-acknowledge messages
            consumer_tag: Consumer identifier

        Returns:
            Consumer tag
        """
        if queue not in self._queues:
            raise ValueError(f"Queue {queue} not found")

        consumer_tag = consumer_tag or f"consumer-{uuid.uuid4()}"

        # Start consumer thread
        def consume():
            queue_obj = self._queues[queue]
            while not self._closed:
                try:
                    message = queue_obj.get(block=True, timeout=0.1)
                    if message:
                        with self._lock:
                            self._delivery_tag_counter += 1
                            message.delivery_tag = self._delivery_tag_counter
                            message.channel = self

                        callback(message)

                        if no_ack:
                            # Auto-acknowledge
                            pass
                except Empty:
                    continue

        thread = Thread(target=consume, daemon=True)
        thread.start()

        return consumer_tag

    def basic_get(self, queue: str, no_ack: bool = False) -> Optional[Message]:
        """
        Get a single message from a queue.

        Args:
            queue: Queue name
            no_ack: Auto-acknowledge

        Returns:
            Message or None
        """
        if queue not in self._queues:
            return None

        queue_obj = self._queues[queue]
        message = queue_obj.get(block=False)

        if message and not no_ack:
            with self._lock:
                self._delivery_tag_counter += 1
                message.delivery_tag = self._delivery_tag_counter
                message.channel = self

        return message

    def basic_ack(self, delivery_tag: int):
        """
        Acknowledge a message.

        Args:
            delivery_tag: Message delivery tag
        """
        # In a real implementation, this would remove from unacked list
        pass

    def basic_reject(self, delivery_tag: int, requeue: bool = True):
        """
        Reject a message.

        Args:
            delivery_tag: Message delivery tag
            requeue: Whether to requeue
        """
        # In a real implementation, this would requeue or discard
        pass

    def close(self):
        """Close the channel."""
        self._closed = True


class Producer:
    """
    Message producer (publisher).
    """

    def __init__(
        self,
        channel: Channel,
        exchange: Optional[Exchange] = None,
        routing_key: str = "",
        serializer: str = "json",
    ):
        """
        Initialize a producer.

        Args:
            channel: Channel for publishing
            exchange: Default exchange
            routing_key: Default routing key
            serializer: Message serializer
        """
        self.channel = channel
        self.exchange = exchange
        self.routing_key = routing_key
        self.serializer = serializer

    def publish(
        self,
        body: Any,
        routing_key: Optional[str] = None,
        exchange: Optional[Union[str, Exchange]] = None,
        **kwargs,
    ):
        """
        Publish a message.

        Args:
            body: Message body
            routing_key: Routing key (overrides default)
            exchange: Exchange (overrides default)
            **kwargs: Additional message properties
        """
        # Serialize body
        if self.serializer == "json":
            serialized_body = json.dumps(body)
        else:
            serialized_body = body

        # Create message
        message = Message(
            body=serialized_body,
            content_type="application/json" if self.serializer == "json" else "text/plain",
            **kwargs,
        )

        # Determine exchange and routing key
        exch_name = ""
        if exchange:
            if isinstance(exchange, Exchange):
                exch_name = exchange.name
            else:
                exch_name = exchange
        elif self.exchange:
            exch_name = self.exchange.name

        rkey = routing_key or self.routing_key

        # Publish
        self.channel.basic_publish(message, exchange=exch_name, routing_key=rkey)


class Consumer:
    """
    Message consumer.
    """

    def __init__(
        self,
        channel: Channel,
        queues: Optional[List[Queue]] = None,
        callbacks: Optional[List[Callable]] = None,
        no_ack: bool = False,
    ):
        """
        Initialize a consumer.

        Args:
            channel: Channel for consuming
            queues: Queues to consume from
            callbacks: Callback functions
            no_ack: Auto-acknowledge messages
        """
        self.channel = channel
        self.queues = queues or []
        self.callbacks = callbacks or []
        self.no_ack = no_ack
        self._consumer_tags: List[str] = []

    def consume(self, no_ack: Optional[bool] = None):
        """
        Start consuming messages.

        Args:
            no_ack: Auto-acknowledge (overrides default)

        Yields:
            Messages from queues
        """
        no_ack = no_ack if no_ack is not None else self.no_ack

        # Start consuming from all queues
        for queue in self.queues:
            for callback in self.callbacks:
                tag = self.channel.basic_consume(
                    queue.name,
                    callback,
                    no_ack=no_ack,
                )
                self._consumer_tags.append(tag)

    def register_callback(self, callback: Callable):
        """
        Register a callback function.

        Args:
            callback: Callback function
        """
        self.callbacks.append(callback)
