from datetime import timedelta
from pathlib import Path
import os

from server.utils import getboolenv, getenv, getintenv, getlistenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = getboolenv("DEBUG", False)

ALLOWED_HOSTS = getlistenv("ALLOWED_HOSTS", [])
if DEBUG:
    ALLOWED_HOSTS.extend(
        ["localhost", "127.0.0.1", "0.0.0.0"],
    )


SOCKET_LOGGER = getboolenv("SOCKET_LOGGER", DEBUG)
CORS_ALLOWED_ORIGINS = ALLOWED_HOSTS

# the async model to use.
SOCKET_ASYNC_MODE = getenv("ASYNC_MODE", "sanic")

# if set to True, event handlers will be run in separate threads
SOCKET_ASYNC_HANDLERS = getboolenv("SOCKET_ASYNC_HANDLERS", True)

# when set to False, new connections are accepted when the connect
# handler returns something other than False
SOCKET_ALWAYS_CONNECT = getboolenv("SOCKET_ALWAYS_CONNECT", False)

# the interval in seconds at which the server pings the client
SOCKET_PING_INTERVAL = getintenv("SOCKET_PING_INTERVAL", 25)

# the time in seconds that the client waits for the server to respond
# before disconnecting
SOCKET_PING_TIMEOUT = getintenv("SOCKET_PING_TIMEOUT", 20)

# the maximum allowed packet size in bytes
_20MB = 20 * 1024 * 1024
SOCKET_MAX_HTTP_BUFFER_SIZE = getintenv("SOCKET_BUFFER_SIZE", _20MB)

# whether to compress packets when using the polling transport
SOCKET_HTTP_COMPRESS = getboolenv("SOCKET_HTTP_COMPRESS", True)

# the HTTP compression threshold in bytes. Below this value, packets will
# not be compressed
SOCKET_COMPRESSION_THRESHOLD = getintenv("SOCKET_COMPRESSION_THRESHOLD", 1024)