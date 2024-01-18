from typing import Any, TypedDict, Optional
from server.clarifai.base import BaseModel, Audio
from server.utils import getenv
from dataclasses import field, dataclass


class TextResponse(TypedDict):
    """Text Response"""

    text: str


@dataclass
class ClarifaiTranscription(BaseModel[Audio, TextResponse]):
    """Clarifai Speech Transcription Model"""

    model_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_TRANSCRIPTION_MODEL_ID")
    )
    model_version_id: Optional[str] = field(
        default_factory=lambda: getenv("CLARIFAI_TRANSCRIPTION_MODEL_VERSION_ID", None)
    )
    app_id: str = field(
        default_factory=lambda: getenv(
            "CLARIFAI_TRANSCRIPTION_APP_ID",
        )
    )
    user_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_TRANSCRIPTION_USER_ID")
    )

    def parse_output(self, output: Any) -> TextResponse:
        return {"text": output.data.text.raw}
