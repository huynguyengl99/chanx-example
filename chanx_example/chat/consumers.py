import asyncio
from typing import Any

from channels.auth import UserLazyObject
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """Websocket to chat"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user: UserLazyObject

    async def websocket_connect(self, message: Any) -> None:
        await super().websocket_connect(message)
        user = self.scope.get("user")
        if user:
            self.user = user

    async def receive_json(self, content: dict[str, Any], **kwargs: Any) -> None:
        message = content.get("message", "")
        await self.send_json({"message": f"Reply: {message}"})
        await asyncio.sleep(0)

    async def receive(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
        **kwargs: Any,
    ) -> None:
        if text_data:
            await self.receive_json(await self.decode_json(text_data), **kwargs)
        elif bytes_data:
            byte_len = len(bytes_data)
            await self.send_json({"message": f"Byte length: {byte_len}"})
        else:
            raise ValueError("No text section for incoming WebSocket frame!")
