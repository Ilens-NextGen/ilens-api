from dataclasses import dataclass, field
import io
from pathlib import Path
from typing import Any, Generic, Optional, Protocol, Type, TypeAlias, TypeVar, Union
from server.utils import getenv, loadenv
# type: ignore[import]
import clarifai_grpc.grpc.api.resources_pb2 as resources_pb2
# type: ignore[import]
import clarifai_grpc.grpc.api.service_pb2 as service_pb2
# type: ignore[import]
import clarifai_grpc.grpc.api.service_pb2_grpc as service_pb2_grpc
# type: ignore[import]
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from grpc import Channel  # type: ignore[import]
# type: ignore[import]
from google.protobuf.internal.containers import RepeatedCompositeFieldContainer
from google.protobuf.struct_pb2 import Struct  # type: ignore[import]
# type: ignore[import]
from clarifai_grpc.grpc.api.status import status_code_pb2
# type: ignore[import]
from clarifai_grpc.grpc.api.status.status_pb2 import Status
from server.logger import CustomLogger
from functools import wraps

Image: TypeAlias = resources_pb2.Image
Video: TypeAlias = resources_pb2.Video
Audio: TypeAlias = resources_pb2.Audio
Text: TypeAlias = resources_pb2.Text
Concept: TypeAlias = resources_pb2.Concept
clarifai_logger = CustomLogger("Clarifai").get_logger()

loadenv()


class _SupportsReadSeekTell(Protocol):
    def read(self, __n: int = ...) -> bytes:
        ...

    def seek(self, __cookie: int, __whence: int) -> object:
        ...

    def tell(self) -> int:
        ...


MediaType = TypeVar("MediaType", Image, Video, Audio, Text)
ResponseType = TypeVar("ResponseType", bound=Any)


def media_from_url(
    type: Type[MediaType], url: str, allow_duplicate_url=False, **kwargs
) -> MediaType:
    """Creates a media from the url."""
    return type(url=url, allow_duplicate_url=allow_duplicate_url, **kwargs)


def media_from_bytes(type: Type[MediaType], bytes: bytes, **kwargs) -> MediaType:
    """Creates a media from the bytes."""
    if type == Text:
        return type(raw=bytes, **kwargs)
    return type(base64=bytes, **kwargs)


def media_from_file(
    type: Type[MediaType], file: Union[str, Path, _SupportsReadSeekTell], **kwargs
) -> MediaType:
    """Creates a media from the file."""
    if isinstance(file, (str, Path)):
        with open(file, "rb") as f:
            file = io.BytesIO(f.read())
    return media_from_bytes(type, file.read(), **kwargs)


def media_from_text(type: Type[MediaType], text: str, **kwargs) -> MediaType:
    """Creates a media from the text."""
    if type != Text:
        raise ValueError("Only Text media type supports text.")
    return type(raw=text, **kwargs)


def logger(model_name="", model_id=""):
    """Logger for my run function"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            clarifai_logger.info(
                f"Running {model_name} model with id {model_id}")
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                clarifai_logger.error(
                    f"Error running {model_name} model with id {model_id}",
                    exc_info=True,
                )
                raise e
            clarifai_logger.info(
                f"Finished running {model_name} model with id {model_id}"
            )
            return result

        return wrapper

    return decorator


@dataclass
class BaseModel(Generic[MediaType, ResponseType]):
    model_id: str
    """The model id."""
    app_id: str
    """The app id."""
    user_id: str
    """The user id."""
    model_version_id: Optional[str] = None
    """The model version id."""
    """A name describing the model's function"""
    pat: str = field(default_factory=lambda: getenv("CLARIFAI_PAT"))

    @property
    def model_name(self) -> str:
        """Returns the model name."""
        return "{app}/{model}@{user}".format(
            model=self.model_id,
            app=self.app_id,
            user=self.user_id,
        )

    def _get_metadata(self) -> dict[str, str]:
        """Returns the metadata for the request."""
        return {"authorization": f"Key {self.pat}"}

    def _get_user_app_id(self) -> resources_pb2.UserAppIDSet:
        """Returns the user app id."""
        return resources_pb2.UserAppIDSet(
            user_id=self.user_id,
            app_id=self.app_id,
        )

    def _get_inference_params(self) -> Optional[dict[str, Any]]:
        """Returns the model's inference params."""
        return None

    def _get_selected_concepts(self) -> list[Concept]:
        """Returns the selected concepts."""
        return []

    def _get_max_concepts(self) -> Optional[int]:
        """Returns the max concepts."""
        return None

    def _get_minimum_value(self) -> Optional[float]:
        """Returns the minimum probability threshold."""
        return None

    def _get_language(self) -> Optional[str]:
        """Returns the language."""
        return None

    def _get_model_output_info_config(self) -> Optional[resources_pb2.OutputConfig]:
        """Returns the output config."""
        output_config: dict[str, Any] = {}
        selected_concepts = self._get_selected_concepts()
        max_concepts = self._get_max_concepts()
        minimum_value = self._get_minimum_value()
        language = self._get_language()

        if selected_concepts:
            output_config["select_concepts"] = selected_concepts
        if max_concepts is not None:
            output_config["max_concepts"] = max_concepts
        if minimum_value is not None:
            output_config["min_value"] = minimum_value
        if language is not None:
            output_config["language"] = language

        if not output_config:
            return None

        return resources_pb2.OutputConfig(**output_config)

    def _get_model_output_info(self) -> Optional[resources_pb2.OutputInfo]:
        """Returns the output info."""
        output_config = self._get_model_output_info_config()
        output_info = {}
        if output_config is not None:
            output_info["output_config"] = output_config
        if not output_info:
            return None

        return resources_pb2.OutputInfo(**output_info)

    def _get_model_version_output_info(self) -> Optional[resources_pb2.OutputInfo]:
        """Returns the model output info."""
        output_info = {}
        inference_params = self._get_inference_params()
        if inference_params is not None:
            params = Struct()
            params.update(inference_params)
            output_info["params"] = params
        if output_info is None:
            return None
        return resources_pb2.OutputInfo(**output_info)

    def _get_model_version(self) -> Optional[resources_pb2.ModelVersion]:
        """Returns the model version."""
        model_output_info = self._get_model_version_output_info()
        if model_output_info is None:
            return None
        return resources_pb2.ModelVersion(
            output_info=self._get_model_version_output_info(),
        )

    def _get_model(self) -> Optional[resources_pb2.Model]:
        """Returns the model."""
        model_version = self._get_model_version()
        get_output_info = self._get_model_output_info()
        model = {}
        if model_version is not None:
            model["model_version"] = model_version
        if get_output_info is not None:
            model["output_info"] = get_output_info
        if not model:
            return None
        return resources_pb2.Model(**model)

    def _create_channel(
        self,
    ) -> tuple[service_pb2_grpc.V2Stub, tuple[tuple[str, str], ...]]:
        """Creates the channel and returns the stub and metadata."""
        channel: Channel = ClarifaiChannel.get_grpc_channel()
        stub = service_pb2_grpc.V2Stub(channel)
        metadata = tuple(self._get_metadata().items())
        return stub, metadata

    # @profile  # noqa: F821 # type: ignore
    def _create_request(self, inputs: list[resources_pb2.Input]):
        return service_pb2.PostModelOutputsRequest(
            user_app_id=self._get_user_app_id(),
            model_id=self.model_id,
            version_id=self.model_version_id,
            inputs=inputs,
            model=self._get_model(),
        )

    def _create_input(self, data: dict[str, MediaType]) -> resources_pb2.Input:
        return resources_pb2.Input(
            data=data,
        )

    # @profile  # noqa: F821 # type: ignore
    def _execute_request(
        self, request: service_pb2.PostModelOutputsRequest
    ) -> service_pb2.MultiOutputResponse:
        stub, metadata = self._create_channel()
        return stub.PostModelOutputs(request, metadata=metadata)

    def parse_output(self, output: Any) -> ResponseType:
        return output

    def parse_outputs(
        self, outputs: RepeatedCompositeFieldContainer
    ) -> list[ResponseType]:
        return [self.parse_output(output) for output in outputs]

    def handle_error(self, error: Status) -> None:
        raise Exception(f"{error.description}")

    def run(self, *data: dict[str, MediaType]) -> list[ResponseType]:
        @logger(model_name=self.model_name, model_id=self.model_id)
        def main_run(*data: dict[str, MediaType]) -> list[ResponseType]:
            """Runs the model on the data."""
            inputs = [self._create_input(d) for d in data]
            request = self._create_request(inputs)
            response = self._execute_request(request)
            if response.status.code != status_code_pb2.SUCCESS:
                self.handle_error(response.status)
                return []
            else:
                return self.parse_outputs(response.outputs)

        return main_run(*data)


@dataclass
class BaseWorkflow(Generic[MediaType, ResponseType]):
    """A clarifai workflow."""

    user_id: str
    """The user id."""
    app_id: str
    """The app id."""
    workflow_id: str
    """The workflow id."""
    pat: str = field(default_factory=lambda: getenv("CLARIFAI_PAT"))

    @property
    def model_name(self) -> str:
        """Returns the model name."""
        return "{workflow}/{app}@{user}".format(
            workflow=self.workflow_id,
            app=self.app_id,
            user=self.user_id,
        )

    # @profile  # noqa: F821 # type: ignore
    def _create_channel(
        self,
    ) -> tuple[service_pb2_grpc.V2Stub, tuple[tuple[str, str], ...]]:
        """Creates the channel and returns the stub and metadata."""
        channel: Channel = ClarifaiChannel.get_grpc_channel()
        stub = service_pb2_grpc.V2Stub(channel)
        metadata = tuple(self._get_metadata().items())
        return stub, metadata

    def _get_metadata(self):
        """Returns the metadata for the request."""
        return {"authorization": f"Key {self.pat}"}

    def _get_user_app_id(self) -> resources_pb2.UserAppIDSet:
        """Returns the user app id."""
        return resources_pb2.UserAppIDSet(
            user_id=self.user_id,
            app_id=self.app_id,
        )

    def _create_input(self, data: dict[str, MediaType]) -> resources_pb2.Input:
        return resources_pb2.Input(
            data=data,
        )

    # @profile  # noqa: F821 # type: ignore
    def _create_workflow_request(
        self, inputs: list[resources_pb2.Input]
    ) -> service_pb2.PostWorkflowResultsRequest:
        return service_pb2.PostWorkflowResultsRequest(
            user_app_id=self._get_user_app_id(),
            workflow_id=self.workflow_id,
            inputs=inputs,
        )

    # @profile  # noqa: F821 # type: ignore
    def _execute_request(
        self, request: service_pb2.PostWorkflowResultsRequest
    ) -> service_pb2.MultiOutputResponse:
        stub, metadata = self._create_channel()
        return stub.PostWorkflowResults(request, metadata=metadata)

    def parse_output(self, output: Any) -> ResponseType:
        return output

    def parse_outputs(
        self, outputs: RepeatedCompositeFieldContainer
    ) -> list[ResponseType]:
        return [self.parse_output(output) for output in outputs]

    def handle_error(self, error: Status) -> None:
        raise Exception(f"{error.description}")

    # @profile  # noqa: F821 # type: ignore
    def run(self, *data: dict[str, MediaType]) -> list[ResponseType]:
        """Runs the workflow on the data."""

        @logger(model_name=self.model_name, model_id=self.workflow_id)
        def main_run(*data: dict[str, MediaType]) -> list[ResponseType]:
            inputs = [self._create_input(d) for d in data]
            request = self._create_workflow_request(inputs)
            response = self._execute_request(request)
            if response.status.code != status_code_pb2.SUCCESS:
                self.handle_error(response.status)
                return []
            else:
                return self.parse_outputs(response.results)

        return main_run(*data)
