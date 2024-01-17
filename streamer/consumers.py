import socketio  # type: ignore[import]
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
    timer = Timer(
        "Query",
        logger=write,
    )
    timer.start()
    # TRANSCRIPT_URL = "http://100.26.250.23/transcript.txt"
    # IMAGE_URL = "http://100.26.250.23/test.png"
    # AUDIO_URL = "http://100.26.250.23/query.wav"
    # ANSWER_URL = "http://100.26.250.23/answer.txt"

    print(
        f"Got a query sent as audio of {len(audio)} bytes and clip of {len(clip)} bytes"
    )

    # @profile  # noqa: F821 # type: ignore
    async def get_image():
        with Timer("Image Selection", logger=write):
            best_frame = await image_processor.process_video(clip)
            image_bytes = await asyncio.to_thread(
                image_processor.convert_result_image_to_bytes, best_frame
            )
        return image_bytes

    # @profile  # noqa: F821 # type: ignore
    async def get_transcript():
        with Timer("Transcription", logger=write):
            transcript = (
                await asyncio.to_thread(
                    transcriber.run,
                    {
                        # "audio": Audio(url=AUDIO_URL),
                        "audio": Audio(base64=audio),
                    },
                )
            )[0]["text"]
            print("Question transcript: ", transcript)
        return transcript

    # asyncio.create_task(sio.send("Question received!"))
    image_bytes, transcript = await asyncio.gather(get_image(), get_transcript())
    # with Timer("LLM Query", logger=write):
    #     answer = (
    #         await asyncio.to_thread(
    #             llm.run,
    #             {
    #                 # "text": Text(url=TRANSCRIPT_URL),
    #                 "text": Text(raw=transcript),
    #                 # "image": Image(url=IMAGE_URL),
    #                 "image": Image(base64=image_bytes),
    #             },
    #         )
    #     )[0]["text"]
    #     print("Answer: ", answer)
    # with Timer("TextToSpeech", logger=write):
    #     audio_stream = (
    #         await asyncio.to_thread(
    #             tts.run,
    #             {
    #                 # "text": Text(url=ANSWER_URL),
    #                 "text": Text(raw=answer),
    #             },
    #         )
    #     )[0]["audio"]
    #     audio_bytes = audio_stream.getvalue()
    #     n_bytes = len(audio_bytes)
    #     print(f"Got a {n_bytes} bytes audio")
    with Timer("GPT Workflow", logger=write):
        audio_stream = (
            await asyncio.to_thread(
                gpt_workflow.run,
                {
                    "text": Text(raw=transcript),
                    # "text": Text(url=TRANSCRIPT_URL),
                    "image": Image(base64=image_bytes),
                    # "image": Image(url=IMAGE_URL),
                },
            )
        )[0]["audio"]
        audio_bytes = audio_stream.getvalue()
        n_bytes = len(audio_bytes)
        print(f"Got a {n_bytes} bytes audio")
    with Timer("Audio emit", logger=write):
        await sio.emit("audio", audio_bytes, to=sid)
    timer.stop()
    with open("timed.txt", "a") as f:
        f.write(stream.getvalue())
        f.write(f"{'-'*20}\n")
        clear()


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
        # await asyncio.to_thread(self.find_obstacles.find_all_objects, image_byte)
        await sio.emit(
            "result", "There's a car in front of you. Watch out", room=self.room_id
        )
        print("Result sent")

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
