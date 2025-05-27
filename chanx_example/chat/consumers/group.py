from typing import Any, TypedDict

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage

from chat.messages.group import GroupChatMessage
from chat.messages.member import OutgoingMemberMessage
from chat.utils import make_user_groups_layer_name


class GroupChatUpdatePayload(TypedDict):
    """Payload for group chat update notifications."""

    group_pk: int
    updated_at: str


class GroupChatUpdateEvent(TypedDict):
    """Event for group chat update notifications."""

    payload: GroupChatUpdatePayload


class GroupChatConsumer(
    AsyncJsonWebsocketConsumer[GroupChatMessage, None, OutgoingMemberMessage]
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
        return [make_user_groups_layer_name(self.user.pk)]

    async def receive_message(self, message: GroupChatMessage, **kwargs: Any) -> None:
        """Handle incoming WebSocket messages."""
        match message:
            case PingMessage():
                await self.send_message(PongMessage())
            case _:
                pass

    async def notify_added_to_group(self, event: dict[str, Any]) -> None:
        """Handle notification when user is added to a group chat."""
        # Send notification to refresh UI
        await self.send_json({"action": "added_to_group", "payload": event["payload"]})

    async def notify_removed_from_group(self, event: dict[str, Any]) -> None:
        """Handle notification when user is removed from a group chat."""
        # Send notification to refresh UI
        await self.send_json(
            {"action": "removed_from_group", "payload": event["payload"]}
        )

    async def notify_group_chat_updated(self, event: GroupChatUpdateEvent) -> None:
        """
        Handle notification of a group chat being updated (e.g., new message).

        Args:
            event: The event containing the updated group chat data
        """
        # Send the notification to the WebSocket client
        await self.send_json(
            {"action": "group_chat_updated", "payload": event["payload"]}
        )
