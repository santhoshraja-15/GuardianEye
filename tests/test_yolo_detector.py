"""
Level 08 YOLO Object Detection & Privacy Filter Verification Tests
"""
import numpy as np
from ai.perception.detector_schemas import Detection, FrameDetections
from ai.perception.privacy_filter import PrivacyFilter
from ai.perception.yolo_detector import YOLODetector


def test_detection_dataclass_initialization():
    """Verify Detection dataclass fields and normalization"""
    det = Detection(
        class_id=0,
        class_name="person",
        confidence=0.945,
        bbox_xyxy=[100.0, 100.0, 200.0, 300.0],
        bbox_normalized=[0.1, 0.1, 0.2, 0.3],
        centroid_xy=(150.0, 200.0),
        width_px=100.0,
        height_px=200.0,
        area_px=20000.0,
    )
    assert det.class_name == "person"
    assert det.centroid_xy == (150.0, 200.0)
    assert det.area_px == 20000.0


def test_privacy_filter_face_blur():
    """Verify PrivacyFilter applies Gaussian blur to person detections"""
    img = np.ones((500, 500, 3), dtype=np.uint8) * 200
    # Add a high-contrast pattern in head region
    img[50:120, 100:180] = 50

    det = Detection(
        class_id=0,
        class_name="person",
        confidence=0.95,
        bbox_xyxy=[100.0, 50.0, 180.0, 350.0],
        bbox_normalized=[0.2, 0.1, 0.36, 0.7],
        centroid_xy=(140.0, 200.0),
        width_px=80.0,
        height_px=300.0,
        area_px=24000.0,
    )

    blurred_img = PrivacyFilter.apply_privacy_blur(img, [det])
    assert blurred_img.shape == img.shape
    # Check that pixels in head region were modified by blurring
    assert not np.array_equal(blurred_img[50:120, 100:180], img[50:120, 100:180])


def test_yolo_detector_inference_on_synthetic_frame():
    """Verify YOLODetector forward pass on synthetic numpy image"""
    detector = YOLODetector()
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    result = detector.detect(test_frame)
    assert isinstance(result, FrameDetections)
    assert result.image_width == 640
    assert result.image_height == 480
    assert result.inference_latency_ms >= 0.0
