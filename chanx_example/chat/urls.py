from django.urls import include, path
from rest_framework.routers import SimpleRouter

from rest_framework_nested import routers

from chat.views import (
    ChatMessageViewSet,
    GroupChatDetailView,
    GroupChatViewSet,
    GroupMemberManagementView,
    HomeView,
    RemoveMemberView,
)

# Main router for group chats API
chat_router = SimpleRouter()
chat_router.register(r"", GroupChatViewSet)

# Nested router for messages within a group chat
chat_messages_router = routers.NestedSimpleRouter(chat_router, r"", lookup="group_chat")
chat_messages_router.register(r"messages", ChatMessageViewSet, basename="chat-messages")


# API endpoints
api_urlpatterns = [
    path("", include(chat_router.urls)),
    path("", include(chat_messages_router.urls)),
]

# Web UI routes - nested under /page/
web_urlpatterns = [
    path("page/", HomeView.as_view(), name="chat-home"),
    path("page/<int:pk>/", GroupChatDetailView.as_view(), name="chat-group-detail"),
    path(
        "page/<int:pk>/members/",
        GroupMemberManagementView.as_view(),
        name="group_members",
    ),
    path(
        "page/<int:pk>/members/<int:member_id>/remove/",
        RemoveMemberView.as_view(),
        name="remove_member",
    ),
]

# Combine all URL patterns
urlpatterns = web_urlpatterns + api_urlpatterns
