"""
Generalized Spatial Event Detection — Zone Transitions & Proximity

Built on ai.spatial.zone_geometry (point-in-polygon) and
ai.spatial.coordinate_transform (anchor point, normalization). These
are two real, scoped detectors — not the full ~14-example event list
in the spec, most of which need capabilities this pipeline doesn't
have (dwell-time needs validated long-horizon per-track state, blind-
spot detection needs a covered-region model, path-deviation needs a
learned "normal route" baseline — none of that exists today and faking
it would be exactly the "fake AI" the spec explicitly forbids).

Both engines are additive: they emit SpatialEvent candidates (see
backend/app/models/spatial_event.py) alongside the existing behaviour-
detection pipeline, without touching BehaviourEvent/Incident at all.
Each engine holds its own small per-track/per-pair state across frames
so it only emits on a real transition (entering/leaving a zone,
becoming/stopping being close) rather than re-emitting the same
steady-state condition on every single frame.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

from ai.spatial.coordinate_transform import anchor_point, normalize
from ai.spatial.zone_geometry import Point, PolygonZone, SpatialGeometryEngine
from ai.tracking.tracker_schemas import TrackedObject

# Two classes closer than this fraction of the frame diagonal are
# considered "in proximity". This is a normalized-space threshold (not
# meters) because most cameras have no calibration yet — see the
# CalibrationQuality discussion in coordinate_transform.py. It is
# deliberately conservative (a fairly tight radius) since a false
# "person near forklift" warning is worse than a missed distant one.
_PROXIMITY_THRESHOLD_NORMALIZED = 0.12
_PROXIMITY_CLASS_PAIRS = {
    frozenset({"person", "forklift"}),
    frozenset({"person", "equipment"}),
}


@dataclass
class SpatialEventCandidate:
    event_type: str
    severity: str
    description: str
    involved_track_ids: List[int]
    zone_id: Optional[str] = None
    from_zone_id: Optional[str] = None
    to_zone_id: Optional[str] = None
    confidence: float = 1.0


class ZoneTransitionEngine:
    """Tracks each track's current zone frame-to-frame and emits an
    event exactly when it changes: entering a zone from open floor,
    leaving a zone entirely, or crossing directly from one into
    another. State is keyed by tracker track_id and is meant to live
    for the duration of a single video's processing run (one instance
    per pipeline_runner.process_video call)."""

    def __init__(self) -> None:
        self._last_zone_id: Dict[int, Optional[str]] = {}
        self._last_zone_code: Dict[int, Optional[str]] = {}

    def evaluate(
        self,
        track: TrackedObject,
        zones: Dict[str, PolygonZone],
        frame_width: float,
        frame_height: float,
    ) -> Optional[SpatialEventCandidate]:
        anchor = anchor_point(track.current_bbox or [0, 0, 0, 0], track.class_name)
        norm_x, norm_y = normalize(anchor, frame_width, frame_height)

        current_zone: Optional[PolygonZone] = None
        current_code: Optional[str] = None
        for code, zone in zones.items():
            if zone.contains_point(Point(norm_x, norm_y)):
                current_zone = zone
                current_code = code
                break

        current_zone_id = current_zone.zone_id if current_zone else None
        prev_zone_id = self._last_zone_id.get(track.track_id)
        prev_zone_code = self._last_zone_code.get(track.track_id)

        self._last_zone_id[track.track_id] = current_zone_id
        self._last_zone_code[track.track_id] = current_code

        if prev_zone_id == current_zone_id:
            return None  # no change, including "never in a zone" -> "still not in one"

        if current_zone_id is not None and prev_zone_id is None:
            return SpatialEventCandidate(
                event_type="ZONE_ENTERED",
                severity="HIGH" if current_zone.is_restricted else "LOW",
                description=f"Track #{track.track_id} ({track.class_name}) entered {current_code}.",
                involved_track_ids=[track.track_id],
                zone_id=current_zone_id,
                to_zone_id=current_zone_id,
                confidence=track.confidence,
            )

        if current_zone_id is None and prev_zone_id is not None:
            return SpatialEventCandidate(
                event_type="ZONE_EXITED",
                severity="LOW",
                description=f"Track #{track.track_id} ({track.class_name}) left {prev_zone_code}.",
                involved_track_ids=[track.track_id],
                zone_id=prev_zone_id,
                from_zone_id=prev_zone_id,
                confidence=track.confidence,
            )

        return SpatialEventCandidate(
            event_type="ZONE_TRANSITION",
            severity="HIGH" if current_zone.is_restricted else "LOW",
            description=f"Track #{track.track_id} ({track.class_name}) moved {prev_zone_code} -> {current_code}.",
            involved_track_ids=[track.track_id],
            zone_id=current_zone_id,
            from_zone_id=prev_zone_id,
            to_zone_id=current_zone_id,
            confidence=track.confidence,
        )


class ProximityEngine:
    """Emits a PROXIMITY_WARNING the moment two entities of a watched
    class pair (person+forklift, person+equipment) cross into close
    range, and stays silent on every subsequent frame they remain close
    — one event per approach, not one per frame."""

    def __init__(self) -> None:
        self._was_close: Dict[FrozenSet[int], bool] = {}

    def evaluate(
        self,
        tracks: List[TrackedObject],
        frame_width: float,
        frame_height: float,
    ) -> List[SpatialEventCandidate]:
        candidates: List[SpatialEventCandidate] = []
        seen_pairs: set = set()

        for i, track_a in enumerate(tracks):
            for track_b in tracks[i + 1 :]:
                pair_classes = frozenset({track_a.class_name, track_b.class_name})
                if pair_classes not in _PROXIMITY_CLASS_PAIRS:
                    continue

                pair_key = frozenset({track_a.track_id, track_b.track_id})
                seen_pairs.add(pair_key)

                anchor_a = normalize(
                    anchor_point(track_a.current_bbox or [0, 0, 0, 0], track_a.class_name),
                    frame_width,
                    frame_height,
                )
                anchor_b = normalize(
                    anchor_point(track_b.current_bbox or [0, 0, 0, 0], track_b.class_name),
                    frame_width,
                    frame_height,
                )
                distance = SpatialGeometryEngine.euclidean_distance(anchor_a, anchor_b)
                is_close = distance <= _PROXIMITY_THRESHOLD_NORMALIZED
                was_close = self._was_close.get(pair_key, False)
                self._was_close[pair_key] = is_close

                if is_close and not was_close:
                    candidates.append(
                        SpatialEventCandidate(
                            event_type="PROXIMITY_WARNING",
                            severity="HIGH",
                            description=(
                                f"Track #{track_a.track_id} ({track_a.class_name}) within proximity "
                                f"of Track #{track_b.track_id} ({track_b.class_name})."
                            ),
                            involved_track_ids=[track_a.track_id, track_b.track_id],
                            confidence=min(track_a.confidence, track_b.confidence),
                        )
                    )

        # Clear proximity state for pairs no longer present this frame
        # (one of them left the scene) so a later reappearance can
        # re-trigger a fresh warning instead of staying stuck "close".
        stale = [pair for pair in self._was_close if pair not in seen_pairs]
        for pair in stale:
            del self._was_close[pair]

        return candidates
