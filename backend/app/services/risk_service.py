"""
Risk Assessment Service for Database Persistence and Querying
"""
import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from ai.risk.risk_schemas import RiskEvaluationResult
from backend.app.models.risk import RiskAssessment


class RiskService:
    @staticmethod
    def create_risk_assessment(
        db: Session,
        behaviour_event_id: str,
        risk_result: RiskEvaluationResult,
    ) -> RiskAssessment:
        assessment = RiskAssessment(
            behaviour_event_id=behaviour_event_id,
            risk_score=risk_result.risk_score,
            risk_level=risk_result.risk_level.value,
            confidence=0.95,
            factors_breakdown=json.dumps(risk_result.factors),
            explanation=risk_result.recommended_action,
            calculated_by="DETERMINISTIC_ENGINE",
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    @staticmethod
    def get_risk_assessment_by_event(
        db: Session,
        behaviour_event_id: str,
    ) -> Optional[RiskAssessment]:
        query = select(RiskAssessment).where(RiskAssessment.behaviour_event_id == behaviour_event_id)
        result = db.execute(query)
        return result.scalar_one_or_none()


risk_service = RiskService()
