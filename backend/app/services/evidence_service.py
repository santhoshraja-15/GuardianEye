"""
Evidence Service for Packaging and Cryptographic Verification
"""
from dataclasses import asdict
import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from ai.evidence.evidence_schemas import EvidencePackageManifest
from backend.app.models.evidence import EvidencePackage


class EvidenceService:
    @staticmethod
    def create_evidence_package(
        db: Session,
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
            overlay_data=json.dumps([asdict(k) for k in manifest.keyframes]),
        )
        db.add(pkg)
        db.commit()
        db.refresh(pkg)
        return pkg

    @staticmethod
    def get_evidence_by_incident(
        db: Session,
        incident_id: str,
    ) -> Optional[EvidencePackage]:
        query = select(EvidencePackage).where(EvidencePackage.incident_id == incident_id)
        result = db.execute(query)
        return result.scalar_one_or_none()


evidence_service = EvidenceService()
