from typing import Any, Literal

from chanx.messages.base import BaseChannelEvent, BaseGroupMessage
from pydantic import BaseModel

from .common_messages import (
    CommonIncomingMessage,
    VoteUpdateEvent,
)


# Payloads for topic detail view message types
class NewReplyEventPayload(BaseModel):
    """Payload for new reply channel events."""

    id: int
    content: str
    author: dict[str, Any]
    vote_count: int
    is_accepted: bool
    created_at: str
    formatted_created_at: str
    topic_id: int
    topic_title: str


class AnswerAcceptedEventPayload(BaseModel):
    """Payload for answer accepted events."""

    topic_id: int
    topic_title: str
    reply_id: int
    reply_author: str


class AnswerUnacceptedEventPayload(BaseModel):
    """Payload for answer unaccepted events."""

    topic_id: int
    topic_title: str
    reply_id: int
    reply_author: str


# Outgoing group messages for topic detail view
class ReplyCreatedMessage(BaseGroupMessage):
    """Broadcast when a new reply is created."""

    action: Literal["reply_created"] = "reply_created"
    payload: NewReplyEventPayload


class AnswerAcceptedMessage(BaseGroupMessage):
    """Broadcast when an answer is accepted."""

    action: Literal["answer_accepted"] = "answer_accepted"
    payload: AnswerAcceptedEventPayload


class AnswerUnacceptedMessage(BaseGroupMessage):
    """Broadcast when an answer is unaccepted."""

    action: Literal["answer_unaccepted"] = "answer_unaccepted"
    payload: AnswerUnacceptedEventPayload


# Channel events for topic detail view
class NewReplyEvent(BaseChannelEvent):
    """Channel event for new reply creation."""

    handler: Literal["handle_new_reply"] = "handle_new_reply"
    payload: NewReplyEventPayload


class AnswerAcceptedEvent(BaseChannelEvent):
    """Channel event for answer acceptance."""

    handler: Literal["handle_answer_accepted"] = "handle_answer_accepted"
    payload: AnswerAcceptedEventPayload


class AnswerUnacceptedEvent(BaseChannelEvent):
    """Channel event for answer unacceptance."""

    handler: Literal["handle_answer_unaccepted"] = "handle_answer_unaccepted"
    payload: AnswerUnacceptedEventPayload


# Union of all incoming messages for topic detail view
TopicDetailMessage = CommonIncomingMessage


# Union of all channel events for topic detail view
TopicDetailEvent = (
    NewReplyEvent | AnswerAcceptedEvent | AnswerUnacceptedEvent | VoteUpdateEvent
)
