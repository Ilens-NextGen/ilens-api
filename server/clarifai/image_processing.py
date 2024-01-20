from dataclasses import dataclass, field
from typing import Any, Optional, TypedDict

from server.clarifai.base import BaseModel, Concept, Image
from server.utils import getenv, getfloatenv, getintenv, getlistenv

DEFAULT_OBSTACLES = [
    "man", "woman", "boy", "girl", "car", "bus",
    "lorry", "truck", "tree", "table", "chair",
    "door", "bicycle", "motorcycle", "bike",
    "traffic light", "traffic sign", "stop sign",
    "parking meter", "bench", "wall", "wardrobe", "bed"
]


class LocationInfo(TypedDict):
    """Object Location Info"""

    top: float
    left: float
    bottom: float
    right: float


class ObjectDetectionInfo(TypedDict):
    """Object Info"""

    id: str
    name: str
    value: float
    location: LocationInfo


class ObjectRecognitionInfo(TypedDict):
    """Object Info"""

    id: str
    name: str
    confidence: float


@dataclass
class ClarifaiImageDetection(BaseModel[Image, list[ObjectDetectionInfo]]):
    """Clarifai Image Detection Model"""

    # MODEL PARAMS
    model_name = "obstacle detection"
    model_id: str = field(
        default_factory=lambda: getenv(
            "CLARIFAI_DETECTION_MODEL_ID", "general-image-detection"
        )
    )
    model_version_id: Optional[str] = field(
        default_factory=lambda: getenv(
            "CLARIFAI_DETECTION_MODEL_VERSION_ID", None)
    )
    app_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_DETECTION_APP_ID", "main")
    )
    user_id: str = field(
        default_factory=lambda: getenv(
            "CLARIFAI_DETECTION_USER_ID", "clarifai")
    )

    # PREDICTION PARAMS
    selected_concept_names: list[str] = field(
        default_factory=lambda: getlistenv(
            "CLARIFAI_DETECTION_SELECTED_CONCEPT_NAMES", []
        )
    )
    selected_concept_ids: list[str] = field(
        default_factory=lambda: getlistenv(
            "CLARIFAI_DETECTION_SELECTED_CONCEPT_IDS", []
        )
    )
    max_concepts: Optional[int] = field(
        default_factory=lambda: getintenv(
            "CLARIFAI_DETECTION_MAX_CONCEPTS", None)
    )
    minimum_value: Optional[float] = field(
        default_factory=lambda: getfloatenv(
            "CLARIFAI_DETECTION_MINIMUM_VALUE", None)
    )
    max_distance_threshold: float = field(
        default_factory=lambda: getfloatenv(
            "CLARIFAI_DETECTION_MAX_DISTANCE_THRESHOLD", 0.05)
    )

    def _get_selected_concepts(self) -> list[str]:
        """Returns the selected concepts."""
        return [Concept(id=concept_id) for concept_id in self.selected_concept_ids] + [
            Concept(name=concept_name) for concept_name in self.selected_concept_names
        ]

    def _get_max_concepts(self) -> int | None:
        """Returns the max concepts."""
        return self.max_concepts

    def _get_minimum_value(self) -> float | None:
        """Returns the minimum probability threshold."""
        return self.minimum_value

    def parse_output(self, output: Any) -> list[ObjectDetectionInfo]:
        regions = output.data.regions
        result: list[ObjectDetectionInfo] = []
        for region in regions:
            location_info: LocationInfo = {
                "top": round(region.region_info.bounding_box.top_row, 3),
                "left": round(region.region_info.bounding_box.left_col, 3),
                "bottom": round(region.region_info.bounding_box.bottom_row, 3),
                "right": round(region.region_info.bounding_box.right_col, 3),
            }
            for concept in region.data.concepts:
                object_info: ObjectDetectionInfo = {
                    "id": concept.id,
                    "name": concept.name,
                    "value": round(concept.value, 4),
                    "location": location_info,
                }
                result.append(object_info)
        return result

    def classify_location(self, location: LocationInfo):
        center_x = (location['left'] + location['right']) / 2
        # remove the line below ?
        center_y = (location['top'] + location['bottom']) / 2

        width = location['right'] - location['left']
        height = location['bottom'] - location['top']

        if center_x < 0.5:
            position = "left"
        else:
            position = "right"

        if width * height > self.max_distance_threshold:
            distance = "near"
        elif width * height > 0.08:
            distance = "very near"
        elif width * height < 0.02:
            distance = "very far"
        else:
            distance = "far"
        return position, distance

    def interpret(self, output: list[ObjectDetectionInfo]) -> list[ObjectDetectionInfo]:
        # FIXME: The maximim number of concepts that can be identified is 20
        # this means one of our concepts might not be among the selected 20
        # concepts. Can we filter in the request?
        # check the selected_concepts attribute
        result = [
            n for n in output if n['name'].lower() in DEFAULT_OBSTACLES]
        final = []
        for x in result:
            r = {}
            horizontal_position, size = self.classify_location(x['location'])
            r['position'] = horizontal_position
            r['distance'] = size
            r['name'] = x['name'].lower()
            final.append(x)
        return result


@dataclass
class ClarifaiImageRecognition(BaseModel[Image, list[ObjectRecognitionInfo]]):
    """Clarifai Image Recognition Model"""

    # MODEL PARAMS
    model_id: str = field(
        default_factory=lambda: getenv(
            "CLARIFAI_RECOGNITION_MODEL_ID", "general-image-recognition"
        )
    )
    model_version_id: Optional[str] = field(
        default_factory=lambda: getenv(
            "CLARIFAI_RECOGNITION_MODEL_VERSION_ID", None)
    )
    app_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_RECOGNITION_APP_ID", "main")
    )
    user_id: str = field(
        default_factory=lambda: getenv(
            "CLARIFAI_RECOGNITION_USER_ID", "clarifai")
    )
    model_name = "image recognition"

    # PREDICTION PARAMS
    selected_concept_names: list[str] = field(
        default_factory=lambda: getlistenv(
            "CLARIFAI_RECOGNITION_SELECTED_CONCEPT_NAMES", []
        )
    )
    selected_concept_ids: list[str] = field(
        default_factory=lambda: getlistenv(
            "CLARIFAI_RECOGNITION_SELECTED_CONCEPT_IDS", []
        )
    )
    max_concepts: Optional[int] = field(
        default_factory=lambda: getintenv(
            "CLARIFAI_RECOGNITION_MAX_CONCEPTS", None)
    )
    minimum_value: Optional[float] = field(
        default_factory=lambda: getfloatenv(
            "CLARIFAI_RECOGNITION_MINIMUM_VALUE", None)
    )

    def _get_selected_concepts(self) -> list[str]:
        """Returns the selected concepts."""
        return [Concept(id=concept_id) for concept_id in self.selected_concept_ids] + [
            Concept(name=concept_name) for concept_name in self.selected_concept_names
        ]

    def _get_max_concepts(self) -> int | None:
        """Returns the max concepts."""
        return self.max_concepts

    def _get_minimum_value(self) -> float | None:
        """Returns the minimum probability threshold."""
        return self.minimum_value

    def parse_output(self, output: Any) -> list[ObjectRecognitionInfo]:
        concepts = output.data.concepts
        result: list[ObjectRecognitionInfo] = []
        for concept in concepts:
            object_info: ObjectRecognitionInfo = {
                "id": concept.id,
                "name": concept.name,
                "confidence": round(concept.value, 4),
            }
            result.append(object_info)
        return result
