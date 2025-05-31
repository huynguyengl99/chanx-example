from typing import Any, Literal

from chanx.messages.base import BaseChannelEvent, BaseGroupMessage, BaseMessage
from pydantic import BaseModel

from .common_messages import (
    CommonIncomingMessage,
    VotePayload,
    VoteUpdatedMessage,
    VoteUpdateEvent,
)


# Payloads for topic detail view message types
class NewReplyPayload(BaseModel):
    """Payload for creating a new reply to a topic."""

    content: str


class AcceptAnswerPayload(BaseModel):
    """Payload for accepting an answer."""

    reply_id: int


class UnacceptAnswerPayload(BaseModel):
    """Payload for unaccepting an answer."""

    reply_id: int


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


# Incoming WebSocket messages for topic detail view
class NewReplyMessage(BaseMessage):
    """Create a new reply to a topic."""

    action: Literal["new_reply"] = "new_reply"
    payload: NewReplyPayload


class VoteMessage(BaseMessage):
    """Vote on a topic or reply."""

    action: Literal["vote"] = "vote"
    payload: VotePayload


class AcceptAnswerMessage(BaseMessage):
    """Accept a reply as the answer."""

    action: Literal["accept_answer"] = "accept_answer"
    payload: AcceptAnswerPayload


class UnacceptAnswerMessage(BaseMessage):
    """Unaccept a reply as the answer."""

    action: Literal["unaccept_answer"] = "unaccept_answer"
    payload: UnacceptAnswerPayload


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
TopicDetailMessage = (
    NewReplyMessage
    | VoteMessage
    | AcceptAnswerMessage
    | UnacceptAnswerMessage
    | CommonIncomingMessage
)


# Union of all outgoing group messages for topic detail view
TopicDetailGroupMessage = (
    ReplyCreatedMessage
    | AnswerAcceptedMessage
    | AnswerUnacceptedMessage
    | VoteUpdatedMessage
)


# Union of all channel events for topic detail view
TopicDetailEvent = (
    NewReplyEvent | AnswerAcceptedEvent | AnswerUnacceptedEvent | VoteUpdateEvent
)
