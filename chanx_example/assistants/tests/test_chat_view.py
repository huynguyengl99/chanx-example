from django.test import TestCase
from django.urls import reverse
from rest_framework import status


class AssistantChatViewTestCase(TestCase):
    """Test cases for AssistantChatView."""

    def setUp(self) -> None:
        self.url = reverse("assistant_chat")

    def test_get_renders_chat_template(self) -> None:
        """Test that GET request renders the chat template."""
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert "assistants/chat.html" in [t.name for t in response.templates]

    def test_contains_required_elements(self) -> None:
        """Test that the rendered page contains required chat elements."""
        response = self.client.get(self.url)
        content = response.content.decode()

        assert "AI Assistant" in content
        assert "chat-container" in content
        assert "chat-messages" in content
        assert "chat-input" in content
        assert "/ws/assistants/" in content

    def test_includes_javascript_libraries(self) -> None:
        """Test that required JavaScript libraries are included."""
        response = self.client.get(self.url)
        content = response.content.decode()

        assert "marked.min.js" in content
        assert "prism-core.min.js" in content
        assert "AssistantChat" in content

    def test_view_accessible_without_authentication(self) -> None:
        """Test that the view is accessible without authentication."""
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
