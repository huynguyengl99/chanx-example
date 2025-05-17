from typing import cast

from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from chat.models import ChatMember, GroupChat
from chat.permissions import (
    CanRemoveChatMember,
    IsGroupChatManagerOrReadOnly,
    IsGroupChatMember,
)
from chat.tasks import (
    task_handle_new_group_chat_member,
    task_handle_remove_group_chat_member,
)
from utils.request import AuthenticatedRequest


class GroupMemberManagementView(APIView):
    """View to manage group chat members using DRF APIView."""

    renderer_classes = [TemplateHTMLRenderer]
    template_name = "chat/group_members.html"
    # Already check permission in permission_classes
    permission_classes = [
        IsAuthenticated,
        IsGroupChatMember,
        IsGroupChatManagerOrReadOnly,
    ]

    def get_django_request(self, request: Request) -> HttpRequest:
        """Helper method to get Django HttpRequest for messages."""
        return cast(HttpRequest, request)

    def add_message(self, request: Request, level: int, message: str) -> None:
        """Helper method to add messages to the request."""
        django_request = self.get_django_request(request)
        messages.add_message(django_request, level, message)

    def get(self, request: Request, pk: int) -> Response:
        """Handle GET requests to display group members."""
        # Get the group chat
        group_chat = get_object_or_404(GroupChat, pk=pk)

        # Get the current user's membership
        request_auth = cast(AuthenticatedRequest, request)
        user_member = ChatMember.objects.get(
            user=request_auth.user, group_chat=group_chat
        )

        # Check if user is at least admin to manage
        can_manage = user_member.chat_role <= ChatMember.ChatMemberRole.ADMIN

        # Return the rendered template with context
        return Response(
            {
                "group_chat": group_chat,
                "members": group_chat.members.select_related("user").all(),
                "user_member": user_member,
                "can_manage": can_manage,
                "roles": ChatMember.ChatMemberRole,
            }
        )

    def post(self, request: Request, pk: int) -> HttpResponseRedirect:
        """Handle POST requests to add a new member."""
        # Permission is already checked by permission_classes
        group_chat = get_object_or_404(GroupChat, pk=pk)

        # Process the form
        data = request.data
        email = str(data.get("email", ""))
        role_value = data.get("role", ChatMember.ChatMemberRole.MEMBER)
        role = int(role_value)

        # Don't allow adding owners
        if role == ChatMember.ChatMemberRole.OWNER:
            self.add_message(request, messages.ERROR, "Cannot add new owners")
            return redirect("group_members", pk=group_chat.pk)

        try:
            # Find the user by email
            user = User.objects.get(email=email)

            # Create the chat member
            ChatMember.objects.create(
                user=user,
                group_chat=group_chat,
                chat_role=role,
                nick_name=user.email,
            )

            # Trigger task to handle WebSocket notification
            task_handle_new_group_chat_member(user.pk, group_chat.pk)

            self.add_message(
                request, messages.SUCCESS, f"Added {user.email} to the group chat"
            )
        except User.DoesNotExist:
            self.add_message(
                request, messages.ERROR, f"User with email {email} not found"
            )
        except IntegrityError:
            self.add_message(
                request,
                messages.ERROR,
                f"User {email} is already a member of this group chat",
            )

        return redirect("group_members", pk=group_chat.pk)


class RemoveMemberView(APIView):
    """View to remove a member from a group chat using DRF APIView."""

    permission_classes = [IsAuthenticated, IsGroupChatMember, CanRemoveChatMember]

    def get_django_request(self, request: Request) -> HttpRequest:
        """Helper method to get Django HttpRequest for messages."""
        return cast(HttpRequest, request)

    def add_message(self, request: Request, level: int, message: str) -> None:
        """Helper method to add messages to the request."""
        django_request = self.get_django_request(request)
        messages.add_message(django_request, level, message)

    def get(self, request: Request, pk: int, member_id: int) -> HttpResponseRedirect:
        """Handle GET requests to remove a member."""
        group_chat = get_object_or_404(GroupChat, pk=pk)
        member_to_remove = get_object_or_404(
            ChatMember, pk=member_id, group_chat=group_chat
        )

        # Save user ID and email before deleting
        user_id = member_to_remove.user.pk
        user_email = member_to_remove.user.email

        # Remove the member
        member_to_remove.delete()

        # Trigger task to handle WebSocket notification
        task_handle_remove_group_chat_member(user_id, group_chat.pk)

        self.add_message(
            request, messages.SUCCESS, f"Removed {user_email} from the group chat"
        )
        return redirect("group_members", pk=group_chat.pk)
