from channels.routing import URLRouter

from chanx.routing import include, path

ws_router = URLRouter(
    [
        # Use ws_include which returns a URLRouter
        path("assistants/", include("assistants.routing")),
        path("discussion/", include("discussion.routing")),
        path("chat/", include("chat.routing")),
    ]
)

router = URLRouter(
    [
        path("ws/", include(ws_router)),
    ]
)
