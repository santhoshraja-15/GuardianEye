"""
Evidence Service for Packaging and Cryptographic Verification
"""
import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ai.evidence.evidence_schemas import EvidencePackageManifest
from backend.app.models.evidence import EvidencePackage


class EvidenceService:
    @staticmethod
    async def create_evidence_package(
        db: AsyncSession,
        incident_id: str,
        manifest: EvidencePackageManifest,
    ) -> EvidencePackage:
        pkg = EvidencePackage(
            incident_id=incident_id,
            snapshot_path=manifest.snapshot_path,
            clip_path=manifest.clip_path,
            pre_event_seconds=manifest.pre_event_seconds,
            post_event_seconds=manifest.post_event_seconds,
            sha256_checksum=manifest.clip_sha256,
            overlay_data=json.dumps([k.__dict__ for k in manifest.keyframes]),
        )
        db.add(pkg)
        await db.commit()
        await db.refresh(pkg)
        return pkg

    @staticmethod
    async def get_evidence_by_incident(
        db: AsyncSession,
        incident_id: str,
    ) -> Optional[EvidencePackage]:
        query = select(EvidencePackage).where(EvidencePackage.incident_id == incident_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


evidence_service = EvidenceService()
