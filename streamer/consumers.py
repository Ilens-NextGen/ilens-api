import socketio  # type: ignore[import]
import asyncio
from random import choice
from django.dispatch import receiver
from ilens.clarifai import ClarifaiTranscription, Audio
from ilens.clarifai import ClarifaiGPT4VAlternative, Text
from ilens.clarifai.text_to_speech import ClarifaiTextToSpeech
from streamer.signals import finished_frame
from image_processor.clarifai_processor import AsyncVideoProcessor
from ilens.clarifai import Image, ClarifaiImageRecognition
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
transcriber = ClarifaiTranscription()
image_processor = AsyncVideoProcessor()
llm = ClarifaiGPT4VAlternative()
tts = ClarifaiTextToSpeech()


@sio.event
async def connect(sid, environ):
    print("Connected", sid)


@sio.event
async def clip(sid, blob: bytes, duration: float):
    print(f"Got a {duration} second clip: [{blob[:10]!r}...]")
    await sio.send("Clip received!")
    print("getting best frame")
    best_frame = await image_processor.process_video(blob)
    print("got best frame")
    image_bytes = image_processor.convert_result_image_to_bytes(best_frame)
    with open("test.png", "wb") as f:
        f.write(image_bytes)
    print("sending image to clarifai")
    recognition = image_recognition.run({"image": Image(base64=image_bytes)})[0]
    print("sending recognition to client")
    await sio.emit(
        "recognition",
        recognition,
        to=sid,
    )


@sio.event
async def query(sid, audio: bytes, clip: bytes):
    print("Question received")
    asyncio.create_task(sio.send("Question received!"))
    transcript = (
        await asyncio.to_thread(transcriber.run, {"audio": Audio(base64=audio)})
    )[0]["text"]
    print("Question transcript: ", transcript)
    best_frame = await image_processor.process_video(clip)
    image_bytes = await asyncio.to_thread(
        image_processor.convert_result_image_to_bytes, best_frame
    )
    answer = (
        await asyncio.to_thread(
            llm.run,
            {
                "text": Text(raw=transcript),
                "image": Image(base64=image_bytes),
            },
        )
    )[0]["text"]
    print("Answer: ", answer)
    await sio.emit("response", answer, to=sid)


# @sio.eve


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
