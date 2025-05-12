from channels.routing import URLRouter

from chanx.urls import path

from chat.routing import ws_chat_router

ws_all_router = URLRouter([*ws_chat_router])

ws_routers = URLRouter(
    [
        path("ws/", ws_all_router),
    ]
)
