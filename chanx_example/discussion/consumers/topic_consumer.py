from typing import Any, cast

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import ErrorMessage, PongMessage

from discussion.messages.common_messages import (
    VoteUpdatedMessage,
    VoteUpdateEvent,
)
from discussion.messages.topic_detail_messages import (
    AcceptAnswerMessage,
    AnswerAcceptedEvent,
    AnswerAcceptedMessage,
    AnswerUnacceptedEvent,
    AnswerUnacceptedMessage,
    NewReplyEvent,
    NewReplyMessage,
    ReplyCreatedMessage,
    TopicDetailEvent,
    TopicDetailGroupMessage,
    TopicDetailMessage,
    UnacceptAnswerMessage,
    VoteMessage,
)
from discussion.models import DiscussionReply, DiscussionTopic
from utils.request import AuthenticatedRequest


class DiscussionTopicConsumer(
    AsyncJsonWebsocketConsumer[
        TopicDetailMessage, TopicDetailEvent, TopicDetailGroupMessage, DiscussionTopic
    ]
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

            # Remove WebSocket reply creation to prevent duplication
            # Replies should only be created via REST API
            case NewReplyMessage():
                await self.send_message(
                    ErrorMessage(
                        payload={
                            "detail": "Please use the API endpoint for creating replies"
                        }
                    )
                )

            case VoteMessage():
                await self._handle_vote(message.payload)

            case AcceptAnswerMessage():
                await self._handle_accept_answer(message.payload)

            case UnacceptAnswerMessage():
                await self._handle_unaccept_answer(message.payload)

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

    async def _handle_vote(self, payload: Any) -> None:
        """Handle voting via WebSocket."""
        try:
            # Voting is now simplified to use the API instead
            await self.send_message(
                ErrorMessage(
                    payload={"detail": "Please use the API endpoint for voting"}
                )
            )

        except Exception as e:
            await self.send_message(
                ErrorMessage(payload={"detail": f"Failed to process vote: {str(e)}"})
            )

    async def _handle_accept_answer(self, payload: Any) -> None:
        """Handle answer acceptance via WebSocket."""
        try:
            request = cast(AuthenticatedRequest, self.request)

            reply_id = payload.reply_id
            if not reply_id:
                await self.send_message(
                    ErrorMessage(payload={"detail": "reply_id is required"})
                )
                return

            reply = get_object_or_404(
                DiscussionReply.objects.select_related("topic", "author"),
                pk=reply_id,
            )

            # Only topic author can accept answers
            if self.obj.author != request.user:
                await self.send_message(
                    ErrorMessage(
                        payload={"detail": "Only the topic author can accept answers"}
                    )
                )
                return

            # Don't allow accepting your own answer
            if reply.author == request.user:
                await self.send_message(
                    ErrorMessage(
                        payload={"detail": "You cannot accept your own answer"}
                    )
                )
                return

            # Update topic's accepted answer
            self.obj.accepted_answer = reply
            await self.obj.asave(update_fields=["accepted_answer"])

            # Import here to avoid circular import
            from discussion.tasks import task_broadcast_answer_accepted

            # Broadcast answer acceptance
            task_broadcast_answer_accepted(self.obj.pk, reply.pk)

        except Exception as e:
            await self.send_message(
                ErrorMessage(payload={"detail": f"Failed to accept answer: {str(e)}"})
            )

    async def _handle_unaccept_answer(self, payload: Any) -> None:
        """Handle answer unacceptance via WebSocket."""
        try:
            request = cast(AuthenticatedRequest, self.request)

            reply_id = payload.reply_id
            if not reply_id:
                await self.send_message(
                    ErrorMessage(payload={"detail": "reply_id is required"})
                )
                return

            # Only topic author can unaccept answers
            if self.obj.author != request.user:
                await self.send_message(
                    ErrorMessage(
                        payload={"detail": "Only the topic author can unaccept answers"}
                    )
                )
                return

            # Check if there's an accepted answer and if it matches the reply_id
            if not self.obj.accepted_answer or self.obj.accepted_answer.pk != reply_id:
                await self.send_message(
                    ErrorMessage(
                        payload={"detail": "This reply is not currently accepted"}
                    )
                )
                return

            # Update topic's accepted answer to None
            self.obj.accepted_answer = None
            await self.obj.asave(update_fields=["accepted_answer"])

            # Import here to avoid circular import
            from discussion.tasks import task_broadcast_answer_unaccepted

            # Broadcast answer unacceptance
            task_broadcast_answer_unaccepted(self.obj.pk, reply_id)

        except Exception as e:
            await self.send_message(
                ErrorMessage(payload={"detail": f"Failed to unaccept answer: {str(e)}"})
            )
