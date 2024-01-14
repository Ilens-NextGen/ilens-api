from typing import Any, TypedDict, Optional
from ilens.clarifai.base import BaseModel, Audio
from ilens.core.utils import getenv
from dataclasses import field, dataclass


class TextResponse(TypedDict):
    """Text Response"""

    text: str


@dataclass
class ClarifaiSpeechRecognition(BaseModel[Audio, TextResponse]):
    """Clarifai Speech Recognition Model"""

    model_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_ASSEMBLY_MODEL_ID", "whisper")
    )
    model_version_id: Optional[str] = field(
        default_factory=lambda: getenv("CLARIFAI_STT_MODEL_VERSION_ID", None)
    )
    app_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_STT_APP_ID", "transcription")
    )
    user_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_STT_USER_ID", "openai")
    )

    def parse_output(self, output: Any) -> TextResponse:
        print(output)
        return {"text": output.data.text.raw}
