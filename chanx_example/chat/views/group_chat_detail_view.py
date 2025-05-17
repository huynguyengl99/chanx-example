from typing import cast

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import GroupChat
from chat.permissions import IsGroupChatMember
from utils.request import AuthenticatedRequest


class GroupChatDetailView(APIView):
    """View for the chat interface using DRF APIView."""

    renderer_classes = [TemplateHTMLRenderer]
    template_name = "chat/group_chat.html"
    permission_classes = [IsAuthenticated, IsGroupChatMember]

    def get(self, request: Request, pk: int) -> Response:
        """Handle GET requests to display the chat interface."""
        # Get the group chat
        group_chat = get_object_or_404(GroupChat, pk=pk)

        # Get all user's chats for the sidebar
        request_auth = cast(AuthenticatedRequest, request)
        user_chats = GroupChat.objects.filter(members__user=request_auth.user).order_by(
            "title"
        )

        # Return the rendered template with context
        return Response(
            {
                "group_chat": group_chat,
                "user_chats": user_chats,
            }
        )
