from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import Mock, patch

from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import (
    PongMessage,
)

from assistants.messages.assistant import (
    MessagePayload,
    NewMessage,
    StreamingMessage,
    StreamingPayload,
)
from test_utils.openai_test_utils import (
    OpenAIChatCompletionMockFactory,
    tokenize_for_streaming,
)
from test_utils.testing import WebsocketTestCase


class TestAssistantConsumer(WebsocketTestCase):
    ws_path = "/ws/assistants/"

    async def test_connect_successfully_and_send_and_reply_message(self) -> None:
        # Test basic connection and message flow (no auth required)
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        # No authentication required, should connect directly
        # Test ping/pong
        await self.auth_communicator.send_message(PingMessage())
        all_messages = await self.auth_communicator.receive_all_json()
        assert all_messages == [PongMessage().model_dump()]

    @patch("assistants.consumers.uuid4", return_value="mock-uuid")
    @patch("openai.resources.chat.completions.AsyncCompletions.create")
    async def test_ai_streaming_response(
        self, mock_acreate: Mock, mock_uuid: Mock
    ) -> None:
        """Test AI streaming response with realistic OpenAI mock."""
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        ai_response = "Hello! How can I help you today? Let me know what you need assistance with."

        async def mock_acreate_side_effect(*args: Any, **kwargs: Any) -> Any:
            return OpenAIChatCompletionMockFactory.build(
                content=ai_response,
                streaming=True,
            )

        mock_acreate.side_effect = mock_acreate_side_effect

        # Send a message to trigger AI response
        await self.auth_communicator.send_message(
            NewMessage(payload=MessagePayload(content="Hello AI"))
        )

        # Collect all messages
        all_messages = await self.auth_communicator.receive_all_json()

        expected_streaming_messages = [
            StreamingMessage(
                payload=StreamingPayload(
                    content=token,
                    is_complete=False,
                    message_id="mock-uuid",
                )
            ).model_dump()
            for token in tokenize_for_streaming(ai_response)
        ]

        # Should have received streaming chunks
        assert len(all_messages) > 0

        assert all_messages == [
            *expected_streaming_messages,
            StreamingMessage(
                payload=StreamingPayload(
                    content="",
                    is_complete=True,
                    message_id="mock-uuid",
                )
            ).model_dump(),
        ]

    @patch("assistants.consumers.uuid4", return_value="error-uuid")
    @patch("openai.resources.chat.completions.AsyncCompletions.create")
    async def test_ai_service_error_handling(
        self, mock_acreate: Mock, mock_uuid: Mock
    ) -> None:
        """Test that errors from AI service are handled gracefully."""
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        # Mock an exception from the AI service
        mock_acreate.side_effect = Exception("API connection failed")

        # Send a message that will trigger the error
        await self.auth_communicator.send_message(
            NewMessage(payload=MessagePayload(content="This will fail"))
        )

        # Should receive an error message
        all_messages = await self.auth_communicator.receive_all_json()

        # Should get a ReplyMessage with error
        assert len(all_messages) == 1
        error_message = all_messages[0]
        assert error_message["action"] == "error"
        assert "Error: API connection failed" in error_message["payload"]["content"]

    @patch("assistants.consumers.uuid4", return_value="stream-error-uuid")
    @patch("assistants.services.ai_service.OpenAIService.generate_stream")
    async def test_streaming_error_during_generation(
        self, mock_generate_stream: Mock, mock_uuid: Mock
    ) -> None:
        """Test error handling when streaming generation fails mid-stream."""
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        # Create an async generator that yields some tokens then raises an error
        async def failing_generator() -> AsyncIterator[str]:
            yield "Hello "
            yield "world "
            raise Exception("Streaming failed")

        mock_generate_stream.return_value = failing_generator()

        # Send a message
        await self.auth_communicator.send_message(
            NewMessage(payload=MessagePayload(content="Tell me a story"))
        )

        # Collect all messages
        all_messages = await self.auth_communicator.receive_all_json()

        # Should receive partial streaming messages and then an error
        streaming_messages = [
            msg for msg in all_messages if msg["action"] == "streaming"
        ]
        error_messages = [msg for msg in all_messages if msg["action"] == "error"]

        # Should have received some streaming tokens
        assert len(streaming_messages) == 2  # noqa
        assert streaming_messages[0]["payload"]["content"] == "Hello "
        assert streaming_messages[1]["payload"]["content"] == "world "

        # Should have received an error message
        assert len(error_messages) == 1
        assert "Error: Streaming failed" in error_messages[0]["payload"]["content"]

    @patch("assistants.consumers.uuid4")
    @patch("openai.resources.chat.completions.AsyncCompletions.create")
    async def test_conversation_history_with_two_messages(
        self, mock_acreate: Mock, mock_uuid: Mock
    ) -> None:
        """Test that conversation history is properly maintained when user sends 2 messages."""
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        # Mock different UUIDs for different messages
        mock_uuid.side_effect = ["uuid-1", "uuid-2"]

        # Mock AI responses
        first_response = "Hello! I'm here to help."
        second_response = "Yes, I remember your first message about greetings."

        call_count = 0

        async def mock_acreate_side_effect(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return OpenAIChatCompletionMockFactory.build(
                    content=first_response, streaming=True
                )
            elif call_count == 2:  # noqa
                return OpenAIChatCompletionMockFactory.build(
                    content=second_response, streaming=True
                )

        mock_acreate.side_effect = mock_acreate_side_effect

        # Send first message
        await self.auth_communicator.send_message(
            NewMessage(payload=MessagePayload(content="Hello AI"))
        )
        first_messages = await self.auth_communicator.receive_all_json()

        expected_streaming_first_messages = [
            StreamingMessage(
                payload=StreamingPayload(
                    content=token,
                    is_complete=False,
                    message_id="uuid-1",
                )
            ).model_dump()
            for token in tokenize_for_streaming(first_response)
        ]

        assert first_messages == [
            *expected_streaming_first_messages,
            StreamingMessage(
                payload=StreamingPayload(
                    content="",
                    is_complete=True,
                    message_id="uuid-1",
                )
            ).model_dump(),
        ]

        # Send second message
        await self.auth_communicator.send_message(
            NewMessage(payload=MessagePayload(content="Do you remember what I said?"))
        )
        second_messages = await self.auth_communicator.receive_all_json()
        expected_streaming_second_messages = [
            StreamingMessage(
                payload=StreamingPayload(
                    content=token,
                    is_complete=False,
                    message_id="uuid-2",
                )
            ).model_dump()
            for token in tokenize_for_streaming(second_response)
        ]

        assert second_messages == [
            *expected_streaming_second_messages,
            StreamingMessage(
                payload=StreamingPayload(
                    content="",
                    is_complete=True,
                    message_id="uuid-2",
                )
            ).model_dump(),
        ]
