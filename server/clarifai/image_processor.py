import asyncio
from io import BytesIO
from math import floor
from typing import List

import cv2
import imageio.v3 as iio
import numpy as np
from PIL import Image

from server.logger import CustomLogger

video_processor_logger = CustomLogger("VideoProcessor").get_logger()


class AsyncVideoProcessor:
    """this class is for handling videos to select the best frame for processing"""

    # @profile  # noqa: F821 # type: ignore
    async def process_video(self, video_bytes: bytes) -> np.ndarray:
        video_processor_logger.info("Began processing video")
        try:
            frames = await asyncio.to_thread(self._bytes_to_frames, video_bytes)
            gray_frames = await asyncio.to_thread(self._grays_scale_image, frames)
            best_frame_index = await asyncio.to_thread(
                self._get_sharpest_frame, gray_frames
            )
            best_frame = frames[best_frame_index]
            # return cv2.resize(best_frame, (0, 0), fx=0.95, fy=0.95)
            video_processor_logger.info("Finished processing video successfully")
            return best_frame
        except Exception as e:
            video_processor_logger.error("VideoProcessorError", exc_info=True)
            raise e

    def _bytes_to_frames(self, video_bytes: bytes) -> List[np.ndarray]:
        video_processor_logger.info("Converting video bytes to frames")
        # frames = iio.imread(video_bytes, index=None, format_hint=".mp4")
        # video_processor_logger.info("Finished converting video bytes to frames")
        # return frames 
        video_stream = io.BytesIO(video_bytes)
        video_stream.seek(0)
        file_bytes = np.asarray(bytearray(video_stream.read()), dtype=np.uint8)
        cap = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
        frames = []
        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret == False:
                break
            frames.append(frame)
        cap.release()
        video_processor_logger.info("Finished converting video bytes to frames")
        return frames

    def _grays_scale_image(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        video_processor_logger.info("Converting frames to grayscale")
        res = [cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) for frame in frames]
        video_processor_logger.info("Finished converting frames to grayscale")
        return res

    def _get_sharpest_frame(self, gray_frames: List[np.ndarray]):
        video_processor_logger.info("Getting sharpest frame")
        sharpest_frame_index = np.argmax(
            [cv2.Laplacian(gray_frame, cv2.CV_64F).var() for gray_frame in gray_frames]
        )
        video_processor_logger.info("Finished getting sharpest frame")
        # print(sharpest_frame_index)
        return sharpest_frame_index

    # @profile  # noqa: F821 # type: ignore
    def convert_result_image_to_bytes(self, image: np.ndarray) -> bytes:
        video_processor_logger.info("Converting result image to bytes")
        image_pil: Image.Image = Image.fromarray(image)
        # initial_size = len(image_pil.tobytes()) / 1024
        x, y = image_pil.size
        if image_pil.width > image_pil.height:
            x2, y2 = floor(x - 50), floor(y - 20)
        else:
            x2, y2 = floor(x - 20), floor(y - 50)
        image_pil.resize((x2, y2), Image.LANCZOS)
        buffer = BytesIO()
        image_pil.save(buffer, format="PNG", optimize=True, quality=75)
        image_bytes = buffer.getvalue()
        video_processor_logger.info("Finished converting result image to bytes")
        return image_bytes
