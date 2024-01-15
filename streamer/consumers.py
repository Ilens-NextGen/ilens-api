import socketio  # type: ignore[import]
import asyncio
from random import choice
from django.dispatch import receiver  # type: ignore[import]
from streamer.signals import finished_frame
from image_processor.clarifai_processor import AsyncVideoProcessor
from ilens.clarifai import ClarifaiImageRecognition
from ilens.socket import server as sio

MOCK_AI_RESPONSES = [
    "Hello! How can I assist you today?",
    "I'm here to help. What do you need?",
    "Greetings! What can I do for you?",
    "Good day! Ask me anything.",
    "Hi there! Ready for a chat?",
    "Welcome! How may I be of service?",
    "Hey! What brings you here?",
    "Greetings! Feel free to ask me questions.",
    "Hello! I'm at your disposal. What's on your mind?",
    "Hi! Let's chat about anything you like.",
]

image_recognition = ClarifaiImageRecognition()


class ChatNamespace(socketio.AsyncNamespace):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_frame = None
        self.room_id = None

    async def on_connect(self, sid, environ):
        room_id = sid
        print("Roomid", room_id)
        # user = authenticate(room_id) # Authenticate the user later
        # if not user:
        #   await self.disconnect("no user found")
        # else:
        #     self.user = user
        #     self.room_id = user.room_id
        self.room_id = room_id
        self.video_processor = AsyncVideoProcessor()
        await sio.enter_room(sid, room_id)
        print("Connected", sid)

    async def on_disconnect(self, sid):
        print("Disconnected", sid)
        await sio.leave_room(sid, self.room_id)

    async def on_clip(self, sid, timestamp, blob: bytes):
        image = await self.video_processor.process_video(blob)
        image_byte = self.video_processor.convert_result_image_to_bytes(image)
        finished_frame.send(instance=self, sender=self, image_byte=image_byte)
        print("clip ", timestamp)
        await asyncio.sleep(2)  # to stimulate running the image handling
        # await asyncio.to_thread(self.find_obstacles.find_all_objects, image_byte)
        await sio.emit(
            "result", "There's a car in front of you. Watch out", room=self.room_id
        )

    async def on_question(self, sid, question):
        print(question)

        @receiver(finished_frame)
        def on_finished_frame(sender, instance, image_byte, **kwargs):
            self.current_frame = image_byte

        if self.current_frame:
            print("Frame received")
        # await query_send_ai_message('question')
        await sio.emit("ai_reply", choice(MOCK_AI_RESPONSES), room=self.room_id)
        self.current_frame = None


sio.register_namespace(ChatNamespace("/"))
