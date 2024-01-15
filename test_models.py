from pathlib import Path
from ilens.clarifai import (
    ClarifaiTextToSpeech,
    Text,
    Audio,
    ClarifaiGPT4,
    ClarifaiTranscription,
)
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
story_transcript = stt.run({"audio": Audio(base64=Path("morning.wav").read_bytes())})[
    0
]["text"]
logging.info("Transcript generated: %s", story_transcript)
