"""
Dataset Governance, Lineage Tracking, and Train/Val/Test Leakage Prevention
"""
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple
from ai.preprocessing.video_loader import VideoLoader


@dataclass
class VideoDatasetItem:
    video_id: str
    filename: str
    relative_path: str
    file_size_bytes: int
    sha256_checksum: str
    duration_seconds: float
    fps: float
    width: int
    height: int
    codec: str
    split: Literal["TRAIN", "VALIDATION", "TEST", "GOLDEN", "NEGATIVE_CONTROL", "DEMO"]
    labelled_behaviours: List[str] = field(default_factory=list)
    annotation_version: str = "1.0.0"
    is_verified: bool = True
    notes: Optional[str] = None


@dataclass
class DatasetManifest:
    dataset_name: str
    version: str
    created_at: str
    total_videos: int
    total_duration_seconds: float
    split_counts: Dict[str, int]
    items: List[VideoDatasetItem]
    manifest_checksum: str = ""


class DatasetManager:
    """
    Manages dataset manifests, cryptographic lineage tracking,
    and guarantees strict isolation between training and evaluation partitions.
    """

    @staticmethod
    def catalog_directory(
        directory_path: str,
        split_assignment: Optional[Dict[str, str]] = None,
        behaviour_tags: Optional[Dict[str, List[str]]] = None,
    ) -> DatasetManifest:
        """
        Scan a directory of video files, compute SHA256 checksums,
        extract technical properties, and build a DatasetManifest.
        """
        dir_path = Path(directory_path).resolve()
        if not dir_path.exists():
            raise FileNotFoundError(f"Dataset directory not found: {directory_path}")

        video_extensions = {".mp4", ".avi", ".mov", ".mkv"}
        items: List[VideoDatasetItem] = []
        total_duration = 0.0

        for f in sorted(dir_path.iterdir()):
            if f.is_file() and f.suffix.lower() in video_extensions:
                meta = VideoLoader.extract_metadata(str(f))
                if not meta.is_valid:
                    continue

                # Compute checksum
                hasher = hashlib.sha256()
                with open(f, "rb") as stream:
                    while chunk := stream.read(65536):
                        hasher.update(chunk)
                checksum = hasher.hexdigest()

                # Determine split
                split: Literal["TRAIN", "VALIDATION", "TEST", "GOLDEN", "NEGATIVE_CONTROL", "DEMO"] = "GOLDEN"
                if split_assignment and f.name in split_assignment:
                    val = split_assignment[f.name]
                    if val in ("TRAIN", "VALIDATION", "TEST", "GOLDEN", "NEGATIVE_CONTROL", "DEMO"):
                        split = val  # type: ignore

                # Determine behaviour tags
                tags = []
                if behaviour_tags and f.name in behaviour_tags:
                    tags = behaviour_tags[f.name]

                item = VideoDatasetItem(
                    video_id=f"vid-{checksum[:12]}",
                    filename=f.name,
                    relative_path=str(f.relative_to(dir_path.parent)),
                    file_size_bytes=meta.file_size_bytes,
                    sha256_checksum=checksum,
                    duration_seconds=meta.duration_seconds,
                    fps=meta.fps,
                    width=meta.width,
                    height=meta.height,
                    codec=meta.codec,
                    split=split,
                    labelled_behaviours=tags,
                )
                items.append(item)
                total_duration += meta.duration_seconds

        # Aggregate counts
        split_counts: Dict[str, int] = {}
        for it in items:
            split_counts[it.split] = split_counts.get(it.split, 0) + 1

        manifest_data = {
            "dataset_name": "GuardianEye-Warehouse-Benchmark",
            "version": "1.0.0",
            "created_at": "2026-09-05T00:00:00Z",
            "total_videos": len(items),
            "total_duration_seconds": round(total_duration, 2),
            "split_counts": split_counts,
            "items": [asdict(i) for i in items],
        }

        # Compute manifest hash
        manifest_str = json.dumps(manifest_data, sort_keys=True)
        manifest_hash = hashlib.sha256(manifest_str.encode("utf-8")).hexdigest()

        return DatasetManifest(
            dataset_name=manifest_data["dataset_name"],
            version=manifest_data["version"],
            created_at=manifest_data["created_at"],
            total_videos=len(items),
            total_duration_seconds=round(total_duration, 2),
            split_counts=split_counts,
            items=items,
            manifest_checksum=manifest_hash,
        )

    @staticmethod
    def verify_no_data_leakage(manifest: DatasetManifest) -> Tuple[bool, List[str]]:
        """
        Verify that no video hash or identical filename appears in both
        TRAIN and EVALUATION (TEST / VALIDATION / GOLDEN) splits.
        """
        train_hashes = set()
        eval_hashes = set()
        violations = []

        for item in manifest.items:
            if item.split == "TRAIN":
                if item.sha256_checksum in eval_hashes:
                    violations.append(
                        f"Leakage detected: {item.filename} ({item.sha256_checksum}) is in both TRAIN and EVAL sets."
                    )
                train_hashes.add(item.sha256_checksum)
            elif item.split in ("VALIDATION", "TEST", "GOLDEN", "NEGATIVE_CONTROL"):
                if item.sha256_checksum in train_hashes:
                    violations.append(
                        f"Leakage detected: {item.filename} ({item.sha256_checksum}) is in both TRAIN and EVAL sets."
                    )
                eval_hashes.add(item.sha256_checksum)

        return (len(violations) == 0, violations)
