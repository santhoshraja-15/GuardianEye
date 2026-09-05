"""
Level 07 Frame Processing & Decoupled Temporal Extraction Verification Tests
"""
from pathlib import Path
import numpy as np
from ai.preprocessing.frame_extractor import FrameExtractor, ProcessedFrame


def test_frame_extractor_batching():
    """Verify FrameExtractor batch creation utility"""
    h, w = 480, 640
    dummy_bgr = np.zeros((h, w, 3), dtype=np.uint8)
    dummy_rgb = np.zeros((h, w, 3), dtype=np.uint8)

    frames = [
        ProcessedFrame(
            frame_index=0,
            source_frame_number=0,
            timestamp_seconds=0.0,
            image_bgr=dummy_bgr,
            image_rgb=dummy_rgb,
            original_width=w,
            original_height=h,
        ),
        ProcessedFrame(
            frame_index=1,
            source_frame_number=3,
            timestamp_seconds=0.1,
            image_bgr=dummy_bgr,
            image_rgb=dummy_rgb,
            original_width=w,
            original_height=h,
        ),
    ]

    batch_imgs, timestamps, indices = FrameExtractor.create_batch(frames)
    assert batch_imgs.shape == (2, h, w, 3)
    assert timestamps == [0.0, 0.1]
    assert indices == [0, 1]


def test_frame_extraction_on_sample_video():
    """Verify real video frame extraction and decoupled sampling on sample warehouse CCTV"""
    sample_dir = Path("./Sample videos")
    if sample_dir.exists():
        video_files = list(sample_dir.glob("*.mp4"))
        if video_files:
            target_video = video_files[0]
            extractor = FrameExtractor(target_fps=5)
            extracted = list(extractor.extract_frames(str(target_video), max_frames=5))

            assert len(extracted) == 5
            for idx, frame in enumerate(extracted):
                assert frame.frame_index == idx
                assert frame.timestamp_seconds >= 0.0
                assert frame.image_rgb.shape[2] == 3  # 3 channels (RGB)
                assert frame.image_bgr.shape[2] == 3  # 3 channels (BGR)
