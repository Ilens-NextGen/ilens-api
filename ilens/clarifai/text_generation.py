import base64
from typing import Any, TypedDict, Optional, Union
from ilens.clarifai.base import BaseModel, Text, Image
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


@dataclass
class ClarifaiGPT4VAlternative(ClarifaiGPT4V):
    """Clarifai GPT4 MultiModal Model"""

    _image: Optional[Image] = field(default=None, repr=False, init=False)
    model_id: str = field(
        default_factory=lambda: getenv(
            "CLARIFAI_GPT4V_MODEL_ID", "gpt-4-vision-alternative"
        )
    )

    def _get_inference_params(self) -> dict[str, Any] | None:
        """Returns the model's inference params."""
        params: dict[str, Any] = super()._get_inference_params() or {}
        if self._image is not None:
            if self._image.url:
                params["image_url"] = self._image.url
            elif self._image.base64:
                b64 = base64.b64encode(self._image.base64).decode("utf-8")
                params["image_base64"] = b64
        if not params:
            return None
        return params

    def run(self, *data: dict[str, Image | Text]) -> list[TextResponse]:
        """Run the model on the given data."""
        images: list[Image] = []
        if len(data) != 1:
            raise ValueError("Only one input is allowed.")
        input = data[0]
        for key, value in list(input.items()):
            if isinstance(value, Image):  # type: ignore
                images.append(value)
                del input[key]

        if len(images) > 1:
            raise ValueError("Only one image is allowed.")
        if len(images) == 1:
            self._image = images[0]
        outputs = super().run(input)
        if self._image:
            self._image = None
        return outputs

    def parse_output(self, output: Any) -> TextResponse:
        return {"text": output.data.text.raw}
