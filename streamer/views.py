import socketio  # type: ignore[import]
from django.conf import settings  # type: ignore[import]

async_mode = "gevent"

sio = socketio.Server(
    async_mode=async_mode, cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS
)


@sio.on("connect")
def connect(sid, environ):
    print("connect ", sid)


@sio.on("disconnect")
def disconnect(sid):
    print("disconnect ", sid)


@sio.on("clip")
def clip(sid, timestamp, blob):
    # create a file with the timestamp as the name
    # save the blob to the file
    # send the file to the model
    # send the result back to the frontend

    with open(f"./{timestamp}.mp4", "wb") as f:
        f.write(blob)
    print("clip ", timestamp)
    sio.emit("result", "Got it!")
