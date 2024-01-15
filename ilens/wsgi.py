"""
WSGI config for a server that supports websockets.
To use go to settings.py and comment 
    1. `ASGI_APPLICATION` and uncomment `WSGI_APPLICATION`
    2. Comment out `daphne` and `channels` in `INSTALLED_APPS`
"""
import socketio  # type: ignore[import]
from django.core.wsgi import get_wsgi_application
from gevent import pywsgi  # type: ignore[import]
from geventwebsocket.handler import WebSocketHandler  # type: ignore[import]
from streamer.views import sio
import logging

logging.basicConfig(level=logging.INFO)

# Django WSGI application
django_app = get_wsgi_application()

# Socket.IO server
sio_app = socketio.WSGIApp(sio, django_app)

# Combine Django and Socket.IO
application = pywsgi.WSGIServer(("", 8000), sio_app, handler_class=WebSocketHandler)
# Uncomment the line below if you want to serve the application using gevent's server
application.serve_forever()
application.log = logging.getLogger()
