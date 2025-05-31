from typing import Any, Literal

from chanx.messages.base import BaseChannelEvent, BaseMessage
from chanx.messages.incoming import PingMessage
from pydantic import BaseModel

GroupChatMessage = PingMessage


class AddedToGroupMessage(BaseMessage):
    action: Literal["added_to_group"] = "added_to_group"
    payload: dict[str, Any]


class NotifyAddedToGroupEvent(BaseChannelEvent):
    handler: Literal["notify_added_to_group"] = "notify_added_to_group"
    payload: dict[str, Any]


class GroupRemovePayload(BaseModel):
    group_pk: int
    group_title: str


class RemovedFromGroupMessage(BaseMessage):
    action: Literal["removed_from_group"] = "removed_from_group"
    payload: GroupRemovePayload


class NotifyRemovedFromGroupEvent(BaseChannelEvent):
    handler: Literal["notify_removed_from_group"] = "notify_removed_from_group"
    payload: GroupRemovePayload


class GroupChatUpdatePayload(BaseModel):
    group_pk: int
    updated_at: str


class GroupChatUpdatedMessage(BaseMessage):
    action: Literal["group_chat_updated"] = "group_chat_updated"
    payload: GroupChatUpdatePayload


class NotifyGroupChatUpdateEvent(BaseChannelEvent):
    handler: Literal["notify_group_chat_update"] = "notify_group_chat_update"
    payload: GroupChatUpdatePayload


GroupChatEvent = (
    NotifyAddedToGroupEvent | NotifyRemovedFromGroupEvent | NotifyGroupChatUpdateEvent
)
