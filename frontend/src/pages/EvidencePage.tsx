import React, { useEffect, useMemo, useRef, useState } from 'react';
import { CheckCircle2, Copy, Download, Hash, Lock, Play, Video } from 'lucide-react';
import { useIncidents } from '../hooks/useIncidents';
import { GuardianAPI } from '../services/api';
import { EvidencePackageItem, IncidentReplayItem } from '../types';

const playbackRates = [0.5, 1, 1.5, 2];

export const EvidencePage: React.FC = () => {
  // Shared cache — same incident list AppLayout/Dashboard/Incident Board use.
  const { data: incidents = [] } = useIncidents();
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<EvidencePackageItem | null>(null);
  const [replay, setReplay] = useState<IncidentReplayItem | null>(null);
  const [copied, setCopied] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (!selectedIncidentId && incidents.length > 0) {
      setSelectedIncidentId(incidents[0].id);
    }
  }, [incidents, selectedIncidentId]);

  useEffect(() => {
    if (!selectedIncidentId) {
      setEvidence(null);
      setReplay(null);
      return;
    }

    let isMounted = true;

    Promise.all([
      GuardianAPI.getEvidenceForIncident(selectedIncidentId),
      GuardianAPI.getIncidentReplay(selectedIncidentId),
    ])
      .then(([evidenceData, replayData]) => {
        if (!isMounted) return;
        setEvidence(evidenceData);
        setReplay(replayData);
        setCurrentTime(0);
      })
      .catch(() => {
        if (!isMounted) return;
        setEvidence(null);
        setReplay(null);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedIncidentId]);

  const selectedIncident = useMemo(
    () => incidents.find((incident) => incident.id === selectedIncidentId) ?? incidents[0] ?? null,
    [incidents, selectedIncidentId],
  );

  const maxTimelineSeconds = useMemo(
    () => Math.max(replay?.duration_seconds ?? 0, (evidence?.pre_event_seconds ?? 0) + (evidence?.post_event_seconds ?? 0), 1),
    [evidence, replay],
  );

  const handleCopyHash = async (hash: string) => {
    await navigator.clipboard.writeText(hash);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const handleSeek = (value: number) => {
    setCurrentTime(value);
    if (videoRef.current) {
      videoRef.current.currentTime = value;
    }
  };

  const handleFullscreen = async () => {
    if (videoRef.current && document.fullscreenElement !== videoRef.current) {
      await videoRef.current.requestFullscreen();
    }
  };

  const displayClipUrl = replay?.clip_url ?? evidence?.clip_path ?? '';
  const displaySnapshotUrl = replay?.snapshot_url ?? evidence?.snapshot_path ?? '';

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#18243A] tracking-tight">
            Evidence Vault & Replay
          </h1>
          <p className="text-xs text-[#6F7F98]">
            Observed evidence from the backend only. No synthetic video, prediction, or incident data is created in the UI.
          </p>
        </div>

        <button className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-[#5D87FF] text-[#18243A] text-xs font-semibold hover:bg-[#3F6AE0] transition-colors">
          <Download className="w-4 h-4" />
          <span>Export evidence pack</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-3 xl:sticky xl:top-24 xl:self-start">
          <div className="text-xs uppercase tracking-wider text-[#6F7F98]">
            Incident evidence
          </div>

          <div className="ge-scroll-panel space-y-3 max-h-[calc(100vh-280px)] pr-1">
          {incidents.length === 0 ? (
            <div className="glass-panel rounded-xl p-4 text-xs text-[#6F7F98]">
              No incident evidence was returned by the backend.
            </div>
          ) : (
            incidents.map((incident) => (
              <button
                key={incident.id}
                type="button"
                onClick={() => setSelectedIncidentId(incident.id)}
                className={`glass-panel rounded-xl p-4 text-left border transition-all w-full ${
                  selectedIncidentId === incident.id
                    ? 'border-[#5D87FF] shadow-lg shadow-[#5D87FF]/10'
                    : 'border-[#E9EDF2] hover:border-[#CBD5E1]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#2F52D6]">{incident.incident_code}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-[rgba(21,128,61,0.15)] text-[#15803d] border border-[rgba(21,128,61,0.3)] flex items-center gap-1 font-bold">
                    <CheckCircle2 className="w-3 h-3" />
                    {incident.status}
                  </span>
                </div>
                <div className="text-xs font-semibold text-[#18243A] mt-1.5">{incident.title}</div>
                <div className="text-[10px] text-[#9DAFC5] mt-2">
                  {new Date(incident.created_at).toLocaleString()}
                </div>
              </button>
            ))
          )}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          {selectedIncident && (
            <div className="glass-panel rounded-xl p-5 space-y-5">
              <div className="flex items-start justify-between border-b border-[#E9EDF2] pb-4">
                <div>
                  <div className="text-xs text-[#6F7F98]">CASE / EVIDENCE MANIFEST</div>
                  <h2 className="text-base font-bold text-[#18243A] mt-0.5">{selectedIncident.title}</h2>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[rgba(21,128,61,0.1)] border border-[rgba(21,128,61,0.3)] text-[#15803d] text-xs">
                  <Lock className="w-3.5 h-3.5" />
                  <span>OBSERVED EVIDENCE</span>
                </div>
              </div>

              <div className="rounded-xl border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
                  <span>Replay workflow</span>
                  <span>{replay?.behaviour_code ?? 'UNKNOWN'}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-[10px] text-[#334155]">
                  {[
                    { label: 'PRE-EVENT', value: `${evidence?.pre_event_seconds ?? 0}s` },
                    { label: 'EVENT', value: replay ? `${replay.duration_seconds.toFixed(1)}s` : 'N/A' },
                    { label: 'POST-EVENT', value: `${evidence?.post_event_seconds ?? 0}s` },
                  ].map((stage) => (
                    <div key={stage.label} className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-2 text-center">
                      <div className="text-[#2F52D6] font-bold">{stage.label}</div>
                      <div className="mt-1 text-[#6F7F98]">{stage.value}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                <div className="mb-3 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
                  <span>Video replay</span>
                  <div className="flex items-center gap-2">
                    {playbackRates.map((rate) => (
                      <button
                        key={rate}
                        type="button"
                        onClick={() => {
                          setPlaybackRate(rate);
                          if (videoRef.current) videoRef.current.playbackRate = rate;
                        }}
                        className={`rounded border px-2 py-1 ${
                          playbackRate === rate
                            ? 'border-[#5D87FF] bg-[#5D87FF]/15 text-[#2F52D6]'
                            : 'border-[#E9EDF2] text-[#6F7F98]'
                        }`}
                      >
                        {rate}x
                      </button>
                    ))}
                  </div>
                </div>

                {displayClipUrl ? (
                  <>
                    <video
                      ref={videoRef}
                      className="w-full rounded-lg border border-[#E9EDF2] bg-black"
                      src={displayClipUrl}
                      poster={displaySnapshotUrl}
                      controls
                      preload="metadata"
                      onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
                      onLoadedMetadata={(event) => setCurrentTime(event.currentTarget.currentTime)}
                      style={{ maxHeight: '420px' }}
                    />
                    <div className="mt-3 space-y-2">
                      <input
                        type="range"
                        aria-label="Seek video timeline"
                        min={0}
                        max={maxTimelineSeconds}
                        step={0.1}
                        value={currentTime}
                        onChange={(event) => handleSeek(Number(event.target.value))}
                        className="w-full accent-blue-500"
                      />
                      <div className="flex items-center justify-between text-[10px] text-[#6F7F98]">
                        <span>{currentTime.toFixed(1)}s</span>
                        <div className="flex items-center gap-2">
                          <button type="button" onClick={() => handleSeek(Math.max(0, currentTime - 1))} className="rounded border border-[#E9EDF2] px-2 py-1">
                            -1s
                          </button>
                          <button type="button" onClick={() => handleSeek(Math.min(maxTimelineSeconds, currentTime + 1))} className="rounded border border-[#E9EDF2] px-2 py-1">
                            +1s
                          </button>
                          <button type="button" onClick={handleFullscreen} className="rounded border border-[#E9EDF2] px-2 py-1 flex items-center gap-1">
                            <Play className="h-3 w-3" />
                            Fullscreen
                          </button>
                        </div>
                        <span>{maxTimelineSeconds.toFixed(1)}s</span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="rounded-lg border border-dashed border-[#E9EDF2] p-6 text-xs text-[#9DAFC5] text-center">
                    No clip URL is exposed by the backend for this incident.
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#E9EDF2] space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#6F7F98] flex items-center gap-1.5">
                      <Hash className="w-3.5 h-3.5 text-[#2F52D6]" />
                      Video clip checksum
                    </span>
                    <button onClick={() => handleCopyHash(evidence?.sha256_checksum ?? replay?.sha256_checksum ?? '')} className="text-[#2F52D6] hover:text-[#2F52D6] flex items-center gap-1 text-[11px]">
                      <Copy className="w-3 h-3" />
                      {copied ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <div className="text-xs text-[#15803d] break-all select-all">
                    {evidence?.sha256_checksum ?? replay?.sha256_checksum ?? 'No checksum exposed'}
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#E9EDF2] space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#6F7F98] flex items-center gap-1.5">
                      <Video className="w-3.5 h-3.5 text-[#2F52D6]" />
                      Snapshot URL
                    </span>
                  </div>
                  <div className="text-[10px] text-[#2F52D6] break-all">
                    {displaySnapshotUrl || 'No snapshot URL exposed'}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="rounded-lg border border-[rgba(21,128,61,0.2)] bg-[rgba(21,128,61,0.1)] p-3">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-[#15803d]">Observed evidence</div>
                  <div className="mt-2 text-xs text-[#18243A]">
                    Clip, checksum, snapshot, pre/post timing, and replay keyframes are all taken from backend evidence and replay responses.
                  </div>
                </div>

                <div className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-[#334155]">Predictions</div>
                  <div className="mt-2 text-xs text-[#6F7F98]">
                    No prediction metadata is exposed by the backend evidence contract for this incident.
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="text-xs uppercase tracking-wider text-[#6F7F98]">
                  Keyframes and track overlays
                </div>

                {replay && replay.keyframes.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {replay.keyframes.map((keyframe) => (
                      <div key={`${keyframe.frame_index}-${keyframe.timestamp_seconds}`} className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                        <div className="mb-2 flex items-center justify-between text-[11px] text-[#334155]">
                          <span>Frame #{keyframe.frame_index}</span>
                          <span>{keyframe.timestamp_seconds.toFixed(1)}s</span>
                        </div>
                        <img src={keyframe.image_url} alt={`Frame ${keyframe.frame_index}`} className="h-28 w-full rounded-lg object-cover border border-[#E9EDF2]" />
                        <div className="mt-3 space-y-2">
                          {keyframe.boxes.length > 0 ? keyframe.boxes.map((box) => (
                            <div key={`${box.track_id}-${box.class_name}-${box.state_label}`} className="rounded border border-[#5D87FF]/30 bg-[#5D87FF]/10 px-2 py-1 text-[10px] text-[#2F52D6]">
                              {box.class_name} · track {box.track_id} · {box.state_label}
                            </div>
                          )) : (
                            <div className="rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1 text-[10px] text-[#6F7F98]">
                              No overlay boxes were returned for this frame.
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed border-[#E9EDF2] p-4 text-xs text-[#9DAFC5]">
                    No replay keyframes or track overlays are exposed for this incident.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
