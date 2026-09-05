"""
Human-Object-Equipment Interaction Engine
"""
import math
from typing import Dict, List, Optional, Tuple
from ai.interaction.interaction_schemas import (
    FrameInteractions,
    InteractionType,
    SpatialInteraction,
)
from ai.spatial.zone_geometry import SpatialGeometryEngine
from ai.tracking.byte_tracker import compute_iou
from ai.tracking.tracker_schemas import FrameTracks, TrackedObject


class InteractionDetector:
    """
    Evaluates spatial-temporal relationships and physical contact graphs between:
    - Person <-> Product/Carton (Approach, Contact, Holding, Carrying, Separated)
    - Person <-> Equipment (Proximity, Operating, Danger Collision Risk)
    - Equipment <-> Product (Loading, Moving, Engagement)
    - Product <-> Product (Stacking, Overhang)
    - Product <-> Floor (Ground contact, Dragging)
    """

    CONTACT_DISTANCE_THRESH_PX = 40.0
    PROXIMITY_DISTANCE_THRESH_PX = 150.0

    def __init__(self):
        # Active interactions cache: (src_id, tgt_id) -> SpatialInteraction
        self.active_interactions: Dict[Tuple[int, int], SpatialInteraction] = {}

    def detect_interactions(self, frame_tracks: FrameTracks) -> FrameInteractions:
        """
        Evaluate pairwise interactions across all active tracks in the frame
        """
        frame_idx = frame_tracks.frame_index
        source_frame_num = frame_tracks.source_frame_number
        timestamp = frame_tracks.timestamp_seconds
        active_tracks = frame_tracks.active_tracks

        current_frame_interactions: List[SpatialInteraction] = []
        observed_pairs = set()

        n = len(active_tracks)
        for i in range(n):
            for j in range(i + 1, n):
                t1 = active_tracks[i]
                t2 = active_tracks[j]

                # Evaluate pair in both directions if asymmetric
                interaction = self._evaluate_pair(t1, t2, frame_idx, timestamp)
                if interaction:
                    current_frame_interactions.append(interaction)
                    observed_pairs.add((t1.track_id, t2.track_id))

        # Clean up stale interactions not seen in this frame
        stale_keys = [k for k in self.active_interactions if k not in observed_pairs]
        for k in stale_keys:
            del self.active_interactions[k]

        return FrameInteractions(
            frame_index=frame_idx,
            source_frame_number=source_frame_num,
            timestamp_seconds=timestamp,
            interactions=current_frame_interactions,
        )

    def _evaluate_pair(
        self,
        t1: TrackedObject,
        t2: TrackedObject,
        frame_idx: int,
        timestamp: float,
    ) -> Optional[SpatialInteraction]:
        # Determine source (typically person or equipment) and target (carton or person)
        if t1.class_name == "person" and t2.class_name in ("carton", "product", "pallet"):
            src, tgt = t1, t2
        elif t2.class_name == "person" and t1.class_name in ("carton", "product", "pallet"):
            src, tgt = t2, t1
        elif t1.class_name in ("forklift", "trolley") and t2.class_name == "person":
            src, tgt = t1, t2
        elif t2.class_name in ("forklift", "trolley") and t1.class_name == "person":
            src, tgt = t2, t1
        elif t1.class_name in ("carton", "product") and t2.class_name in ("carton", "product", "pallet"):
            src, tgt = t1, t2
        else:
            src, tgt = t1, t2

        distance = SpatialGeometryEngine.bbox_distance(src.current_bbox, tgt.current_bbox)
        iou = compute_iou(src.current_bbox, tgt.current_bbox)

        # Compute relative velocity
        vx_rel = src.velocity_xy[0] - tgt.velocity_xy[0]
        vy_rel = src.velocity_xy[1] - tgt.velocity_xy[1]
        rel_speed = math.sqrt(vx_rel * vx_rel + vy_rel * vy_rel)

        interaction_type = None

        # 1. Person <-> Carton interactions
        if src.class_name == "person" and tgt.class_name in ("carton", "product"):
            if iou > 0.05 or distance < self.CONTACT_DISTANCE_THRESH_PX:
                # If moving together at similar speed
                if src.speed_px_per_sec > 10.0 and rel_speed < 15.0:
                    interaction_type = InteractionType.CARRYING
                else:
                    interaction_type = InteractionType.HOLDING
            elif distance < self.PROXIMITY_DISTANCE_THRESH_PX:
                interaction_type = InteractionType.APPROACHING

        # 2. Equipment <-> Person interactions (Collision risk)
        elif src.class_name in ("forklift", "trolley", "vehicle") and tgt.class_name == "person":
            if distance < 60.0 or iou > 0.0:
                interaction_type = InteractionType.COLLISION_RISK
            elif distance < self.PROXIMITY_DISTANCE_THRESH_PX:
                interaction_type = InteractionType.NEAR_EQUIPMENT

        # 3. Product <-> Product / Pallet (Stacking)
        elif src.class_name in ("carton", "product") and tgt.class_name in ("carton", "product", "pallet"):
            # Check vertical alignment (src is above tgt)
            src_bottom = src.current_bbox[3]
            tgt_top = tgt.current_bbox[1]
            if abs(src_bottom - tgt_top) < 30.0 and iou > 0.1:
                interaction_type = InteractionType.STACKED_ON

        if not interaction_type:
            return None

        # Track interaction lifecycle
        pair_key = (src.track_id, tgt.track_id)
        if pair_key in self.active_interactions:
            existing = self.active_interactions[pair_key]
            existing.current_frame = frame_idx
            existing.current_time_seconds = timestamp
            existing.duration_seconds = max(0.0, timestamp - existing.start_time_seconds)
            existing.distance_px = round(distance, 2)
            existing.iou = round(iou, 4)
            existing.interaction_type = interaction_type
            existing.relative_velocity = (round(vx_rel, 2), round(vy_rel, 2))
            return existing
        else:
            interaction_id = f"int-{src.track_id}-{tgt.track_id}-{frame_idx}"
            new_interaction = SpatialInteraction(
                interaction_id=interaction_id,
                source_track_id=src.track_id,
                source_class=src.class_name,
                target_track_id=tgt.track_id,
                target_class=tgt.class_name,
                interaction_type=interaction_type,
                distance_px=round(distance, 2),
                iou=round(iou, 4),
                relative_velocity=(round(vx_rel, 2), round(vy_rel, 2)),
                start_frame=frame_idx,
                current_frame=frame_idx,
                start_time_seconds=timestamp,
                current_time_seconds=timestamp,
                duration_seconds=0.0,
                confidence=round(min(src.confidence, tgt.confidence), 4),
            )
            self.active_interactions[pair_key] = new_interaction
            return new_interaction


interaction_detector = InteractionDetector()
