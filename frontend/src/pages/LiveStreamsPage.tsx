import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Camera, Expand, Gauge, Target } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { appConfig } from '../config/app';
import { useAlerts } from '../hooks/useAlerts';
import { useIncidents } from '../hooks/useIncidents';
import { GuardianAPI } from '../services/api';
import { useAppStore } from '../stores/app-store';
import { BehaviourEventResponse, TrackResponse, VideoResponse } from '../types';

const formatSeverity = (value?: string) => value?.toUpperCase() ?? 'UNKNOWN';
const PLAYBACK_RATES = [0.25, 0.5, 1, 1.5, 2];
// A track's nearest sampled point has to be within this many seconds of
// the current playhead to render at all — otherwise a track that
// hasn't been seen in a while would keep showing its last known (now
// stale) box forever, which is exactly the "frozen final frame"
// behaviour this rebuild replaces.
const SYNC_TOLERANCE_SECONDS = 0.6;
const MAX_FULL_LABELS = 6;

interface LiveOverlayEntity {
  trackId: number;
  className: string;
  confidence: number;
  xPct: number;
  yPct: number;
  velocity: number;
  zoneId?: string;
}

export const LiveStreamsPage: React.FC = () => {
  const [videos, setVideos] = useState<VideoResponse[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [tracks, setTracks] = useState<TrackResponse[]>([]);
  const [behaviourEvents, setBehaviourEvents] = useState<BehaviourEventResponse[]>([]);
  // Shared cache — same alert/incident data AppLayout, Dashboard, etc. use.
  const { data: alerts = [] } = useAlerts();
  const { data: incidents = [] } = useIncidents();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showTrails, setShowTrails] = useState(true);
  const [selectedTrackId, setSelectedTrackId] = useState<number | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const pendingFocusVideoId = useAppStore((state) => state.pendingFocusVideoId);
  const setPendingFocusVideoId = useAppStore((state) => state.setPendingFocusVideoId);

  useEffect(() => {
    GuardianAPI.getVideos().then((videoList) => {
      setVideos(videoList);
      // A "view source video" request from the Digital Twin (see
      // stores/app-store.ts) takes priority over the default first
      // video — this is the twin -> video half of the bidirectional
      // link the architecture spec asks for.
      if (pendingFocusVideoId && videoList.some((video) => video.id === pendingFocusVideoId)) {
        setSelectedVideoId(pendingFocusVideoId);
        setPendingFocusVideoId(null);
      } else {
        setSelectedVideoId(videoList[0]?.id ?? null);
      }
    });
    // Only ever consumed once, on mount — deliberately not in the deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedVideoId) {
      setTracks([]);
      setBehaviourEvents([]);
      return;
    }

    setCurrentTime(0);
    setSelectedTrackId(null);

    void (async () => {
      const [trackSummary, behaviourList] = await Promise.all([
        GuardianAPI.getVideoTracks(selectedVideoId),
        GuardianAPI.getBehavioursForVideo(selectedVideoId),
      ]);

      setTracks(trackSummary.tracks ?? []);
      setBehaviourEvents(behaviourList ?? []);
    })();
  }, [selectedVideoId]);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate, selectedVideoId]);

  const selectedVideo = useMemo(
    () => videos.find((video) => video.id === selectedVideoId) ?? videos[0] ?? null,
    [selectedVideoId, videos],
  );

  const videoSrc = useMemo(
    () => (selectedVideo ? `${appConfig.apiBaseUrl}/videos/${selectedVideo.id}/stream` : undefined),
    [selectedVideo],
  );

  const activeAlerts = useMemo(
    () => alerts.filter((alert) => alert.status === 'OPEN' || alert.status === 'ACKNOWLEDGED'),
    [alerts],
  );

  const relatedIncidents = useMemo(
    () =>
      selectedVideo?.camera_id
        ? incidents.filter((incident) => incident.camera_id === selectedVideo.camera_id)
        : [],
    [incidents, selectedVideo],
  );

  // The actual per-frame overlay: for every track, find the trajectory
  // point closest to the video's current playhead and render there —
  // not a frozen snapshot of the track's last-ever position. A track
  // whose nearest sample is more than SYNC_TOLERANCE_SECONDS away is
  // simply not currently visible, matching what a viewer would expect
  // ("this object isn't on screen right now") instead of a stale box.
  const liveEntities = useMemo<LiveOverlayEntity[]>(() => {
    if (!selectedVideo) return [];
    const width = Math.max(selectedVideo.width, 1);
    const height = Math.max(selectedVideo.height, 1);
    const out: LiveOverlayEntity[] = [];

    for (const track of tracks) {
      let nearestDelta = Infinity;
      let nearestPoint: TrackResponse['trajectory_points'][number] | null = null;
      for (const point of track.trajectory_points) {
        const delta = Math.abs(point.timestamp_seconds - currentTime);
        if (delta < nearestDelta) {
          nearestDelta = delta;
          nearestPoint = point;
        }
      }
      if (!nearestPoint || nearestDelta > SYNC_TOLERANCE_SECONDS) continue;

      const normalized = nearestPoint.normalized_xy
        ?? (nearestPoint.anchor_xy
          ? ([nearestPoint.anchor_xy[0] / width, nearestPoint.anchor_xy[1] / height] as [number, number])
          : ([nearestPoint.centroid_xy[0] / width, nearestPoint.bbox_xyxy[3] / height] as [number, number]));

      out.push({
        trackId: track.track_id,
        className: track.class_name,
        confidence: nearestPoint.confidence,
        xPct: normalized[0] * 100,
        yPct: normalized[1] * 100,
        velocity: Math.hypot(nearestPoint.velocity_xy[0], nearestPoint.velocity_xy[1]),
        zoneId: nearestPoint.zone_id,
      });
    }
    return out;
  }, [selectedVideo, tracks, currentTime]);

  // Crowd/congestion handling (spec section 22): only the top
  // MAX_FULL_LABELS entities (selected track first, then highest
  // confidence) get a text label with a simple vertical collision
  // nudge; the rest render as unlabeled dots plus an aggregate count,
  // instead of every track's label stacking illegibly on top of the
  // others.
  const { labeledEntities, dotOnlyEntities, overflowCount } = useMemo(() => {
    const sorted = [...liveEntities].sort((a, b) => {
      if (a.trackId === selectedTrackId) return -1;
      if (b.trackId === selectedTrackId) return 1;
      return b.confidence - a.confidence;
    });
    const labeled = sorted.slice(0, MAX_FULL_LABELS);
    const rest = sorted.slice(MAX_FULL_LABELS);

    const byY = [...labeled].sort((a, b) => a.yPct - b.yPct);
    const placedY: number[] = [];
    const withLabelY = byY.map((entity) => {
      let labelY = entity.yPct;
      for (const y of placedY) {
        if (Math.abs(y - labelY) < 7) labelY = y + 7;
      }
      placedY.push(labelY);
      return { ...entity, labelYPct: Math.min(96, labelY) };
    });

    return { labeledEntities: withLabelY, dotOnlyEntities: rest, overflowCount: rest.length };
  }, [liveEntities, selectedTrackId]);

  const selectedTrack = useMemo(
    () => tracks.find((track) => track.track_id === selectedTrackId) ?? null,
    [tracks, selectedTrackId],
  );

  const trajectoryTrail = useMemo(() => {
    if (!showTrails || !selectedTrack || !selectedVideo) {
      return [] as Array<{ x: number; y: number }>;
    }
    const width = Math.max(selectedVideo.width, 1);
    const height = Math.max(selectedVideo.height, 1);
    return selectedTrack.trajectory_points
      .filter((point) => point.timestamp_seconds <= currentTime + 0.05)
      .map((point) => {
        const normalized = point.normalized_xy ?? [point.centroid_xy[0] / width, point.centroid_xy[1] / height];
        return { x: normalized[0] * 100, y: normalized[1] * 100 };
      });
  }, [showTrails, selectedTrack, selectedVideo, currentTime]);

  const toggleFullscreen = async () => {
    const root = document.documentElement;

    if (!document.fullscreenElement) {
      await root.requestFullscreen();
      setIsFullscreen(true);
      return;
    }

    await document.exitFullscreen();
    setIsFullscreen(false);
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#18243A] tracking-tight">Multi-Camera Live Intelligence Matrix</h1>
          <p className="text-xs text-[#6F7F98]">Backend-backed warehouse monitoring with track overlays, behaviour events, and incident context.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center gap-2 rounded-lg border border-[#E9EDF2] bg-[#F1F5F9] px-3 py-1.5 text-[10px] uppercase tracking-[0.18em] text-[#18243A]">
            <Camera className="h-3.5 w-3.5 text-[#2F52D6]" />
            {videos.length} processed videos
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
        <div className="space-y-6">
          <div className="glass-panel rounded-xl p-4">
            <div className="mb-3 flex items-center justify-between gap-3 border-b border-[#E9EDF2] pb-3">
              <div className="flex items-center gap-2">
                <Camera className="h-4 w-4 text-[#2F52D6]" />
                <h2 className="text-sm font-bold text-[#18243A]">Selected Camera</h2>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge level={selectedVideo?.status === 'COMPLETED' ? 'LOW' : 'MEDIUM'} />
                <span className="text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">{selectedVideo?.camera_id ?? 'camera-unassigned'}</span>
              </div>
            </div>

            {selectedVideo ? (
              <>
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.18em] text-[#2F52D6]">{selectedVideo.camera_id ?? selectedVideo.id}</div>
                    <div className="mt-1 text-lg font-semibold text-[#18243A]">{selectedVideo.filename}</div>
                  </div>
                  <div className="rounded-full border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1 text-[10px] uppercase text-[#334155]">
                    {selectedVideo.fps} FPS · {selectedVideo.width}x{selectedVideo.height}
                  </div>
                </div>

                <div className="relative overflow-hidden rounded-xl border border-[#E9EDF2] bg-[#04070b]">
                  <video
                    key={selectedVideo.id}
                    ref={videoRef}
                    controls
                    src={videoSrc}
                    className="block aspect-video w-full bg-black object-cover"
                    onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                    onSeeked={(event) => setCurrentTime(event.currentTarget.currentTime)}
                  />

                  <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                    {trajectoryTrail.length > 1 && (
                      <polyline
                        points={trajectoryTrail.map((point) => `${point.x},${point.y}`).join(' ')}
                        fill="none"
                        stroke="#60a5fa"
                        strokeWidth="0.8"
                        strokeDasharray="1.2 1.2"
                        opacity={0.8}
                      />
                    )}

                    {dotOnlyEntities.map((entity) => (
                      <circle
                        key={entity.trackId}
                        cx={entity.xPct}
                        cy={entity.yPct}
                        r={0.9}
                        fill="rgba(157,175,197,0.85)"
                        className="pointer-events-auto"
                        style={{ cursor: 'pointer' }}
                        onClick={() => setSelectedTrackId(entity.trackId)}
                      />
                    ))}

                    {labeledEntities.map((entity) => {
                      const isSelected = entity.trackId === selectedTrackId;
                      const labelOffset = entity.labelYPct !== entity.yPct;
                      return (
                        <g key={entity.trackId}>
                          {labelOffset && (
                            <line
                              x1={entity.xPct}
                              y1={entity.yPct}
                              x2={entity.xPct}
                              y2={entity.labelYPct}
                              stroke="rgba(96,165,250,0.5)"
                              strokeWidth="0.25"
                            />
                          )}
                          <circle
                            cx={entity.xPct}
                            cy={entity.yPct}
                            r={isSelected ? 1.6 : 1.1}
                            fill={isSelected ? '#5D87FF' : 'rgba(96,165,250,0.9)'}
                            stroke="#e0f2fe"
                            strokeWidth="0.25"
                            className="pointer-events-auto"
                            style={{ cursor: 'pointer' }}
                            onClick={() => setSelectedTrackId(entity.trackId)}
                          />
                          <text
                            x={entity.xPct + 1.6}
                            y={entity.labelYPct + 0.8}
                            fill={isSelected ? '#ffffff' : '#dbeafe'}
                            fontSize="2.6"
                          >
                            #{entity.trackId} {entity.className}
                          </text>
                        </g>
                      );
                    })}
                  </svg>

                  {overflowCount > 0 && (
                    <div className="absolute right-3 top-3 rounded-full border border-white/15 bg-black/60 px-2.5 py-1 text-[10px] text-gray-100 backdrop-blur-sm">
                      +{overflowCount} more objects
                    </div>
                  )}

                  {/* Overlays the live video feed itself, so this strip stays dark
                      regardless of the page theme — matching text/status colors
                      need to read against arbitrary video footage, not the canvas. */}
                  <div className="absolute bottom-3 left-3 right-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/10 bg-black/60 px-3 py-2 text-[10px] text-gray-100 backdrop-blur-sm">
                    <div className="flex items-center gap-3">
                      <span className={`inline-flex items-center gap-1 ${isPlaying ? 'text-emerald-400' : 'text-amber-400'}`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${isPlaying ? 'bg-emerald-400 pulse-live' : 'bg-amber-400'}`} />
                        {isPlaying ? 'PLAYING' : 'PAUSED'}
                      </span>
                      <span>{liveEntities.length} objects in frame</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setShowTrails((value) => !value)}
                        className={`rounded border px-2 py-0.5 uppercase tracking-[0.1em] ${showTrails ? 'border-blue-400 text-blue-300' : 'border-white/20 text-gray-300'}`}
                      >
                        Trail
                      </button>
                      {PLAYBACK_RATES.map((rate) => (
                        <button
                          key={rate}
                          type="button"
                          onClick={() => setPlaybackRate(rate)}
                          className={`rounded border px-1.5 py-0.5 ${playbackRate === rate ? 'border-blue-400 text-blue-300' : 'border-white/20 text-gray-300'}`}
                        >
                          {rate}x
                        </button>
                      ))}
                      <button
                        type="button"
                        onClick={toggleFullscreen}
                        className="rounded border border-white/20 px-1.5 py-0.5 text-gray-300 hover:text-white"
                      >
                        <Expand className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                </div>

                {isFullscreen && <span className="sr-only">Fullscreen mode active</span>}
              </>
            ) : (
              <div className="rounded-lg border border-dashed border-[#E9EDF2] bg-[#F8FAFC] p-5 text-xs text-[#9DAFC5]">
                No processed video is available from the backend.
              </div>
            )}
          </div>

          <div className="glass-panel rounded-xl p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-[#18243A]">Camera Rail</h2>
              <span className="text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">Secondary views</span>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              {videos.map((video) => (
                <button
                  key={video.id}
                  type="button"
                  onClick={() => setSelectedVideoId(video.id)}
                  className={`rounded-lg border p-3 text-left transition ${selectedVideo?.id === video.id ? 'border-[#5D87FF] bg-[#5D87FF]/10' : 'border-[#E9EDF2] bg-[#F1F5F9] hover:border-[#CBD5E1]'}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Camera className="h-3.5 w-3.5 text-[#2F52D6]" />
                      <span className="text-[10px] uppercase tracking-[0.18em] text-[#2F52D6]">{video.camera_id ?? video.id}</span>
                    </div>
                    <StatusBadge level={video.status === 'COMPLETED' ? 'LOW' : 'MEDIUM'} size="sm" />
                  </div>
                  <div className="mt-2 text-sm font-medium text-[#18243A]">{video.filename}</div>
                  <div className="mt-1 text-[10px] text-[#6F7F98]">{video.storage_path}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <aside className="space-y-4">
          {selectedTrack ? (
            <div className="glass-panel rounded-xl p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-[#2F52D6]" />
                  <h2 className="text-sm font-bold text-[#18243A]">Track #{selectedTrack.track_id}</h2>
                </div>
                <button type="button" onClick={() => setSelectedTrackId(null)} className="text-[#9DAFC5] hover:text-[#18243A]">
                  ✕
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px] text-[#334155]">
                <div className="rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1.5">
                  <div className="text-[#9DAFC5]">Class</div>
                  <div className="font-semibold capitalize text-[#18243A]">{selectedTrack.class_name}</div>
                </div>
                <div className="rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1.5">
                  <div className="text-[#9DAFC5]">Confidence</div>
                  <div className="font-semibold text-[#18243A]">{(selectedTrack.confidence * 100).toFixed(1)}%</div>
                </div>
                <div className="rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1.5">
                  <div className="text-[#9DAFC5]">Duration tracked</div>
                  <div className="font-semibold text-[#18243A]">{selectedTrack.duration_seconds.toFixed(1)}s</div>
                </div>
                <div className="rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1.5">
                  <div className="text-[#9DAFC5]">Trajectory points</div>
                  <div className="font-semibold text-[#18243A]">{selectedTrack.trajectory_points.length}</div>
                </div>
              </div>
            </div>
          ) : null}

          <div className="glass-panel rounded-xl p-4">
            <div className="mb-3 flex items-center gap-2">
              <Target className="h-4 w-4 text-[#2F52D6]" />
              <h2 className="text-sm font-bold text-[#18243A]">Intelligence Sidebar</h2>
            </div>

            <div className="space-y-3">
              <div className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">Objects currently in frame</div>
                {liveEntities.length === 0 ? (
                  <div className="text-xs text-[#9DAFC5]">Nothing detected at the current playhead.</div>
                ) : (
                  liveEntities.map((entity) => (
                    <button
                      key={entity.trackId}
                      type="button"
                      onClick={() => setSelectedTrackId(entity.trackId)}
                      className={`mt-2 flex w-full items-center justify-between gap-3 rounded border px-2 py-1.5 text-left ${
                        selectedTrackId === entity.trackId ? 'border-[#5D87FF] bg-[#5D87FF]/10' : 'border-[#E9EDF2] bg-[#F1F5F9]'
                      }`}
                    >
                      <span className="text-xs capitalize text-[#18243A]">{entity.className}</span>
                      <span className="text-[10px] text-[#2F52D6]">Track #{entity.trackId}</span>
                    </button>
                  ))
                )}
              </div>

              <div className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">All tracks (full video)</div>
                {tracks.length === 0 ? (
                  <div className="text-xs text-[#9DAFC5]">No tracks exposed by the backend.</div>
                ) : (
                  tracks.map((track) => (
                    <button
                      key={track.id}
                      type="button"
                      onClick={() => setSelectedTrackId(track.track_id)}
                      className="mt-2 w-full rounded border border-[#E9EDF2] bg-[#F1F5F9] px-2 py-1.5 text-left"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs text-[#18243A]">Track #{track.track_id}</span>
                        <span className="text-[10px] text-[#15803d]">{track.class_name}</span>
                      </div>
                      <div className="mt-1 text-[10px] text-[#6F7F98]">{track.trajectory_points.length} points · {track.duration_seconds.toFixed(2)}s</div>
                    </button>
                  ))
                )}
              </div>

              <div className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">Behaviour</div>
                {behaviourEvents.length === 0 ? (
                  <div className="text-xs text-[#9DAFC5]">No behaviour events are available for this camera.</div>
                ) : (
                  behaviourEvents.map((event) => (
                    <div key={event.id ?? `${event.behaviour_type}-${event.start_frame}`} className="mt-2 rounded border border-[#E9EDF2] bg-[#F1F5F9] px-2 py-1.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-medium text-[#18243A]">{event.behaviour_type}</span>
                        <StatusBadge level={formatSeverity(event.severity)} size="sm" />
                      </div>
                      <div className="mt-1 text-[10px] text-[#6F7F98]">{event.description}</div>
                      <div className="mt-1 text-[10px] text-[#92400e]">confidence {event.confidence}</div>
                    </div>
                  ))
                )}
              </div>

              <div className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">Alerts</div>
                {activeAlerts.length === 0 ? (
                  <div className="text-xs text-[#9DAFC5]">No active alerts are available.</div>
                ) : (
                  activeAlerts.map((alert) => (
                    <div key={alert.id} className="mt-2 rounded border border-[#E9EDF2] bg-[#F1F5F9] px-2 py-1.5">
                      <div className="flex items-center justify-between gap-2">
                        <StatusBadge level={alert.alert_level} size="sm" />
                        <span className="text-[10px] text-[#6F7F98]">{alert.status}</span>
                      </div>
                      <div className="mt-1 text-[10px] text-[#334155]">{alert.message}</div>
                    </div>
                  ))
                )}
              </div>

              <div className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">Camera state</div>
                <div className="space-y-2 text-[10px] text-[#334155]">
                  <div className="flex items-center justify-between"><span>status</span><span>{selectedVideo?.status ?? 'UNKNOWN'}</span></div>
                  <div className="flex items-center justify-between"><span>camera</span><span>{selectedVideo?.camera_id ?? 'n/a'}</span></div>
                  <div className="flex items-center justify-between"><span>source</span><span className="truncate max-w-[120px]">{selectedVideo?.storage_path ?? 'n/a'}</span></div>
                  <div className="flex items-center justify-between"><span>tracks</span><span>{tracks.length}</span></div>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-xl p-4">
            <div className="mb-3 flex items-center gap-2">
              <Gauge className="h-4 w-4 text-[#92400e]" />
              <h2 className="text-sm font-bold text-[#18243A]">Event timeline</h2>
            </div>

            <div className="space-y-3 border-l border-[#E9EDF2] pl-3">
              {relatedIncidents.length === 0 ? (
                <div className="text-xs text-[#9DAFC5]">No camera-linked incidents are exposed for this view.</div>
              ) : (
                relatedIncidents.map((incident) => (
                  <div key={incident.id} className="relative">
                    <span className="absolute -left-[0.85rem] top-2.5 h-2.5 w-2.5 rounded-full bg-[#5D87FF]" />
                    <div className="rounded-lg border border-[#E9EDF2] bg-[#F1F5F9] p-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] uppercase tracking-[0.18em] text-[#2F52D6]">{incident.incident_code}</span>
                        <StatusBadge level={incident.severity} size="sm" />
                      </div>
                      <div className="mt-1 text-xs text-[#18243A]">{incident.title}</div>
                      <div className="mt-1 text-[10px] text-[#6F7F98]">{new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};
