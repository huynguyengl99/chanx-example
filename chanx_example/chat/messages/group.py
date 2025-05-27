from typing import Literal

from chanx.messages.base import BaseMessage
from chanx.messages.incoming import PingMessage
from pydantic import BaseModel


class GroupChatRefreshPayload(BaseModel):
    """Simple payload for requesting group chat list refresh."""

    refresh: bool = True


class GroupChatRefreshRequest(BaseMessage):
    """Request to refresh the group chat list."""

    action: Literal["refresh_group_chats"] = "refresh_group_chats"
    payload: GroupChatRefreshPayload


GroupChatMessage = GroupChatRefreshRequest | PingMessage
