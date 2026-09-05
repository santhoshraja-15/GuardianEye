"""
ByteTrack Multi-Object Tracker with Kalman Filtering & Occlusion Recovery
"""
import math
from typing import Dict, List, Optional, Tuple
import numpy as np
from ai.perception.detector_schemas import Detection, FrameDetections
from ai.tracking.kalman_filter import KalmanBoxTracker
from ai.tracking.tracker_schemas import (
    FrameTracks,
    TrackedObject,
    TrackPointData,
    TrackState,
)


def compute_iou(bbox1: List[float], bbox2: List[float]) -> float:
    """Calculate Intersection-over-Union (IoU) between two bounding boxes [x1, y1, x2, y2]"""
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = max(0.0, (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1]))
    area2 = max(0.0, (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1]))

    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area


class STrack:
    """Internal single track state wrapper with Kalman filter"""

    _count = 0

    def __init__(self, detection: Detection, frame_index: int, timestamp: float):
        STrack._count += 1
        self.track_id = STrack._count
        self.class_id = detection.class_id
        self.class_name = detection.class_name
        self.confidence = detection.confidence
        self.state = TrackState.NEW
        self.kalman = KalmanBoxTracker(detection.bbox_xyxy)
        self.current_bbox = detection.bbox_xyxy
        self.first_frame = frame_index
        self.last_frame = frame_index
        self.start_time = timestamp
        self.last_time = timestamp
        self.hits = 1
        self.age = 0
        self.time_since_update = 0
        self.trajectory: List[TrackPointData] = []
        self._record_point(frame_index, timestamp, detection.bbox_xyxy, detection.confidence)

    def _record_point(
        self, frame_index: int, timestamp: float, bbox: List[float], conf: float
    ):
        w = max(1.0, bbox[2] - bbox[0])
        h = max(1.0, bbox[3] - bbox[1])
        cx = bbox[0] + w / 2.0
        cy = bbox[1] + h / 2.0

        vx, vy = self.kalman.get_velocity()
        # Compute speed in pixels/sec assuming nominal delta
        dt = max(0.001, timestamp - self.last_time) if self.trajectory else 0.1
        speed = math.sqrt(vx * vx + vy * vy) / dt

        pt = TrackPointData(
            frame_index=frame_index,
            timestamp_seconds=timestamp,
            bbox_xyxy=[round(c, 2) for c in bbox],
            centroid_xy=(round(cx, 2), round(cy, 2)),
            velocity_xy=(vx, vy),
            speed_px_per_sec=round(speed, 2),
            confidence=round(conf, 4),
        )
        self.trajectory.append(pt)
        # Keep trajectory length bounded (last 150 points)
        if len(self.trajectory) > 150:
            self.trajectory.pop(0)

    def predict(self) -> List[float]:
        self.current_bbox = self.kalman.predict()
        self.age += 1
        self.time_since_update += 1
        return self.current_bbox

    def update(self, detection: Detection, frame_index: int, timestamp: float):
        self.kalman.update(detection.bbox_xyxy)
        self.current_bbox = self.kalman.get_bbox()
        self.confidence = detection.confidence
        self.hits += 1
        self.time_since_update = 0
        self.last_frame = frame_index
        self.last_time = timestamp
        self.state = TrackState.TRACKED
        self._record_point(frame_index, timestamp, self.current_bbox, detection.confidence)

    def mark_lost(self):
        self.state = TrackState.LOST

    def mark_removed(self):
        self.state = TrackState.REMOVED

    def to_tracked_object(self) -> TrackedObject:
        w = max(1.0, self.current_bbox[2] - self.current_bbox[0])
        h = max(1.0, self.current_bbox[3] - self.current_bbox[1])
        cx = self.current_bbox[0] + w / 2.0
        cy = self.current_bbox[1] + h / 2.0
        vx, vy = self.kalman.get_velocity()
        speed = math.sqrt(vx * vx + vy * vy)
        direction = math.degrees(math.atan2(vy, vx)) % 360

        return TrackedObject(
            track_id=self.track_id,
            class_id=self.class_id,
            class_name=self.class_name,
            state=self.state,
            confidence=self.confidence,
            current_bbox=[round(c, 2) for c in self.current_bbox],
            current_centroid=(round(cx, 2), round(cy, 2)),
            velocity_xy=(vx, vy),
            speed_px_per_sec=round(speed, 2),
            direction_degrees=round(direction, 1),
            first_frame_index=self.first_frame,
            last_frame_index=self.last_frame,
            start_time_seconds=self.start_time,
            last_time_seconds=self.last_time,
            hits=self.hits,
            age_frames=self.age,
            time_since_update=self.time_since_update,
            trajectory=list(self.trajectory),
        )


class ByteTracker:
    """
    ByteTrack multi-object tracker associating high and low confidence detections
    via two-stage IoU bipartite matching.
    """

    def __init__(
        self,
        high_conf_thresh: float = 0.5,
        low_conf_thresh: float = 0.2,
        match_thresh: float = 0.3,
        max_age_frames: int = 30,
        min_hits: int = 3,
    ):
        self.high_conf_thresh = high_conf_thresh
        self.low_conf_thresh = low_conf_thresh
        self.match_thresh = match_thresh
        self.max_age_frames = max_age_frames
        self.min_hits = min_hits

        self.tracked_stracks: List[STrack] = []
        self.lost_stracks: List[STrack] = []
        self.removed_stracks: List[STrack] = []

    def update(self, frame_detections: FrameDetections) -> FrameTracks:
        """
        Process a new frame's detections and return active & lost tracks
        """
        frame_idx = frame_detections.frame_index
        source_frame_num = frame_detections.source_frame_number
        timestamp = frame_detections.timestamp_seconds

        # 1. Split detections into high and low confidence sets
        det_high: List[Detection] = []
        det_low: List[Detection] = []

        for d in frame_detections.detections:
            if d.confidence >= self.high_conf_thresh:
                det_high.append(d)
            elif d.confidence >= self.low_conf_thresh:
                det_low.append(d)

        # 2. Predict positions of existing tracks
        for strack in self.tracked_stracks + self.lost_stracks:
            strack.predict()

        # 3. First association with high-confidence detections
        pool_tracks = [t for t in self.tracked_stracks if t.state == TrackState.TRACKED]
        pool_tracks += self.lost_stracks

        matched_tracks_1, unmatched_tracks_1, unmatched_dets_1 = self._match_iou(
            pool_tracks, det_high, thresh=self.match_thresh
        )

        for track_idx, det_idx in matched_tracks_1:
            track = pool_tracks[track_idx]
            det = det_high[det_idx]
            track.update(det, frame_idx, timestamp)
            if track in self.lost_stracks:
                self.lost_stracks.remove(track)
                self.tracked_stracks.append(track)

        # 4. Second association with low-confidence detections
        unmatched_active_tracks = [
            pool_tracks[i] for i in unmatched_tracks_1 if pool_tracks[i].state == TrackState.TRACKED
        ]

        matched_tracks_2, unmatched_tracks_2, _ = self._match_iou(
            unmatched_active_tracks, det_low, thresh=0.2
        )

        for track_idx, det_idx in matched_tracks_2:
            track = unmatched_active_tracks[track_idx]
            det = det_low[det_idx]
            track.update(det, frame_idx, timestamp)

        # Mark unmatched active tracks as lost
        for i in unmatched_tracks_2:
            track = unmatched_active_tracks[i]
            track.mark_lost()
            if track in self.tracked_stracks:
                self.tracked_stracks.remove(track)
            self.lost_stracks.append(track)

        # 5. Initialize new tracks from unmatched high-confidence detections
        for i in unmatched_dets_1:
            det = det_high[i]
            new_track = STrack(det, frame_idx, timestamp)
            new_track.state = TrackState.TRACKED
            self.tracked_stracks.append(new_track)

        # 6. Remove stale lost tracks exceeding max age
        for track in list(self.lost_stracks):
            if track.time_since_update > self.max_age_frames:
                track.mark_removed()
                self.lost_stracks.remove(track)
                self.removed_stracks.append(track)

        active_objects = [t.to_tracked_object() for t in self.tracked_stracks]
        lost_objects = [t.to_tracked_object() for t in self.lost_stracks]

        return FrameTracks(
            frame_index=frame_idx,
            source_frame_number=source_frame_num,
            timestamp_seconds=timestamp,
            active_tracks=active_objects,
            lost_tracks=lost_objects,
        )

    def _match_iou(
        self,
        tracks: List[STrack],
        detections: List[Detection],
        thresh: float,
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Greedy bipartite IoU matching between tracks and detections"""
        if not tracks or not detections:
            return [], list(range(len(tracks))), list(range(len(detections)))

        iou_matrix = np.zeros((len(tracks), len(detections)), dtype=np.float32)
        for t_idx, track in enumerate(tracks):
            for d_idx, det in enumerate(detections):
                # Only match same or compatible class families
                if track.class_name == det.class_name or track.class_name in ("carton", "product"):
                    iou_matrix[t_idx, d_idx] = compute_iou(track.current_bbox, det.bbox_xyxy)
                else:
                    iou_matrix[t_idx, d_idx] = 0.0

        matched_tracks: List[Tuple[int, int]] = []
        unmatched_tracks = set(range(len(tracks)))
        unmatched_dets = set(range(len(detections)))

        while True:
            max_idx = np.unravel_index(np.argmax(iou_matrix, axis=None), iou_matrix.shape)
            max_val = iou_matrix[max_idx]

            if max_val < thresh:
                break

            t_idx, d_idx = max_idx
            matched_tracks.append((t_idx, d_idx))
            unmatched_tracks.discard(t_idx)
            unmatched_dets.discard(d_idx)

            # Invalidate row and column
            iou_matrix[t_idx, :] = -1.0
            iou_matrix[:, d_idx] = -1.0

        return matched_tracks, sorted(list(unmatched_tracks)), sorted(list(unmatched_dets))


byte_tracker = ByteTracker()
