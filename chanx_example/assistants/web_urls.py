from django.urls import path

from .views import AssistantChatView

urlpatterns = [
    path("", AssistantChatView.as_view(), name="assistant_chat"),
]
