import asyncio
import logging
from ilens.clarifai import ClarifaiTranscription, Audio
from ilens.clarifai import Text
from ilens.clarifai.workflows import ClarifaiMultimodalToSpeechWF
from ilens.core.image_processor import AsyncVideoProcessor
from ilens.clarifai import Image, ClarifaiImageRecognition
from ilens.socket import server as sio
from codetiming import Timer as _Timer


class Timer(_Timer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.text.startswith("Elapsed time:") and self.name:
            self.text = "{name} time: {seconds:.2f} s"
        if self.logger == print:
            self.logger = logging.getLogger("timer").debug


image_recognition = ClarifaiImageRecognition()
transcriber = ClarifaiTranscription()
llm_workflow = ClarifaiMultimodalToSpeechWF()
image_processor = AsyncVideoProcessor()


@sio.event
async def connect(sid, environ):
    print("Connected", sid)


@sio.event
async def clip(sid, blob: bytes, duration: float):
    timer = Timer("Clip")
    timer.start()
    # n_bytes = len(blob)
    # write(f"Got a {duration} second clip of {n_bytes} bytes")
    timer2 = Timer("Image Selection")
    timer2.start()
    best_frame = await image_processor.process_video(blob)
    image_bytes = image_bytes = await asyncio.to_thread(
        image_processor.convert_result_image_to_bytes, best_frame
    )
    timer2.stop()
    with Timer("image recognition"):
        recognition = image_recognition.run({"image": Image(base64=image_bytes)})[0]
    timer.stop()
    await sio.emit(
        "recognition",
        recognition,
        to=sid,
    )


@sio.event
# @profile  # noqa: F821 # type: ignore
async def query(sid, audio: bytes, clip: bytes):
    timer = Timer(
        "Query",
    )
    timer.start()

    # write(
    # (
    # f"Got a query sent as audio of {len(audio) / 1024}KB"
    # f" and a clip of {len(clip) / 1024}KB"
    # )
    # )

    # @profile  # noqa: F821 # type: ignore
    async def get_image():
        timer = Timer("Image Recognition")
        timer.start()
        best_frame = await image_processor.process_video(clip)
        image_bytes = await asyncio.to_thread(
            image_processor.convert_result_image_to_bytes, best_frame
        )
        timer.stop()
        return image_bytes

    # @profile  # noqa: F821 # type: ignore
    async def get_transcript():
        timer = Timer("Transcription")
        timer.start()
        transcript = (
            await asyncio.to_thread(
                transcriber.run,
                {
                    "audio": Audio(base64=audio),
                },
            )
        )[0]["text"]
        print("Question transcript: ", transcript)
        timer.stop()
        return transcript

    image_bytes, transcript = await asyncio.gather(get_image(), get_transcript())

    timer2 = Timer("GPT Workflow")
    timer2.start()
    audio_stream = (
        await asyncio.to_thread(
            llm_workflow.run,
            {
                "text": Text(raw=transcript),
                "image": Image(base64=image_bytes),
            },
        )
    )[0]["audio"]
    audio_bytes = audio_stream.getvalue()
    # n_bytes = len(audio_bytes)
    # write(f"Got a {n_bytes} bytes audio")
    timer2.stop()
    await sio.emit("audio", audio_bytes, to=sid)
    timer.stop()
