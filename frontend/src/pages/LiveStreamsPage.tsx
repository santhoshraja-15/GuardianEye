import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Camera,
  CheckCircle,
  Eye,
  Maximize2,
  Play,
  RefreshCw,
  Shield,
  Volume2,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';

interface CameraStream {
  id: string;
  name: string;
  zone: string;
  status: 'LIVE' | 'STANDBY';
  fps: number;
  resolution: string;
  activeTracks: number;
  riskStatus: 'NORMAL' | 'ELEVATED' | 'CRITICAL';
  sampleVideoName: string;
  detectedObjects: { id: number; class: string; state: string; speed: string; x: number; y: number }[];
}

const sampleStreams: CameraStream[] = [
  {
    id: 'CAM-01',
    name: 'Inbound Dock 01 (Cargo Unload)',
    zone: 'DOCK_BAY_01',
    status: 'LIVE',
    fps: 29.97,
    resolution: '1920x1080',
    activeTracks: 4,
    riskStatus: 'CRITICAL',
    sampleVideoName: 'Dock level, dragging cupboard.mp4',
    detectedObjects: [
      { id: 14, class: 'person', state: 'APPROACHING', speed: '4.2 px/s', x: 25, y: 35 },
      { id: 18, class: 'carton', state: 'FALLING', speed: '34.8 px/s', x: 38, y: 55 },
      { id: 22, class: 'pallet', state: 'STATIONARY', speed: '0.0 px/s', x: 50, y: 75 },
    ],
  },
  {
    id: 'CAM-02',
    name: 'Inbound Dock 02 (Wet Floor Area)',
    zone: 'DOCK_BAY_02_WET',
    status: 'LIVE',
    fps: 30.0,
    resolution: '1920x1080',
    activeTracks: 3,
    riskStatus: 'ELEVATED',
    sampleVideoName: 'Rolling and dragging on wet floor.mp4',
    detectedObjects: [
      { id: 29, class: 'carton', state: 'DRAGGING', speed: '18.4 px/s', x: 45, y: 60 },
      { id: 31, class: 'person', state: 'HOLDING', speed: '18.1 px/s', x: 52, y: 40 },
    ],
  },
  {
    id: 'CAM-03',
    name: 'High-Rack Storage Aisle A',
    zone: 'HIGH_RACK_01',
    status: 'LIVE',
    fps: 25.0,
    resolution: '1920x1080',
    activeTracks: 2,
    riskStatus: 'NORMAL',
    sampleVideoName: 'Stepping on cartons.mp4',
    detectedObjects: [
      { id: 45, class: 'forklift', state: 'MOVING', speed: '12.0 px/s', x: 60, y: 50 },
    ],
  },
  {
    id: 'CAM-04',
    name: 'Outbound Sorting & Staging Buffer',
    zone: 'BUFFER_STAGE',
    status: 'LIVE',
    fps: 30.0,
    resolution: '1280x720',
    activeTracks: 5,
    riskStatus: 'NORMAL',
    sampleVideoName: 'Throwing seating cartons.mp4',
    detectedObjects: [
      { id: 52, class: 'person', state: 'IDLE', speed: '0.5 px/s', x: 30, y: 40 },
      { id: 53, class: 'carton', state: 'STATIONARY', speed: '0.0 px/s', x: 70, y: 70 },
    ],
  },
];

export const LiveStreamsPage: React.FC = () => {
  const [selectedCam, setSelectedCam] = useState<CameraStream>(sampleStreams[0]);

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Multi-Camera Live Intelligence Matrix
          </h1>
          <p className="text-xs text-gray-400">
            Real-time inference decoding with ByteTrack bounding box telemetry and privacy blur.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-mono font-bold">
            <span className="w-2 h-2 rounded-full bg-red-500 pulse-live" />
            4 STREAMS ACTIVE (GPU 0)
          </div>
        </div>
      </div>

      {/* 2x2 Camera Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sampleStreams.map((cam) => (
          <div
            key={cam.id}
            onClick={() => setSelectedCam(cam)}
            className={`glass-panel rounded-xl overflow-hidden cursor-pointer border transition-all ${
              selectedCam.id === cam.id
                ? 'border-blue-500 shadow-xl shadow-blue-500/10'
                : 'border-white/10 hover:border-white/20'
            }`}
          >
            {/* Camera Header Bar */}
            <div className="px-4 py-2.5 bg-black/60 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Camera className="w-4 h-4 text-blue-400" />
                <span className="text-xs font-bold text-white font-mono">{cam.id}:</span>
                <span className="text-xs text-gray-300 truncate max-w-[200px]">{cam.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  {cam.zone}
                </span>
                <StatusBadge level={cam.riskStatus} />
              </div>
            </div>

            {/* Simulated Live Video Canvas with Bounding Boxes */}
            <div className="relative aspect-video bg-[#05070A] overflow-hidden flex items-center justify-center group">
              {/* Grid Background Pattern */}
              <div
                className="absolute inset-0 opacity-10"
                style={{
                  backgroundImage:
                    'linear-gradient(to right, #3B82F6 1px, transparent 1px), linear-gradient(to bottom, #3B82F6 1px, transparent 1px)',
                  backgroundSize: '40px 40px',
                }}
              />

              {/* Dynamic Scanning Scanline */}
              <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-blue-400/40 to-transparent animate-scanline" />

              {/* Simulated Detected Bounding Box Overlays */}
              {cam.detectedObjects.map((obj) => (
                <div
                  key={obj.id}
                  className={`absolute p-1 border rounded transition-all ${
                    obj.state === 'FALLING' || obj.state === 'DRAGGING'
                      ? 'border-red-500 bg-red-500/10 text-red-300 shadow-lg shadow-red-500/20 animate-pulse'
                      : 'border-blue-400 bg-blue-500/10 text-blue-200'
                  }`}
                  style={{
                    left: `${obj.x}%`,
                    top: `${obj.y}%`,
                    width: '90px',
                    height: '80px',
                  }}
                >
                  <div className="text-[9px] font-mono font-bold leading-none uppercase flex items-center justify-between">
                    <span>{obj.class} #{obj.id}</span>
                    <span>{obj.speed}</span>
                  </div>
                  <div className="text-[8px] font-mono mt-0.5 text-gray-300 bg-black/60 px-1 py-0.5 rounded inline-block">
                    STATE: {obj.state}
                  </div>
                </div>
              ))}

              {/* Live HUD Bottom Overlay */}
              <div className="absolute bottom-2 left-3 right-3 flex items-center justify-between text-[10px] font-mono text-gray-400 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10">
                <div className="flex items-center gap-3">
                  <span className="text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-live" />
                    LIVE
                  </span>
                  <span>{cam.fps} FPS</span>
                  <span>{cam.resolution}</span>
                </div>
                <div>{cam.activeTracks} ENTITIES TRACKED</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
