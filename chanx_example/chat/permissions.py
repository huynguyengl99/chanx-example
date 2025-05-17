from typing import cast

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from chat.models import ChatMember, GroupChat
from utils.request import AuthenticatedRequest


class ReadOnlyMemberOrOwner(permissions.BasePermission):
    message = "Only group owner can modify state, or a member to fetch"

    def has_object_permission(
        self, request: Request, view: APIView, obj: GroupChat
    ) -> bool:
        request = cast(AuthenticatedRequest, request)

        if request.method in permissions.SAFE_METHODS:
            return ChatMember.objects.filter(
                user=request.user.pk, group_chat=obj
            ).exists()
        else:
            return ChatMember.objects.filter(
                user=request.user.pk,
                group_chat=obj,
                chat_role=ChatMember.ChatMemberRole.OWNER,
            ).exists()


class IsGroupChatMember(permissions.BasePermission):
    """
    Permission to only allow members of a group chat to access it.

    This permission expects the view to have a 'pk' URL parameter
    representing the group chat ID.
    """

    message = "You are not a member of this group chat."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        request_auth = cast(AuthenticatedRequest, request)
        group_chat_pk = view.kwargs.get("pk")

        if not group_chat_pk:
            return False

        return ChatMember.objects.filter(
            user=request_auth.user, group_chat_id=group_chat_pk
        ).exists()


class IsGroupChatManagerOrReadOnly(permissions.BasePermission):
    """
    Permission that checks if the user has at least admin permissions in the group.

    This permission expects the view to have a 'pk' URL parameter
    representing the group chat ID.
    """

    message = "You don't have permission to manage this group chat."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        request_auth = cast(AuthenticatedRequest, request)
        group_chat_pk = view.kwargs.get("pk")

        if not group_chat_pk:
            return False

        try:
            member = ChatMember.objects.get(
                user=request_auth.user, group_chat_id=group_chat_pk
            )
            return member.chat_role <= ChatMember.ChatMemberRole.ADMIN
        except ChatMember.DoesNotExist:
            return False


class IsGroupChatMemberNested(permissions.BasePermission):
    message = "Only group members are allowed for these nested route apis."

    def has_permission(self, request: Request, view: APIView) -> bool:
        request = cast(AuthenticatedRequest, request)

        return ChatMember.objects.filter(
            user=request.user.pk,
            group_chat=view.kwargs.get("group_chat_pk"),
        ).exists()


class CanRemoveChatMember(permissions.BasePermission):
    """
    Permission that checks if the user can remove a specific member.

    This permission checks:
    1. If the user is a member with admin or higher role
    2. If the target member is not an owner

    This permission expects the view to have 'pk' and 'member_id' URL parameters.
    """

    message = "You cannot remove this member."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        request_auth = cast(AuthenticatedRequest, request)
        group_chat_pk = view.kwargs.get("pk")
        member_id = view.kwargs.get("member_id")

        if not group_chat_pk or not member_id:
            return False

        # First check if the user is a member with sufficient permissions
        try:
            ChatMember.objects.get(
                user=request_auth.user,
                group_chat_id=group_chat_pk,
                chat_role__lte=ChatMember.ChatMemberRole.ADMIN,
            )

            # Next check if the member to be removed is an owner
            member_to_remove = ChatMember.objects.get(
                pk=member_id, group_chat_id=group_chat_pk
            )
            # Cannot remove owners
            if member_to_remove.chat_role == ChatMember.ChatMemberRole.OWNER:
                self.message = "Cannot remove the group owner."
                return False

            return True
        except ChatMember.DoesNotExist:
            return False
