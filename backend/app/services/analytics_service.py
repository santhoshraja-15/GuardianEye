"""
Analytics and Operational Health Aggregation Service

    Database -> Incident/Event records -> Analytics service -> API
    -> Dashboard state -> Charts/KPIs/heatmaps

Every KPI below is a real aggregate over Incident / BehaviourEvent /
RiskAssessment / DamagePrediction / Alert / Zone rows, a documented
deterministic formula over those rows, or explicitly None/empty when the
data doesn't exist — none of it is a plausible-looking placeholder. See
`AnalyticsProvenance` in the response for a one-line method statement per
KPI, and the module-level comments below for why each metric is scoped
the way it is.

Trend/comparison numbers are computed via `temporal_analytics_service`,
the same module the assistant's comparative answers use — this is
deliberate: the dashboard and the assistant must never define "average
risk" or "this shift" differently.
"""
import json
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ai.spatial.coordinate_transform import normalize_zone_polygons
from ai.spatial.zone_geometry import SpatialGeometryEngine
from backend.app.models.behaviour import BehaviourEvent
from backend.app.models.incident import Alert, Incident
from backend.app.models.risk import DamagePrediction, RiskAssessment
from backend.app.models.video import Video
from backend.app.models.warehouse import Zone
from backend.app.schemas.analytics import (
    AnalyticsProvenance,
    BehaviourDistributionItem,
    DashboardSummaryResponse,
    HeatmapPoint,
    RiskTrendComparison,
    RiskTrendPoint,
)
from backend.app.services import temporal_analytics_service as tas


class AnalyticsService:
    @staticmethod
    def _avg_risk_by_behaviour(db: Session, warehouse_id: Optional[str]) -> Dict[str, float]:
        query = (
            db.query(BehaviourEvent.behaviour_code, func.avg(RiskAssessment.risk_score))
            .join(RiskAssessment, RiskAssessment.behaviour_event_id == BehaviourEvent.id)
            .group_by(BehaviourEvent.behaviour_code)
        )
        return {code: round(avg, 1) for code, avg in query.all() if avg is not None}

    @staticmethod
    def _damage_totals(db: Session) -> Dict[str, float]:
        """SUM(estimated_financial_loss_usd) split by whether the damage was
        ever actually confirmed vs. only ever a model estimate. Only counts
        events that were significant enough to become an Incident, matching
        how every other Incident-scoped KPI on this dashboard is scoped.
        NULLs (rows persisted before this column existed) are excluded by
        SQL's SUM automatically rather than treated as zero."""
        base_query = (
            db.query(DamagePrediction.damage_status, func.sum(DamagePrediction.estimated_financial_loss_usd))
            .join(BehaviourEvent, DamagePrediction.behaviour_event_id == BehaviourEvent.id)
            .join(Incident, Incident.behaviour_event_id == BehaviourEvent.id)
            .group_by(DamagePrediction.damage_status)
        )
        totals = {status: (total or 0.0) for status, total in base_query.all()}
        potential = round(totals.get("POTENTIAL_DAMAGE", 0.0), 2)
        confirmed = round(
            totals.get("CONFIRMED_BY_HUMAN", 0.0) + totals.get("CONFIRMED_BY_EXTERNAL_SYSTEM", 0.0), 2
        )
        return {"potential": potential, "confirmed": confirmed}

    @staticmethod
    def _mean_acknowledge_seconds(db: Session) -> Optional[float]:
        rows = (
            db.query(Alert.created_at, Alert.acknowledged_at)
            .filter(Alert.acknowledged_at.isnot(None))
            .all()
        )
        deltas = [(ack - created).total_seconds() for created, ack in rows if created and ack]
        if not deltas:
            return None
        return round(sum(deltas) / len(deltas), 1)

    @staticmethod
    def _real_heatmap(db: Session, warehouse_id: Optional[str]) -> List[HeatmapPoint]:
        """Real zone geometry + real per-zone incident counts. Position is
        the zone polygon's centroid, normalized against the bounding box of
        every configured zone's own vertices (not an external "warehouse
        meters" field — the seeded zone polygons and warehouse
        width/length aren't on the same coordinate scale, so normalizing
        against the layout's own extent is the only way to get an honest
        0-1 position instead of a nonsensical one). Intensity is this
        zone's incident count relative to the busiest zone — a zone with
        zero incidents gets 0.0, not a decorative minimum."""
        zone_query = db.query(Zone)
        if warehouse_id:
            zone_query = zone_query.filter(Zone.warehouse_id == warehouse_id)
        zones = zone_query.all()
        if not zones:
            return []

        zone_polygons: Dict[str, List[tuple]] = {}
        for z in zones:
            try:
                coords = json.loads(z.polygon_coordinates) if z.polygon_coordinates else []
                zone_polygons[z.id] = [(float(p[0]), float(p[1])) for p in coords if len(p) >= 2]
            except (ValueError, TypeError):
                zone_polygons[z.id] = []

        if not any(zone_polygons.values()):
            return []
        # Shared with digital_twin_service and ai.pipeline_runner — one
        # implementation of "put zone polygons on a 0-1 plane" rather
        # than three that could quietly drift apart.
        normalized_polygons = normalize_zone_polygons(zone_polygons)

        counts_by_zone = dict(
            db.query(Incident.zone_id, func.count(Incident.id))
            .filter(Incident.zone_id.isnot(None))
            .group_by(Incident.zone_id)
            .all()
        )
        max_count = max(counts_by_zone.values(), default=0)

        points: List[HeatmapPoint] = []
        for z in zones:
            polygon = normalized_polygons.get(z.id, [])
            if not polygon:
                continue
            cx, cy = SpatialGeometryEngine.polygon_centroid(polygon)
            count = counts_by_zone.get(z.id, 0)
            points.append(
                HeatmapPoint(
                    x_normalized=round(cx, 4),
                    y_normalized=round(cy, 4),
                    intensity=round(count / max_count, 3) if max_count else 0.0,
                    zone_code=z.code,
                    zone_name=z.name,
                    incident_count=count,
                )
            )
        return points

    @staticmethod
    def _shift_risk_trend(db: Session, warehouse_id: Optional[str]) -> RiskTrendComparison:
        now = tas.utc_now()
        previous_shift = tas.resolve_period_phrase("previous shift", now)
        current_shift = tas.resolve_period_phrase("this shift", now)
        comparison = tas.compare_periods(db, previous_shift, current_shift, warehouse_id)

        data_available = (
            comparison.metrics_a.avg_risk_score is not None and comparison.metrics_b.avg_risk_score is not None
        )
        avg_delta = next((d for d in comparison.overall if d.label == "Average risk score"), None)
        # _delta() treats a missing average as 0.0 so it can still report on
        # metrics where a real zero is meaningful (e.g. incident counts) —
        # but a *risk score* of "0 because there's no data" is not a real
        # measurement, so direction/percent_change must not surface here
        # unless both periods actually have a risk average to compare.
        return RiskTrendComparison(
            period_a_label=previous_shift.label,
            period_b_label=current_shift.label,
            period_a_avg_risk=comparison.metrics_a.avg_risk_score,
            period_b_avg_risk=comparison.metrics_b.avg_risk_score,
            direction=avg_delta.direction if (avg_delta and data_available) else None,
            percent_change=avg_delta.percent_change if (avg_delta and data_available) else None,
            data_available=data_available,
        )

    @staticmethod
    def get_dashboard_summary(
        db: Session,
        warehouse_id: Optional[str] = None,
    ) -> DashboardSummaryResponse:
        total_videos = db.query(func.count(Video.id)).scalar() or 0
        total_incidents = db.query(func.count(Incident.id)).scalar() or 0
        critical_incidents = (
            db.query(func.count(Incident.id)).filter(Incident.severity == "CRITICAL").scalar() or 0
        )
        open_alerts = db.query(func.count(Alert.id)).filter(Alert.status == "OPEN").scalar() or 0

        behaviour_dist_query = (
            db.query(BehaviourEvent.behaviour_code, func.count(BehaviourEvent.id).label("cnt"))
            .group_by(BehaviourEvent.behaviour_code)
            .order_by(func.count(BehaviourEvent.id).desc())
        )
        rows = behaviour_dist_query.all()
        total_events = sum(r.cnt for r in rows) if rows else 1
        avg_risk_by_code = AnalyticsService._avg_risk_by_behaviour(db, warehouse_id)

        dist_items = [
            BehaviourDistributionItem(
                behaviour_code=r[0],
                count=r[1],
                percentage=round((r[1] / total_events) * 100.0, 1),
                avg_risk_score=avg_risk_by_code.get(r[0]),
            )
            for r in rows
        ]

        heatmap_points = AnalyticsService._real_heatmap(db, warehouse_id)
        damage_totals = AnalyticsService._damage_totals(db)
        mean_ack_seconds = AnalyticsService._mean_acknowledge_seconds(db)

        daily_series = tas.compute_series(db, tas.daily_buckets(tas.utc_now(), num_days=7), warehouse_id)
        risk_trend_daily = [
            RiskTrendPoint(
                label=m.period.label,
                period_start=m.period.start,
                period_end=m.period.end,
                total_incidents=m.total_incidents,
                avg_risk_score=m.avg_risk_score,
            )
            for m in daily_series
        ]
        risk_trend_shift = AnalyticsService._shift_risk_trend(db, warehouse_id)

        health_status = "OPTIMAL"
        if open_alerts > 10 or critical_incidents > 5:
            health_status = "CRITICAL"
        elif open_alerts > 3 or critical_incidents > 0:
            health_status = "DEGRADED"

        provenance = AnalyticsProvenance(
            avg_risk_score_method="AVG(risk_assessments.risk_score) grouped by behaviour_code; omitted where no assessment exists.",
            damage_exposure_method=(
                "SUM(damage_predictions.estimated_financial_loss_usd = product_unit_value x damage_probability) "
                "for incident-linked events, split by damage_status (potential vs. human/external-confirmed)."
            ),
            heatmap_method=(
                "Real incident counts grouped by zone_id; position is each zone polygon's centroid, "
                "normalized against the bounding box of all configured zone vertices."
            ),
            response_time_method="AVG(alerts.acknowledged_at - alerts.created_at) over alerts with a recorded acknowledgement.",
            generated_at=tas.utc_now(),
        )

        return DashboardSummaryResponse(
            total_videos_processed=total_videos,
            total_incidents_detected=total_incidents,
            critical_incidents=critical_incidents,
            open_alerts=open_alerts,
            estimated_damage_loss_usd=damage_totals["potential"],
            potential_damage_exposure_usd=damage_totals["potential"],
            confirmed_damage_cost_usd=damage_totals["confirmed"],
            mean_time_to_acknowledge_seconds=mean_ack_seconds,
            behaviour_distribution=dist_items,
            risk_heatmaps=heatmap_points,
            operational_health_status=health_status,
            risk_trend_daily=risk_trend_daily,
            risk_trend_shift=risk_trend_shift,
            provenance=provenance,
        )


analytics_service = AnalyticsService()
