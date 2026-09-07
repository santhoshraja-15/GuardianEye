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
          <h1 className="text-xl font-bold text-white tracking-tight">
            Evidence Vault & Replay
          </h1>
          <p className="text-xs text-gray-400">
            Observed evidence from the backend only. No synthetic video, prediction, or incident data is created in the UI.
          </p>
        </div>

        <button className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-500 transition-colors">
          <Download className="w-4 h-4" />
          <span>Export evidence pack</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-3">
          <div className="text-xs font-mono uppercase tracking-wider text-gray-400">
            Incident evidence
          </div>

          {incidents.length === 0 ? (
            <div className="glass-panel rounded-xl p-4 text-xs text-gray-400">
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
                    ? 'border-blue-500 shadow-lg shadow-blue-500/10'
                    : 'border-white/10 hover:border-white/20'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-blue-400">{incident.incident_code}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 font-bold">
                    <CheckCircle2 className="w-3 h-3" />
                    {incident.status}
                  </span>
                </div>
                <div className="text-xs font-semibold text-white mt-1.5">{incident.title}</div>
                <div className="text-[10px] font-mono text-gray-500 mt-2">
                  {new Date(incident.created_at).toLocaleString()}
                </div>
              </button>
            ))
          )}
        </div>

        <div className="lg:col-span-2 space-y-4">
          {selectedIncident && (
            <div className="glass-panel rounded-xl p-5 space-y-5">
              <div className="flex items-start justify-between border-b border-white/10 pb-4">
                <div>
                  <div className="text-xs font-mono text-gray-400">CASE / EVIDENCE MANIFEST</div>
                  <h2 className="text-base font-bold text-white mt-0.5">{selectedIncident.title}</h2>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
                  <Lock className="w-3.5 h-3.5" />
                  <span>OBSERVED EVIDENCE</span>
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
                  <span>Replay workflow</span>
                  <span>{replay?.behaviour_code ?? 'UNKNOWN'}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-[10px] font-mono text-gray-300">
                  {[
                    { label: 'PRE-EVENT', value: `${evidence?.pre_event_seconds ?? 0}s` },
                    { label: 'EVENT', value: replay ? `${replay.duration_seconds.toFixed(1)}s` : 'N/A' },
                    { label: 'POST-EVENT', value: `${evidence?.post_event_seconds ?? 0}s` },
                  ].map((stage) => (
                    <div key={stage.label} className="rounded-lg border border-white/10 bg-white/[0.02] p-2 text-center">
                      <div className="text-blue-300 font-bold">{stage.label}</div>
                      <div className="mt-1 text-gray-400">{stage.value}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                <div className="mb-3 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
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
                            ? 'border-blue-500 bg-blue-500/20 text-blue-300'
                            : 'border-white/10 text-gray-400'
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
                      className="w-full rounded-lg border border-white/10 bg-black"
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
                      <div className="flex items-center justify-between text-[10px] text-gray-400 font-mono">
                        <span>{currentTime.toFixed(1)}s</span>
                        <div className="flex items-center gap-2">
                          <button type="button" onClick={() => handleSeek(Math.max(0, currentTime - 1))} className="rounded border border-white/10 px-2 py-1">
                            -1s
                          </button>
                          <button type="button" onClick={() => handleSeek(Math.min(maxTimelineSeconds, currentTime + 1))} className="rounded border border-white/10 px-2 py-1">
                            +1s
                          </button>
                          <button type="button" onClick={handleFullscreen} className="rounded border border-white/10 px-2 py-1 flex items-center gap-1">
                            <Play className="h-3 w-3" />
                            Fullscreen
                          </button>
                        </div>
                        <span>{maxTimelineSeconds.toFixed(1)}s</span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="rounded-lg border border-dashed border-white/10 p-6 text-xs text-gray-500 text-center">
                    No clip URL is exposed by the backend for this incident.
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-gray-400 flex items-center gap-1.5">
                      <Hash className="w-3.5 h-3.5 text-blue-400" />
                      Video clip checksum
                    </span>
                    <button onClick={() => handleCopyHash(evidence?.sha256_checksum ?? replay?.sha256_checksum ?? '')} className="text-blue-400 hover:text-blue-300 flex items-center gap-1 text-[11px]">
                      <Copy className="w-3 h-3" />
                      {copied ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <div className="font-mono text-xs text-emerald-400 break-all select-all">
                    {evidence?.sha256_checksum ?? replay?.sha256_checksum ?? 'No checksum exposed'}
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-gray-400 flex items-center gap-1.5">
                      <Video className="w-3.5 h-3.5 text-purple-400" />
                      Snapshot URL
                    </span>
                  </div>
                  <div className="font-mono text-[10px] text-purple-300 break-all">
                    {displaySnapshotUrl || 'No snapshot URL exposed'}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-emerald-300">Observed evidence</div>
                  <div className="mt-2 text-xs text-gray-200">
                    Clip, checksum, snapshot, pre/post timing, and replay keyframes are all taken from backend evidence and replay responses.
                  </div>
                </div>

                <div className="rounded-lg border border-slate-500/20 bg-slate-500/5 p-3">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-300">Predictions</div>
                  <div className="mt-2 text-xs text-gray-400">
                    No prediction metadata is exposed by the backend evidence contract for this incident.
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="text-xs font-mono uppercase tracking-wider text-gray-400">
                  Keyframes and track overlays
                </div>

                {replay && replay.keyframes.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {replay.keyframes.map((keyframe) => (
                      <div key={`${keyframe.frame_index}-${keyframe.timestamp_seconds}`} className="rounded-lg border border-white/10 bg-black/30 p-3">
                        <div className="mb-2 flex items-center justify-between text-[11px] font-mono text-gray-300">
                          <span>Frame #{keyframe.frame_index}</span>
                          <span>{keyframe.timestamp_seconds.toFixed(1)}s</span>
                        </div>
                        <img src={keyframe.image_url} alt={`Frame ${keyframe.frame_index}`} className="h-28 w-full rounded-lg object-cover border border-white/10" />
                        <div className="mt-3 space-y-2">
                          {keyframe.boxes.length > 0 ? keyframe.boxes.map((box) => (
                            <div key={`${box.track_id}-${box.class_name}-${box.state_label}`} className="rounded border border-blue-500/30 bg-blue-500/10 px-2 py-1 text-[10px] text-blue-200 font-mono">
                              {box.class_name} · track {box.track_id} · {box.state_label}
                            </div>
                          )) : (
                            <div className="rounded border border-white/10 bg-white/[0.02] px-2 py-1 text-[10px] text-gray-400 font-mono">
                              No overlay boxes were returned for this frame.
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed border-white/10 p-4 text-xs text-gray-500">
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
