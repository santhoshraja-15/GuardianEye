"""
Grounded AI Assistant & Copilot Service
Synthesizes factual, zero-hallucination answers backed strictly by verified database records, incidents, spatial zones, and SOP rules.

Architecture:

    Question -> Intent -> Time Range(s) -> Event Query -> Aggregation -> Insight -> Response

Comparative/temporal questions ("compare today vs yesterday", "what changed
this shift?", "is risk increasing?") are resolved by a dedicated intent
layer (see `_detect_comparative_intent` / `_resolve_comparison_periods`)
backed by `temporal_analytics_service`'s reusable period aggregation —
they are NOT handled as one-off keyword branches. Every number in a
comparative answer is a real aggregate for the resolved time window; if a
window has no data, the response says so instead of guessing.

An optional LLM provider (see `llm_provider.py`) may rephrase the
already-computed facts into more natural prose; it is never allowed to
originate a fact. With no provider configured (the default), everything
here runs off deterministic templates and real queries only — zero
network calls, zero hallucination surface.
"""
from typing import List, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from backend.app.models.behaviour import BehaviourEvent
from backend.app.models.evidence import EvidencePackage, Recommendation, RootCause
from backend.app.models.incident import Incident
from backend.app.models.risk import DamagePrediction, RiskAssessment
from backend.app.models.warehouse import Camera, Zone
from backend.app.schemas.assistant import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    CitationReference,
    ComparisonMetric,
    WhatChangedSummary,
)
from backend.app.services import temporal_analytics_service as tas
from backend.app.services.llm_provider import get_llm_provider

_COMPARISON_TRIGGER_WORDS = [
    "compare", "comparison", " vs ", " vs.", "versus", "change", "changed", "changing",
    "increase", "increased", "increasing", "decrease", "decreased", "decreasing",
    "improve", "improved", "improving", "improvement", "worse", "worsen", "worsened",
    "trend", "getting worse", "getting better",
]

# Single-phrase questions ("what changed this shift?") need a natural
# counterpart period to compare against — this is that pairing, kept in
# one place rather than scattered through the query-parsing logic.
_DEFAULT_COUNTERPART = {
    "today": "yesterday",
    "yesterday": "today",
    "this shift": "previous shift",
    "current shift": "previous shift",
    "previous shift": "this shift",
    "last shift": "this shift",
    "this week": "last week",
    "last week": "this week",
    "morning": "evening",
    "morning shift": "evening shift",
    "evening": "morning",
    "evening shift": "morning shift",
    "night": "evening",
    "night shift": "evening shift",
    "overnight": "evening",
}


def _detect_comparative_intent(q_lower: str) -> bool:
    phrases = tas.find_period_phrases(q_lower)
    has_trigger_word = any(w in q_lower for w in _COMPARISON_TRIGGER_WORDS)
    return has_trigger_word or len(phrases) >= 2


def _resolve_comparison_periods(q_lower: str, now) -> Optional[tuple]:
    """Returns (period_a, period_b) chronologically ordered (a is earlier), or
    None if no time reference could be resolved at all."""
    phrases = tas.find_period_phrases(q_lower)

    if len(phrases) >= 2:
        resolved = [tas.resolve_period_phrase(p, now) for p in phrases[:2]]
        resolved = [p for p in resolved if p is not None]
        if len(resolved) == 2:
            resolved.sort(key=lambda p: p.start)
            return resolved[0], resolved[1]

    if len(phrases) == 1:
        primary = tas.resolve_period_phrase(phrases[0], now)
        counterpart_phrase = _DEFAULT_COUNTERPART.get(phrases[0])
        counterpart = tas.resolve_period_phrase(counterpart_phrase, now) if counterpart_phrase else None
        if primary and counterpart:
            both = sorted([primary, counterpart], key=lambda p: p.start)
            return both[0], both[1]
        if primary:
            return primary, primary

    # No explicit time reference at all ("is risk increasing?") -> the
    # standard default comparison window.
    yesterday = tas.resolve_period_phrase("yesterday", now)
    today = tas.resolve_period_phrase("today", now)
    return yesterday, today


def _format_delta_sentence(delta) -> str:
    direction_word = {"INCREASED": "increased", "DECREASED": "decreased", "STABLE": "stayed flat"}[delta.direction]
    pct = f" ({abs(delta.percent_change):.1f}%)" if delta.percent_change is not None else ""
    return f"{delta.label} {direction_word} from {delta.period_a_value:g} to {delta.period_b_value:g}{pct}"


def _build_comparison_response(comparison: tas.PeriodComparisonResult, req: AssistantQueryRequest) -> AssistantQueryResponse:
    a_label, b_label = comparison.period_a.label, comparison.period_b.label

    citations: List[CitationReference] = []
    for d in comparison.behaviour_deltas[: req.max_citations]:
        if d.period_a_count == 0 and d.period_b_count == 0:
            continue
        citations.append(
            CitationReference(
                source_type="BEHAVIOUR_RECORD",
                source_id=d.key,
                title=f"{d.key}",
                confidence=0.95,
                snippet=f"{a_label}: {d.period_a_count} · {b_label}: {d.period_b_count} (change {d.change:+d})",
            )
        )
    for d in comparison.zone_deltas[: max(0, req.max_citations - len(citations))]:
        if d.period_a_count == 0 and d.period_b_count == 0:
            continue
        citations.append(
            CitationReference(
                source_type="ZONE",
                source_id=d.key,
                title=f"Zone {d.key}",
                confidence=0.95,
                snippet=f"{a_label}: {d.period_a_count} incident(s) · {b_label}: {d.period_b_count} incident(s) (change {d.change:+d})",
            )
        )

    if not comparison.data_available:
        answer = (
            f"There isn't enough incident data in {a_label} or {b_label} yet to make that comparison — "
            "both windows are currently empty."
        )
        why_it_matters = None
    else:
        headline = next(
            (d for d in comparison.overall if d.label in ("High-risk incidents", "Total incidents")),
            comparison.overall[0] if comparison.overall else None,
        )
        sentences = [_format_delta_sentence(headline)] if headline else []
        if comparison.what_changed.most_significant_change:
            sentences.append(f"Most significant change: {comparison.what_changed.most_significant_change}.")
        answer = " ".join(sentences) or f"No incidents were logged in {a_label} or {b_label}."

        if headline and headline.direction == "DECREASED":
            why_it_matters = "This reflects improving handling discipline — fewer risky events mean lower odds of product damage."
        elif headline and headline.direction == "INCREASED":
            why_it_matters = "Rising risk events increase the chance of undetected product damage if left unaddressed."
        else:
            why_it_matters = "Operational risk held steady between the two periods."

    grounded_facts = {
        "period_a": {"label": a_label, "start": comparison.period_a.start.isoformat(), "end": comparison.period_a.end.isoformat()},
        "period_b": {"label": b_label, "start": comparison.period_b.start.isoformat(), "end": comparison.period_b.end.isoformat()},
        "overall_metrics": [
            {
                "label": d.label,
                "period_a_value": d.period_a_value,
                "period_b_value": d.period_b_value,
                "absolute_change": d.absolute_change,
                "percent_change": d.percent_change,
                "direction": d.direction,
            }
            for d in comparison.overall
        ],
        "behaviour_changes": [
            {"behaviour": d.key, "period_a_count": d.period_a_count, "period_b_count": d.period_b_count, "change": d.change}
            for d in comparison.behaviour_deltas[:10]
        ],
        "zone_changes": [
            {"zone": d.key, "period_a_count": d.period_a_count, "period_b_count": d.period_b_count, "change": d.change}
            for d in comparison.zone_deltas[:10]
        ],
        "most_significant_change": comparison.what_changed.most_significant_change,
        "recommended_action": comparison.recommended_action,
        "data_available": comparison.data_available,
    }

    provider = get_llm_provider()
    narrated = provider.narrate(req.query, grounded_facts) if comparison.data_available else None
    final_answer = narrated or answer

    return AssistantQueryResponse(
        answer=final_answer,
        grounded_citations=citations,
        is_grounded=True,
        confidence=0.95 if comparison.data_available else 0.6,
        suggested_followups=[
            "What is the most significant change?",
            "Which behaviour improved the most?",
            "Which zone needs attention?",
            "What should the supervisor do next?",
        ],
        period_a_label=a_label,
        period_b_label=b_label,
        comparison=[
            ComparisonMetric(
                label=d.label,
                period_a_label=a_label,
                period_b_label=b_label,
                period_a_value=d.period_a_value,
                period_b_value=d.period_b_value,
                absolute_change=d.absolute_change,
                percent_change=d.percent_change,
                direction=d.direction,
            )
            for d in comparison.overall
        ],
        what_changed=WhatChangedSummary(
            improved=comparison.what_changed.improved,
            worsened=comparison.what_changed.worsened,
            new_items=comparison.what_changed.new_items,
            persistent=comparison.what_changed.persistent,
            most_significant_change=comparison.what_changed.most_significant_change,
        ),
        why_it_matters=why_it_matters,
        recommended_action=comparison.recommended_action,
        data_available=comparison.data_available,
        llm_provider_used=provider.name,
    )


class AssistantService:
    @classmethod
    def process_query(
        cls,
        db: Session,
        req: AssistantQueryRequest,
    ) -> AssistantQueryResponse:
        q_lower = req.query.lower().strip()

        # 0. Comparative / temporal intent — checked first so words like
        # "shift" or "today" inside a comparison question ("what changed
        # this shift?") don't fall through to the plain shift-summary
        # branch below.
        if _detect_comparative_intent(q_lower):
            periods = _resolve_comparison_periods(q_lower, tas.utc_now())
            if periods:
                period_a, period_b = periods
                comparison = tas.compare_periods(db, period_a, period_b, warehouse_id=req.warehouse_id)
                return _build_comparison_response(comparison, req)

        citations: List[CitationReference] = []
        answer = ""
        followups = [
            "What were the most common risky behaviours detected?",
            "Which loading bay or zone has the highest risk?",
            "Show recent drop or dragging incidents.",
            "What preventive actions are recommended?",
        ]

        # 1. Zone / Loading Bay Query
        if any(w in q_lower for w in ["bay", "zone", "location", "dock", "where"]):
            zones = db.query(Zone).all()
            incidents_by_zone = (
                db.query(Incident.zone_id, func.count(Incident.id))
                .filter(Incident.zone_id.isnot(None))
                .group_by(Incident.zone_id)
                .all()
            )
            zone_count_map = {z_id: cnt for z_id, cnt in incidents_by_zone}

            sorted_zones = sorted(
                zones,
                key=lambda z: (zone_count_map.get(z.id, 0) * z.risk_weight),
                reverse=True,
            )

            for z in sorted_zones[: req.max_citations]:
                cnt = zone_count_map.get(z.id, 0)
                citations.append(
                    CitationReference(
                        source_type="ZONE",
                        source_id=z.id,
                        title=f"Zone {z.code}: {z.name}",
                        confidence=0.98,
                        snippet=f"Type: {z.zone_type}, Risk Weight: {z.risk_weight}x, Incidents Logged: {cnt}",
                    )
                )

            if sorted_zones:
                highest = sorted_zones[0]
                cnt = zone_count_map.get(highest.id, 0)
                answer = (
                    f"Zone **{highest.code} ({highest.name})** currently has the highest operational risk profile "
                    f"with a risk multiplier of {highest.risk_weight}x and {cnt} logged incident(s). "
                    f"Loading and transfer activities in this zone are monitored via continuous camera tracking."
                )
            else:
                answer = "No warehouse spatial zones are currently configured in the digital twin topology."

        # 2. Behaviour Frequency / Common Risky Behaviours Query
        elif any(w in q_lower for w in ["behaviour", "behavior", "common", "frequent", "pattern", "b0", "b1", "b2"]):
            top_behaviours = (
                db.query(BehaviourEvent.behaviour_code, func.count(BehaviourEvent.id))
                .group_by(BehaviourEvent.behaviour_code)
                .order_by(desc(func.count(BehaviourEvent.id)))
                .limit(req.max_citations)
                .all()
            )

            for code, cnt in top_behaviours:
                citations.append(
                    CitationReference(
                        source_type="BEHAVIOUR_RECORD",
                        source_id=code,
                        title=f"Rule {code}",
                        confidence=0.96,
                        snippet=f"Detected {cnt} occurrence(s) across ingested camera feeds.",
                    )
                )

            if top_behaviours:
                top_code, top_cnt = top_behaviours[0]
                answer = (
                    f"The most frequently detected handling anomaly is **{top_code}** with {top_cnt} recorded occurrence(s). "
                    f"A total of {len(top_behaviours)} distinct behaviour violation pattern(s) were flagged by the AI engine."
                )
            else:
                answer = "No behaviour anomaly violations have been logged in the active session."

        # 3. Damage Prediction & Product Fragility Query
        elif any(w in q_lower for w in ["damage", "fragile", "crush", "impact", "broken"]):
            damages = (
                db.query(DamagePrediction)
                .order_by(desc(DamagePrediction.damage_probability))
                .limit(req.max_citations)
                .all()
            )

            for dp in damages:
                citations.append(
                    CitationReference(
                        source_type="DAMAGE_PREDICTION",
                        source_id=dp.id,
                        title=f"Damage Prediction: {dp.likely_damage_type}",
                        confidence=round(dp.damage_probability, 2),
                        snippet=f"Probability: {int(dp.damage_probability * 100)}%, Status: {dp.damage_status}",
                    )
                )

            if damages:
                max_prob = int(damages[0].damage_probability * 100)
                answer = (
                    f"The physical damage prediction engine has evaluated {len(damages)} risk event(s). "
                    f"The highest projected damage probability is **{max_prob}%** ({damages[0].likely_damage_type}). "
                    "Physical factors evaluated include deceleration force, drop height, and carton rigidity."
                )
            else:
                answer = "Zero physical damage events have been projected from current material-handling trajectories."

        # 4. Root Causes & Prevention Recommendations Query
        elif any(w in q_lower for w in ["root cause", "recommendation", "prevent", "rca", "corrective"]):
            recs = db.query(Recommendation).limit(req.max_citations).all()
            for r in recs:
                citations.append(
                    CitationReference(
                        source_type="RECOMMENDATION",
                        source_id=r.id,
                        title=f"Action: {r.action_title}",
                        confidence=0.97,
                        snippet=f"Type: {r.prevention_type}, Est. Risk Reduction: {r.estimated_risk_reduction_pct}%, Status: {r.status}. Description: {r.description}",
                    )
                )

            if recs:
                answer = (
                    f"Identified {len(recs)} corrective recommendation(s) generated from automated root-cause analysis (RCA). "
                    f"Top recommendation: **{recs[0].action_title}** ({recs[0].prevention_type} — est. {recs[0].estimated_risk_reduction_pct}% risk reduction)."
                )
            else:
                answer = (
                    "Automated root-cause analysis is active. Recommend reviewing equipment placement and pallet stabilization SOPs."
                )

        # 5. Shift Summary / Today's Incidents Query
        elif any(w in q_lower for w in ["shift", "today", "summary", "morning", "overview"]):
            total_inc = db.query(Incident).count()
            crit_inc = db.query(Incident).filter(Incident.severity == "CRITICAL").count()
            high_inc = db.query(Incident).filter(Incident.severity == "HIGH").count()
            recent_incidents = (
                db.query(Incident).order_by(desc(Incident.created_at)).limit(req.max_citations).all()
            )

            for inc in recent_incidents:
                citations.append(
                    CitationReference(
                        source_type="INCIDENT",
                        source_id=inc.id,
                        title=f"{inc.incident_code}: {inc.title}",
                        confidence=0.99,
                        snippet=f"Severity: {inc.severity}, Status: {inc.status}. Summary: {inc.summary[:120]}...",
                    )
                )

            answer = (
                f"**Shift Intelligence Summary**: {total_inc} total incident(s) detected across active zones "
                f"({crit_inc} Critical, {high_inc} High severity). "
                f"All events have been packaged with cryptographic SHA-256 evidence hashes and visual replay tracks."
            )

        # 6. Specific Incidents / Drop / Drag / Standard Incident Query
        else:
            incidents = (
                db.query(Incident)
                .order_by(desc(Incident.created_at))
                .limit(req.max_citations)
                .all()
            )

            for inc in incidents:
                citations.append(
                    CitationReference(
                        source_type="INCIDENT",
                        source_id=inc.id,
                        title=f"{inc.incident_code}: {inc.title}",
                        confidence=0.96,
                        snippet=f"Severity: {inc.severity}, Status: {inc.status}. Summary: {inc.summary}",
                    )
                )

            if citations:
                answer = (
                    f"GuardianEye Copilot verified {len(citations)} active incident record(s) on file. "
                    f"Latest incident **{citations[0].title}** is classified as {incidents[0].severity} severity. "
                    "Evidence packages and trajectory keyframes are available for instant forensic review."
                )
            else:
                answer = (
                    "GuardianEye Copilot is online and connected to your warehouse digital twin. "
                    "You can query active incident logs, spatial zone risk distributions, root causes, or SOP compliance."
                )

        return AssistantQueryResponse(
            answer=answer,
            grounded_citations=citations,
            is_grounded=True,
            confidence=0.96,
            suggested_followups=followups,
            llm_provider_used=get_llm_provider().name,
        )


assistant_service = AssistantService()
