"""
Level 06 Video Ingestion & Metadata Extraction Verification Tests
"""
import os
from pathlib import Path
from ai.preprocessing.video_loader import VideoLoader, VideoMetadata
from backend.app.schemas.video import VideoMetadataResponse, VideoResponse


def test_video_metadata_nonexistent_file():
    """Verify video loader handles missing file gracefully without crashing"""
    meta = VideoLoader.extract_metadata("non_existent_video_path.mp4")
    assert meta.is_valid is False
    assert "not found" in meta.error_message.lower()


def test_video_metadata_empty_file(tmp_path):
    """Verify video loader detects 0-byte corrupt files"""
    empty_file = tmp_path / "empty_corrupt.mp4"
    empty_file.write_bytes(b"")

    meta = VideoLoader.extract_metadata(str(empty_file))
    assert meta.is_valid is False
    assert "0 bytes" in meta.error_message


def test_video_metadata_sample_video_extraction():
    """Verify metadata extraction on sample warehouse CCTV video if available"""
    sample_dir = Path("./Sample videos")
    if sample_dir.exists():
        video_files = list(sample_dir.glob("*.mp4"))
        if video_files:
            target_video = video_files[0]
            meta = VideoLoader.extract_metadata(str(target_video))
            assert meta.is_valid is True
            assert meta.fps > 0
            assert meta.width > 0
            assert meta.height > 0
            assert meta.duration_seconds > 0
            assert meta.file_size_bytes > 0
            assert meta.codec is not None


def test_video_schemas():
    """Verify video response schema serialization"""
    meta_resp = VideoMetadataResponse(
        duration_seconds=12.5,
        fps=30.0,
        width=1920,
        height=1080,
        codec="h264",
        aspect_ratio="16:9",
        total_frames=375,
        file_size_bytes=10485760,
    )
    assert meta_resp.fps == 30.0
    assert meta_resp.aspect_ratio == "16:9"
