from typing import cast

from django.urls import reverse
from rest_framework import status

from accounts.factories.user import UserFactory
from chat.factories.group_chat import GroupChatFactory
from chat.models import ChatMember, ChatMessage, GroupChat
from test_utils.auth_api_test_case import AuthAPITestCase


class GroupChatDetailViewTestCase(AuthAPITestCase):
    """Test case for GroupChatDetailView (Chat Detail Page)."""

    def setUp(self) -> None:
        super().setUp()

        # Create a group chat that the user is a member of
        self.group_chat = GroupChatFactory.create(title="Test Chat")
        self.chat_member = ChatMember.objects.create(
            user=self.user,
            group_chat=self.group_chat,
            chat_role=ChatMember.ChatMemberRole.MEMBER,
            nick_name=self.user.email,
        )

        # Create some sample messages
        self.message = ChatMessage.objects.create(
            group_chat=self.group_chat,
            sender=self.chat_member,
            content="Test message content",
        )

        # URL for the detail view
        self.url = reverse("chat-group-detail", kwargs={"pk": self.group_chat.pk})

    def test_get_chat_detail_as_member(self) -> None:
        """Test that a member can access the chat detail page."""
        # Make the request
        response = self.auth_client.get(self.url)

        # Verify response
        assert response.status_code == status.HTTP_200_OK

        # Check that the template was rendered
        assert "chat/group_chat.html" in [t.name for t in response.templates]

        # Check that the group chat is in the context
        group_chat = response.context.get("group_chat")
        assert group_chat is not None
        assert group_chat.title == "Test Chat"

        # Check that the user's chats list is in the context
        user_chats = response.context.get("user_chats")
        assert user_chats is not None
        assert len(user_chats) == 1
        assert user_chats[0].title == "Test Chat"

    def test_get_chat_detail_unauthenticated(self) -> None:
        """Test that an unauthenticated user cannot access the chat detail page."""
        # Make the request with unauthenticated client
        response = self.client.get(self.url)

        # Verify that we get an unauthorized response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_chat_detail_as_non_member(self) -> None:
        """Test that a non-member cannot access the chat detail page."""
        # Create a new user who is not a member of the group chat
        other_user = UserFactory.create()
        other_client = self.get_client_for_user(other_user)

        # Make the request
        response = other_client.get(self.url)

        # Verify the user cannot access the chat detail page
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_chat_detail_page_contains_required_elements(self) -> None:
        """Test that the chat detail page contains all required UI elements."""
        # Make the request
        response = self.auth_client.get(self.url)
        content = response.content.decode()

        # Check for important UI elements
        assert self.group_chat.title in content
        assert "My Chats" in content
        assert "Members" in content

        # Check for message-related elements
        assert "messagesContainer" in content or "messages" in content
        assert "messageForm" in content
        assert "messageInput" in content
        assert "messageTemplate" in content

        # Check for WebSocket connection elements
        assert "connectionStatus" in content
        assert "connectWebSocket" in content
        assert "socket = new WebSocket" in content
        assert f"groupId = {self.group_chat.pk}" in content

        # Check for message handling functions
        assert "loadMessages" in content
        assert "sendMessage" in content
        assert "addMessageToUI" in content

    def test_chat_detail_url_with_invalid_id(self) -> None:
        """Test accessing the chat detail page with an invalid group chat ID."""
        # URL for a nonexistent group chat
        url = reverse("chat-group-detail", kwargs={"pk": 99999})

        # Make the request
        response = self.auth_client.get(url)

        # Verify response - should return 403 or 404 (depends on permission check order)
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_chat_detail_with_multiple_members(self) -> None:
        """Test chat detail page with multiple chat members."""
        # Add another user to the group chat
        other_user = UserFactory.create(email="other@mail.com")
        ChatMember.objects.create(
            user=other_user,
            group_chat=self.group_chat,
            chat_role=ChatMember.ChatMemberRole.MEMBER,
            nick_name=other_user.email,
        )

        # Make the request
        response = self.auth_client.get(self.url)

        # Verify response
        assert response.status_code == status.HTTP_200_OK

        # Get the group chat object
        group_chat = cast(GroupChat, response.context.get("group_chat"))

        # Verify the group chat has two members
        assert group_chat.members.count() == 2
