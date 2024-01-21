import asyncio
from pathlib import Path
from typing import Literal
from uuid import uuid4
from server.clarifai import ClarifaiTranscription
from server.clarifai.base import Audio
from server.clarifai.workflows import ClarifaiMultimodalToSpeechWF
from server.clarifai.image_processor import AsyncVideoProcessor
from server.clarifai import Image, ClarifaiImageRecognition, ClarifaiImageDetection
from server.socket import server as sio
from server.utils import timed
from server.logger import CustomLogger
from server.settings import SERVER_ID
import aiofiles
import aiofiles.os

BASE_DIR = Path(__file__).parent.parent

image_recognition = ClarifaiImageRecognition()
transcriber = ClarifaiTranscription()
llm_workflow = ClarifaiMultimodalToSpeechWF()
image_processor = AsyncVideoProcessor()
image_detection = ClarifaiImageDetection()
websocket_logger = CustomLogger("Websocket").get_logger()


def get_baseurl(environ: dict):
    scheme = environ["wsgi.url_scheme"]
    host = environ["HTTP_HOST"]
    return f"{scheme}://{host}/{SERVER_ID}"


async def upload_file(content: bytes, filename: str, base_url: str):
    id = uuid4().hex[:8]
    location = BASE_DIR / "uploads" / f"{id}_{filename}"
    websocket_logger.info(f"Uploading file to {location}")
    aiofiles.os.makedirs(location.parent, exist_ok=True)
    async with aiofiles.open(location, "wb") as f:
        await f.write(content)
    url = f"{base_url}/resource/{id}_{filename}"
    return url


@sio.event
async def connect(sid, environ):
    websocket_logger.info(f"Connected {sid}")
    websocket_logger.info("Connected", sio.environ)
    await sio.emit("server-id", SERVER_ID, to=sid)


@sio.event
@timed.async_("Handle Recognition")
async def recognize(sid, clip: bytes):
    websocket_logger.info("Clip processing began")
    try:
        async with timed("Image Selection For Recognizer"):
            best_frame = await image_processor.process_video(clip)
            image_bytes = await asyncio.to_thread(
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
    except Exception as e:
        websocket_logger.error("WebsocketError", exc_info=True)
        raise e
    websocket_logger.info("Clip successfully processed")


@sio.event
@timed.async_("Handle Detection")
async def detect(sid, clip: bytes):
    websocket_logger.info("Clip processing began")
    try:
        async with timed("Image Selection For Detector"):
            best_frame = await image_processor.process_video(clip)
            image_bytes = await asyncio.to_thread(
                image_processor.convert_result_image_to_bytes, best_frame
            )
        detection = await asyncio.to_thread(
            timed("Image Recognition")(image_detection.run),
            {"image": Image(base64=image_bytes)},
        )
        sentence = await asyncio.to_thread(
            image_detection.construct_warning, detection[0]
        )
        await sio.emit(
            "detection",
            sentence,
            to=sid,
        )
    except Exception as e:
        websocket_logger.error("WebsocketError", exc_info=True)
        raise e
    websocket_logger.info("Clip successfully processed")


# @sio.event
# @timed.async_("Handle Query")
# async def query(sid, audio: bytes, clip: bytes):
#     websocket_logger.info(
#         f"Got a query sent as audio of {len(audio) / 1024}KB and a clip of {len(clip) / 1024}KB"
#     )

#     @timed.async_("Image Selection For Query")
#     async def get_image():
#         best_frame = await image_processor.process_video(clip)
#         image_bytes = await asyncio.to_thread(
#             image_processor.convert_result_image_to_bytes, best_frame
#         )
#         return image_bytes

#     @timed.async_("Transcription")
#     async def get_transcript():
#         transcript = (
#             await asyncio.to_thread(
#                 transcriber.run,
#                 {
#                     "audio": Audio(base64=audio),
#                 },
#             )
#         )[0]["text"]
#         return transcript

#     try:
#         image_bytes, transcript = await asyncio.gather(get_image(), get_transcript())
#         if not transcript:
#             websocket_logger.info("No transcript found")
#             return await sio.emit("no-audio", to=sid)
#         if len(transcript) > 500:
#             websocket_logger.info("Transcript too long")
#             return await sio.emit("long-audio", to=sid)
#         elif len(transcript) < 10:
#             websocket_logger.info("Transcript too short")
#             return await sio.emit("short-audio", to=sid)
#         audio_stream = (
#             await asyncio.to_thread(
#                 timed("MultiModal To Speech")(llm_workflow.run),
#                 {
#                     "text": Text(raw=transcript),
#                     "image": Image(base64=image_bytes),
#                 },
#             )
#         )[0]["audio"]
#         audio_bytes = audio_stream.getvalue()
#     except Exception as e:
#         websocket_logger.error("WebsocketError", exc_info=True)
#         raise e
#     await sio.emit("audio", audio_bytes, to=sid)
#     websocket_logger.info(
#         f"Query successfully processed. Got {len(audio_bytes) / 1024}KB audio"
#     )


@sio.on("query")
@timed.async_("Handle Query")
async def dummy_query(
    sid,
    audio: bytes,
    clip: bytes,
    output_type: Literal["audio", "chunk", "text", "url"] = "audio",
):
    websocket_logger.info(
        f"Got a query sent as audio of {len(audio) / 1024}KB and a clip of {len(clip) / 1024}KB"
    )
    websocket_logger.info(f"output_type: {output_type}")
    if output_type == "audio":
        websocket_logger.info("Sending audio")
        await sio.emit("audio", audio, to=sid)
    elif output_type == "chunk":
        websocket_logger.info("Sending audio in chunks")
        for i in range(0, len(audio), 1024):
            await sio.emit("audio-chunk", audio[i : i + 1024], to=sid)
        await asyncio.sleep(0.1)
        websocket_logger.info("Sending empty chunk")
        await sio.emit("audio-chunk", b"", to=sid)
    elif output_type == "url":
        websocket_logger.info("Sending audio url")
        url = await upload_file(audio, "query.wav", sio.environ["HTTP_ORIGIN"])
        await sio.emit("audio-url", url, to=sid)
    elif output_type == "text":
        websocket_logger.info("Sending text")
        transcript = (
            await asyncio.to_thread(
                transcriber.run,
                {
                    "audio": Audio(base64=audio),
                },
            )
        )[0]["text"]
        if not transcript:
            websocket_logger.info("No transcript found")
            return await sio.emit("no-audio", to=sid)
        elif len(transcript) > 500:
            websocket_logger.info("Transcript too long")
            return await sio.emit("long-audio", to=sid)
        elif len(transcript) < 10:
            websocket_logger.info("Transcript too short")
            return await sio.emit("short-audio", to=sid)
        await sio.emit("text", transcript, to=sid)
    websocket_logger.info("Query successfully processed.")


@sio.event
async def disconnect(sid):
    websocket_logger.info(f"Disconnected {sid}")
