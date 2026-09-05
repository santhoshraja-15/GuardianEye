"""
Data Models and Types for Evidence Packages and Tamper-Proof Audit Manifests
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OverlayBox:
    track_id: int
    class_name: str
    bbox_xyxy: List[float]
    state_label: str
    is_primary: bool = False


@dataclass
class KeyframeEvidence:
    frame_index: int
    timestamp_seconds: float
    image_path: str
    sha256_hash: str
    overlay_boxes: List[OverlayBox] = field(default_factory=list)


@dataclass
class EvidencePackageManifest:
    incident_id: str
    behaviour_code: str
    video_id: str
    clip_path: str
    clip_sha256: str
    snapshot_path: str
    snapshot_sha256: str
    pre_event_seconds: float
    post_event_seconds: float
    keyframes: List[KeyframeEvidence] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
