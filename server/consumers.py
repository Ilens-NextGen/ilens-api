import asyncio
from typing import Literal
from server.clarifai import ClarifaiTranscription
from server.clarifai.base import Audio
from server.clarifai.workflows import ClarifaiMultimodalToSpeechWF
from server.clarifai.image_processor import AsyncVideoProcessor
from server.clarifai import Image, ClarifaiImageRecognition, ClarifaiImageDetection
from server.socket import server as sio
from server.utils import timed
from server.logger import CustomLogger
from server.settings import SERVER_ID

image_recognition = ClarifaiImageRecognition()
transcriber = ClarifaiTranscription()
llm_workflow = ClarifaiMultimodalToSpeechWF()
image_processor = AsyncVideoProcessor()
image_detection = ClarifaiImageDetection()
websocket_logger = CustomLogger("Websocket").get_logger()


@sio.event
async def connect(sid, environ):
    websocket_logger.info(f"Connected {sid}")
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
    if output_type == "audio":
        await sio.emit("audio", audio, to=sid)
    elif output_type == "chunk":
        for i in range(0, len(audio), 1024):
            await sio.emit("audio-chunk", audio[i : i + 1024], to=sid)
        await asyncio.sleep(0.1)
        await sio.emit("audio-chunk", b"", to=sid)
    elif output_type == "url":
        await sio.emit(
            "url",
            "https://file-examples.com/wp-content/storage/2017/11/file_example_WAV_10MG.wav",
            to=sid,
        )
    elif output_type == "text":
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


@sio.event
async def disconnect(sid):
    websocket_logger.info(f"Disconnected {sid}")
