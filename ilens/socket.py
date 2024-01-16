from socketio.async_server import AsyncServer  # type: ignore[import]
from socketio import ASGIApp
from django.conf import settings

sio = AsyncServer(
    async_mode="asgi", cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS
)

socketio_app = ASGIApp(sio)
from streamer.consumers import *