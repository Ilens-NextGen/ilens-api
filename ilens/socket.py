from socketio.async_server import AsyncServer  # type: ignore[import]
from socketio import ASGIApp  # type: ignore[import]
from django.conf import settings

server = AsyncServer(
    async_mode="asgi", cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS
)
socketio_app = ASGIApp(server)
