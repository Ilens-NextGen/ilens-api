from socketio.async_server import AsyncServer  # type: ignore[import]
from server import settings

server = AsyncServer(
    async_mode=settings.SOCKET_ASYNC_MODE,
    cors_allowed_origins=[],
    logger=settings.SOCKET_LOGGER,
    engineio_logger=settings.SOCKET_LOGGER,
    async_handlers=settings.SOCKET_ASYNC_HANDLERS,
    always_connect=settings.SOCKET_ALWAYS_CONNECT,
    ping_interval=settings.SOCKET_PING_INTERVAL,
    ping_timeout=settings.SOCKET_PING_TIMEOUT,
    max_http_buffer_size=settings.SOCKET_MAX_HTTP_BUFFER_SIZE,
    http_compression=settings.SOCKET_HTTP_COMPRESS,
    compression_threshold=settings.SOCKET_COMPRESSION_THRESHOLD,
)
# server.instrument(auth={"username": "admin", "password": "admin"})
from server import consumers  # noqa: E402, F401
