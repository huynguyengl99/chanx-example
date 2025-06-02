from typing import Any, Literal

from chanx.messages.base import BaseChannelEvent, BaseMessage
from chanx.messages.incoming import PingMessage
from pydantic import BaseModel

ChatIncomingMessage = PingMessage


class MemberAddedMessage(BaseMessage):
    action: Literal["member_added"] = "member_added"
    payload: dict[str, Any]


class NotifyMemberAddedEvent(BaseChannelEvent):
    handler: Literal["notify_member_added"] = "notify_member_added"
    payload: dict[str, Any]


class MemberRemovedPayload(BaseModel):
    user_pk: int
    email: str


class MemberRemovedMessage(BaseMessage):
    action: Literal["member_removed"] = "member_removed"
    payload: MemberRemovedPayload


class UserRemovedFromGroupMessage(BaseMessage):
    class Payload(BaseModel):
        redirect: str
        message: str

    action: Literal["user_removed_from_group"] = "user_removed_from_group"
    payload: Payload


class NotifyMemberRemovedEvent(BaseChannelEvent):
    handler: Literal["notify_member_removed"] = "notify_member_removed"
    payload: MemberRemovedPayload


class NewChatMessageEvent(BaseChannelEvent):
    class Payload(BaseModel):
        message_data: dict[str, Any]
        user_pk: int | None

    handler: Literal["new_chat_message"] = "new_chat_message"
    payload: Payload


ChatDetailEvent = (
    NotifyMemberAddedEvent | NotifyMemberRemovedEvent | NewChatMessageEvent
)
