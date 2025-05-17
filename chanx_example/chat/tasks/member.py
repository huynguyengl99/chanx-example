from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync

from accounts.models import User
from chat.models import ChatMember, GroupChat
from chat.serializers import ChatMemberSerializer
from chat.utils import name_group_chat

channel_layer = get_channel_layer()


def task_handle_new_group_member(user_id: int, group_chat_id: int) -> None:
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

        if not channel_layer:
            return

        # Send notification to the specific group chat members
        async_to_sync(channel_layer.group_send)(
            chat_group,
            {
                "type": "notify_member_added",
                "payload": {
                    "member": serializer.data,
                },
            },
        )

        # Note: We don't send WebSocket notifications for group list updates here.
        # The UI will use API calls for that.
    except (User.DoesNotExist, GroupChat.DoesNotExist, ChatMember.DoesNotExist):
        # Log error or handle gracefully
        pass


def task_handle_remove_group_member(user_id: int, group_chat_id: int) -> None:
    """
    Handle removing a member from a group chat.

    Args:
        user_id: The user ID of the removed member
        group_chat_id: The group chat ID
    """
    try:
        group_chat = GroupChat.objects.get(id=group_chat_id)
        user = User.objects.get(id=user_id)

        # Get the group chat channel name
        chat_group = name_group_chat(group_chat_id)

        if not channel_layer:
            return

        # Send notification to the specific group chat members
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

        # Note: The removed user will be redirected away from the chat
        # and the group list will update via API call, not WebSocket.
    except (User.DoesNotExist, GroupChat.DoesNotExist):
        # Log error or handle gracefully
        pass
