from typing import Any, assert_never

from rest_framework.permissions import IsAuthenticated

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage

from discussion.messages.common_messages import (
    VoteUpdatedMessage,
    VoteUpdateEvent,
)
from discussion.messages.topic_detail_messages import (
    AnswerAcceptedEvent,
    AnswerAcceptedMessage,
    AnswerUnacceptedEvent,
    AnswerUnacceptedMessage,
)
from discussion.messages.topic_list_messages import (
    NewTopicEvent,
    TopicCreatedMessage,
    TopicListEvent,
    TopicListGroupMessage,
    TopicListMessage,
)


class DiscussionListConsumer(
    AsyncJsonWebsocketConsumer[TopicListMessage, TopicListEvent, TopicListGroupMessage]
):
    """
    WebSocket consumer for discussion topic list view.

    Handles global discussion updates like new topics, votes, and answer acceptance/unacceptance.
    """

    permission_classes = [IsAuthenticated]

    async def build_groups(self) -> list[str]:
        """Join the global discussion updates group."""
        return ["discussion_updates"]  # Global discussion updates

    async def receive_message(self, message: TopicListMessage, **kwargs: Any) -> None:
        """Handle incoming WebSocket messages."""
        match message:
            case PingMessage():
                await self.send_message(PongMessage())
            case _:
                assert_never(message)

    async def receive_event(self, event: TopicListEvent) -> None:
        """Handle channel events and broadcast to connected clients."""
        match event:
            case NewTopicEvent(payload=payload):
                # Only broadcast, don't create - creation happens via API
                await self.send_message(TopicCreatedMessage(payload=payload))

            case VoteUpdateEvent(payload=payload):
                await self.send_message(VoteUpdatedMessage(payload=payload))

            # Answer acceptance events are handled by topic-specific consumers
            case AnswerAcceptedEvent(payload=payload):
                await self.send_message(AnswerAcceptedMessage(payload=payload))

            # Answer unacceptance events are handled by topic-specific consumers
            case AnswerUnacceptedEvent(payload=payload):
                await self.send_message(AnswerUnacceptedMessage(payload=payload))

            case _:
                assert_never(event)
