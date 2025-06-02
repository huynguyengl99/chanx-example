import sys

from rest_framework import status

from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import PongMessage

from chat.consumers.chat_detail import ChatDetailConsumer
from chat.factories.chat_member import ChatMemberFactory
from chat.messages.chat import (
    MemberRemovedPayload,
    NewChatMessageEvent,
    NotifyMemberAddedEvent,
    NotifyMemberRemovedEvent,
)
from chat.models import GroupChat
from test_utils.testing import WebsocketTestCase

if sys.version_info < (3, 11):  # pragma: no cover
    pass


class TestChatDetailConsumer(WebsocketTestCase):
    """Unit tests for ChatDetailConsumer - focuses on consumer event handling logic"""

    def setUp(self) -> None:
        super().setUp()
        # Create a group chat for testing
        self.group_chat = GroupChat.objects.create(title="Test Group Chat")

        # Add the authenticated user as a member
        ChatMemberFactory.create(user=self.user, group_chat=self.group_chat)

        self.ws_path = f"/ws/chat/{self.group_chat.pk}/"

    async def test_connect_successfully_and_ping(self) -> None:
        """Test basic connection and ping/pong functionality"""
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        await self.auth_communicator.send_message(PingMessage())

        all_messages = await self.auth_communicator.receive_all_json()
        assert all_messages == [PongMessage().model_dump()]

    async def test_unauthorized_access(self) -> None:
        """Test that non-members cannot connect to the chat"""
        # Create a new user who is not a member of the group chat
        _, non_member_headers = await self.acreate_user_and_ws_headers()

        non_member_communicator = self.create_communicator(headers=non_member_headers)

        # Try to connect - this should fail
        await non_member_communicator.connect()

        # Check authentication response
        auth = await non_member_communicator.wait_for_auth(max_auth_time=1000)
        assert auth
        assert auth.payload.status_code == status.HTTP_403_FORBIDDEN

        # Connection should be closed
        await non_member_communicator.assert_closed()

    async def test_notify_member_add_event(self) -> None:
        """Test consumer handles member addition events correctly"""
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        # Create test member data (using dict as per the message model)
        test_member_payload = {
            "id": 123,
            "user": "newmember@example.com",
            "chat_role": 2003,  # ChatMemberRole.MEMBER
        }

        # Send member added event directly to test consumer's event handling
        await ChatDetailConsumer.asend_channel_event(
            f"group_chat.{self.group_chat.pk}",
            NotifyMemberAddedEvent(payload=test_member_payload),
        )

        # Verify consumer processed and forwarded the event correctly
        all_messages = await self.auth_communicator.receive_all_json()

        assert len(all_messages) == 1
        message = all_messages[0]
        assert message["action"] == "member_added"
        assert message["payload"] == test_member_payload

    async def test_notify_member_remove_event_other_user(self) -> None:
        """Test consumer handles member removal events for other users"""
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        # Create test payload for removing another user using proper model
        removed_user_payload = MemberRemovedPayload(
            user_pk=999, email="removed@example.com"  # Different from self.user.pk
        )

        # Send member removed event
        await ChatDetailConsumer.asend_channel_event(
            f"group_chat.{self.group_chat.pk}",
            NotifyMemberRemovedEvent(payload=removed_user_payload),
        )

        # Should receive member_removed message (not user_removed_from_group)
        all_messages = await self.auth_communicator.receive_all_json()

        assert len(all_messages) == 1
        message = all_messages[0]
        assert message["action"] == "member_removed"
        assert message["payload"]["user_pk"] == 999
        assert message["payload"]["email"] == "removed@example.com"

    async def test_notify_member_remove_event_self_removal(self) -> None:
        """Test consumer handles self-removal correctly (closes connection)"""
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        # Create test payload for removing the current user using proper model
        self_removal_payload = MemberRemovedPayload(
            user_pk=self.user.pk, email=self.user.email  # Same as connected user
        )

        # Send member removed event for current user
        await ChatDetailConsumer.asend_channel_event(
            f"group_chat.{self.group_chat.pk}",
            NotifyMemberRemovedEvent(payload=self_removal_payload),
        )

        # Should receive user_removed_from_group message and connection closes
        all_messages = await self.auth_communicator.receive_all_json()

        assert len(all_messages) == 1
        message = all_messages[0]
        assert message["action"] == "user_removed_from_group"
        assert message["payload"]["redirect"] == "/chat/"
        assert "removed" in message["payload"]["message"]

    async def test_new_chat_message_event_own_message(self) -> None:
        """Test consumer handles new chat message events for own messages"""
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        # Create test message data
        test_message_data = {
            "id": 456,
            "content": "Hello everyone!",
            "sender": {"user": self.user.email},
            "created_at": "2023-01-01T12:00:00Z",
        }

        # Create proper payload using the Pydantic model
        test_payload = NewChatMessageEvent.Payload(
            message_data=test_message_data,
            user_pk=self.user.pk,  # Same as connected user
        )

        # Send new message event
        await ChatDetailConsumer.asend_channel_event(
            f"group_chat.{self.group_chat.pk}",
            NewChatMessageEvent(payload=test_payload),
        )

        # Should receive member_message with is_mine=True
        all_messages = await self.auth_communicator.receive_all_json()

        assert len(all_messages) == 1
        message = all_messages[0]
        assert message["action"] == "member_message"
        assert message["payload"] == test_message_data
        assert message["is_mine"] is True
        assert message["is_current"] is False

    async def test_new_chat_message_event_other_user_message(self) -> None:
        """Test consumer handles new chat message events from other users"""
        await self.auth_communicator.connect()
        await self.auth_communicator.assert_authenticated_status_ok()

        # Create test message data from another user
        test_message_data = {
            "id": 789,
            "content": "Hi there!",
            "sender": {"user": "other@example.com"},
            "created_at": "2023-01-01T12:05:00Z",
        }

        # Create proper payload using the Pydantic model
        test_payload = NewChatMessageEvent.Payload(
            message_data=test_message_data, user_pk=888  # Different from self.user.pk
        )

        # Send new message event
        await ChatDetailConsumer.asend_channel_event(
            f"group_chat.{self.group_chat.pk}",
            NewChatMessageEvent(payload=test_payload),
        )

        # Should receive member_message with is_mine=False
        all_messages = await self.auth_communicator.receive_all_json()

        assert len(all_messages) == 1
        message = all_messages[0]
        assert message["action"] == "member_message"
        assert message["payload"] == test_message_data
        assert message["is_mine"] is False
        assert message["is_current"] is False
