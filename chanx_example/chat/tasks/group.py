from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync

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
        async_to_sync(channel_layer.group_send)(
            "group_chat_updates",
            {
                "type": "notify_group_chat_updated",
                "payload": {
                    "group_pk": group_chat.pk,
                    "updated_at": group_chat.updated_at.isoformat(),
                },
            },
        )
    except GroupChat.DoesNotExist:
        # Log error or handle gracefully
        pass


def task_handle_group_chat_create(group_chat_id: int) -> None:
    """
    Handle notifying users that a new group chat has been created.

    This doesn't use WebSockets directly - it just sends a notification
    to refresh the group list via API. For real-time updates, the UI will
    make an API call to refresh the list.

    Args:
        group_chat_id: ID of the newly created group chat
    """
    # No WebSocket notification needed - users will refresh via API
    pass


def task_handle_group_chat_delete(group_chat_id: int) -> None:
    """
    Handle notifying users that a group chat has been deleted.

    This doesn't use WebSockets directly - when users try to access
    a deleted group chat, they'll be redirected to the group list.

    Args:
        group_chat_id: ID of the deleted group chat
    """
    # No WebSocket notification needed - users will refresh via API
    pass
