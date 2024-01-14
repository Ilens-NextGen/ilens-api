from dataclasses import dataclass, field
from typing import Any, Optional, TypedDict, Union
from ilens.clarifai.base import BaseModel, Image, Text
from ilens.core.utils import getenv, getfloatenv, getintenv


class TextResponse(TypedDict):
    """Text Response"""

    text: str


@dataclass
class ClarifaiGPT4V(BaseModel[Union[Image, Text], TextResponse]):
    """Clarifai GPT4 MultiModal Model"""

    # INFERENCING PARAMS

    temperature: Optional[float] = field(
        default_factory=lambda: getfloatenv("CLARIFAI_GPT4V_TEMPERATURE", None)
    )
    top_p: Optional[float] = field(
        default_factory=lambda: getfloatenv("CLARIFAI_GPT4V_TOP_P", None)
    )
    max_tokens: Optional[int] = field(
        default_factory=lambda: getintenv("CLARIFAI_GPT4V_MAX_TOKENS", None)
    )

    # MODEL PARAMS

    model_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_GPT4V_MODEL_ID", "openai-gpt-4-vision")
    )
    model_version_id: Optional[str] = field(
        default_factory=lambda: getenv("CLARIFAI_GPT4V_MODEL_VERSION_ID", None)
    )
    app_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_GPT4V_APP_ID", "chat-completion")
    )
    user_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_GPT4V_USER_ID", "openai")
    )

    def _get_inference_params(self) -> dict[str, Any] | None:
        """Returns the model's inference params."""
        params = {}
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if not params:
            return None
        return params

    def parse_output(self, output: Any) -> TextResponse:
        return {"text": output.data.text.raw}
