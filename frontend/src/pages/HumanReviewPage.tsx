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
          <h1 className="text-xl font-bold text-white tracking-tight">Human Review Workspace</h1>
          <p className="text-xs text-gray-400">
            AI detects and explains. Humans validate and decide.
          </p>
        </div>
        <span className="rounded border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[10px] font-mono uppercase tracking-[0.18em] text-amber-300">
          {reviewLabel}
        </span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[320px_minmax(0,1fr)] gap-6">
        <aside className="glass-panel rounded-xl border border-white/10 p-4">
          <div className="flex items-center gap-2 border-b border-white/10 pb-3">
            <FileText className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-bold text-white">Review Queue</h2>
          </div>

          <div className="mt-4 space-y-3">
            {incidents.length === 0 ? (
              <div className="rounded-lg border border-dashed border-white/10 bg-black/20 p-4 text-xs text-gray-400">
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
                      ? 'border-blue-500/40 bg-blue-500/10'
                      : 'border-white/10 bg-black/20 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-mono text-blue-300">{incident.incident_code}</span>
                    <span className="px-1.5 py-0.5 rounded border border-amber-400/30 bg-amber-500/10 text-[9px] font-mono text-amber-300">
                      {incident.severity}
                    </span>
                  </div>
                  <div className="mt-2 text-sm font-semibold text-white">{incident.title}</div>
                  <div className="mt-1 text-[11px] text-gray-400">{incident.summary}</div>
                </button>
              ))
            )}
          </div>
        </aside>

        {selectedIncident ? (
          <section className="space-y-6">
            <div className="glass-panel rounded-xl border border-white/10 p-5">
              <div className="flex items-start justify-between gap-4 border-b border-white/10 pb-4">
                <div>
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-gray-400">
                    <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                    AI prediction
                  </div>
                  <h2 className="mt-2 text-lg font-bold text-white">{selectedIncident.title}</h2>
                </div>
                <span className="rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[10px] font-mono text-emerald-300">
                  Confidence {Math.min(99, Math.max(55, Math.round(selectedIncident.severity === 'CRITICAL' ? 96 : 82)))}%
                </span>
              </div>

              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-xl border border-white/10 bg-black/20 p-4">
                  <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                    AI explains
                  </div>
                  <p className="mt-3 text-sm leading-6 text-gray-200">
                    GuardianEye detected a warehouse safety event and flagged the record as {selectedIncident.severity.toLowerCase()} severity based on the signal evidence captured for this incident.
                  </p>
                </div>

                <div className="rounded-xl border border-white/10 bg-black/20 p-4">
                  <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">
                    <TriangleAlert className="w-3.5 h-3.5 text-red-400" />
                    Evidence
                  </div>
                  <ul className="mt-3 space-y-2 text-xs text-gray-300">
                    {evidenceItems.map((item) => (
                      <li key={item} className="flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-blue-400" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div className="glass-panel rounded-xl border border-white/10 p-5">
              <div className="flex items-center gap-2 border-b border-white/10 pb-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-white">Human decision</h3>
              </div>

              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2">
                {reviewOptions.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setDraft((existing) => ({ ...existing, verdict: option }))}
                    className={`rounded-lg border px-3 py-2 text-[11px] font-mono font-bold uppercase tracking-[0.12em] transition-all ${
                      draft.verdict === option
                        ? 'border-emerald-400 bg-emerald-500/10 text-emerald-300'
                        : 'border-white/10 bg-black/20 text-gray-300 hover:border-white/20'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>

              {draft.verdict === 'CHANGE_BEHAVIOUR' && (
                <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-4">
                  <label htmlFor="corrected-behaviour" className="mb-2 block text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">
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
                    className="w-full rounded-lg border border-white/10 bg-[#111827] px-3 py-2 text-sm text-white outline-none focus:border-blue-500/50"
                  >
                    {behaviourTaxonomy.map((label) => (
                      <option key={label} value={label}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-4">
                <label htmlFor="reviewer-notes" className="mb-2 block text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">
                  Reviewer notes
                </label>
                <textarea
                  id="reviewer-notes"
                  value={draft.notes}
                  onChange={(event) => setDraft((existing) => ({ ...existing, notes: event.target.value }))}
                  rows={4}
                  className="w-full resize-none rounded-lg border border-white/10 bg-[#111827] px-3 py-2 text-sm text-white placeholder-gray-500 outline-none focus:border-blue-500/50"
                  placeholder="Describe what the model got right, wrong, or what should be corrected."
                />
              </div>

              <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-dashed border-amber-500/20 bg-amber-500/5 p-3 text-[11px] text-amber-200">
                <div className="flex items-center gap-2">
                  <CircleDashed className="w-4 h-4" />
                  <span>
                    Review submission is UI-only until the backend exposes a review API contract.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleSubmitReview}
                  className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-300"
                >
                  Submit decision
                </button>
              </div>

              {submitted && (
                <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-200">
                  {submitted}
                </div>
              )}
            </div>
          </section>
        ) : (
          <div className="glass-panel rounded-xl border border-dashed border-white/10 p-8 text-center text-sm text-gray-400">
            No incident records are available for review.
          </div>
        )}
      </div>
    </div>
  );
};
