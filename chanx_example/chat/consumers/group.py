from typing import Any

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage

from chat.messages.group import (
    AddedToGroupMessage,
    GroupChatEvent,
    GroupChatMessage,
    GroupChatUpdatedMessage,
    NotifyAddedToGroupEvent,
    NotifyGroupChatUpdateEvent,
    NotifyRemovedFromGroupEvent,
    RemovedFromGroupMessage,
)
from chat.messages.member import OutgoingMemberMessage
from chat.utils import make_user_groups_layer_name


class GroupChatConsumer(
    AsyncJsonWebsocketConsumer[GroupChatMessage, GroupChatEvent, OutgoingMemberMessage]
):
    """
    WebSocket consumer for group chat updates.

    This consumer provides:
    - Notifications when a group chat receives new messages (timestamp updates)
    - Notifications when user is added/removed from groups
    """

    async def build_groups(self) -> list[str]:
        """
        Build groups to join based on user authentication.

        Returns:
            List of channel group names to join
        """
        if not self.user or not self.user.is_authenticated:
            return []

        assert self.user.pk
        # Just join the user's personal notification group
        return [make_user_groups_layer_name(self.user.pk), "group_chat_updates"]

    async def receive_message(self, message: GroupChatMessage, **kwargs: Any) -> None:
        """Handle incoming WebSocket messages."""
        match message:
            case PingMessage():
                await self.send_message(PongMessage())

    async def receive_event(self, event: GroupChatEvent) -> None:
        """Handle incoming WebSocket events."""
        match event:
            case NotifyAddedToGroupEvent(payload=payload):
                await self.send_message(AddedToGroupMessage(payload=payload))
            case NotifyRemovedFromGroupEvent(payload=payload):
                await self.send_message(RemovedFromGroupMessage(payload=payload))
            case NotifyGroupChatUpdateEvent(payload=payload):
                await self.send_message(GroupChatUpdatedMessage(payload=payload))
