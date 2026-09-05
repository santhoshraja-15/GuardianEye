"""
Script to catalog all sample warehouse videos into data/manifest.json
"""
import json
from dataclasses import asdict
from pathlib import Path
from ai.learning.dataset_manager import DatasetManager

# Scenario mappings for provided sample videos
BEHAVIOUR_MAPPINGS = {
    "Dock level, dragging cupboard.mp4": ["B02_DRAGGING", "B08_HANDLING_WITHOUT_EQUIPMENT"],
    "KD packets dragged, heavy box kept on other packets.mp4": ["B02_DRAGGING", "B05_IMPROPER_STACKING"],
    "Rolling and dragging on wet floor.mp4": ["B02_DRAGGING", "B12_ROLLING"],
    "Rolling and dropping carton.mp4": ["B01_PRODUCT_DROP", "B12_ROLLING"],
    "Stepping on cartons, vertical product kept horizontally, heavy product kept on top.mp4": [
        "B05_IMPROPER_STACKING",
        "B16_STEPPING_ON_PRODUCT",
    ],
    "Throwing Mattresses.mp4": ["B03_THROWING", "B04_ROUGH_HANDLING"],
    "Throwing seating cartons, using strap to hold.mp4": ["B03_THROWING", "B04_ROUGH_HANDLING"],
}

SPLIT_ASSIGNMENTS = {
    "Dock level, dragging cupboard.mp4": "GOLDEN",
    "KD packets dragged, heavy box kept on other packets.mp4": "GOLDEN",
    "Rolling and dragging on wet floor.mp4": "GOLDEN",
    "Rolling and dropping carton.mp4": "GOLDEN",
    "Stepping on cartons, vertical product kept horizontally, heavy product kept on top.mp4": "GOLDEN",
    "Throwing Mattresses.mp4": "GOLDEN",
    "Throwing seating cartons, using strap to hold.mp4": "GOLDEN",
}


def main():
    sample_dir = Path("./Sample videos").resolve()
    if not sample_dir.exists():
        print(f"Sample videos directory not found at: {sample_dir}")
        return

    manifest = DatasetManager.catalog_directory(
        str(sample_dir),
        split_assignment=SPLIT_ASSIGNMENTS,
        behaviour_tags=BEHAVIOUR_MAPPINGS,
    )

    data_dir = Path("./data").resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = data_dir / "manifest.json"

    manifest_dict = {
        "dataset_name": manifest.dataset_name,
        "version": manifest.version,
        "created_at": manifest.created_at,
        "total_videos": manifest.total_videos,
        "total_duration_seconds": manifest.total_duration_seconds,
        "split_counts": manifest.split_counts,
        "manifest_checksum": manifest.manifest_checksum,
        "items": [asdict(i) for i in manifest.items],
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2)

    print(f"Successfully cataloged {manifest.total_videos} sample videos to {manifest_path}")
    print(f"Total Duration: {manifest.total_duration_seconds} seconds")
    print(f"Split counts: {manifest.split_counts}")


if __name__ == "__main__":
    main()
