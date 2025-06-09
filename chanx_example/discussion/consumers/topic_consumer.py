from typing import Any

from rest_framework.permissions import IsAuthenticated

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage
from typing_extensions import assert_never

from discussion.messages.common_messages import (
    VoteUpdatedMessage,
    VoteUpdateEvent,
)
from discussion.messages.topic_detail_messages import (
    AnswerAcceptedEvent,
    AnswerAcceptedMessage,
    AnswerUnacceptedEvent,
    AnswerUnacceptedMessage,
    NewReplyEvent,
    ReplyCreatedMessage,
    TopicDetailEvent,
    TopicDetailMessage,
)
from discussion.models import DiscussionTopic


class DiscussionTopicConsumer(
    AsyncJsonWebsocketConsumer[TopicDetailMessage, TopicDetailEvent, DiscussionTopic]
):
    """
    WebSocket consumer for discussion topic detail view.

    Handles topic-specific operations like replying, voting, and accepting/unaccepting answers.
    """

    permission_classes = [IsAuthenticated]
    queryset = DiscussionTopic.objects.all()

    async def build_groups(self) -> list[str]:
        """Join topic-specific group."""
        groups: list[str] = []

        # Join the topic-specific group
        if self.obj:
            groups.append(f"discussion_topic_{self.obj.pk}")

        return groups

    async def receive_message(self, message: TopicDetailMessage, **kwargs: Any) -> None:
        """Handle incoming WebSocket messages."""
        match message:
            case PingMessage():
                await self.send_message(PongMessage())
            case _:
                assert_never(message)

    async def receive_event(self, event: TopicDetailEvent) -> None:
        """Handle channel events and broadcast to connected clients."""
        match event:
            case NewReplyEvent(payload=payload):
                # Only broadcast, don't create - creation happens via API
                await self.send_message(ReplyCreatedMessage(payload=payload))

            case VoteUpdateEvent(payload=payload):
                await self.send_message(VoteUpdatedMessage(payload=payload))

            case AnswerAcceptedEvent(payload=payload):
                await self.send_message(AnswerAcceptedMessage(payload=payload))

            case AnswerUnacceptedEvent(payload=payload):
                await self.send_message(AnswerUnacceptedMessage(payload=payload))

            case _:
                assert_never(event)
