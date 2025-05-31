from channels.layers import get_channel_layer

from chat.consumers.group import GroupChatConsumer
from chat.messages.group import GroupChatUpdatePayload, NotifyGroupChatUpdateEvent
from chat.models import GroupChat

channel_layer = get_channel_layer()


def task_handle_group_chat_update(group_chat_id: int) -> None:
    """
    Handle broadcasting group chat updates to all members.

    This function notifies all users connected to the group_chat_updates group
    that a group chat has been updated, triggering timestamp updates in the UI.

    Args:
        group_chat_id: ID of the updated group chat
    """
    try:
        group_chat = GroupChat.objects.get(id=group_chat_id)

        if not channel_layer:
            return

        # Broadcast to the group_chat_updates group

        GroupChatConsumer.send_channel_event(
            "group_chat_updates",
            NotifyGroupChatUpdateEvent(
                payload=GroupChatUpdatePayload(
                    group_pk=group_chat.pk,
                    updated_at=group_chat.updated_at.isoformat(),
                )
            ),
        )

    except GroupChat.DoesNotExist:
        # Log error or handle gracefully
        pass
