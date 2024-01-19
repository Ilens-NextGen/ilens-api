import asyncio
from server.clarifai import ClarifaiTranscription, Audio
from server.clarifai import Text
from server.clarifai.workflows import ClarifaiMultimodalToSpeechWF
from server.clarifai.image_processor import AsyncVideoProcessor
from server.clarifai import Image, ClarifaiImageRecognition
from server.socket import server as sio
from server.utils import timed
from server.logger import CustomLogger

image_recognition = ClarifaiImageRecognition()
transcriber = ClarifaiTranscription()
llm_workflow = ClarifaiMultimodalToSpeechWF()
image_processor = AsyncVideoProcessor()

websocket_logger = CustomLogger("Websocket").get_logger()

@sio.event
async def connect(sid, environ):
    websocket_logger.info(f"Connected {sid}")

@sio.event
@timed.async_("Handle Recognition")
async def recognize(sid, blob: bytes, duration: float):
    websocket_logger.info("Clip processing began")
    try:
        async with timed("Image Selection For Recognizer"):
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
    except Exception as e:
        websocket_logger.error(f"WebsocketError", exc_info=True)
        raise e
    websocket_logger.info("Clip successfully processed")

@sio.event
@timed.async_("Handle Detection")
async def detect(sid, clip: bytes):
    websocket_logger.info("Clip processing began")
    try:
        async with timed("Image Selection For Detector"):
            best_frame = await image_processor.process_video(clip)
            image_bytes = image_bytes = await asyncio.to_thread(
                image_processor.convert_result_image_to_bytes, best_frame
            )
        detection = (
            await asyncio.to_thread(
                timed("Image Recognition")(image_recognition.run),
                {"image": Image(base64=image_bytes)},
            )
        )[0]
        await sio.emit(
            "detection",
            detection,
            to=sid,
        )
    except Exception as e:
        websocket_logger.error(f"WebsocketError", exc_info=True)
        raise e
    websocket_logger.info("Clip successfully processed")

@sio.event
# @profile  # noqa: F821 # type: ignore
@timed.async_("Handle Query")
async def query(sid, audio: bytes, clip: bytes):
    websocket_logger.info(f"Got a query sent as audio of {len(audio) / 1024}KB and a clip of {len(clip) / 1024}KB")
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
    try:
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
    except Exception as e:
        websocket_logger.error(f"WebsocketError", exc_info=True)
        raise e
    await sio.emit("audio", audio_bytes, to=sid)
    websocket_logger.info(f"Query successfully processed. Got {len(audio_bytes) / 1024}KB audio")


@sio.event
async def disconnect(sid):
    websocket_logger.info(f"Disconnected {sid}")
