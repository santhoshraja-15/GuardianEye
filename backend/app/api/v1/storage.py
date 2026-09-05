"""
Object Storage API Endpoints
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.storage import StorageUploadResponse
from backend.app.services.storage_service import storage_service

router = APIRouter()


@router.post(
    "/upload",
    response_model=StorageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Storage Artifact",
    description="Upload raw video, snapshot image, or report document to object storage.",
)
async def upload_artifact(
    file: UploadFile = File(...),
    category: str = "videos",
    current_user: User = Depends(get_current_user),
) -> StorageUploadResponse:
    relative_path, abs_path, size_bytes, checksum = await storage_service.save_upload_file(
        file, category=category
    )
    return StorageUploadResponse(
        success=True,
        filename=file.filename,
        relative_path=relative_path,
        absolute_path=abs_path,
        file_size_bytes=size_bytes,
        sha256_checksum=checksum,
        category=category,
    )


@router.get(
    "/download",
    summary="Download Stored Artifact",
    description="Retrieve a file artifact by its relative storage path.",
)
def download_artifact(
    path: str,
    current_user: User = Depends(get_current_user),
):
    target = storage_service.get_file_path(path)
    return FileResponse(
        path=target,
        filename=target.name,
        media_type="application/octet-stream",
    )
