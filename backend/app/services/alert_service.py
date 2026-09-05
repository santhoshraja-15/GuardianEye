"""
Alert Management Service with Deduplication & Lifecycle Transitions
"""
from datetime import datetime, timezone
import hashlib
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ai.behaviour.behaviour_schemas import DetectedBehaviour
from ai.risk.risk_schemas import RiskEvaluationResult, RiskLevel
from backend.app.models.incident import Alert


class AlertService:
    def __init__(self, dedup_window_seconds: float = 5.0):
        self.dedup_window_seconds = dedup_window_seconds
        # dedup_key -> last_alert_time_sec
        self._recent_alerts: Dict[str, float] = {}

    def generate_dedup_key(self, video_id: str, track_id: int, behaviour_code: str) -> str:
        raw = f"{video_id}:{track_id}:{behaviour_code}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def should_suppress_alert(self, dedup_key: str, current_time_sec: float) -> bool:
        if dedup_key in self._recent_alerts:
            last_time = self._recent_alerts[dedup_key]
            if current_time_sec - last_time < self.dedup_window_seconds:
                return True
        self._recent_alerts[dedup_key] = current_time_sec
        return False

    async def create_alert_if_actionable(
        self,
        db: AsyncSession,
        video_id: str,
        behaviour_event_id: str,
        behaviour: DetectedBehaviour,
        risk: RiskEvaluationResult,
        zone_id: Optional[str] = None,
    ) -> Optional[Alert]:
        if not risk.is_actionable and risk.risk_level == RiskLevel.LOW:
            return None

        dedup_key = self.generate_dedup_key(
            video_id, behaviour.evidence.primary_entity_id, behaviour.behaviour_type.value
        )
        if self.should_suppress_alert(dedup_key, behaviour.end_time_seconds):
            return None

        alert = Alert(
            behaviour_event_id=behaviour_event_id,
            zone_id=zone_id,
            alert_level=risk.risk_level.value,
            message=f"[{risk.risk_level.value}] {behaviour.description} (Risk Score: {risk.risk_score})",
            status="OPEN",
            deduplication_key=dedup_key,
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert

    @staticmethod
    async def acknowledge_alert(
        db: AsyncSession,
        alert_id: str,
        user_id: str,
    ) -> Optional[Alert]:
        query = select(Alert).where(Alert.id == alert_id)
        result = await db.execute(query)
        alert = result.scalar_one_or_none()
        if alert:
            alert.status = "ACKNOWLEDGED"
            alert.acknowledged_by = user_id
            alert.acknowledged_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(alert)
        return alert

    @staticmethod
    async def get_active_alerts(
        db: AsyncSession,
        limit: int = 50,
    ) -> List[Alert]:
        query = (
            select(Alert)
            .where(Alert.status.in_(["OPEN", "ACKNOWLEDGED"]))
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


alert_service = AlertService()
