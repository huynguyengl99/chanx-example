from typing import Any, TypedDict

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.base import BaseMessage
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage

from chat.messages.group import GroupChatIncomingMessage, GroupChatRefreshRequest
from chat.messages.member import OutgoingMemberMessage
from chat.models import GroupChat


class GroupChatUpdatePayload(TypedDict):
    """Payload for group chat update notifications."""

    group_id: int
    updated_at: str


class GroupChatUpdateEvent(TypedDict):
    """Event for group chat update notifications."""

    payload: GroupChatUpdatePayload


class GroupChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for group chat updates.

    This consumer provides:
    - Notifications when a group chat receives new messages (timestamp updates)
    - Simple API for manual refresh of the group chat list

    For adding/removing users from group chats, the application uses REST API calls
    to refresh the list instead of WebSocket events.
    """

    INCOMING_MESSAGE_SCHEMA = GroupChatIncomingMessage
    OUTGOING_GROUP_MESSAGE_SCHEMA = OutgoingMemberMessage
    groups = ["group_chat_updates"]  # Global group for all users

    async def connect(self) -> None:
        """Handle WebSocket connection with authentication."""
        await super().connect()

        # If connection was successful and user authenticated
        if (
            self.connecting
            or not hasattr(self, "user")
            or not self.user
            or not self.user.is_authenticated
        ):
            return

    async def receive_message(self, message: BaseMessage, **kwargs: Any) -> None:
        """Handle incoming WebSocket messages."""
        match message:
            case PingMessage():
                await self.send_message(PongMessage())
            case GroupChatRefreshRequest():
                await self.refresh_group_chats()
            case _:
                pass

    async def refresh_group_chats(self) -> None:
        """Send a signal to refresh the group chat list via JavaScript."""
        if not self.user or not self.user.is_authenticated:
            return

        # Just send a simple notification that the client should refresh its list via API
        await self.send_json({"action": "refresh_group_chats", "payload": {}})

    async def notify_group_chat_updated(self, event: GroupChatUpdateEvent) -> None:
        """
        Handle notification of a group chat being updated (e.g., new message).

        This is used only to update timestamps, not to modify the group chat list structure.
        For adding/removing users, the application uses REST API calls.

        Args:
            event: The event containing the updated group chat data
        """
        # Extract the payload
        payload = event["payload"]

        # Only forward to the client if they are a member of this group chat
        if not self.user or not self.user.is_authenticated:
            return

        group_id = payload.get("group_id")
        if (
            group_id
            and await GroupChat.objects.filter(
                id=group_id, members__user=self.user
            ).aexists()
        ):
            # Send the notification to the WebSocket client
            await self.send_json({"action": "group_chat_updated", "payload": payload})
