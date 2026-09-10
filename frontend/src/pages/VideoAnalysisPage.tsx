import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  FileVideo,
  Loader2,
  Pause,
  Play,
  RotateCcw,
  UploadCloud,
  X,
  Zap,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { GuardianAPI } from '../services/api';
import { BehaviourEventResponse, TrackResponse, VideoResponse } from '../types';

export const VideoAnalysisPage: React.FC = () => {
  const [videos, setVideos] = useState<VideoResponse[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [tracks, setTracks] = useState<TrackResponse[]>([]);
  const [behaviours, setBehaviours] = useState<BehaviourEventResponse[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);

  const refreshVideos = async () => {
    try {
      const list = await GuardianAPI.getVideos();
      setVideos(list);
      if (list.length > 0 && !selectedVideoId) {
        setSelectedVideoId(list[0].id);
      }
    } catch {
      // Keep existing
    }
  };

  useEffect(() => {
    void refreshVideos();
  }, []);

  const selectedVideo = useMemo(
    () => videos.find((v) => v.id === selectedVideoId) ?? videos[0] ?? null,
    [selectedVideoId, videos],
  );

  useEffect(() => {
    if (!selectedVideo) {
      setTracks([]);
      setBehaviours([]);
      return;
    }

    let isMounted = true;
    Promise.all([
      GuardianAPI.getVideoTracks(selectedVideo.id).catch(() => ({ total_tracks: 0, tracks: [] })),
      GuardianAPI.getBehavioursForVideo(selectedVideo.id).catch(() => []),
    ]).then(([trackSummary, behaviourList]) => {
      if (!isMounted) return;
      setTracks(trackSummary.tracks || []);
      setBehaviours(behaviourList || []);
    });

    return () => {
      isMounted = false;
    };
  }, [selectedVideo]);

  const handleTriggerAnalysis = async () => {
    if (!selectedVideo) return;
    setIsProcessing(true);
    try {
      await GuardianAPI.processVideo(selectedVideo.id);
      await refreshVideos();
    } catch (e) {
      console.error(e);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploading(true);
    try {
      await GuardianAPI.uploadVideo(uploadFile, undefined, true);
      setUploadModalOpen(false);
      setUploadFile(null);
      await refreshVideos();
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const activeTracksAtCurrentTime = useMemo(() => {
    if (!selectedVideo || tracks.length === 0) return [];
    return tracks
      .map((track) => {
        const matchingPoint = track.trajectory_points.find(
          (p) => Math.abs(p.timestamp_seconds - currentTime) < 0.2,
        );
        if (!matchingPoint) return null;
        const [x1, y1, x2, y2] = matchingPoint.bbox_xyxy;
        const left = (Math.min(x1, x2) / Math.max(selectedVideo.width || 1920, 1)) * 100;
        const top = (Math.min(y1, y2) / Math.max(selectedVideo.height || 1080, 1)) * 100;
        const width = (Math.abs(x2 - x1) / Math.max(selectedVideo.width || 1920, 1)) * 100;
        const height = (Math.abs(y2 - y1) / Math.max(selectedVideo.height || 1080, 1)) * 100;
        return {
          trackId: track.track_id,
          className: track.class_name,
          confidence: track.confidence,
          velocity: Math.hypot(matchingPoint.velocity_xy[0], matchingPoint.velocity_xy[1]),
          left,
          top,
          width,
          height,
        };
      })
      .filter((item): item is NonNullable<typeof item> => item !== null);
  }, [currentTime, selectedVideo, tracks]);

  const videoSrc = selectedVideo ? `/storage/${selectedVideo.storage_path}` : '';

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#18243A] tracking-tight">
            Video Intelligence & Anomaly Forensic Replay
          </h1>
          <p className="text-xs text-[#6F7F98]">
            Frame-by-frame entity perception, Kalman speed vectors, and state machine transition histories.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {selectedVideo && selectedVideo.status !== 'PROCESSING' && (
            <button
              onClick={handleTriggerAnalysis}
              disabled={isProcessing}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[rgba(21,128,61,0.08)] text-[#15803d] border border-[rgba(21,128,61,0.3)] text-xs font-semibold hover:bg-[rgba(21,128,61,0.14)] transition-all"
            >
              {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              <span>{isProcessing ? 'Processing...' : 'Run AI Analysis'}</span>
            </button>
          )}

          <button
            onClick={() => setUploadModalOpen(true)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#5D87FF] text-white text-xs font-semibold hover:bg-[#3F6AE0] transition-all"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload New Stream</span>
          </button>
        </div>
      </div>

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Interactive Video Overlay Canvas & Scrubber */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-panel rounded-xl overflow-hidden border border-[#E9EDF2]">
            {/* Top Video Toolbar — sits above the frame, not over it, so it
                follows the page's light chrome rather than staying dark. */}
            <div className="px-4 py-3 bg-[#F8FAFC] border-b border-[#E9EDF2] flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs">
                <FileVideo className="w-4 h-4 text-[#2F52D6]" />
                <span className="text-[#18243A] font-semibold">
                  {selectedVideo?.filename ?? 'No video selected'}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[11px] text-[#6F7F98]">
                  STATUS:{' '}
                  <strong className="text-[#18243A]">
                    {selectedVideo?.status ?? 'UNKNOWN'}
                  </strong>
                </span>
                <StatusBadge level={selectedVideo?.status === 'COMPLETED' ? 'LOW' : 'CRITICAL'} />
              </div>
            </div>

            {/* Video Canvas & Dynamic Overlays */}
            <div className="relative aspect-video bg-[#05070A] overflow-hidden flex items-center justify-center">
              {videoSrc ? (
                <video
                  ref={videoRef}
                  src={videoSrc}
                  className="w-full h-full object-contain"
                  onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                  onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                />
              ) : (
                <div className="text-xs text-[#9DAFC5]">Select a video from the library to load</div>
              )}

              {/* Scanline Animation */}
              <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-blue-400/40 to-transparent animate-scanline pointer-events-none" />

              {/* Dynamic Bounding Boxes — drawn over the video frame itself,
                  so these stay bright/high-contrast against arbitrary
                  footage rather than following the page's light palette. */}
              {activeTracksAtCurrentTime.map((box, idx) => (
                <div
                  key={idx}
                  className={`absolute border-2 rounded p-1 transition-all pointer-events-none ${
                    box.className === 'carton'
                      ? 'border-red-500 bg-red-500/20 shadow-lg shadow-red-500/30 animate-pulse'
                      : 'border-blue-400 bg-blue-500/10'
                  }`}
                  style={{
                    left: `${box.left}%`,
                    top: `${box.top}%`,
                    width: `${Math.max(box.width, 5)}%`,
                    height: `${Math.max(box.height, 5)}%`,
                  }}
                >
                  <div className="text-[9px] font-bold text-gray-100 flex justify-between bg-black/70 px-1 rounded">
                    <span>{box.className.toUpperCase()} #{box.trackId}</span>
                    <span>{box.velocity.toFixed(1)} px/s</span>
                  </div>
                </div>
              ))}

              {/* HUD Telemetry Overlay — same reasoning: overlays the video,
                  stays dark regardless of page theme. */}
              <div className="absolute top-3 left-3 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10 text-[10px] space-y-0.5 pointer-events-none">
                <div className="text-blue-400 font-bold">DETECTION LAYER: ACTIVE</div>
                <div className="text-gray-300">ACTIVE TRACKS: {tracks.length}</div>
                <div className="text-amber-400">BEHAVIOUR EVENTS: {behaviours.length}</div>
              </div>
            </div>

            {/* Playback Controls & Scrubber — below the frame, so this
                follows the page's light chrome like the toolbar above it. */}
            <div className="p-4 bg-[#F8FAFC] space-y-3">
              <input
                type="range"
                aria-label="Seek video frame"
                min="0"
                max={duration || 100}
                step="0.05"
                value={currentTime}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setCurrentTime(val);
                  if (videoRef.current) videoRef.current.currentTime = val;
                }}
                className="w-full h-1.5 bg-[#E9EDF2] rounded-lg appearance-none cursor-pointer accent-[#5D87FF]"
              />

              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    aria-label={isPlaying ? 'Pause playback' : 'Play video'}
                    onClick={() => {
                      if (!videoRef.current) return;
                      if (isPlaying) videoRef.current.pause();
                      else videoRef.current.play();
                    }}
                    className="p-2 rounded-lg bg-[#5D87FF] text-white hover:bg-[#3F6AE0]"
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                  <button
                    type="button"
                    aria-label="Restart from beginning"
                    onClick={() => {
                      if (!videoRef.current) return;
                      videoRef.current.currentTime = 0;
                      setCurrentTime(0);
                    }}
                    className="p-2 rounded-lg bg-white border border-[#E9EDF2] text-[#6F7F98] hover:text-[#18243A]"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                  <span className="text-[#6F7F98]">
                    {currentTime.toFixed(2)}s / {(duration || selectedVideo?.duration_seconds || 0).toFixed(2)}s
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-[#6F7F98]">ACTIVE EVENTS:</span>
                  {behaviours.slice(0, 2).map((b, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded bg-[rgba(185,28,28,0.1)] text-[#b91c1c] border border-[rgba(185,28,28,0.3)] font-bold"
                    >
                      {b.behaviour_type}
                    </span>
                  ))}
                  {behaviours.length === 0 && (
                    <span className="text-[11px] text-[#15803d] font-bold">NORMAL ACTIVITY</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Video Library & Processing Progress */}
        <div className="space-y-4">
          <div className="glass-panel rounded-xl p-5 space-y-3">
            <h3 className="text-xs font-bold text-[#334155] uppercase tracking-wider">
              Warehouse CCTV Stream Library ({videos.length} Ingested)
            </h3>

            <div className="space-y-2 max-h-[480px] overflow-y-auto">
              {videos.map((vid) => (
                <div
                  key={vid.id}
                  onClick={() => setSelectedVideoId(vid.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedVideo?.id === vid.id
                      ? 'bg-[#5D87FF]/10 border-[#5D87FF] text-[#18243A]'
                      : 'bg-[#F8FAFC] border-[#E9EDF2] text-[#334155] hover:border-[#CBD5E1]'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="truncate max-w-[200px]">{vid.filename}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        vid.status === 'COMPLETED'
                          ? 'bg-[rgba(21,128,61,0.1)] text-[#15803d]'
                          : vid.status === 'PROCESSING'
                          ? 'bg-[#5D87FF]/20 text-[#2F52D6] animate-pulse'
                          : 'bg-[rgba(146,64,14,0.1)] text-[#92400e]'
                      }`}
                    >
                      {vid.status}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-[#6F7F98] mt-2">
                    <span>{vid.duration_seconds}s · {vid.fps} FPS</span>
                    <span>{(vid.file_size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Upload Video Stream Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 bg-[#18243A]/45 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="rounded-2xl bg-white border border-[#E9EDF2] shadow-[0_0_0_1px_rgba(4,23,43,0.05),0_20px_60px_rgba(0,0,0,0.12)] p-6 max-w-md w-full space-y-4">
            <div className="flex items-center justify-between border-b border-[#E9EDF2] pb-3">
              <div className="flex items-center gap-2">
                <UploadCloud className="w-5 h-5 text-[#2F52D6]" />
                <h2 className="text-base font-bold text-[#18243A]">Upload Warehouse Footage</h2>
              </div>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="text-[#6F7F98] hover:text-[#18243A]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleFileUpload} className="space-y-4">
              <div className="space-y-2">
                <label className="block text-xs text-[#334155]">Select Video File (MP4, AVI, MOV)</label>
                <input
                  type="file"
                  accept="video/*"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  required
                  className="w-full text-xs text-[#334155] file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-[#5D87FF] file:text-white hover:file:bg-[#3F6AE0]"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-[#F1F5F9] text-[#6F7F98] text-xs font-semibold hover:text-[#18243A]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#5D87FF] text-white text-xs font-semibold hover:bg-[#3F6AE0] disabled:opacity-50"
                >
                  {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
                  <span>{uploading ? 'Uploading & Analyzing...' : 'Upload & Start AI'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
