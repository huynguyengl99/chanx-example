from typing import Any, assert_never

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage

from accounts.models import User
from assistants.messages.assistant import (
    AssistantEvent,
    AssistantIncomingMessage,
    ErrorEvent,
    ErrorMessage,
    NewAssistantMessage,
    NewAssistantMessageEvent,
    StreamingEvent,
    StreamingMessage,
)
from assistants.models import AssistantConversation
from assistants.permissions import ConversationOwner


class ConversationAssistantConsumer(
    AsyncJsonWebsocketConsumer[
        AssistantIncomingMessage,
        AssistantEvent,
        AssistantConversation,
    ]
):
    """WebSocket consumer for both authenticated and anonymous users with specific conversations."""

    permission_classes = [ConversationOwner]
    user: User | None
    conversation: AssistantConversation | None
    queryset = AssistantConversation.objects.all()

    async def build_groups(self) -> list[str]:
        """Build groups based on conversation type (authenticated or anonymous)."""
        # Get conversation_id from URL path
        conversation_id = self.obj.id

        if self.user and self.user.is_authenticated:
            return [f"user_{self.user.pk}_conversation_{conversation_id}"]
        else:
            return [f"anonymous_{conversation_id}"]

    async def receive_message(
        self, message: AssistantIncomingMessage, **kwargs: Any
    ) -> None:
        """Handle incoming WebSocket messages."""
        match message:
            case PingMessage():
                await self.send_message(PongMessage())
            case _:
                assert_never(message)

    async def receive_event(self, event: AssistantEvent) -> None:
        """Handle incoming channel events."""
        match event:
            case StreamingEvent(payload=payload):
                await self.send_message(StreamingMessage(payload=payload))
            case NewAssistantMessageEvent(payload=payload):
                await self.send_message(NewAssistantMessage(payload=payload))
            case ErrorEvent(payload=payload):
                await self.send_message(ErrorMessage(payload=payload))
            case _:
                assert_never(event)
