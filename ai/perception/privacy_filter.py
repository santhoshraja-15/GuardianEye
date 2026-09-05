"""
Responsible AI: Privacy by Design & Automated Face / Operator Blurring
"""
from typing import List
import cv2
import numpy as np
from ai.perception.detector_schemas import Detection


class PrivacyFilter:
    """
    Applies Gaussian blurring to detected human head/upper body regions
    to enforce privacy-by-design principles and prevent unconsented facial surveillance.
    """

    @staticmethod
    def apply_privacy_blur(
        image: np.ndarray,
        detections: List[Detection],
        blur_ksize: int = 51,
    ) -> np.ndarray:
        """
        Apply Gaussian blur to the upper 30% of detected 'person' bounding boxes (head region)
        """
        blurred_image = image.copy()
        h, w = blurred_image.shape[:2]

        for det in detections:
            if det.class_name == "person":
                x1, y1, x2, y2 = [int(coord) for coord in det.bbox_xyxy]
                # Clamp to image bounds
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)

                # Focus on upper head region (top 30% of height)
                person_height = y2 - y1
                head_y2 = y1 + int(person_height * 0.35)

                if head_y2 > y1 and x2 > x1:
                    head_roi = blurred_image[y1:head_y2, x1:x2]
                    # Ensure kernel size is odd
                    k = blur_ksize if blur_ksize % 2 == 1 else blur_ksize + 1
                    blurred_roi = cv2.GaussianBlur(head_roi, (k, k), 30)
                    blurred_image[y1:head_y2, x1:x2] = blurred_roi

        return blurred_image
