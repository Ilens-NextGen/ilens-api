import asyncio
from pathlib import Path
from typing import Literal, TypedDict
from uuid import uuid4
from server import settings
from server.clarifai import ClarifaiTranscription
from server.clarifai.base import Audio, Text
from server.clarifai.workflows import ClarifaiMultimodalToSpeechWF
from server.clarifai.image_processor import AsyncVideoProcessor
from server.clarifai import Image, ClarifaiImageRecognition, ClarifaiImageDetection
from server.socket import server as sio
from server.utils import timed
from server.logger import CustomLogger
from server.settings import SERVER_ID
import aiofiles  # type: ignore
import aiofiles.os  # type: ignore

BASE_DIR = Path(__file__).parent.parent

TEMPLATE = """
system:
You're an AI aiding the visually impaired. Analyze images from the user's phone camera
and respond to their spoken queries. If unsure, say "I'm not sure, but I think it's a <answer>".
If confident, say "I'm very sure it's a <answer>". If unable to answer due to security reasons,
politely say "I'm sorry, I can't provide details on this image for security reasons".
Keep it brief. Assure users of privacy.

NOTE: Keep it short and simple. This app is a safe app so you are expected to be able to
answer personal questions, never decline to answer due to security reasons.

Respond to user's query: "{transcript}"
"""

if settings.DEBUG:
    BASE_URL = "http://localhost:8000"
else:
    BASE_URL = f"https://ilens.allcanlearn.me/{SERVER_ID}"

image_recognition = ClarifaiImageRecognition()
transcriber = ClarifaiTranscription()
llm_workflow = ClarifaiMultimodalToSpeechWF()
image_processor = AsyncVideoProcessor()
image_detection = ClarifaiImageDetection()
websocket_logger = CustomLogger("Websocket").get_logger()


class resource(TypedDict):
    raw: bytes
    mimetype: str


async def upload_file(content: bytes, filename: str, base_url: str):
    id = uuid4().hex[:8]
    location = BASE_DIR / "uploads" / f"{id}_{filename}"
    websocket_logger.info(f"Uploading file to {location}")
    await aiofiles.os.makedirs(location.parent, exist_ok=True)
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
async def recognize(sid, clip: resource):
    websocket_logger.info("Clip processing began")
    try:
        async with timed("Image Selection For Recognizer"):
            best_frame = await image_processor.process_video(
                clip["raw"], clip["mimetype"]
            )
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
async def detect(sid, clip: resource):
    websocket_logger.info("Clip processing began")
    try:
        async with timed("Image Selection For Detector"):
            best_frame = await image_processor.process_video(
                clip["raw"], clip["mimetype"]
            )
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


@sio.event
@timed.async_("Handle Query")
async def query(
    sid,
    audio: resource,
    clip: resource,
    output_type: Literal["audio", "chunk", "text", "url"] = "audio",
):
    clip_raw = clip["raw"]
    clip_type = clip["mimetype"]
    clip_size = len(clip_raw) / 1024
    audio_raw = audio["raw"]
    audio_type = audio["mimetype"]
    audio_size = len(audio_raw) / 1024
    websocket_logger.info(
        (
            f"Got a query sent as {audio_type} audio of {audio_size}KB"
            f" and a {clip_type} clip of {clip_size}KB"
        )
    )

    @timed.async_("Image Selection For Query")
    async def get_image():
        best_frame = await image_processor.process_video(clip_raw, clip_type)
        image_bytes = await asyncio.to_thread(
            image_processor.convert_result_image_to_bytes, best_frame
        )
        return image_bytes

    @timed.async_("Transcription")
    async def get_transcript():
        transcript = (
            await asyncio.to_thread(
                transcriber.run,
                {
                    "audio": Audio(base64=audio_raw),
                },
            )
        )[0]["text"]
        return transcript

    try:
        image_bytes, transcript = await asyncio.gather(get_image(), get_transcript())
        if not transcript:
            websocket_logger.info("No transcript found")
            return await sio.emit("no-audio", to=sid)
        if len(transcript) > 500:
            websocket_logger.info("Transcript too long")
            return await sio.emit("long-audio", to=sid)
        elif len(transcript) < 10:
            websocket_logger.info("Transcript too short")
            return await sio.emit("short-audio", to=sid)
        if output_type == "text":
            websocket_logger.info("Sending text")
            return await sio.emit("text", transcript, to=sid)
        audio_stream = (
            await asyncio.to_thread(
                timed("MultiModal To Speech")(llm_workflow.run),
                {
                    "text": Text(raw=TEMPLATE.format(transcript=transcript)),
                    "image": Image(base64=image_bytes),
                },
            )
        )[0]["audio"]
        audio_bytes = audio_stream.getvalue()
        websocket_logger.info(
            "Query successfully processed." f" Got {len(audio_bytes) / 1024}KB audio"
        )
        if output_type == "audio":
            websocket_logger.info("Sending audio")
            return await sio.emit("audio", audio_bytes, to=sid)
        elif output_type == "chunk":
            websocket_logger.info("Sending audio in chunks")
            for i in range(0, len(audio_bytes), 1024):
                await sio.emit("audio-chunk", audio_bytes[i : i + 1024], to=sid)
            await asyncio.sleep(0.1)
            await sio.emit("audio-chunk", b"", to=sid)
            websocket_logger.info("Finished sending chunks")
        elif output_type == "url":
            websocket_logger.info("Sending audio url")
            url = await upload_file(audio_bytes, "query.wav", BASE_URL)
            await sio.emit("audio-url", url, to=sid)
    except Exception as e:
        websocket_logger.error("WebsocketError", exc_info=True)
        raise e


@sio.event
async def disconnect(sid):
    websocket_logger.info(f"Disconnected {sid}")
