from typing import cast

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from assistants.models import AssistantConversation, AssistantMessage
from assistants.serializers import (
    AssistantMessageSerializer,
    CreateAssistantMessageSerializer,
)
from assistants.tasks import task_handle_new_assistant_message
from utils.request import AuthenticatedRequest


class AssistantMessageViewSet(ModelViewSet[AssistantMessage]):
    """ViewSet for assistant messages."""

    permission_classes = [
        AllowAny
    ]  # Allow both authenticated and unauthenticated users
    serializer_class = AssistantMessageSerializer

    def get_queryset(self) -> QuerySet[AssistantMessage]:
        """Get messages for the conversation."""
        conversation_id = self.kwargs.get("conversation_pk")

        if conversation_id:
            # For specific conversation
            if self.request.user.is_authenticated:
                # Authenticated user - check ownership
                request = cast(AuthenticatedRequest, self.request)
                conversation = get_object_or_404(
                    AssistantConversation, id=conversation_id, user=request.user
                )
                return conversation.messages.order_by("created_at")
            else:
                # Anonymous user - check if conversation exists and is anonymous
                try:
                    conversation = AssistantConversation.objects.get(
                        id=conversation_id, user__isnull=True  # Anonymous conversation
                    )
                    return conversation.messages.order_by("created_at")
                except AssistantConversation.DoesNotExist:
                    return AssistantMessage.objects.none()

        # No conversation specified
        return AssistantMessage.objects.none()

    def get_serializer_class(self) -> type[BaseSerializer[AssistantMessage]]:
        if self.action == "create":
            return CreateAssistantMessageSerializer
        return AssistantMessageSerializer

    def perform_create(self, serializer: BaseSerializer[AssistantMessage]) -> None:
        """Create a new user message and trigger AI response."""
        conversation_id = self.kwargs.get("conversation_pk")

        if not conversation_id:
            raise ValueError("conversation_pk is required")

        if self.request.user.is_authenticated:
            # Authenticated user with specific conversation
            request = cast(AuthenticatedRequest, self.request)
            conversation = get_object_or_404(
                AssistantConversation, id=conversation_id, user=request.user
            )

            # Save the user message
            user_message = serializer.save(
                conversation=conversation,
                message_type=AssistantMessage.MessageType.USER,
            )

            # Generate title if this is the first message
            if conversation.messages.count() == 1:
                conversation.generate_title_from_first_message()

            # Trigger async task to generate AI response
            task_handle_new_assistant_message(user_message_id=user_message.pk)

        else:
            # Anonymous user
            try:
                conversation = AssistantConversation.objects.get(
                    id=conversation_id,
                    user__isnull=True,  # Must be anonymous conversation
                )

                # Save the user message
                user_message = serializer.save(
                    conversation=conversation,
                    message_type=AssistantMessage.MessageType.USER,
                )

                # Generate title if this is the first message
                if conversation.messages.count() == 1:
                    conversation.generate_title_from_first_message()

                # Trigger async task to generate AI response for anonymous user
                task_handle_new_assistant_message(
                    user_message_id=user_message.pk,
                )

            except AssistantConversation.DoesNotExist:
                raise ValueError("Invalid anonymous conversation") from None
