# chat/routing.py
"""Ignore for now. In the future this may be used as a fallback for the
socketio connections in case simply specifying websocket as the protocol isn't enough"""
from django.urls import re_path
from ilens.socket import socketio_app

urlpatterns = [
    re_path(r"^socket.io/", socketio_app, name="socketio"),
    re_path(r"^longpoll/$", socketio_app, name="socketio-longpoll"),
]
