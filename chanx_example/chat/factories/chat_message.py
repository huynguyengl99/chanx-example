from chat.models import ChatMessage
from test_utils.factory import BaseModelFactory


class ChatMessageFactory(BaseModelFactory[ChatMessage]):
    class Meta:
        model = ChatMessage

    content = "Test message content"
    is_edited = False
