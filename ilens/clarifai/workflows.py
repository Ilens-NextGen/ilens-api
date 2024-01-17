from dataclasses import dataclass, field

from clarifai_grpc.grpc.api.resources_pb2 import Input  # type: ignore[import]
from clarifai_grpc.grpc.api.service_pb2 import PostWorkflowResultsRequest  # type: ignore[import]
from ilens.clarifai.base import BaseWorkflow, Image, Text
from typing import Any, TypedDict
from io import BytesIO
from ilens.core.utils import getenv


class AudioResponse(TypedDict):
    audio: BytesIO


@dataclass
class ClarifaiMultimodalToSpeechWF(BaseWorkflow[Text | Image, AudioResponse]):
    """A  multimodal workflow that respond with audio"""

    user_id: str = field(default_factory=lambda: getenv("CLARIFAI_MMTS_USER_ID"))
    app_id: str = field(default_factory=lambda: getenv("CLARIFAI_MMTS_APP_ID"))
    workflow_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_MMTS_WORKFLOW_ID")
    )

    def _create_workflow_request(
        self, inputs: list[Input]
    ) -> PostWorkflowResultsRequest:
        req = super()._create_workflow_request(inputs)
        # print(req)
        return req

    def parse_output(self, output: Any) -> AudioResponse:
        audio_bytes: bytes = output.outputs[-1].data.audio.base64
        buffer = BytesIO(audio_bytes)
        return {"audio": buffer}
