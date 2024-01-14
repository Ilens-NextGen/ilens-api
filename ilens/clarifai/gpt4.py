from typing import Any, TypedDict, Optional
from ilens.clarifai.base import BaseModel, Text
from dataclasses import dataclass, field
from ilens.core.utils import getenv, getfloatenv, getintenv


class TextResponse(TypedDict):
    """Text Response"""

    text: str


@dataclass
class ClarifaiGPT4(BaseModel[Text, TextResponse]):
    """Clarifai GPT4 Model"""

    # INFERENCING PARAMS
    temperature: Optional[float] = field(
        default_factory=lambda: getfloatenv("CLARIFAI_GPT4_TEMPERATURE", None)
    )
    top_p: Optional[float] = field(
        default_factory=lambda: getfloatenv("CLARIFAI_GPT4_TOP_P", None)
    )
    max_tokens: Optional[int] = field(
        default_factory=lambda: getintenv("CLARIFAI_GPT4_MAX_TOKENS", None)
    )

    model_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_GPT4_MODEL_ID", "gpt-4-turbo")
    )
    model_version_id: Optional[str] = field(
        default_factory=lambda: getenv("CLARIFAI_GPT4_MODEL_VERSION_ID", None)
    )
    app_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_GPT4_APP_ID", "chat-completion")
    )
    user_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_GPT4_USER_ID", "openai")
    )

    def parse_output(self, output: Any) -> TextResponse:
        return {"text": output.data.text.raw}
