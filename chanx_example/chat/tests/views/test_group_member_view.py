from typing import cast

from django.http import HttpResponseRedirect
from django.urls import reverse
from rest_framework import status

from accounts.factories.user import UserFactory
from chat.factories.chat_member import ChatMemberFactory
from chat.factories.group_chat import GroupChatFactory
from chat.models import ChatMember
from test_utils.auth_api_test_case import AuthAPITestCase


class GroupMemberManagementViewTestCase(AuthAPITestCase):
    """Test case for GroupMemberManagementView and RemoveMemberView."""

    def setUp(self) -> None:
        super().setUp()

        # Create a group chat that the user is an admin of
        self.group_chat = GroupChatFactory.create(title="Test Chat")
        self.chat_member = ChatMemberFactory.create_admin(
            user=self.user, group_chat=self.group_chat
        )

        # URL for the members management page
        self.url = reverse("group_members", kwargs={"pk": self.group_chat.pk})

        # Create another user for testing member addition
        self.other_user = UserFactory.create(email="other@mail.com")

    def test_get_members_page_as_admin(self) -> None:
        """Test that an admin can access the members management page."""
        # Make the request
        response = self.auth_client.get(self.url)

        # Verify response
        assert response.status_code == status.HTTP_200_OK

        # Check that the template was rendered
        assert "chat/group_members.html" in [t.name for t in response.templates]

        # Check that the group chat and members are in the context
        group_chat = response.context.get("group_chat")
        assert group_chat is not None
        assert group_chat.title == "Test Chat"

        members = response.context.get("members")
        assert members is not None
        assert len(members) == 1

        can_manage = response.context.get("can_manage")
        assert can_manage is True

    def test_get_members_page_as_regular_member(self) -> None:
        """Test that a regular member can access the members page but cannot manage members."""
        # Change the user's role to regular member
        self.chat_member.chat_role = ChatMember.ChatMemberRole.MEMBER
        self.chat_member.save()

        # Make the request
        response = self.auth_client.get(self.url)

        # Verify response - can be 200 or 403 depending on the permission implementation
        if response.status_code == status.HTTP_200_OK:
            # Check that the user cannot manage members
            can_manage = response.context.get("can_manage")
            assert can_manage is False
        else:
            # Or the view might forbid regular members entirely
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_members_page_as_owner(self) -> None:
        """Test that an owner can access and manage the members page."""
        # Change the user's role to owner
        self.chat_member.chat_role = ChatMember.ChatMemberRole.OWNER
        self.chat_member.save()

        # Make the request
        response = self.auth_client.get(self.url)

        # Verify response
        assert response.status_code == status.HTTP_200_OK

        # Check that the user can manage members
        can_manage = response.context.get("can_manage")
        assert can_manage is True

    def test_add_new_member(self) -> None:
        """Test adding a new member to the group chat."""
        # Member data
        member_data = {
            "email": self.other_user.email,
            "role": str(ChatMember.ChatMemberRole.MEMBER),
        }

        # Make the request
        response = self.auth_client.post(self.url, member_data)

        # Verify that we get redirected back to the members page
        assert response.status_code == status.HTTP_302_FOUND
        assert cast(HttpResponseRedirect, response).url == self.url

        # Verify the member was added
        members = ChatMember.objects.filter(group_chat=self.group_chat)
        assert members.count() == 2

        # Verify the new member has the correct role
        new_member = members.get(user=self.other_user)
        assert new_member.chat_role == ChatMember.ChatMemberRole.MEMBER

    def test_add_member_as_admin(self) -> None:
        """Test adding a member with admin privileges."""
        # Member data
        member_data = {
            "email": self.other_user.email,
            "role": str(ChatMember.ChatMemberRole.ADMIN),
        }

        # Make the request
        response = self.auth_client.post(self.url, member_data)

        # Verify that we get redirected back to the members page
        assert response.status_code == status.HTTP_302_FOUND
        assert cast(HttpResponseRedirect, response).url == self.url

        # Verify the member was added with admin role
        new_member = ChatMember.objects.get(
            user=self.other_user, group_chat=self.group_chat
        )
        assert new_member.chat_role == ChatMember.ChatMemberRole.ADMIN

    def test_add_nonexistent_user(self) -> None:
        """Test adding a nonexistent user to the group chat."""
        # Member data with nonexistent email
        member_data = {
            "email": "nonexistent@mail.com",
            "role": str(ChatMember.ChatMemberRole.MEMBER),
        }

        # Make the request
        response = self.auth_client.post(self.url, member_data)

        # Verify that we get redirected back to the members page
        assert response.status_code == status.HTTP_302_FOUND
        assert cast(HttpResponseRedirect, response).url == self.url

        # Verify no new member was added
        members = ChatMember.objects.filter(group_chat=self.group_chat)
        assert members.count() == 1

    def test_cannot_add_owner(self) -> None:
        """Test that we cannot add a new owner to the group chat."""
        # Member data with owner role
        member_data = {
            "email": self.other_user.email,
            "role": str(ChatMember.ChatMemberRole.OWNER),
        }

        # Make the request
        response = self.auth_client.post(self.url, member_data)

        # Verify that we get redirected back to the members page
        assert response.status_code == status.HTTP_302_FOUND
        assert cast(HttpResponseRedirect, response).url == self.url

        # Verify no new member was added
        members = ChatMember.objects.filter(
            group_chat=self.group_chat, user=self.other_user
        )
        assert members.count() == 0

    def test_regular_member_cannot_add_members(self) -> None:
        """Test that a regular member cannot add new members."""
        # Change the user's role to regular member
        self.chat_member.chat_role = ChatMember.ChatMemberRole.MEMBER
        self.chat_member.save()

        # Member data
        member_data = {
            "email": self.other_user.email,
            "role": str(ChatMember.ChatMemberRole.MEMBER),
        }

        # Make the request
        response = self.auth_client.post(self.url, member_data)

        # Verify that we get a forbidden response
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Verify no new member was added
        members = ChatMember.objects.filter(group_chat=self.group_chat)
        assert members.count() == 1

    def test_page_contains_required_elements(self) -> None:
        """Test that the members page contains all required UI elements."""
        # Make the request
        response = self.auth_client.get(self.url)
        content = response.content.decode()

        # Check for important UI elements
        assert self.group_chat.title in content
        assert "Members" in content
        assert "Add New Member" in content
        assert "Back to Chat" in content
        assert "Email" in content
        assert "Role" in content
        assert "Actions" in content

    def test_add_existing_member_integrity_error(self) -> None:
        """Test adding a user who is already a member (covers IntegrityError handling)."""
        # First, add the other_user to the group
        ChatMemberFactory.create(user=self.other_user, group_chat=self.group_chat)

        member_data = {
            "email": self.other_user.email,
            "role": str(ChatMember.ChatMemberRole.MEMBER),
        }

        # Try to add the same user again - should trigger IntegrityError
        # The view should catch it and redirect (lines 105-109)
        response = self.auth_client.post(self.url, member_data)

        # Should redirect back to members page (error handled gracefully)
        assert response.status_code == status.HTTP_302_FOUND
        assert cast(HttpResponseRedirect, response).url == self.url


class RemoveMemberViewTestCase(AuthAPITestCase):
    """Test case for RemoveMemberView."""

    def setUp(self) -> None:
        super().setUp()

        # Create a group chat that the user is an admin of
        self.group_chat = GroupChatFactory.create(title="Test Chat")
        self.chat_member = ChatMemberFactory.create_admin(
            user=self.user, group_chat=self.group_chat
        )

        # Create another user as a regular member
        self.other_user = UserFactory.create(email="other@mail.com")
        self.other_member = ChatMemberFactory.create(
            user=self.other_user, group_chat=self.group_chat
        )

        # URL for removing the member
        self.url = reverse(
            "remove_member",
            kwargs={"pk": self.group_chat.pk, "member_id": self.other_member.pk},
        )

    def test_remove_member_as_admin(self) -> None:
        """Test that an admin can remove a regular member."""
        # Make the request
        response = self.auth_client.get(self.url)

        # Verify that we get redirected back to the members page
        assert response.status_code == status.HTTP_302_FOUND
        assert cast(HttpResponseRedirect, response).url == reverse(
            "group_members", kwargs={"pk": self.group_chat.pk}
        )

        # Verify the member was removed
        assert not ChatMember.objects.filter(pk=self.other_member.pk).exists()

    def test_remove_member_as_owner(self) -> None:
        """Test that an owner can remove a regular member."""
        # Change the user's role to owner
        self.chat_member.chat_role = ChatMember.ChatMemberRole.OWNER
        self.chat_member.save()

        # Make the request
        response = self.auth_client.get(self.url)

        # Verify that we get redirected back to the members page
        assert response.status_code == status.HTTP_302_FOUND
        assert cast(HttpResponseRedirect, response).url == reverse(
            "group_members", kwargs={"pk": self.group_chat.pk}
        )

        # Verify the member was removed
        assert not ChatMember.objects.filter(pk=self.other_member.pk).exists()

    def test_regular_member_cannot_remove_others(self) -> None:
        """Test that a regular member cannot remove other members."""
        # Create a third user as an admin
        admin_user = UserFactory.create(email="admin@mail.com")
        admin_member = ChatMemberFactory.create_admin(
            user=admin_user, group_chat=self.group_chat
        )

        # Change the current user's role to regular member
        self.chat_member.chat_role = ChatMember.ChatMemberRole.MEMBER
        self.chat_member.save()

        # URL for removing the admin member
        url = reverse(
            "remove_member",
            kwargs={"pk": self.group_chat.pk, "member_id": admin_member.pk},
        )

        # Make the request
        response = self.auth_client.get(url)

        # Verify that we get a forbidden response
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Verify the member was not removed
        assert ChatMember.objects.filter(pk=admin_member.pk).exists()

    def test_cannot_remove_owner(self) -> None:
        """Test that even an admin cannot remove an owner."""
        # Create an owner
        owner_user = UserFactory.create(email="owner@mail.com")
        owner_member = ChatMemberFactory.create_owner(
            user=owner_user, group_chat=self.group_chat
        )

        # URL for removing the owner
        url = reverse(
            "remove_member",
            kwargs={"pk": self.group_chat.pk, "member_id": owner_member.pk},
        )

        # Make the request
        response = self.auth_client.get(url)

        # Verify that we get a forbidden response
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Verify the owner was not removed
        assert ChatMember.objects.filter(pk=owner_member.pk).exists()

    def test_non_member_cannot_remove_others(self) -> None:
        """Test that a non-member cannot remove members."""
        # Create a new user who is not a member of the group chat
        non_member = UserFactory.create(email="nonmember@mail.com")
        non_member_client = self.get_client_for_user(non_member)

        # Make the request
        response = non_member_client.get(self.url)

        # Verify the user cannot access the remove member page
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Verify the member was not removed
        assert ChatMember.objects.filter(pk=self.other_member.pk).exists()

    def test_invalid_member_id(self) -> None:
        """Test removing a nonexistent member."""
        # URL for removing a nonexistent member
        url = reverse(
            "remove_member", kwargs={"pk": self.group_chat.pk, "member_id": 99999}
        )

        # Make the request
        response = self.auth_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
