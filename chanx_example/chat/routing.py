from chanx.urls import path

from chat.consumers import ChatConsumer

ws_chat_router = [
    path("chat/", ChatConsumer.as_asgi()),
]
