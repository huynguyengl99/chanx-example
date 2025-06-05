import logging
from dataclasses import dataclass
from typing import Any, cast

from channels.layers import get_channel_layer

from assistants.consumers import ConversationAssistantConsumer
from assistants.messages.assistant import (
    NewAssistantMessageEvent,
    StreamingEvent,
    StreamingPayload,
)
from assistants.models import AssistantConversation, AssistantMessage
from assistants.serializers import AssistantMessageSerializer
from assistants.services.ai_service import ConversationMessage, OpenAIService

channel_layer = get_channel_layer()
logger = logging.getLogger(__name__)


@dataclass
class StreamingContext:
    """Context data for streaming AI response generation."""

    user_content: str
    history: list[ConversationMessage]
    channel_name: str
    message_id: str


def _get_conversation_history(
    conversation: AssistantConversation,
) -> list[ConversationMessage]:
    conversation_history = list(
        conversation.messages.order_by("created_at").values("content", "message_type")
    )
    # Convert to OpenAI format (exclude current message)
    formatted_history: list[ConversationMessage] = []
    for msg in conversation_history[:-1]:
        role = "user" if msg["message_type"] == "user" else "assistant"
        formatted_history.append({"role": role, "content": msg["content"]})
    return formatted_history


def get_channel_name(conversation: AssistantConversation) -> str:
    conversation_id = conversation.pk
    # Determine if this is an authenticated or anonymous conversation
    is_anonymous = conversation.user is None
    # Build channel name based on conversation type
    if is_anonymous:
        channel_name = f"anonymous_{conversation_id}"
    else:
        user_id = conversation.user.pk if conversation.user else None
        if user_id is None:
            raise ValueError("User ID cannot be None for authenticated conversation")
        channel_name = f"user_{user_id}_conversation_{conversation_id}"
    return channel_name


def task_handle_new_assistant_message(user_message_id: int) -> None:
    """
    Handle a new user message and generate AI response.
    Works for both authenticated and anonymous conversations.

    Args:
        user_message_id: ID of the user message to respond to
    """
    assert channel_layer is not None

    # Get the user message and conversation
    user_message = AssistantMessage.objects.select_related("conversation").get(
        id=user_message_id
    )
    conversation = user_message.conversation
    channel_name = get_channel_name(conversation)

    # Get conversation history
    formatted_history = _get_conversation_history(conversation)

    # Broadcast the user message first
    message_serializer = AssistantMessageSerializer(user_message)
    message_data = cast(dict[str, Any], message_serializer.data)

    # Create streaming context
    context = StreamingContext(
        user_content=user_message.content,
        history=formatted_history,
        channel_name=channel_name,
        message_id=str(user_message_id),
    )

    # Generate and stream AI response
    ConversationAssistantConsumer.send_channel_event(
        channel_name,
        NewAssistantMessageEvent(payload=message_data),
    )

    complete_msg = _generate_streaming_response(context)

    AssistantMessage.objects.create(
        conversation=conversation,
        content=complete_msg,
        message_type=AssistantMessage.MessageType.ASSISTANT,
    )


def _generate_streaming_response(context: StreamingContext) -> str:
    """Generate streaming AI response and broadcast chunks."""
    complete_response = ""

    ai_service = OpenAIService()

    # Generate streaming response
    for token in ai_service.generate_stream(context.user_content, context.history):
        complete_response += token

        # Send streaming chunk
        ConversationAssistantConsumer.send_channel_event(
            context.channel_name,
            StreamingEvent(
                payload=StreamingPayload(
                    content=token,
                    is_complete=False,
                    message_id=context.message_id,
                )
            ),
        )

    # Send completion signal
    ConversationAssistantConsumer.send_channel_event(
        context.channel_name,
        StreamingEvent(
            payload=StreamingPayload(
                content="",
                is_complete=True,
                message_id=context.message_id,
            )
        ),
    )

    return complete_response
