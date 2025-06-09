from typing import Any

from rest_framework.permissions import IsAuthenticated

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage
from typing_extensions import assert_never

from chat.messages.chat import (
    ChatDetailEvent,
    ChatIncomingMessage,
    MemberAddedMessage,
    MemberRemovedMessage,
    MemberRemovedPayload,
    NewChatMessageEvent,
    NotifyMemberAddedEvent,
    NotifyMemberRemovedEvent,
    UserRemovedFromGroupMessage,
)
from chat.messages.member import MemberMessage
from chat.models import ChatMember, GroupChat
from chat.permissions import IsGroupChatMember
from chat.utils import name_group_chat


class ChatDetailConsumer(
    AsyncJsonWebsocketConsumer[ChatIncomingMessage, ChatDetailEvent, GroupChat]
):
    """WebSocket consumer for group chat details."""

    permission_classes = [IsAuthenticated, IsGroupChatMember]
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
            case _:
                assert_never(message)

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
            case _:
                assert_never(event)

    async def handle_notify_member_remove_event(
        self, payload: MemberRemovedPayload
    ) -> None:
        removed_user_pk = payload.user_pk
        if self.user and str(self.user.pk) == str(removed_user_pk):
            await self.send_message(
                UserRemovedFromGroupMessage(
                    payload=UserRemovedFromGroupMessage.Payload(
                        redirect="/chat/",
                        message="You have been removed from this group chat",
                    )
                )
            )
            return
        await self.send_message(MemberRemovedMessage(payload=payload))
