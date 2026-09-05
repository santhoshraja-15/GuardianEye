import React, { useState } from 'react';
import {
  Activity,
  CheckCircle,
  Clock,
  Cpu,
  FileVideo,
  Layers,
  Pause,
  Play,
  RotateCcw,
  Sliders,
  UploadCloud,
  Zap,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';

const catalogVideos = [
  {
    id: 'vid-01',
    name: 'Dock level, dragging cupboard.mp4',
    size: '14.2 MB',
    duration: '18.4s',
    fps: 30,
    anomaly: 'B02_DRAG & B01_DROP',
    severity: 'CRITICAL',
    riskScore: 94.2,
  },
  {
    id: 'vid-02',
    name: 'Rolling and dragging on wet floor.mp4',
    size: '11.8 MB',
    duration: '15.0s',
    fps: 30,
    anomaly: 'B15_WET_FLOOR_DRAGGING',
    severity: 'HIGH',
    riskScore: 88.0,
  },
  {
    id: 'vid-03',
    name: 'Throwing Mattresses.mp4',
    size: '9.4 MB',
    duration: '12.6s',
    fps: 25,
    anomaly: 'B03_THROW',
    severity: 'CRITICAL',
    riskScore: 91.5,
  },
  {
    id: 'vid-04',
    name: 'Stepping on cartons to reach items.mp4',
    size: '16.1 MB',
    duration: '22.0s',
    fps: 30,
    anomaly: 'B11_STEPPING_ON_CARTON',
    severity: 'CRITICAL',
    riskScore: 96.0,
  },
  {
    id: 'vid-05',
    name: 'Rolling and dropping carton.mp4',
    size: '13.0 MB',
    duration: '16.5s',
    fps: 30,
    anomaly: 'B13_ROLLING & B01_DROP',
    severity: 'HIGH',
    riskScore: 85.0,
  },
];

export const VideoAnalysisPage: React.FC = () => {
  const [selectedVid, setSelectedVid] = useState(catalogVideos[0]);
  const [isPlaying, setIsPlaying] = useState(true);
  const [currentFrame, setCurrentFrame] = useState(45);
  const [totalFrames] = useState(552);

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Video Intelligence & Anomaly Forensic Replay
          </h1>
          <p className="text-xs text-gray-400">
            Frame-by-frame entity perception, Kalman speed vectors, and state machine transition histories.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600/30 text-blue-400 border border-blue-500/40 text-xs font-semibold hover:bg-blue-600/50 transition-all glow-accent">
            <UploadCloud className="w-4 h-4" />
            <span>Upload New Stream</span>
          </button>
        </div>
      </div>

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Interactive Video Overlay Canvas & Scrubber */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-panel rounded-xl overflow-hidden border border-white/10">
            {/* Top Video Toolbar */}
            <div className="px-4 py-3 bg-black/60 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-mono">
                <FileVideo className="w-4 h-4 text-blue-400" />
                <span className="text-white font-semibold">{selectedVid.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[11px] font-mono text-gray-400">
                  FRAME: <strong className="text-white">{currentFrame}</strong> / {totalFrames}
                </span>
                <StatusBadge level={selectedVid.severity} />
              </div>
            </div>

            {/* Video Canvas Simulation */}
            <div className="relative aspect-video bg-[#05070A] overflow-hidden flex items-center justify-center">
              {/* Scanline Animation */}
              <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-blue-400/40 to-transparent animate-scanline" />

              {/* Bounding Box 1: Person (Operator) */}
              <div
                className="absolute border border-blue-400 bg-blue-500/10 rounded p-1.5 transition-all"
                style={{ left: '30%', top: '25%', width: '110px', height: '180px' }}
              >
                <div className="text-[10px] font-mono font-bold text-blue-300 flex justify-between">
                  <span>PERSON #1</span>
                  <span>0.95 CONF</span>
                </div>
                <div className="text-[9px] font-mono text-gray-300 mt-1 bg-black/60 px-1 py-0.5 rounded">
                  STATE: RELEASED
                </div>
              </div>

              {/* Bounding Box 2: Anomaly Product (Dropping / Falling) */}
              <div
                className="absolute border-2 border-red-500 bg-red-500/20 rounded p-1.5 shadow-2xl shadow-red-500/50 animate-pulse transition-all"
                style={{ left: '42%', top: '55%', width: '120px', height: '90px' }}
              >
                <div className="text-[10px] font-mono font-bold text-red-300 flex justify-between">
                  <span>CARTON #14</span>
                  <span>34.8 px/s</span>
                </div>
                <div className="text-[9px] font-mono font-bold text-white bg-red-600/80 px-1 py-0.5 rounded mt-1">
                  IMPACT / FALLING
                </div>
              </div>

              {/* HUD Telemetry Overlay */}
              <div className="absolute top-3 left-3 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10 text-[10px] font-mono space-y-0.5">
                <div className="text-blue-400 font-bold">DETECTION LAYER: ACTIVE</div>
                <div className="text-gray-300">VELOCITY: [0.0, 34.8] px/s</div>
                <div className="text-amber-400">ZONE: DOCK_BAY_01 (1.4x MULT)</div>
              </div>
            </div>

            {/* Playback Controls & Scrubber */}
            <div className="p-4 bg-[#0B0F17] space-y-3">
              <input
                type="range"
                min="0"
                max={totalFrames}
                value={currentFrame}
                onChange={(e) => setCurrentFrame(Number(e.target.value))}
                className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />

              <div className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="p-2 rounded-lg bg-blue-600/30 text-blue-400 border border-blue-500/40 hover:bg-blue-600/50"
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={() => setCurrentFrame(0)}
                    className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                  <span className="text-gray-400">
                    {(currentFrame * 0.033).toFixed(2)}s / {(totalFrames * 0.033).toFixed(2)}s
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-gray-400">TEMPORAL STATE:</span>
                  <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/40 font-bold">
                    HOLDING -&gt; FALLING -&gt; IMPACT
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Video Catalog Browser & Forensic Telemetry */}
        <div className="space-y-4">
          <div className="glass-panel rounded-xl p-5 space-y-3">
            <h3 className="text-xs font-bold font-mono text-gray-300 uppercase tracking-wider">
              Cataloged CCTV Test Library (7 Sample Videos)
            </h3>

            <div className="space-y-2 max-h-[480px] overflow-y-auto">
              {catalogVideos.map((vid) => (
                <div
                  key={vid.id}
                  onClick={() => setSelectedVid(vid)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedVid.id === vid.id
                      ? 'bg-blue-600/20 border-blue-500 text-white'
                      : 'bg-black/30 border-white/5 text-gray-300 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="truncate max-w-[200px]">{vid.name}</span>
                    <StatusBadge level={vid.severity} />
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-gray-400 mt-2">
                    <span>{vid.anomaly}</span>
                    <span className="text-amber-400 font-bold">RISK: {vid.riskScore}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
