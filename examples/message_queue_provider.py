"""
Message Queue Provider Example

This example demonstrates how to implement a provider that interacts with a message queue using the Arbvantage Provider Framework and explicit Pydantic schemas.
It shows how to:
1. Connect to a message queue (e.g., RabbitMQ)
2. Register actions for publishing and consuming messages
3. Handle connection and error handling

Environment variables required:
- PROVIDER_NAME: Name of the provider (defaults to "message-queue-provider")
- PROVIDER_AUTH_TOKEN: Authentication token for the hub
- HUB_GRPC_URL: URL of the hub service (defaults to "hub-grpc:50051")
- MQ_URL: Message queue connection URL

Why is this important?
----------------------
This example shows how to safely and cleanly wrap message queue operations with strict validation and error handling.
"""

from typing import Optional
from pydantic import BaseModel, Field
from arbvantage_provider import Provider, ProviderResponse
import os
import pika

# --- Pydantic Schemas ---
class PublishMessagePayload(BaseModel):
    queue: str = Field(..., description="Queue name to publish to")
    message: str = Field(..., description="Message body")

class ConsumeMessagePayload(BaseModel):
    queue: str = Field(..., description="Queue name to consume from")
    auto_ack: Optional[bool] = Field(True, description="Auto-acknowledge messages")

class MQAccount(BaseModel):
    url: str = Field(..., description="Message queue connection URL")

class MessageQueueProvider(Provider):
    """
    Example provider for interacting with a message queue using explicit Pydantic schemas.
    """
    def __init__(self):
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "message-queue-provider"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN", "your-auth-token"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        self._register_actions()

    def _register_actions(self):
        @self.actions.register(
            name="publish_message",
            description="Publish a message to a queue",
            payload_schema=PublishMessagePayload,
            account_schema=MQAccount
        )
        def publish_message(payload: PublishMessagePayload, account: MQAccount) -> ProviderResponse:
            try:
                connection = pika.BlockingConnection(pika.URLParameters(account.url))
                channel = connection.channel()
                channel.queue_declare(queue=payload.queue, durable=True)
                channel.basic_publish(
                    exchange='',
                    routing_key=payload.queue,
                    body=payload.message.encode('utf-8'),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                connection.close()
                return ProviderResponse(status="success", data={"queue": payload.queue, "message": payload.message})
            except Exception as e:
                return ProviderResponse(status="error", message=str(e))

        @self.actions.register(
            name="consume_message",
            description="Consume a message from a queue",
            payload_schema=ConsumeMessagePayload,
            account_schema=MQAccount
        )
        def consume_message(payload: ConsumeMessagePayload, account: MQAccount) -> ProviderResponse:
            try:
                connection = pika.BlockingConnection(pika.URLParameters(account.url))
                channel = connection.channel()
                channel.queue_declare(queue=payload.queue, durable=True)
                method_frame, header_frame, body = channel.basic_get(queue=payload.queue, auto_ack=payload.auto_ack)
                connection.close()
                if method_frame:
                    return ProviderResponse(status="success", data={"message": body.decode('utf-8')})
                else:
                    return ProviderResponse(status="success", data={"message": None})
            except Exception as e:
                return ProviderResponse(status="error", message=str(e))

if __name__ == "__main__":
    provider = MessageQueueProvider()
    provider.start() 