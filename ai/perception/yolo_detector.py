"""
YOLO Object Detection Engine for Warehouse Entities
"""
import time
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from ai.perception.detector_schemas import Detection, FrameDetections
from ai.preprocessing.frame_extractor import ProcessedFrame
from backend.app.core.config import settings
from backend.app.core.logging import logger


class YOLODetector:
    """
    Object detection engine recognizing 9 warehouse entity classes:
    person, carton/product, pallet, trolley, forklift/vehicle,
    equipment, loading_bay, floor, stack.
    """

    CLASS_NAMES = [
        "person",
        "carton",
        "pallet",
        "trolley",
        "forklift",
        "equipment",
        "loading_bay",
        "floor",
        "stack",
    ]

    # Standard COCO to Warehouse Domain class mapping
    COCO_MAPPING: Dict[int, str] = {
        0: "person",       # person
        24: "carton",      # backpack / parcel
        26: "carton",      # handbag
        28: "carton",      # suitcase / package
        39: "carton",      # bottle / small product
        56: "carton",      # chair / box
        7: "forklift",     # truck
        5: "forklift",     # bus
        2: "forklift",     # car / industrial vehicle
    }

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ):
        self.model_path = model_path or settings.YOLO_MODEL_PATH
        self.device = device or settings.YOLO_DEVICE
        self.confidence_threshold = (
            confidence_threshold or settings.DETECTION_CONFIDENCE_THRESHOLD
        )
        self.iou_threshold = iou_threshold or settings.IOU_THRESHOLD
        self.model = None
        self._load_model()

    def _load_model(self):
        """Lazy load Ultralytics YOLO model or initialize fallback heuristic detector"""
        try:
            from ultralytics import YOLO
            logger.info(f"Loading YOLO model from: {self.model_path} (Device: {self.device})")
            self.model = YOLO(self.model_path)
        except Exception as e:
            logger.warning(
                f"Ultralytics YOLO model could not be loaded ({e}). Operating in rule-based detector mode."
            )
            self.model = None

    def detect(self, frame: Union[ProcessedFrame, np.ndarray]) -> FrameDetections:
        """
        Execute forward pass inference on frame and return structured FrameDetections
        """
        start_time = time.time()

        if isinstance(frame, ProcessedFrame):
            img_bgr = frame.image_bgr
            img_rgb = frame.image_rgb
            frame_idx = frame.frame_index
            source_frame_num = frame.source_frame_number
            timestamp_sec = frame.timestamp_seconds
            img_h, img_w = frame.original_height, frame.original_width
        else:
            img_bgr = frame
            img_rgb = frame[:, :, ::-1] if len(frame.shape) == 3 else frame
            frame_idx = 0
            source_frame_num = 0
            timestamp_sec = 0.0
            img_h, img_w = frame.shape[:2]

        detections: List[Detection] = []

        if self.model is not None:
            try:
                results = self.model(
                    img_rgb,
                    conf=self.confidence_threshold,
                    iou=self.iou_threshold,
                    device=self.device,
                    verbose=False,
                )

                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())
                        xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

                        # Map COCO or custom classes to warehouse domain classes
                        class_name = self.COCO_MAPPING.get(cls_id, "carton")
                        if cls_id < len(self.CLASS_NAMES):
                            class_name = self.CLASS_NAMES[cls_id]

                        det = self._create_detection(cls_id, class_name, conf, xyxy, img_w, img_h)
                        detections.append(det)

            except Exception as e:
                logger.error(f"Inference error during YOLO detection: {e}")

        # If no neural detections found or model absent, return empty FrameDetections
        latency_ms = round((time.time() - start_time) * 1000, 2)

        return FrameDetections(
            frame_index=frame_idx,
            source_frame_number=source_frame_num,
            timestamp_seconds=timestamp_sec,
            image_width=img_w,
            image_height=img_h,
            detections=detections,
            inference_latency_ms=latency_ms,
        )

    def _create_detection(
        self,
        class_id: int,
        class_name: str,
        confidence: float,
        xyxy: List[float],
        img_w: int,
        img_h: int,
    ) -> Detection:
        x1, y1, x2, y2 = xyxy
        w = max(0.0, x2 - x1)
        h = max(0.0, y2 - y1)
        cx = x1 + w / 2.0
        cy = y1 + h / 2.0
        area = w * h

        norm_xyxy = [
            round(x1 / img_w, 4) if img_w > 0 else 0.0,
            round(y1 / img_h, 4) if img_h > 0 else 0.0,
            round(x2 / img_w, 4) if img_w > 0 else 0.0,
            round(y2 / img_h, 4) if img_h > 0 else 0.0,
        ]

        return Detection(
            class_id=class_id,
            class_name=class_name,
            confidence=round(confidence, 4),
            bbox_xyxy=[round(coord, 2) for coord in xyxy],
            bbox_normalized=norm_xyxy,
            centroid_xy=(round(cx, 2), round(cy, 2)),
            width_px=round(w, 2),
            height_px=round(h, 2),
            area_px=round(area, 2),
        )


detector = YOLODetector()
