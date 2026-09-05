"""
Level 05 Object Storage Service Verification Tests
"""
import io
import os
from backend.app.core.errors import ValidationException, NotFoundException
from backend.app.services.storage_service import StorageService


def test_storage_service_initialization(tmp_path):
    """Verify storage service initializes subdirectories"""
    service = StorageService()
    assert service.local_dir.exists()
    assert (service.local_dir / "videos").exists()
    assert (service.local_dir / "snapshots").exists()
    assert (service.local_dir / "clips").exists()


def test_sha256_checksum_calculation():
    """Verify SHA256 calculation on byte stream"""
    sample_data = b"GuardianEye Warehouse Intelligence Platform 2026"
    file_obj = io.BytesIO(sample_data)
    checksum = StorageService.calculate_sha256(file_obj)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length


def test_path_traversal_protection():
    """Verify storage service rejects path traversal attempts"""
    service = StorageService()
    try:
        service.sanitize_and_generate_path("../../../etc/passwd.mp4")
    except ValidationException as e:
        assert "not supported" in str(e) or "traversal" in str(e)


def test_save_bytes_and_retrieval(tmp_path):
    """Verify saving raw bytes and reading them back"""
    service = StorageService()
    test_content = b"Mock Frame Snapshot Buffer"
    rel_path, abs_path, size, checksum = service.save_bytes(
        test_content, "snapshot_001.jpg", category="snapshots"
    )

    assert rel_path.startswith("snapshots/")
    assert os.path.exists(abs_path)
    assert size == len(test_content)
    assert len(checksum) == 64

    # Verify retrieval
    retrieved_path = service.get_file_path(rel_path)
    assert retrieved_path.exists()
    with open(retrieved_path, "rb") as f:
        assert f.read() == test_content

    # Clean up
    assert service.delete_file(rel_path) is True
