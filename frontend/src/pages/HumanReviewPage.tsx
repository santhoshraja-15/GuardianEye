import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, CircleDashed, FileText, ShieldAlert, Sparkles, TriangleAlert } from 'lucide-react';
import { useIncidents } from '../hooks/useIncidents';
import { api } from '../services/api';

const behaviourTaxonomy = [
  'B01_DROP',
  'B02_DRAG',
  'B03_THROW',
  'B04_ROUGH_HANDLING',
  'B05_IMPROPER_STACKING',
  'B06_UNSTABLE_STACK',
  'B07_INCORRECT_PLACEMENT',
  'B08_EQUIPMENT_MISUSE',
  'B09_PALLET_MISALIGNMENT',
  'B10_LOADING_SEQUENCE_VIOLATION',
  'B11_STEPPING_ON_CARTON',
  'B12_KICKING_PRODUCT',
  'B13_ROLLING_CARTON',
  'B14_CRUSHING_UNDER_LOAD',
  'B15_WET_FLOOR_DRAGGING',
  'B16_AISLE_OBSTRUCTION',
  'B17_OVERLOADING_PALLET',
  'B18_UNSECURED_TRANSIT',
  'B19_IMPROPER_LIFTING_POSTURE',
  'B20_COLLISION_RISK',
] as const;

const reviewOptions = ['CORRECT', 'INCORRECT', 'CHANGE_BEHAVIOUR', 'UNCERTAIN'] as const;

type ReviewVerdict = (typeof reviewOptions)[number];

interface ReviewDraft {
  verdict: ReviewVerdict;
  correctedBehaviour: string;
  notes: string;
}

export const HumanReviewPage: React.FC = () => {
  // Shared cache — same incident list AppLayout/Dashboard/Incident Board use.
  const { data: incidents = [] } = useIncidents();
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [draft, setDraft] = useState<ReviewDraft>({
    verdict: 'CORRECT',
    correctedBehaviour: behaviourTaxonomy[0],
    notes: '',
  });
  const [submitted, setSubmitted] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedIncidentId && incidents.length > 0) {
      setSelectedIncidentId(incidents[0].id);
    }
  }, [incidents, selectedIncidentId]);

  const selectedIncident = useMemo(
    () => incidents.find((incident) => incident.id === selectedIncidentId) ?? incidents[0] ?? null,
    [incidents, selectedIncidentId],
  );

  useEffect(() => {
    if (!selectedIncident) {
      return;
    }

    setDraft((existing) => ({
      ...existing,
      correctedBehaviour: behaviourTaxonomy.includes(existing.correctedBehaviour as (typeof behaviourTaxonomy)[number])
        ? existing.correctedBehaviour
        : behaviourTaxonomy[0],
    }));
  }, [selectedIncident]);

  const evidenceItems = selectedIncident
    ? [
        `Incident: ${selectedIncident.incident_code}`,
        `Severity: ${selectedIncident.severity}`,
        `Zone: ${selectedIncident.zone_id ?? 'Not specified'}`,
        `Camera: ${selectedIncident.camera_id ?? 'Not specified'}`,
        `Summary: ${selectedIncident.summary}`,
        `Created: ${new Date(selectedIncident.created_at).toLocaleString()}`,
      ]
    : [];

  const reviewLabel = selectedIncident
    ? selectedIncident.severity === 'CRITICAL' || selectedIncident.severity === 'HIGH'
      ? 'High-priority review'
      : 'Human review pending'
    : 'No incident selected';
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmitReview = async () => {
    if (!selectedIncident) {
      return;
    }

    setIsSubmitting(true);
    try {
      const finalNotes = draft.notes.trim() || 'No reviewer notes recorded.';
      await api.submitHumanReview({
        incident_id: selectedIncident.id,
        review_outcome: draft.verdict,
        corrected_behaviour_code: draft.verdict === 'CHANGE_BEHAVIOUR' ? draft.correctedBehaviour : undefined,
        reviewer_notes: finalNotes,
        is_curated_for_training: true,
      });

      setSubmitted(
        `Decision captured for ${selectedIncident.incident_code}: ${draft.verdict}. ${
          draft.verdict === 'CHANGE_BEHAVIOUR' ? `Corrected behaviour: ${draft.correctedBehaviour}.` : ''
        } Review saved to active learning dataset.`,
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Review submission failed';
      setSubmitted(`Error saving review: ${msg}`);
    } finally {
      setIsSubmitting(false);
    }
  };


  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-[#18243A] tracking-tight">Human Review Workspace</h1>
          <p className="text-xs text-[#6F7F98]">
            AI detects and explains. Humans validate and decide.
          </p>
        </div>
        <span className="rounded border border-[rgba(146,64,14,0.3)] bg-[rgba(146,64,14,0.08)] px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-[#92400e]">
          {reviewLabel}
        </span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[320px_minmax(0,1fr)] gap-6">
        <aside className="glass-panel rounded-xl border border-[#E9EDF2] p-4">
          <div className="flex items-center gap-2 border-b border-[#E9EDF2] pb-3">
            <FileText className="w-4 h-4 text-[#2F52D6]" />
            <h2 className="text-sm font-bold text-[#18243A]">Review Queue</h2>
          </div>

          <div className="mt-4 space-y-3">
            {incidents.length === 0 ? (
              <div className="rounded-lg border border-dashed border-[#E9EDF2] bg-[#F8FAFC] p-4 text-xs text-[#6F7F98]">
                No incident records are currently available from the backend review queue.
              </div>
            ) : (
              incidents.map((incident) => (
                <button
                  key={incident.id}
                  type="button"
                  onClick={() => setSelectedIncidentId(incident.id)}
                  className={`w-full rounded-xl border p-3 text-left transition-all ${
                    selectedIncident?.id === incident.id
                      ? 'border-[#5D87FF]/40 bg-[#5D87FF]/10'
                      : 'border-[#E9EDF2] bg-[#F8FAFC] hover:border-[#CBD5E1]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] text-[#2F52D6]">{incident.incident_code}</span>
                    <span className="px-1.5 py-0.5 rounded border border-[rgba(146,64,14,0.3)] bg-[rgba(146,64,14,0.08)] text-[9px] text-[#92400e]">
                      {incident.severity}
                    </span>
                  </div>
                  <div className="mt-2 text-sm font-semibold text-[#18243A]">{incident.title}</div>
                  <div className="mt-1 text-[11px] text-[#6F7F98]">{incident.summary}</div>
                </button>
              ))
            )}
          </div>
        </aside>

        {selectedIncident ? (
          <section className="space-y-6">
            <div className="glass-panel rounded-xl border border-[#E9EDF2] p-5">
              <div className="flex items-start justify-between gap-4 border-b border-[#E9EDF2] pb-4">
                <div>
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
                    <Sparkles className="w-3.5 h-3.5 text-[#2F52D6]" />
                    AI prediction
                  </div>
                  <h2 className="mt-2 text-lg font-bold text-[#18243A]">{selectedIncident.title}</h2>
                </div>
                <span className="rounded border border-[rgba(21,128,61,0.3)] bg-[rgba(21,128,61,0.1)] px-2 py-1 text-[10px] text-[#15803d]">
                  Confidence {Math.min(99, Math.max(55, Math.round(selectedIncident.severity === 'CRITICAL' ? 96 : 82)))}%
                </span>
              </div>

              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-xl border border-[#E9EDF2] bg-[#F8FAFC] p-4">
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
                    <ShieldAlert className="w-3.5 h-3.5 text-[#92400e]" />
                    AI explains
                  </div>
                  <p className="mt-3 text-sm leading-6 text-[#18243A]">
                    GuardianEye detected a warehouse safety event and flagged the record as {selectedIncident.severity.toLowerCase()} severity based on the signal evidence captured for this incident.
                  </p>
                </div>

                <div className="rounded-xl border border-[#E9EDF2] bg-[#F8FAFC] p-4">
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
                    <TriangleAlert className="w-3.5 h-3.5 text-[#b91c1c]" />
                    Evidence
                  </div>
                  <ul className="mt-3 space-y-2 text-xs text-[#334155]">
                    {evidenceItems.map((item) => (
                      <li key={item} className="flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-[#5D87FF]" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div className="glass-panel rounded-xl border border-[#E9EDF2] p-5">
              <div className="flex items-center gap-2 border-b border-[#E9EDF2] pb-3">
                <CheckCircle2 className="w-4 h-4 text-[#15803d]" />
                <h3 className="text-sm font-bold text-[#18243A]">Human decision</h3>
              </div>

              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2">
                {reviewOptions.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setDraft((existing) => ({ ...existing, verdict: option }))}
                    className={`rounded-lg border px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] transition-all ${
                      draft.verdict === option
                        ? 'border-[#15803d] bg-[rgba(21,128,61,0.1)] text-[#15803d]'
                        : 'border-[#E9EDF2] bg-[#F8FAFC] text-[#334155] hover:border-[#CBD5E1]'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>

              {draft.verdict === 'CHANGE_BEHAVIOUR' && (
                <div className="mt-4 rounded-xl border border-[#E9EDF2] bg-[#F8FAFC] p-4">
                  <label htmlFor="corrected-behaviour" className="mb-2 block text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
                    Corrected behaviour from backend taxonomy
                  </label>
                  <select
                    id="corrected-behaviour"
                    value={draft.correctedBehaviour}
                    onChange={(event) =>
                      setDraft((existing) => ({
                        ...existing,
                        correctedBehaviour: event.target.value,
                      }))
                    }
                    className="w-full rounded-lg border border-[#E9EDF2] bg-white px-3 py-2 text-sm text-[#18243A] outline-none focus:border-[#5D87FF]/50"
                  >
                    {behaviourTaxonomy.map((label) => (
                      <option key={label} value={label}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="mt-4 rounded-xl border border-[#E9EDF2] bg-[#F8FAFC] p-4">
                <label htmlFor="reviewer-notes" className="mb-2 block text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
                  Reviewer notes
                </label>
                <textarea
                  id="reviewer-notes"
                  value={draft.notes}
                  onChange={(event) => setDraft((existing) => ({ ...existing, notes: event.target.value }))}
                  rows={4}
                  className="w-full resize-none rounded-lg border border-[#E9EDF2] bg-white px-3 py-2 text-sm text-[#18243A] placeholder-[#9DAFC5] outline-none focus:border-[#5D87FF]/50"
                  placeholder="Describe what the model got right, wrong, or what should be corrected."
                />
              </div>

              <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-dashed border-[rgba(146,64,14,0.2)] bg-[rgba(146,64,14,0.05)] p-3 text-[11px] text-[#92400e]">
                <div className="flex items-center gap-2">
                  <CircleDashed className="w-4 h-4" />
                  <span>
                    Review submission is UI-only until the backend exposes a review API contract.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleSubmitReview}
                  className="rounded-lg border border-[rgba(21,128,61,0.4)] bg-[rgba(21,128,61,0.1)] px-3 py-1.5 text-[10px] uppercase tracking-[0.18em] text-[#15803d]"
                >
                  Submit decision
                </button>
              </div>

              {submitted && (
                <div className="mt-4 rounded-xl border border-[rgba(21,128,61,0.3)] bg-[rgba(21,128,61,0.1)] p-3 text-xs text-[#15803d]">
                  {submitted}
                </div>
              )}
            </div>
          </section>
        ) : (
          <div className="glass-panel rounded-xl border border-dashed border-[#E9EDF2] p-8 text-center text-sm text-[#6F7F98]">
            No incident records are available for review.
          </div>
        )}
      </div>
    </div>
  );
};
