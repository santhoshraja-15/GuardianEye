"""
Level 09 Dataset Governance, Lineage Tracking & Leakage Prevention Verification Tests
"""
import json
from pathlib import Path
from ai.learning.dataset_manager import DatasetManager, DatasetManifest, VideoDatasetItem


def test_manifest_structure_and_integrity():
    """Verify data/manifest.json loads and satisfies required fields"""
    manifest_path = Path("./data/manifest.json")
    assert manifest_path.exists(), "data/manifest.json is missing"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["dataset_name"] == "GuardianEye-Warehouse-Benchmark"
    assert data["total_videos"] == 7
    assert "items" in data
    assert len(data["items"]) == 7

    for item in data["items"]:
        assert item["sha256_checksum"] is not None
        assert len(item["sha256_checksum"]) == 64
        assert item["split"] in ("TRAIN", "VALIDATION", "TEST", "GOLDEN", "NEGATIVE_CONTROL")
        assert len(item["labelled_behaviours"]) > 0


def test_data_leakage_detection():
    """Verify DatasetManager.verify_no_data_leakage catches duplicate video hashes across train/eval"""
    items = [
        VideoDatasetItem(
            video_id="v1",
            filename="drop_01.mp4",
            relative_path="videos/drop_01.mp4",
            file_size_bytes=1000,
            sha256_checksum="hash_abc_123",
            duration_seconds=10.0,
            fps=30.0,
            width=1920,
            height=1080,
            codec="h264",
            split="TRAIN",
        ),
        VideoDatasetItem(
            video_id="v2",
            filename="drop_01_duplicate.mp4",
            relative_path="videos/drop_01_duplicate.mp4",
            file_size_bytes=1000,
            sha256_checksum="hash_abc_123",  # Duplicate hash in test
            duration_seconds=10.0,
            fps=30.0,
            width=1920,
            height=1080,
            codec="h264",
            split="TEST",
        ),
    ]

    manifest = DatasetManifest(
        dataset_name="TestLeakage",
        version="1.0.0",
        created_at="2026-09-05",
        total_videos=2,
        total_duration_seconds=20.0,
        split_counts={"TRAIN": 1, "TEST": 1},
        items=items,
        manifest_checksum="test",
    )

    is_clean, violations = DatasetManager.verify_no_data_leakage(manifest)
    assert is_clean is False
    assert len(violations) == 1
    assert "Leakage detected" in violations[0]
