from typing import Literal

from chanx.messages.base import BaseIncomingMessage, BaseMessage
from chanx.messages.incoming import PingMessage
from pydantic import BaseModel


class MessagePayload(BaseModel):
    content: str


class NewMessage(BaseMessage):
    """
    New message for assistant.
    """

    action: Literal["new_message"] = "new_message"
    payload: MessagePayload


class StreamingPayload(BaseModel):
    content: str
    is_complete: bool = False
    message_id: str


class StreamingMessage(BaseMessage):
    """Streaming message chunk from assistant."""

    action: Literal["streaming"] = "streaming"
    payload: StreamingPayload


class ReplyMessage(BaseMessage):
    action: Literal["reply"] = "reply"
    payload: MessagePayload


class AssistantIncomingMessage(BaseIncomingMessage):
    message: NewMessage | PingMessage
