import asyncio
from server.clarifai import ClarifaiTranscription, Audio
from server.clarifai import Text
from server.clarifai.workflows import ClarifaiMultimodalToSpeechWF
from server.clarifai.image_processor import AsyncVideoProcessor
from server.clarifai import Image, ClarifaiImageRecognition
from server.socket import server as sio
from server.utils import timed


image_recognition = ClarifaiImageRecognition()
transcriber = ClarifaiTranscription()
llm_workflow = ClarifaiMultimodalToSpeechWF()
image_processor = AsyncVideoProcessor()


@sio.event
async def connect(sid, environ):
    print("Connected", sid)


@sio.event
@timed.async_("Handle Clip")
async def clip(sid, blob: bytes, duration: float):
    # n_bytes = len(blob)
    # write(f"Got a {duration} second clip of {n_bytes} bytes")
    async with timed("Image Selection For Detector"):
        best_frame = await image_processor.process_video(blob)
        image_bytes = image_bytes = await asyncio.to_thread(
            image_processor.convert_result_image_to_bytes, best_frame
        )
    recognition = (
        await asyncio.to_thread(
            timed("Image Recognition")(image_recognition.run),
            {"image": Image(base64=image_bytes)},
        )
    )[0]
    await sio.emit(
        "recognition",
        recognition,
        to=sid,
    )


@sio.event
# @profile  # noqa: F821 # type: ignore
@timed.async_("Handle Query")
async def query(sid, audio: bytes, clip: bytes):
    # write(
    # (
    # f"Got a query sent as audio of {len(audio) / 1024}KB"
    # f" and a clip of {len(clip) / 1024}KB"
    # )
    # )

    # @profile  # noqa: F821 # type: ignore
    @timed.async_("Image Selection For Query")
    async def get_image():
        best_frame = await image_processor.process_video(clip)
        image_bytes = await asyncio.to_thread(
            image_processor.convert_result_image_to_bytes, best_frame
        )
        return image_bytes

    # @profile  # noqa: F821 # type: ignore
    @timed.async_("Transcription")
    async def get_transcript():
        transcript = (
            await asyncio.to_thread(
                transcriber.run,
                {
                    "audio": Audio(base64=audio),
                },
            )
        )[0]["text"]
        return transcript

    image_bytes, transcript = await asyncio.gather(get_image(), get_transcript())

    audio_stream = (
        await asyncio.to_thread(
            timed("MultiModal To Speech")(llm_workflow.run),
            {
                "text": Text(raw=transcript),
                "image": Image(base64=image_bytes),
            },
        )
    )[0]["audio"]
    audio_bytes = audio_stream.getvalue()
    # n_bytes = len(audio_bytes)
    # write(f"Got a {n_bytes} bytes audio")
    await sio.emit("audio", audio_bytes, to=sid)
