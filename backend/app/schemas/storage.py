"""
Pydantic Schemas for Object Storage and Artifact Management
"""
from typing import Optional
from pydantic import BaseModel, Field


class StorageUploadResponse(BaseModel):
    success: bool = True
    filename: str
    relative_path: str
    absolute_path: str
    file_size_bytes: int
    sha256_checksum: str
    category: str


class FileMetadata(BaseModel):
    relative_path: str
    filename: str
    file_size_bytes: int
    content_type: str
    sha256_checksum: str
