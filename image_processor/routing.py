from django.urls import re_path

from .consumers import ImageProcessorConsumer

websocket_urlpatterns = [
    re_path(r"ws/(?P<type>\w+)/(?P<room_name>\w+)/$", ImageProcessorConsumer.as_asgi()), # type can either be stream or chat
]