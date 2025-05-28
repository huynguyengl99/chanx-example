from channels.layers import get_channel_layer

from accounts.models import User
from chat.consumers.chat_detail import ChatDetailConsumer
from chat.consumers.group import GroupChatConsumer
from chat.messages.chat import (
    MemberRemovedPayload,
    NotifyMemberAddedEvent,
    NotifyMemberRemovedEvent,
)
from chat.messages.group import (
    GroupRemovePayload,
    NotifyAddedToGroupEvent,
    NotifyRemovedFromGroupEvent,
)
from chat.models import ChatMember, GroupChat
from chat.serializers import GroupChatSerializer, ManageChatMemberSerializer
from chat.utils import make_user_groups_layer_name, name_group_chat

channel_layer = get_channel_layer()

assert channel_layer


def task_handle_new_group_member(user_id: int, group_chat_id: int) -> None:
    """
    Notify a user when they are added to a group chat.

    Args:
        user_id: The user ID of the new member
        group_chat_id: The group chat ID
    """
    try:
        # Get the group chat data for the notification
        group_chat = GroupChat.objects.get(id=group_chat_id)
        group_serializer = GroupChatSerializer(group_chat)

        # Find the member
        member = ChatMember.objects.get(user_id=user_id, group_chat_id=group_chat_id)
        member_serializer = ManageChatMemberSerializer(member)

        if not channel_layer:
            return

        # 1. Notify the added user through their personal channel
        user_group = make_user_groups_layer_name(user_id)
        GroupChatConsumer.send_channel_event(
            user_group,
            NotifyAddedToGroupEvent(
                payload=group_serializer.data,  # pyright: ignore[reportUnknownArgumentType]
            ),
        )

        # 2. Notify the chat detail page (for users already viewing that page)
        chat_group = name_group_chat(group_chat_id)

        ChatDetailConsumer.send_channel_event(
            chat_group,
            NotifyMemberAddedEvent(
                payload=member_serializer.data  # pyright: ignore[reportUnknownArgumentType]
            ),
        )
    except Exception:
        # Log error or handle gracefully
        pass


def task_handle_remove_group_member(user_id: int, group_chat_id: int) -> None:
    """
    Notify a user when they are removed from a group chat.

    Args:
        user_id: The user ID of the removed member
        group_chat_id: The group chat ID
    """
    if not channel_layer:
        return

    try:
        # Try to get the group chat and user info
        group_chat = GroupChat.objects.get(id=group_chat_id)
        user = User.objects.get(id=user_id)

        # 1. Notify the removed user through their personal channel
        user_group = make_user_groups_layer_name(user_id)
        GroupChatConsumer.send_channel_event(
            user_group,
            NotifyRemovedFromGroupEvent(
                payload=GroupRemovePayload(
                    group_pk=group_chat.pk, group_title=group_chat.title
                ),
            ),
        )

        # 2. Also notify the chat detail page (for other users viewing that page)
        chat_group = name_group_chat(group_chat_id)
        ChatDetailConsumer.send_channel_event(
            chat_group,
            NotifyMemberRemovedEvent(
                payload=MemberRemovedPayload(
                    user_pk=user_id,
                    email=user.email,
                )
            ),
        )
    except (GroupChat.DoesNotExist, User.DoesNotExist):
        # Even if objects don't exist, still try to notify the user if possible
        try:
            user_group = make_user_groups_layer_name(user_id)
            GroupChatConsumer.send_channel_event(
                user_group,
                NotifyRemovedFromGroupEvent(
                    payload=GroupRemovePayload(group_pk=group_chat_id, group_title=""),
                ),
            )
        except Exception:
            pass
    except Exception:
        # Log other errors
        pass
