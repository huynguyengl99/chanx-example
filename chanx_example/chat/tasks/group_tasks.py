from typing import Any

from channels.layers import get_channel_layer

channel_layer = get_channel_layer()


def task_handle_new_group_chat_member(user_id: Any, group_chat_id: Any) -> None:
    pass


def task_handle_remove_group_chat_member(user_id: Any, group_chat_id: Any) -> None:
    pass


def task_handle_delete_group_chat(group_chat_id: Any) -> None:
    pass
