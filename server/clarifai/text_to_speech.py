from typing import Any, Optional, TypedDict
from server.clarifai.base import BaseModel, Text
from server.utils import getenv, getfloatenv
from dataclasses import field, dataclass
from io import BytesIO

AVAILABLE_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


class AudioResponse(TypedDict):
    """Audio Response"""

    audio: BytesIO


@dataclass
class ClarifaiTextToSpeech(BaseModel[Text, AudioResponse]):
    """Clarifai Text To Speech Model"""

    # INFERENCING PARAMS
    voice: str = field(default_factory=lambda: getenv("CLARIFAI_TTS_VOICE", "alloy"))
    speed: Optional[float] = field(
        default_factory=lambda: getfloatenv("CLARIFAI_TTS_SPEED", None)
    )
    model_name = "text to speech"

    # MODEL PARAMS

    model_id: str = field(default_factory=lambda: getenv("CLARIFAI_TTS_MODEL_ID"))
    model_version_id: Optional[str] = field(
        default_factory=lambda: getenv("CLARIFAI_TTS_MODEL_VERSION_ID", None)
    )
    app_id: str = field(default_factory=lambda: getenv("CLARIFAI_TTS_APP_ID"))
    user_id: str = field(default_factory=lambda: getenv("CLARIFAI_TTS_USER_ID"))

    def _get_inference_params(self) -> dict[str, Any] | None:
        """Returns the model's inference params."""
        params: dict[str, Any] = {}
        if self.speed is not None:
            params["speed"] = self.speed
        assert self.voice in AVAILABLE_VOICES, f"Voice {self.voice} not available."
        params["voice"] = self.voice
        if not params:
            return None
        return params

    def parse_output(self, output: Any) -> AudioResponse:
        audio_bytes: bytes = output.data.audio.base64
        buffer = BytesIO(audio_bytes)
        return {"audio": buffer}
