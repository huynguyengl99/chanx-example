from typing import Any, Literal

from chanx.messages.base import BaseChannelEvent, BaseGroupMessage
from chanx.messages.incoming import PingMessage
from pydantic import BaseModel


# Payloads
class StreamingPayload(BaseModel):
    content: str
    is_complete: bool = False
    message_id: int


class ErrorPayload(BaseModel):
    content: str
    message_id: str


class MessagePayload(BaseModel):
    content: str


# Outgoing group messages (WebSocket → Client)
class StreamingMessage(BaseGroupMessage):
    """Streaming message chunk from assistant."""

    action: Literal["streaming"] = "streaming"
    payload: StreamingPayload


class CompleteStreamingMessage(BaseGroupMessage):
    """Streaming message chunk from assistant."""

    action: Literal["complete_streaming"] = "complete_streaming"
    payload: StreamingPayload


class NewAssistantMessage(BaseGroupMessage):
    """New assistant message (user or AI)."""

    action: Literal["new_assistant_message"] = "new_assistant_message"
    payload: dict[str, Any]


class ErrorMessage(BaseGroupMessage):
    """Error message from assistant."""

    action: Literal["error"] = "error"
    payload: ErrorPayload


# Channel events (Task → Consumer)
class StreamingEvent(BaseChannelEvent):
    """Channel event for streaming chunks."""

    handler: Literal["handle_streaming"] = "handle_streaming"
    payload: StreamingPayload


class CompleteStreamingEvent(BaseChannelEvent):
    """Channel event for streaming chunks."""

    handler: Literal["handle_complete_streaming"] = "handle_complete_streaming"
    payload: StreamingPayload


class NewAssistantMessageEvent(BaseChannelEvent):
    """Channel event for new assistant messages."""

    handler: Literal["handle_new_assistant_message"] = "handle_new_assistant_message"
    payload: dict[str, Any]


class ErrorEvent(BaseChannelEvent):
    """Channel event for errors."""

    handler: Literal["handle_error"] = "handle_error"
    payload: ErrorPayload


# Union types
AssistantIncomingMessage = PingMessage
AssistantEvent = (
    StreamingEvent | CompleteStreamingEvent | NewAssistantMessageEvent | ErrorEvent
)
