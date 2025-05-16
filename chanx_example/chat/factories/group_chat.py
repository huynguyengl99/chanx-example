from chat.models import GroupChat
from test_utils.factory import BaseModelFactory


class GroupChatFactory(BaseModelFactory[GroupChat]):
    class Meta:  # pyright: ignore
        model = "chat.GroupChat"
