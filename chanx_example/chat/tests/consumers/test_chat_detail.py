import sys

from rest_framework import status

from chanx.messages.incoming import PingMessage
from chanx.messages.outgoing import (
    PongMessage,
)

from chat.models import GroupChat
from test_utils.testing import WebsocketTestCase

if sys.version_info < (3, 11):  # pragma: no cover
    pass


class TestChatDetailConsumer(WebsocketTestCase):
    def setUp(self) -> None:
        super().setUp()
        # Create a group chat for testing
        # Add the authenticated user as a member
        self.group_chat = GroupChat.objects.create(title="Test Group Chat")
        self.group_chat.users.add(self.user)

        self.ws_path = f"/ws/chat/{self.group_chat.pk}/"

    async def test_connect_successfully_and_ping(self) -> None:
        await self.auth_communicator.connect()

        await self.auth_communicator.assert_authenticated_status_ok()

        await self.auth_communicator.send_message(PingMessage())

        # Receive the message that was broadcast
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

    async def test_notify_member_add_event(self):
        pass
