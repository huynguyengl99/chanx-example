from typing import Any
from uuid import uuid4

from rest_framework.permissions import AllowAny

from chanx.generic.websocket import AsyncJsonWebsocketConsumer
from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import ErrorMessage, PongMessage

from assistants.messages.assistant import (
    AssistantMessage,
    MessagePayload,
    NewMessage,
    StreamingMessage,
    StreamingPayload,
)
from assistants.services.ai_service import ConversationMessage, OpenAIService


class AssistantConsumer(AsyncJsonWebsocketConsumer[AssistantMessage]):
    """Websocket to chat with AI assistant with streaming support."""

    authentication_classes = []
    permission_classes = [AllowAny]

    log_ignored_actions = {"streaming"}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.openai_service = OpenAIService()
        self.conversation_history: list[ConversationMessage] = []

    async def receive_message(self, message: AssistantMessage, **kwargs: Any) -> None:
        match message:
            case PingMessage():
                # Reply with a PONG message
                await self.send_message(PongMessage())
            case NewMessage(payload=new_message_payload):
                # Generate streaming AI response
                await self._handle_ai_message(new_message_payload)

    async def _handle_ai_message(self, payload: MessagePayload) -> None:
        """Handle AI message with streaming response."""
        # Generate unique message ID for this conversation
        message_id = str(uuid4())

        # Add user message to conversation history
        user_message: ConversationMessage = {"role": "user", "content": payload.content}
        self.conversation_history.append(user_message)

        # Track the complete response for final message
        complete_response = ""

        try:
            # Stream AI response
            async for token in self.openai_service.generate_stream(
                payload.content,
                self.conversation_history[
                    :-1
                ],  # Exclude the current message from history
            ):
                complete_response += token

                # Send streaming chunk
                await self.send_message(
                    StreamingMessage(
                        payload=StreamingPayload(
                            content=token,
                            is_complete=False,
                            message_id=message_id,
                        )
                    )
                )

            # Add assistant response to conversation history
            assistant_message: ConversationMessage = {
                "role": "assistant",
                "content": complete_response,
            }
            self.conversation_history.append(assistant_message)

            # Send completion signal
            await self.send_message(
                StreamingMessage(
                    payload=StreamingPayload(
                        content="",
                        is_complete=True,
                        message_id=message_id,
                    )
                )
            )

        except Exception as e:
            # Remove the user message from history since we couldn't process it
            await self.send_message(
                ErrorMessage(payload=MessagePayload(content=f"Error: {str(e)}"))
            )
