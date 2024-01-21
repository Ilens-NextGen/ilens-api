from dataclasses import dataclass, field
from typing import Any, Optional, TypedDict
from itertools import groupby
from server.clarifai.base import BaseModel, Concept, Image
from server.utils import getenv, getfloatenv, getintenv, getlistenv

DEFAULT_OBSTACLES = [
    "Ambulance",
    "Barrel",
    "Bathroom cabinet",
    "Bed",
    "Bench",
    "Bicycle",
    "Bookcase",
    "Boy",
    "Building",
    "Bus",
    "Cabinetry",
    "Car",
    "Cart",
    "Chair",
    "Christmas tree",
    "Closet",
    "Coffee table",
    "Convenience store",
    "Couch",
    "Countertop",
    "Dishwasher",
    "Dog",
    "Door",
    "Drawer",
    "Filing cabinet",
    "Fire hydrant",
    "Fountain",
    "Infant bed",
    "Kitchen & dining room table",
    "Ladder",
    "Land vehicle",
    "Luggage and bags",
    "Man",
    "Motorcycle",
    "Office building",
    "Palm tree",
    "Parking meter",
    "Piano",
    "Plant",
    "Porch",
    "Refrigerator",
    "Sculpture",
    "Shelf",
    "Sofa bed",
    "Sports equipment",
    "Stationary bicycle",
    "Stop sign",
    "Street light",
    "Tank",
    "Taxi",
    "Tableware",
    "Table",
    "Television",
    "Tent",
    "Traffic light",
    "Traffic sign",
    "Train",
    "Training bench",
    "Tree",
    "Truck",
    "Van",
    "Vehicle",
    "Wardrobe",
    "Washing machine",
    "Waste container",
    "Wheelchair",
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


class ObstacleInfo(TypedDict):
    """Obstacle Info"""

    name: str
    position: str
    distance: str
    depth: float
    value: float


@dataclass
class ClarifaiImageDetection(BaseModel[Image, list[ObstacleInfo]]):
    """Clarifai Image Detection Model"""

    # MODEL PARAMS
    model_name = "obstacle detection"
    model_id: str = field(
        default_factory=lambda: getenv(
            "CLARIFAI_DETECTION_MODEL_ID", "general-image-detection"
        )
    )
    model_version_id: Optional[str] = field(
        default_factory=lambda: getenv("CLARIFAI_DETECTION_MODEL_VERSION_ID", None)
    )
    app_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_DETECTION_APP_ID", "main")
    )
    user_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_DETECTION_USER_ID", "clarifai")
    )

    # PREDICTION PARAMS
    selected_concept_names: list[str] = field(
        default_factory=lambda: getlistenv(
            "CLARIFAI_DETECTION_SELECTED_CONCEPT_NAMES", DEFAULT_OBSTACLES
        )
    )
    selected_concept_ids: list[str] = field(
        default_factory=lambda: getlistenv(
            "CLARIFAI_DETECTION_SELECTED_CONCEPT_IDS", []
        )
    )
    max_concepts: Optional[int] = field(
        default_factory=lambda: getintenv("CLARIFAI_DETECTION_MAX_CONCEPTS", None)
    )
    minimum_value: Optional[float] = field(
        default_factory=lambda: getfloatenv("CLARIFAI_DETECTION_MINIMUM_VALUE", None)
    )
    max_distance_threshold: float = field(
        default_factory=lambda: getfloatenv(
            "CLARIFAI_DETECTION_MAX_DISTANCE_THRESHOLD", 0.05
        )
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

    def parse_output(self, output: Any) -> list[ObstacleInfo]:
        regions = output.data.regions
        result: list[ObstacleInfo] = []
        for region in regions:
            location_info: LocationInfo = {
                "top": round(region.region_info.bounding_box.top_row, 3),
                "left": round(region.region_info.bounding_box.left_col, 3),
                "bottom": round(region.region_info.bounding_box.bottom_row, 3),
                "right": round(region.region_info.bounding_box.right_col, 3),
            }
            position, distance, depth = self.classify_location(location_info)
            # TODO: accept all objects
            # only accept objects that are near
            if "near" not in distance:
                continue
            for concept in region.data.concepts:
                object_info: ObstacleInfo = {
                    "name": concept.name,
                    "value": round(concept.value, 4),
                    "position": position,
                    "distance": distance,
                    "depth": depth,
                }
                result.append(object_info)
        return result

    def classify_location(self, location: LocationInfo):
        center_x = (location["left"] + location["right"]) / 2

        width = location["right"] - location["left"]
        height = location["bottom"] - location["top"]

        if center_x < 0.5:
            position = "left"
        else:
            position = "right"

        if width * height > 0.5:
            distance = "very near"
        elif width * height > self.max_distance_threshold:
            distance = "near"
        elif width * height < 0.02:
            distance = "very far"
        else:
            distance = "far"
        return position, distance, width * height

    def construct_warning(self, output: list[ObstacleInfo]) -> str:
        output.sort(key=lambda x: x["position"])
        groups = groupby(output, lambda x: x["position"])
        sentences = []
        for position, _group in groups:
            group = list(_group)
            sentence = f"In front on your {position} there {'are' if len(group) > 1 else 'is a'}: "
            for value in group:
                sentence += f"{value['name']} {value['distance']}, "
            sentences.append(sentence[:-2])
        return " and ".join(sentences)


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
        default_factory=lambda: getenv("CLARIFAI_RECOGNITION_MODEL_VERSION_ID", None)
    )
    app_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_RECOGNITION_APP_ID", "main")
    )
    user_id: str = field(
        default_factory=lambda: getenv("CLARIFAI_RECOGNITION_USER_ID", "clarifai")
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
        default_factory=lambda: getintenv("CLARIFAI_RECOGNITION_MAX_CONCEPTS", None)
    )
    minimum_value: Optional[float] = field(
        default_factory=lambda: getfloatenv("CLARIFAI_RECOGNITION_MINIMUM_VALUE", None)
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
