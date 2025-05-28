from typing import Any, cast

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage

from chat.messages.chat import (
    ChatDetailEvent,
    ChatIncomingMessage,
    MemberAddedMessage,
    MemberRemovedMessage,
    MemberRemovedPayload,
    NewChatMessage,
    NewChatMessageEvent,
    NotifyMemberAddedEvent,
    NotifyMemberRemovedEvent,
    UserRemovedFromGroupMessage,
)
from chat.messages.member import MemberMessage, OutgoingMemberMessage
from chat.models import ChatMember, ChatMessage, GroupChat
from chat.permissions import IsGroupChatMember
from chat.serializers import ChatMessageSerializer
from chat.utils import name_group_chat


class ChatDetailConsumer(
    AsyncJsonWebsocketConsumer[
        ChatIncomingMessage, ChatDetailEvent, OutgoingMemberMessage, GroupChat
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

    async def receive_event(self, event: ChatDetailEvent) -> None:
        match event:
            case NotifyMemberAddedEvent(payload=payload):
                await self.send_message(MemberAddedMessage(payload=payload))
            case NotifyMemberRemovedEvent(payload=payload):
                await self.handle_notify_member_remove_event(payload)
            case NewChatMessageEvent(payload=payload):
                assert self.user is not None
                await self.send_message(
                    MemberMessage(
                        payload=payload.message_data,
                        is_mine=self.user.pk == payload.user_pk,
                        is_current=False,
                    )
                )

    async def handle_notify_member_remove_event(
        self, payload: MemberRemovedPayload
    ) -> None:
        removed_user_pk = payload.user_pk
        if self.user and str(self.user.pk) == str(removed_user_pk):
            await self.send_message(
                UserRemovedFromGroupMessage(
                    payload=UserRemovedFromGroupMessage.Payload(
                        redirect="/api/chat/page/",
                        message="You have been removed from this group chat",
                    )
                )
            )
            await self.close()
            return
        await self.send_message(MemberRemovedMessage(payload=payload))
