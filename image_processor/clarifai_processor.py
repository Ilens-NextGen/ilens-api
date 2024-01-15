import asyncio
import cv2
import numpy as np
from PIL import Image
import imageio.v3 as iio
from typing import List
from io import BytesIO


class AsyncVideoProcessor:
    """this class is for handling videos to select the best frame for processing"""

    async def process_video(self, video_bytes: bytes) -> List[np.ndarray]:
        try:
            frames = await asyncio.to_thread(self._bytes_to_frames, video_bytes)
            gray_frames = await asyncio.to_thread(self._grays_scale_image, frames)
            best_frame = await asyncio.to_thread(self._get_sharpest_frame, gray_frames)
            return cv2.resize(best_frame, (0, 0), fx=0.95, fy=0.95)  # type: ignore
        except Exception as e:
            print(f"Error processing video: {e}")
            raise e

    def _bytes_to_frames(self, video_bytes: bytes) -> List[np.ndarray]:
        frames = iio.imread(video_bytes, index=None, format_hint=".mp4")
        return frames  # type: ignore

    def _grays_scale_image(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        return [cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) for frame in frames]

    def _get_sharpest_frame(self, gray_frames: List[np.ndarray]) -> np.ndarray:
        sharpest_frame_index = np.argmax(
            [cv2.Laplacian(gray_frame, cv2.CV_64F).var() for gray_frame in gray_frames]
        )
        # print(sharpest_frame_index)
        return gray_frames[sharpest_frame_index]

    def convert_result_image_to_bytes(self, image: np.ndarray) -> bytes:
        image_pil = Image.fromarray(image)
        with BytesIO() as buffer:
            image_pil.save(buffer, format="PNG")
            return buffer.getvalue()
