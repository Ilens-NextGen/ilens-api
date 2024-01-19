from server.utils import getboolenv, getenv, getintenv, getlistenv, loadenv
from socket import gethostname

# load the environment variables from the env file if it exists
loadenv()


# if the server is running in debug mode
DEBUG = getboolenv("DEBUG", False)

# the port to run the server on
SERVER_ID = getenv("SERVER_ID", gethostname())

# if we should monitor the socket connections
SOCKET_MONITORING = getboolenv("SOCKET_MONITORING", False)

# the allowed hosts for the server
ALLOWED_HOSTS = getlistenv("ALLOWED_HOSTS", [])


if DEBUG:
    # allow local connections in debug mode
    ALLOWED_HOSTS.extend(
        ["localhost", "127.0.0.1", "0.0.0.0"],
    )

if SOCKET_MONITORING:
    # allow the monitoring client to connect
    ALLOWED_HOSTS.append("admin.socket.io")

SOCKET_ADMIN_USERNAME = getenv("SOCKET_ADMIN_USERNAME", None)
SOCKET_ADMIN_PASSWORD = getenv("SOCKET_ADMIN_PASSWORD", None)


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
