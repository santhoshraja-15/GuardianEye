import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  Camera,
  Expand,
  Gauge,
  MapPinned,
  ShieldAlert,
  Target,
  Video,
  Zap,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { useAlerts } from '../hooks/useAlerts';
import { useIncidents } from '../hooks/useIncidents';
import { GuardianAPI } from '../services/api';
import { BehaviourEventResponse, TrackResponse, VideoResponse } from '../types';

const formatSeverity = (value?: string) => value?.toUpperCase() ?? 'UNKNOWN';

export const LiveStreamsPage: React.FC = () => {
  const [videos, setVideos] = useState<VideoResponse[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [tracks, setTracks] = useState<TrackResponse[]>([]);
  const [behaviourEvents, setBehaviourEvents] = useState<BehaviourEventResponse[]>([]);
  // Shared cache — same alert/incident data AppLayout, Dashboard, etc. use.
  const { data: alerts = [] } = useAlerts();
  const { data: incidents = [] } = useIncidents();
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    GuardianAPI.getVideos().then((videoList) => {
      setVideos(videoList);
      setSelectedVideoId(videoList[0]?.id ?? null);
    });
  }, []);

  useEffect(() => {
    if (!selectedVideoId) {
      setTracks([]);
      setBehaviourEvents([]);
      return;
    }

    void (async () => {
      const [trackSummary, behaviourList] = await Promise.all([
        GuardianAPI.getVideoTracks(selectedVideoId),
        GuardianAPI.getBehavioursForVideo(selectedVideoId),
      ]);

      setTracks(trackSummary.tracks ?? []);
      setBehaviourEvents(behaviourList ?? []);
    })();
  }, [selectedVideoId]);

  const selectedVideo = useMemo(
    () => videos.find((video) => video.id === selectedVideoId) ?? videos[0] ?? null,
    [selectedVideoId, videos],
  );

  const primaryTrack = useMemo(
    () => tracks[0] ?? null,
    [tracks],
  );

  const activeAlerts = useMemo(
    () => alerts.filter((alert) => alert.status === 'OPEN' || alert.status === 'ACKNOWLEDGED'),
    [alerts],
  );

  const relatedIncidents = useMemo(
    () => incidents.filter((incident) => incident.camera_id === selectedVideo?.camera_id || incident.zone_id === (selectedVideo ? selectedVideo.camera_id : undefined)),
    [incidents, selectedVideo],
  );

  const videoBoxOverlays = useMemo(() => {
    if (!selectedVideo || tracks.length === 0) {
      return [] as Array<{ id: string; left: number; top: number; width: number; height: number; label: string; confidence: number; className: string; trackId: number; velocity: number }>; 
    }

    return tracks.flatMap((track) =>
      track.trajectory_points.slice(-1).map((point) => {
        const [x1, y1, x2, y2] = point.bbox_xyxy;
        const left = (Math.min(x1, x2) / Math.max(selectedVideo.width, 1)) * 100;
        const top = (Math.min(y1, y2) / Math.max(selectedVideo.height, 1)) * 100;
        const width = (Math.abs(x2 - x1) / Math.max(selectedVideo.width, 1)) * 100;
        const height = (Math.abs(y2 - y1) / Math.max(selectedVideo.height, 1)) * 100;

        return {
          id: `${track.id}-${point.frame_number}`,
          left,
          top,
          width,
          height,
          label: `Track #${track.track_id}`,
          confidence: track.confidence,
          className: track.class_name,
          trackId: track.track_id,
          velocity: Math.hypot(point.velocity_xy[0], point.velocity_xy[1]),
        };
      }),
    );
  }, [selectedVideo, tracks]);

  const trajectoryPoints = useMemo(() => {
    if (!primaryTrack) {
      return [] as Array<{ x: number; y: number }>;
    }

    return primaryTrack.trajectory_points.map((point) => {
      const [x, y] = point.centroid_xy;
      return {
        x: (x / Math.max(selectedVideo?.width ?? 1, 1)) * 100,
        y: (y / Math.max(selectedVideo?.height ?? 1, 1)) * 100,
      };
    });
  }, [primaryTrack, selectedVideo]);

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
          <h1 className="text-xl font-bold text-white tracking-tight">Multi-Camera Live Intelligence Matrix</h1>
          <p className="text-xs text-gray-400">Backend-backed warehouse monitoring with track overlays, behaviour events, and incident context.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-[10px] font-mono uppercase tracking-[0.18em] text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400 pulse-live" />
            {videos.length} streams active
          </div>
          <button
            type="button"
            onClick={toggleFullscreen}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-black/30 px-3 py-1.5 text-[10px] font-mono uppercase tracking-[0.18em] text-gray-200"
          >
            <Expand className="h-3.5 w-3.5" />
            {isFullscreen ? 'Exit full' : 'Full screen'}
          </button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
        <div className="space-y-6">
          <div className="glass-panel rounded-xl p-4">
            <div className="mb-3 flex items-center justify-between gap-3 border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <Camera className="h-4 w-4 text-blue-400" />
                <h2 className="text-sm font-bold text-white">Selected Camera</h2>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge level={selectedVideo?.status === 'PROCESSED' ? 'LOW' : 'MEDIUM'} />
                <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">{selectedVideo?.camera_id ?? 'camera-unassigned'}</span>
              </div>
            </div>

            {selectedVideo ? (
              <>
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-blue-400">{selectedVideo.camera_id ?? selectedVideo.id}</div>
                    <div className="mt-1 text-lg font-semibold text-white">{selectedVideo.filename}</div>
                  </div>
                  <div className="rounded-full border border-white/10 bg-white/[0.02] px-2 py-1 text-[10px] font-mono uppercase text-gray-300">
                    {selectedVideo.fps} FPS · {selectedVideo.width}x{selectedVideo.height}
                  </div>
                </div>

                <div className="relative overflow-hidden rounded-xl border border-white/10 bg-[#04070b]">
                  <video
                    key={selectedVideo.id}
                    controls
                    src={selectedVideo.storage_path}
                    className="block aspect-video w-full bg-black object-cover"
                  />

                  <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                    {trajectoryPoints.length > 0 && (
                      <polyline
                        points={trajectoryPoints.map((point) => `${point.x},${point.y}`).join(' ')}
                        fill="none"
                        stroke="#60a5fa"
                        strokeWidth="0.8"
                        strokeDasharray="1.2 1.2"
                      />
                    )}
                    {videoBoxOverlays.map((box) => (
                      <g key={box.id}>
                        <rect
                          x={box.left}
                          y={box.top}
                          width={box.width}
                          height={box.height}
                          fill="rgba(96,165,250,0.08)"
                          stroke="rgba(96,165,250,0.9)"
                          strokeWidth="0.6"
                          rx="1"
                        />
                        <text x={box.left + 1} y={Math.max(box.top - 1, 2)} fill="#dbeafe" fontSize="2.4">{box.label}</text>
                      </g>
                    ))}
                  </svg>

                  <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/60 px-3 py-2 text-[10px] font-mono text-gray-200 backdrop-blur-sm">
                    <div className="flex items-center gap-3">
                      <span className="inline-flex items-center gap-1 text-emerald-400">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 pulse-live" />
                        LIVE
                      </span>
                      <span>{selectedVideo.status}</span>
                    </div>
                    <span>{selectedVideo.storage_path}</span>
                  </div>
                </div>
              </>
            ) : (
              <div className="rounded-lg border border-dashed border-white/10 bg-white/[0.02] p-5 text-xs text-gray-500">
                No live camera feed is available from the backend.
              </div>
            )}
          </div>

          <div className="glass-panel rounded-xl p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Camera Rail</h2>
              <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">Secondary views</span>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              {videos.map((video) => (
                <button
                  key={video.id}
                  type="button"
                  onClick={() => setSelectedVideoId(video.id)}
                  className={`rounded-lg border p-3 text-left transition ${selectedVideo?.id === video.id ? 'border-blue-500 bg-blue-500/10' : 'border-white/10 bg-black/20 hover:border-white/20'}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Camera className="h-3.5 w-3.5 text-blue-400" />
                      <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-blue-300">{video.camera_id ?? video.id}</span>
                    </div>
                    <StatusBadge level={video.status === 'PROCESSED' ? 'LOW' : 'MEDIUM'} size="sm" />
                  </div>
                  <div className="mt-2 text-sm font-medium text-white">{video.filename}</div>
                  <div className="mt-1 text-[10px] text-gray-400">{video.storage_path}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <aside className="space-y-4">
          <div className="glass-panel rounded-xl p-4">
            <div className="mb-3 flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-400" />
              <h2 className="text-sm font-bold text-white">Intelligence Sidebar</h2>
            </div>

            <div className="space-y-3">
              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                <div className="mb-2 text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">Objects</div>
                {tracks.length === 0 ? (
                  <div className="text-xs text-gray-500">No objects reported for this camera.</div>
                ) : (
                  tracks.map((track) => (
                    <button
                      key={track.id}
                      type="button"
                      onClick={() => setSelectedVideoId(selectedVideo?.id ?? null)}
                      className="mt-2 flex w-full items-center justify-between gap-3 rounded border border-white/10 bg-black/20 px-2 py-1.5 text-left"
                    >
                      <span className="text-xs text-white">{track.class_name}</span>
                      <span className="text-[10px] font-mono text-blue-300">Track #{track.track_id}</span>
                    </button>
                  ))
                )}
              </div>

              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                <div className="mb-2 text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">Tracks</div>
                {tracks.length === 0 ? (
                  <div className="text-xs text-gray-500">No tracks exposed by the backend.</div>
                ) : (
                  tracks.map((track) => (
                    <div key={track.id} className="mt-2 rounded border border-white/10 bg-black/20 px-2 py-1.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs text-white">Track #{track.track_id}</span>
                        <span className="text-[10px] font-mono text-emerald-300">{track.class_name}</span>
                      </div>
                      <div className="mt-1 text-[10px] text-gray-400">{track.trajectory_points.length} points · {track.duration_seconds.toFixed(2)}s</div>
                    </div>
                  ))
                )}
              </div>

              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                <div className="mb-2 text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">Behaviour</div>
                {behaviourEvents.length === 0 ? (
                  <div className="text-xs text-gray-500">No behaviour events are available for this camera.</div>
                ) : (
                  behaviourEvents.map((event) => (
                    <div key={event.id ?? `${event.behaviour_type}-${event.start_frame}`} className="mt-2 rounded border border-white/10 bg-black/20 px-2 py-1.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-medium text-white">{event.behaviour_type}</span>
                        <StatusBadge level={formatSeverity(event.severity)} size="sm" />
                      </div>
                      <div className="mt-1 text-[10px] text-gray-400">{event.description}</div>
                      <div className="mt-1 text-[10px] font-mono text-amber-300">confidence {event.confidence}</div>
                    </div>
                  ))
                )}
              </div>

              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                <div className="mb-2 text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">Risk</div>
                {behaviourEvents.length === 0 ? (
                  <div className="text-xs text-gray-500">No risk data exposed by the backend.</div>
                ) : (
                  behaviourEvents.map((event) => (
                    <div key={`${event.id ?? event.behaviour_type}-risk`} className="mt-2 rounded border border-white/10 bg-black/20 px-2 py-1.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs text-white">{event.behaviour_type}</span>
                        <StatusBadge level={formatSeverity(event.severity)} size="sm" />
                      </div>
                      <div className="mt-1 text-[10px] text-gray-400">{event.evidence?.zone_code ?? 'zone unassigned'}</div>
                    </div>
                  ))
                )}
              </div>

              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                <div className="mb-2 text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">Alerts</div>
                {activeAlerts.length === 0 ? (
                  <div className="text-xs text-gray-500">No active alerts are available.</div>
                ) : (
                  activeAlerts.map((alert) => (
                    <div key={alert.id} className="mt-2 rounded border border-white/10 bg-black/20 px-2 py-1.5">
                      <div className="flex items-center justify-between gap-2">
                        <StatusBadge level={alert.alert_level} size="sm" />
                        <span className="text-[10px] font-mono text-gray-400">{alert.status}</span>
                      </div>
                      <div className="mt-1 text-[10px] text-gray-300">{alert.message}</div>
                    </div>
                  ))
                )}
              </div>

              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                <div className="mb-2 text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">Camera state</div>
                <div className="space-y-2 text-[10px] text-gray-300">
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
              <Gauge className="h-4 w-4 text-amber-400" />
              <h2 className="text-sm font-bold text-white">Event timeline</h2>
            </div>

            <div className="space-y-3 border-l border-white/10 pl-3">
              {relatedIncidents.length === 0 ? (
                <div className="text-xs text-gray-500">No camera-linked incidents are exposed for this view.</div>
              ) : (
                relatedIncidents.map((incident) => (
                  <div key={incident.id} className="relative">
                    <span className="absolute -left-[0.85rem] top-2.5 h-2.5 w-2.5 rounded-full bg-blue-500" />
                    <div className="rounded-lg border border-white/10 bg-black/20 p-2">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-blue-300">{incident.incident_code}</span>
                        <StatusBadge level={incident.severity} size="sm" />
                      </div>
                      <div className="mt-1 text-xs text-white">{incident.title}</div>
                      <div className="mt-1 text-[10px] text-gray-400">{new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
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
