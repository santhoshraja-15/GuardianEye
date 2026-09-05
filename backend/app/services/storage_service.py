"""
Unified Object Storage Service (Local Filesystem & MinIO/S3)
"""
import hashlib
import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Optional, Tuple
from fastapi import UploadFile
from backend.app.core.config import settings
from backend.app.core.errors import ValidationException, NotFoundException


class StorageService:
    """
    Unified storage service managing video artifacts, frame snapshots,
    incident evidence clips, and reports with cryptographic SHA256 validation.
    """

    ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_DOC_EXTENSIONS = {".pdf", ".csv", ".json"}
    MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB

    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.local_dir = Path(settings.LOCAL_STORAGE_DIR).resolve()
        self._ensure_storage_directories()

    def _ensure_storage_directories(self):
        """Create structured storage subdirectories if running in local mode"""
        subdirs = ["videos", "snapshots", "clips", "evidence", "reports", "temp"]
        for subdir in subdirs:
            target = self.local_dir / subdir
            target.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def calculate_sha256(file_obj: BinaryIO) -> str:
        """Compute cryptographic SHA256 hash of a file stream"""
        hasher = hashlib.sha256()
        file_obj.seek(0)
        while chunk := file_obj.read(8192):
            hasher.update(chunk)
        file_obj.seek(0)
        return hasher.hexdigest()

    def sanitize_and_generate_path(self, filename: str, category: str = "videos") -> Tuple[str, Path]:
        """
        Sanitize input filename, prevent path traversal, and generate safe storage target
        """
        # Strip path traversal characters
        clean_name = Path(filename).name
        ext = Path(clean_name).suffix.lower()

        allowed_all = (
            self.ALLOWED_VIDEO_EXTENSIONS
            | self.ALLOWED_IMAGE_EXTENSIONS
            | self.ALLOWED_DOC_EXTENSIONS
        )
        if ext not in allowed_all:
            raise ValidationException(
                f"File extension '{ext}' is not supported. Allowed: {allowed_all}"
            )

        unique_id = str(uuid.uuid4())
        safe_filename = f"{unique_id}{ext}"
        relative_path = f"{category}/{safe_filename}"
        absolute_path = (self.local_dir / category / safe_filename).resolve()

        # Strict path traversal check
        if not str(absolute_path).startswith(str(self.local_dir)):
            raise ValidationException("Path traversal attempt detected.")

        return relative_path, absolute_path

    async def save_upload_file(
        self, upload_file: UploadFile, category: str = "videos"
    ) -> Tuple[str, str, int, str]:
        """
        Save an incoming FastAPI UploadFile to storage and return (relative_path, abs_path, size_bytes, sha256)
        """
        relative_path, abs_path = self.sanitize_and_generate_path(
            upload_file.filename, category=category
        )

        # Write to destination and calculate checksum
        hasher = hashlib.sha256()
        size_bytes = 0

        with open(abs_path, "wb") as buffer:
            while chunk := await upload_file.read(8192):
                size_bytes += len(chunk)
                if size_bytes > self.MAX_FILE_SIZE_BYTES:
                    abs_path.unlink(missing_ok=True)
                    raise ValidationException(
                        f"File exceeds maximum allowed size of {self.MAX_FILE_SIZE_BYTES / (1024*1024)} MB."
                    )
                hasher.update(chunk)
                buffer.write(chunk)

        sha256_checksum = hasher.hexdigest()
        return relative_path, str(abs_path), size_bytes, sha256_checksum

    def save_bytes(
        self, data: bytes, filename: str, category: str = "snapshots"
    ) -> Tuple[str, str, int, str]:
        """Save raw bytes to storage (used for snapshots and clips)"""
        relative_path, abs_path = self.sanitize_and_generate_path(
            filename, category=category
        )

        with open(abs_path, "wb") as f:
            f.write(data)

        size_bytes = len(data)
        sha256_checksum = hashlib.sha256(data).hexdigest()
        return relative_path, str(abs_path), size_bytes, sha256_checksum

    def get_file_path(self, relative_path: str) -> Path:
        """Resolve and verify existence of a stored file"""
        target = (self.local_dir / relative_path).resolve()
        if not str(target).startswith(str(self.local_dir)) or not target.is_file():
            raise NotFoundException("StorageFile", relative_path)
        return target

    def delete_file(self, relative_path: str) -> bool:
        """Delete a file from storage"""
        try:
            target = self.get_file_path(relative_path)
            target.unlink(missing_ok=True)
            return True
        except NotFoundException:
            return False


storage_service = StorageService()
