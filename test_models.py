from pathlib import Path
from server.clarifai import (
    ClarifaiTextToSpeech,
    Text,
    Audio,
    Image,
    ClarifaiGPT4,
    ClarifaiTranscription,
    ClarifaiImageDetection,
)
from server.clarifai.image_processing import ObjectDetectionInfo
import logging


logging.basicConfig(level=logging.INFO)

FILE_NAME = "audio.wav"
VOICE = "alloy"
MAX_TOKENS = 100
PROMPT = (
    "Generate a short story about a robot. This story should not be more than 50 words."
)

logging.info("Loading models...")
llm = ClarifaiGPT4(max_tokens=MAX_TOKENS)
tts = ClarifaiTextToSpeech(voice=VOICE)
stt = ClarifaiTranscription()
detect = ClarifaiImageDetection()
logging.info("Models loaded.")
logging.info("Generating story...")
story = llm.run({"text": Text(raw=PROMPT)})[0]["text"]
logging.info("Story generated: %s", story)
logging.info("Generating audio...")
story_audio = tts.run({"text": Text(raw=story)})[0]["audio"]
story_audio.seek(0)
logging.info("Audio generated.")
logging.info("Saving audio...")
with open(FILE_NAME, "wb") as f:
    f.write(story_audio.read())
logging.info("Audio saved.")
logging.info("Transcribing audio...")
story_audio.seek(0)
story_bytes = story_audio.read()
story_transcript = stt.run({"audio": Audio(base64=Path("audio.wav").read_bytes())})[
    0
]["text"]
logging.info("Transcript generated: %s", story_transcript)

obstacles = ["man", "woman", "boy", "girl", "car", "bus",
             "lorry", "truck", "tree", "window", "wheel", "table", "chair"
             "door", "bicycle", "motorcycle", "bike"
             "traffic light", "traffic sign", "stop sign", "parking meter", "bench",
             ]
values = detect.run({"image": Image(base64=Path("test4.jpeg").read_bytes())})
print(len(values))
for x in detect.interpret(values):
    print(x)
