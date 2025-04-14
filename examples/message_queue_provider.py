"""
Example of a provider with message queue support.

This example demonstrates how to implement message queue operations in a provider.
It shows:
- Message queue connection management
- Publishing messages
- Consuming messages
- Error handling with queues
"""

import os
import json
import pika
from typing import Dict, Any, Optional
from threading import Thread
from queue import Queue
from arbvantage_provider import Provider, ProviderResponse

class MessageQueueProvider(Provider):
    """
    Provider with message queue support.
    
    This provider demonstrates how to implement message queue operations.
    It uses RabbitMQ for message queuing and provides pub/sub functionality.
    """
    
    def __init__(self):
        super().__init__(
            name="message-queue-provider",
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        
        # Initialize message queue connection
        self.connection = None
        self.channel = None
        self.message_queue = Queue()
        
        # Initialize RabbitMQ connection
        self._init_rabbitmq()
        
        # Start message consumer thread
        self.consumer_thread = Thread(target=self._consume_messages, daemon=True)
        self.consumer_thread.start()
        
        # Register message queue actions
        self._register_queue_actions()
        
    def _init_rabbitmq(self):
        """Initialize RabbitMQ connection."""
        try:
            # Get RabbitMQ connection parameters
            host = os.getenv("RABBITMQ_HOST", "localhost")
            port = int(os.getenv("RABBITMQ_PORT", 5672))
            username = os.getenv("RABBITMQ_USERNAME", "guest")
            password = os.getenv("RABBITMQ_PASSWORD", "guest")
            
            # Create connection
            credentials = pika.PlainCredentials(username, password)
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange and queue
            self.channel.exchange_declare(
                exchange="arbvantage",
                exchange_type="topic"
            )
            self.channel.queue_declare(queue="arbvantage_queue")
            self.channel.queue_bind(
                exchange="arbvantage",
                queue="arbvantage_queue",
                routing_key="provider.#"
            )
            
            self.logger.info("RabbitMQ connection established")
            
        except Exception as e:
            self.logger.error("Failed to initialize RabbitMQ", error=str(e))
            raise
            
    def _register_queue_actions(self):
        """Register message queue actions."""
        
        @self.actions.register(
            name="publish_message",
            description="Publish message to queue",
            payload_schema={
                "routing_key": str,
                "message": Dict[str, Any]
            }
        )
        def publish_message(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Publish message to the queue.
            
            Args:
                payload: Dictionary containing routing key and message
                
            Returns:
                ProviderResponse with publish status
            """
            try:
                routing_key = payload["routing_key"]
                message = payload["message"]
                
                # Publish message
                self.channel.basic_publish(
                    exchange="arbvantage",
                    routing_key=routing_key,
                    body=json.dumps(message)
                )
                
                return ProviderResponse(
                    status="success",
                    message="Message published successfully",
                    data={
                        "routing_key": routing_key,
                        "message": message
                    }
                )
                
            except Exception as e:
                self.logger.error("Error publishing message", error=str(e))
                return ProviderResponse(
                    status="error",
                    message=f"Failed to publish message: {str(e)}"
                )
                
        @self.actions.register(
            name="get_messages",
            description="Get messages from queue",
            payload_schema={"count": int}
        )
        def get_messages(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Get messages from the queue.
            
            Args:
                payload: Dictionary containing message count
                
            Returns:
                ProviderResponse with messages
            """
            try:
                count = payload.get("count", 10)
                messages = []
                
                # Get messages from queue
                for _ in range(count):
                    try:
                        message = self.message_queue.get_nowait()
                        messages.append(message)
                    except:
                        break
                        
                return ProviderResponse(
                    status="success",
                    message=f"Retrieved {len(messages)} messages",
                    data={"messages": messages}
                )
                
            except Exception as e:
                self.logger.error("Error getting messages", error=str(e))
                return ProviderResponse(
                    status="error",
                    message=f"Failed to get messages: {str(e)}"
                )
                
    def _consume_messages(self):
        """Consume messages from the queue."""
        def callback(ch, method, properties, body):
            try:
                # Parse message
                message = json.loads(body)
                
                # Add to message queue
                self.message_queue.put({
                    "routing_key": method.routing_key,
                    "message": message,
                    "timestamp": properties.timestamp
                })
                
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
            except Exception as e:
                self.logger.error("Error processing message", error=str(e))
                
        try:
            # Start consuming
            self.channel.basic_consume(
                queue="arbvantage_queue",
                on_message_callback=callback
            )
            self.channel.start_consuming()
            
        except Exception as e:
            self.logger.error("Error in consumer thread", error=str(e))
            
    def cleanup(self):
        """Cleanup resources."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            
if __name__ == "__main__":
    provider = MessageQueueProvider()
    try:
        provider.start()
    finally:
        provider.cleanup() 