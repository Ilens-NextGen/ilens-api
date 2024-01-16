import asyncio
from pathlib import Path
from pprint import pprint
import socketio  # type: ignore[import]

sio = socketio.AsyncClient()
VIDEO_PATH = Path("clip.mp4")


@sio.event
async def connect():
    print("connection established")


@sio.event
async def detection(data):
    print("detection received with: ")
    pprint(data)


@sio.event
async def my_message(data):
    print("message received with ", data)
    await sio.emit("my response", {"response": "my response"})


@sio.event
async def disconnect():
    print("disconnected from server")


async def main():
    await sio.connect("http://localhost:8000")
    video_bytes = VIDEO_PATH.read_bytes()
    # await sio.wait()
    print("Sending video")
    await sio.emit("clip", (video_bytes, 1))
    print("Sent video")


if __name__ == "__main__":
    asyncio.run(main())
