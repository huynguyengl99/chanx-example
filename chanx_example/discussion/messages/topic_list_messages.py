from typing import Any, Literal

from chanx.messages.base import BaseChannelEvent, BaseGroupMessage, BaseMessage
from pydantic import BaseModel

from .common_messages import CommonIncomingMessage, VoteUpdatedMessage, VoteUpdateEvent
from .topic_detail_messages import AnswerAcceptedEvent, AnswerUnacceptedEvent


# Payloads for topic list view message types
class NewTopicPayload(BaseModel):
    """Payload for creating a new topic."""

    title: str
    content: str


class NewTopicEventPayload(BaseModel):
    """Payload for new topic channel events."""

    id: int
    title: str
    author: dict[str, Any]
    vote_count: int
    reply_count: int
    has_accepted_answer: bool
    view_count: int
    created_at: str
    formatted_created_at: str


# Incoming WebSocket messages for topic list view
class NewTopicMessage(BaseMessage):
    """Create a new discussion topic."""

    action: Literal["new_topic"] = "new_topic"
    payload: NewTopicPayload


# Outgoing group messages for topic list view
class TopicCreatedMessage(BaseGroupMessage):
    """Broadcast when a new topic is created."""

    action: Literal["topic_created"] = "topic_created"
    payload: NewTopicEventPayload


# Channel events for topic list view
class NewTopicEvent(BaseChannelEvent):
    """Channel event for new topic creation."""

    handler: Literal["handle_new_topic"] = "handle_new_topic"
    payload: NewTopicEventPayload


# Union of all incoming messages for topic list view
TopicListMessage = NewTopicMessage | CommonIncomingMessage


# Union of all outgoing group messages for topic list view
TopicListGroupMessage = TopicCreatedMessage | VoteUpdatedMessage


# Union of all channel events for topic list view
TopicListEvent = (
    NewTopicEvent | VoteUpdateEvent | AnswerAcceptedEvent | AnswerUnacceptedEvent
)
