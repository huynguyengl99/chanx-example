from typing import Any, cast

from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync

from chat.models import ChatMessage
from chat.serializers import ChatMessageSerializer
from chat.utils import name_group_chat

channel_layer = get_channel_layer()


def task_handle_new_chat_message(message_id: int) -> None:
    """
    Handle broadcasting a new chat message to all group members.

    This version uses the standard chanx group messaging system instead
    of a custom message type, reusing the same path as WebSocket messages.

    Args:
        message_id: ID of the new ChatMessage to broadcast
    """
    # Get the message with all related objects
    message = ChatMessage.objects.select_related("group_chat", "sender__user").get(
        id=message_id
    )

    # Serialize the message
    serializer = ChatMessageSerializer(message)
    serialized_data: dict[str, Any] = cast(dict[str, Any], serializer.data)

    # Get the group chat channel name
    chat_group = name_group_chat(message.group_chat.pk)

    # Add additional properties to have the action match what the client expects
    content: dict[str, Any] = {"action": "member_message", "payload": serialized_data}

    # Use the standard group member message format that will be
    # processed by send_group_member in the AsyncJsonWebsocketConsumer
    assert channel_layer
    async_to_sync(channel_layer.group_send)(
        chat_group,
        {
            "type": "send_group_member",
            "content": content,
            "kind": (
                "json"
            ),  # Use "json" since we don't have OUTGOING_GROUP_MESSAGE_SCHEMA
            "exclude_current": False,  # Don't exclude any clients
            "from_channel": "",  # No specific originating channel
            "from_user_pk": message.sender.user.pk if message.sender else None,
        },
    )
