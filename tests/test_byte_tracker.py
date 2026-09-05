"""
Level 10 ByteTrack Multi-Object Tracking Verification Tests
"""
from ai.perception.detector_schemas import Detection, FrameDetections
from ai.tracking.byte_tracker import ByteTracker, compute_iou
from ai.tracking.kalman_filter import KalmanBoxTracker


def test_iou_calculation():
    """Verify Intersection-over-Union computation"""
    bbox1 = [0.0, 0.0, 10.0, 10.0]
    bbox2 = [5.0, 0.0, 15.0, 10.0]
    # Inter: 5x10=50, Area1=100, Area2=100, Union=150, IoU=50/150=0.333
    iou = compute_iou(bbox1, bbox2)
    assert abs(iou - (1.0 / 3.0)) < 0.01

    # Disjoint boxes
    bbox3 = [20.0, 20.0, 30.0, 30.0]
    assert compute_iou(bbox1, bbox3) == 0.0


def test_kalman_box_tracker_prediction_and_update():
    """Verify Kalman Box Tracker predicts and smooths trajectory"""
    initial_bbox = [100.0, 100.0, 200.0, 200.0]
    tracker = KalmanBoxTracker(initial_bbox)

    pred = tracker.predict()
    assert len(pred) == 4
    # State should remain near initial position with low initial velocity
    assert abs(pred[0] - 100.0) < 5.0

    # Update with moved box
    moved_bbox = [105.0, 105.0, 205.0, 205.0]
    tracker.update(moved_bbox)
    vx, vy = tracker.get_velocity()
    assert isinstance(vx, float)
    assert isinstance(vy, float)


def test_byte_tracker_association_and_persistence():
    """Verify ByteTracker maintains consistent track IDs across consecutive frames"""
    tracker = ByteTracker(high_conf_thresh=0.4, match_thresh=0.2)

    # Frame 1: Initial detection of a carton
    det_f1 = Detection(
        class_id=1,
        class_name="carton",
        confidence=0.88,
        bbox_xyxy=[100.0, 100.0, 150.0, 150.0],
        bbox_normalized=[0.1, 0.1, 0.15, 0.15],
        centroid_xy=(125.0, 125.0),
        width_px=50.0,
        height_px=50.0,
        area_px=2500.0,
    )
    frame1 = FrameDetections(
        frame_index=0,
        source_frame_number=0,
        timestamp_seconds=0.0,
        image_width=1000,
        image_height=1000,
        detections=[det_f1],
    )
    tracks_f1 = tracker.update(frame1)
    assert len(tracks_f1.active_tracks) == 1
    assigned_id = tracks_f1.active_tracks[0].track_id

    # Frame 2: Carton slightly moved
    det_f2 = Detection(
        class_id=1,
        class_name="carton",
        confidence=0.85,
        bbox_xyxy=[104.0, 102.0, 154.0, 152.0],
        bbox_normalized=[0.104, 0.102, 0.154, 0.152],
        centroid_xy=(129.0, 127.0),
        width_px=50.0,
        height_px=50.0,
        area_px=2500.0,
    )
    frame2 = FrameDetections(
        frame_index=1,
        source_frame_number=3,
        timestamp_seconds=0.1,
        image_width=1000,
        image_height=1000,
        detections=[det_f2],
    )
    tracks_f2 = tracker.update(frame2)
    assert len(tracks_f2.active_tracks) == 1
    # Track ID MUST be preserved
    assert tracks_f2.active_tracks[0].track_id == assigned_id
    assert len(tracks_f2.active_tracks[0].trajectory) >= 2
