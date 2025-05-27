from typing import Any, TypedDict, cast

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage

from chat.messages.chat import (
    ChatIncomingMessage,
    NewChatMessage,
)
from chat.messages.member import MemberMessage, OutgoingMemberMessage
from chat.models import ChatMember, ChatMessage, GroupChat
from chat.permissions import IsGroupChatMember
from chat.serializers import ChatMessageSerializer
from chat.utils import name_group_chat


# Define TypedDict classes for different event payloads
class MemberAddedPayload(TypedDict):
    member: dict[str, Any]


class MemberRemovedPayload(TypedDict):
    user_id: int
    email: str


class GroupDeletedPayload(TypedDict):
    group_chat_id: int


# Define TypedDict classes for different event types
class MemberAddedEvent(TypedDict):
    payload: MemberAddedPayload


class MemberRemovedEvent(TypedDict):
    payload: MemberRemovedPayload


class GroupDeletedEvent(TypedDict):
    payload: GroupDeletedPayload


class ChatDetailConsumer(
    AsyncJsonWebsocketConsumer[
        ChatIncomingMessage, None, OutgoingMemberMessage, GroupChat
    ]
):
    """WebSocket consumer for group chat details."""

    permission_classes = [IsGroupChatMember]
    queryset = GroupChat.objects.get_queryset()

    member: ChatMember

    async def build_groups(self) -> list[str]:
        """Build the list of groups to join."""
        assert self.obj
        self.group_name = name_group_chat(self.obj.pk)
        return [self.group_name]

    async def post_authentication(self) -> None:
        """Set up after authentication."""
        assert self.user is not None
        assert self.obj
        self.member = await self.obj.members.select_related("user").aget(user=self.user)

    async def receive_message(
        self, message: ChatIncomingMessage, **kwargs: Any
    ) -> None:
        """Handle incoming WebSocket messages."""
        match message:
            case PingMessage():
                await self.send_message(PongMessage())
            case NewChatMessage(payload=message_payload):
                assert self.obj
                new_message = await ChatMessage.objects.acreate(
                    content=message_payload.content,
                    group_chat_id=self.obj.pk,
                    sender=self.member,
                )
                groups = message_payload.groups

                message_serializer = ChatMessageSerializer(
                    instance=new_message, context={"request": self.request}
                )

                await self.send_group_message(
                    MemberMessage(payload=cast(Any, message_serializer.data)),
                    groups=groups,
                    exclude_current=False,
                )
            case _:
                pass

    async def notify_member_added(self, event: MemberAddedEvent) -> None:
        """
        Handle member added event sent via the channel layer.

        Args:
            event: The event data containing the member payload
        """
        # Extract the payload
        payload = event["payload"]

        # Send the notification to the WebSocket client
        await self.send_json(
            {
                "action": "member_added",
                "payload": payload,
            }
        )

    async def notify_member_removed(self, event: MemberRemovedEvent) -> None:
        """
        Handle member removed event sent via the channel layer.

        Args:
            event: The event data containing the member payload
        """
        # Extract the payload
        payload = event["payload"]
        removed_user_id = payload.get("user_id")

        # Check if the removed user is the current user
        if self.user and str(self.user.pk) == str(removed_user_id):
            # Send notification to client to redirect
            await self.send_json(
                {
                    "action": "user_removed_from_group",
                    "payload": {
                        "redirect": "/api/chat/page/",  # Redirect to home page
                        "message": "You have been removed from this group chat",
                    },
                }
            )

            # Close the connection
            await self.close()
            return

        # If it's another user being removed, just notify
        await self.send_json(
            {
                "action": "member_removed",
                "payload": payload,
            }
        )

    async def notify_group_deleted(self, event: GroupDeletedEvent) -> None:
        """
        Handle group deleted event sent via the channel layer.

        Args:
            event: The event data
        """
        # Send the notification to the WebSocket client
        await self.send_json(
            {
                "action": "group_deleted",
                "payload": event["payload"],
            }
        )

        # Close the connection
        await self.close()
