from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync

from accounts.models import User
from chat.models import ChatMember, GroupChat
from chat.serializers import ChatMemberSerializer
from chat.utils import name_group_chat

channel_layer = get_channel_layer()


def task_handle_new_group_chat_member(user_id: int, group_chat_id: int) -> None:
    """
    Handle adding a new member to a group chat.

    Args:
        user_id: The user ID of the new member
        group_chat_id: The group chat ID
    """
    try:
        group_chat = GroupChat.objects.get(id=group_chat_id)
        user = User.objects.get(id=user_id)

        # Get the member record
        member = ChatMember.objects.get(user=user, group_chat=group_chat)

        # Serialize the member
        serializer = ChatMemberSerializer(member)

        # Get the group chat channel name
        chat_group = name_group_chat(group_chat_id)

        assert channel_layer
        async_to_sync(channel_layer.group_send)(
            chat_group,
            {
                "type": "notify_member_added",
                "payload": {
                    "member": serializer.data,
                },
            },
        )
    except (User.DoesNotExist, GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        # Log error or handle gracefully
        pass


def task_handle_remove_group_chat_member(user_id: int, group_chat_id: int) -> None:
    """
    Handle removing a member from a group chat.

    Args:
        user_id: The user ID of the removed member
        group_chat_id: The group chat ID
    """
    try:
        GroupChat.objects.get(id=group_chat_id)
        user = User.objects.get(id=user_id)

        # Get the group chat channel name
        chat_group = name_group_chat(group_chat_id)

        assert channel_layer
        async_to_sync(channel_layer.group_send)(
            chat_group,
            {
                "type": "notify_member_removed",
                "payload": {
                    "user_id": user_id,
                    "email": user.email,
                },
            },
        )
    except (User.DoesNotExist, GroupChat.DoesNotExist):
        # Log error or handle gracefully
        pass


def task_handle_delete_group_chat(group_chat_id: int) -> None:
    """
    Handle deleting a group chat.

    Args:
        group_chat_id: The group chat ID to delete
    """
    try:
        # Get the group chat channel name
        chat_group = name_group_chat(group_chat_id)

        assert channel_layer
        async_to_sync(channel_layer.group_send)(
            chat_group,
            {
                "type": "notify_group_deleted",
                "payload": {
                    "group_chat_id": group_chat_id,
                },
            },
        )
    except Exception:
        # Log error or handle gracefully
        pass
