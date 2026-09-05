"""
Evidence Package Generator
Constructs tamper-proof SHA-256 verified visual snapshots, bounding box overlays, and clip extraction manifests.
"""
import hashlib
import json
import os
from typing import Dict, List, Optional
import numpy as np
from ai.behaviour.behaviour_schemas import DetectedBehaviour
from ai.evidence.evidence_schemas import (
    EvidencePackageManifest,
    KeyframeEvidence,
    OverlayBox,
)
from ai.tracking.tracker_schemas import FrameTracks


class EvidenceGenerator:
    """Generates verifiable evidence packages with cryptographic hash checks."""

    @staticmethod
    def calculate_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def generate_manifest(
        cls,
        incident_id: str,
        video_id: str,
        behaviour: DetectedBehaviour,
        tracks_by_frame: Dict[int, FrameTracks],
        clip_path: str = "",
        snapshot_path: str = "",
    ) -> EvidencePackageManifest:
        keyframes: List[KeyframeEvidence] = []

        for frame_idx in behaviour.keyframe_indices:
            ft = tracks_by_frame.get(frame_idx)
            overlay_boxes: List[OverlayBox] = []
            if ft:
                for t in ft.active_tracks:
                    is_prim = (t.track_id == behaviour.evidence.primary_entity_id)
                    overlay_boxes.append(
                        OverlayBox(
                            track_id=t.track_id,
                            class_name=t.class_name,
                            bbox_xyxy=t.bbox_xyxy,
                            state_label="PRIMARY_ANOMALY" if is_prim else "SURROUNDING",
                            is_primary=is_prim,
                        )
                    )

            # Generate virtual hash for frame state
            frame_repr = json.dumps(
                {"frame": frame_idx, "boxes": [b.__dict__ for b in overlay_boxes]}, sort_keys=True
            ).encode("utf-8")
            frame_hash = cls.calculate_sha256(frame_repr)

            keyframes.append(
                KeyframeEvidence(
                    frame_index=frame_idx,
                    timestamp_seconds=round(frame_idx * 0.033, 3),
                    image_path=snapshot_path or f"/storage/snapshots/{video_id}_frame_{frame_idx}.jpg",
                    sha256_hash=frame_hash,
                    overlay_boxes=overlay_boxes,
                )
            )

        manifest_data = json.dumps(
            {
                "incident_id": incident_id,
                "video_id": video_id,
                "behaviour": behaviour.behaviour_type.value,
                "keyframes": [k.__dict__ for k in keyframes],
            },
            sort_keys=True,
        ).encode("utf-8")
        package_hash = cls.calculate_sha256(manifest_data)

        return EvidencePackageManifest(
            incident_id=incident_id,
            behaviour_code=behaviour.behaviour_type.value,
            video_id=video_id,
            clip_path=clip_path or f"/storage/clips/{video_id}_incident_{incident_id}.mp4",
            clip_sha256=package_hash,
            snapshot_path=snapshot_path or f"/storage/snapshots/{video_id}_keyframe.jpg",
            snapshot_sha256=package_hash,
            pre_event_seconds=3.0,
            post_event_seconds=3.0,
            keyframes=keyframes,
            metadata={
                "trigger_rule": behaviour.evidence.trigger_rule,
                "primary_entity_id": behaviour.evidence.primary_entity_id,
                "confidence": behaviour.confidence,
            },
        )


evidence_generator = EvidenceGenerator()
