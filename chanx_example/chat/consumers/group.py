from typing import Any, assert_never

from rest_framework.permissions import IsAuthenticated

from asgiref.sync import sync_to_async
from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage

from accounts.models import User
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
from chat.models import GroupChat
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

    permission_classes = [IsAuthenticated]
    user: User | None

    async def build_groups(self) -> list[str]:
        """
        Build groups to join based on user authentication and group memberships.

        Returns:
            List of channel group names to join
        """
        if not self.user or not self.user.is_authenticated:
            return []

        assert self.user.pk

        groups = [
            make_user_groups_layer_name(self.user.pk),  # Personal notifications
        ]

        # Add groups for each chat the user is a member of
        user_group_chats = await sync_to_async(
            lambda: list(
                GroupChat.objects.filter(members__user=self.user).values_list(
                    "pk", flat=True
                )
            )
        )()

        for group_chat_id in user_group_chats:
            groups.append(f"group_chat_{group_chat_id}_updates")

        return groups

    async def receive_message(self, message: GroupChatMessage, **kwargs: Any) -> None:
        """Handle incoming WebSocket messages."""
        match message:
            case PingMessage():
                await self.send_message(PongMessage())
            case _:
                assert_never(message)

    async def receive_event(self, event: GroupChatEvent) -> None:
        """Handle incoming WebSocket events."""
        match event:
            case NotifyAddedToGroupEvent(payload=payload):
                # User was added to a group - subscribe to that group's updates
                group_id = payload.get("id")
                await self.channel_layer.group_add(
                    f"group_chat_{group_id}_updates", self.channel_name
                )
                await self.send_message(AddedToGroupMessage(payload=payload))

            case NotifyRemovedFromGroupEvent(payload=payload):
                # User was removed from a group - unsubscribe from that group's updates
                group_id = payload.group_pk
                await self.channel_layer.group_discard(
                    f"group_chat_{group_id}_updates", self.channel_name
                )
                await self.send_message(RemovedFromGroupMessage(payload=payload))

            case NotifyGroupChatUpdateEvent(payload=payload):
                await self.send_message(GroupChatUpdatedMessage(payload=payload))

            case _:
                assert_never(event)
