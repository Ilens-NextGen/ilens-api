import os
from ilens.socket import socketio_app

from channels.routing import ProtocolTypeRouter  # type: ignore[import]
from django.core.asgi import get_asgi_application

# from streamer.consumers import socketio_app

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

asgi_app = get_asgi_application()
application = ProtocolTypeRouter(
    {
        "http": asgi_app,
        "websocket": socketio_app,
    }
)
# application = asgi_app
