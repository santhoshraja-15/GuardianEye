import React, { useEffect, useState } from 'react';
import {
  Camera,
  Compass,
  Layers,
  MapPin,
  Maximize2,
  RefreshCw,
  Shield,
  Zap,
} from 'lucide-react';
import { GuardianAPI } from '../services/api';
import { DigitalTwinTopology } from '../types';

export const DigitalTwinPage: React.FC = () => {
  const [topology, setTopology] = useState<DigitalTwinTopology | null>(null);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  useEffect(() => {
    GuardianAPI.getDigitalTwinTopology().then(setTopology);
  }, []);

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Digital Twin & Spatial Warehouse Topology
          </h1>
          <p className="text-xs text-gray-400">
            Interactive 2D spatial grid layout, polygon risk zones, camera fields of view, and live entity centroids.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs text-gray-400">
          <span className="px-2.5 py-1 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400">
            DIMENSIONS: {topology?.dimensions_meters[0]}m x {topology?.dimensions_meters[1]}m
          </span>
          <span className="px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            {topology?.active_entity_count} LIVE TRACKS
          </span>
        </div>
      </div>

      {/* Main Floor Plan Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: 2D Interactive Warehouse Floor Map Canvas */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-bold text-white">Warehouse Floor 01 (Inbound &amp; High-Rack)</h3>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
              <span className="w-2.5 h-2.5 rounded-sm bg-red-500/40 border border-red-500 inline-block" />
              <span>Wet Floor (2.0x)</span>
              <span className="w-2.5 h-2.5 rounded-sm bg-amber-500/40 border border-amber-500 inline-block ml-2" />
              <span>Loading Dock (1.4x)</span>
              <span className="w-2.5 h-2.5 rounded-sm bg-blue-500/40 border border-blue-500 inline-block ml-2" />
              <span>Rack Aisle (1.6x)</span>
            </div>
          </div>

          {/* Simulated 2D Floor Plan Canvas */}
          <div className="relative aspect-[16/10] bg-[#05070A] rounded-xl border border-white/10 overflow-hidden p-6 flex items-center justify-center">
            {/* Grid Mesh */}
            <div
              className="absolute inset-0 opacity-15"
              style={{
                backgroundImage:
                  'linear-gradient(to right, #3B82F6 1px, transparent 1px), linear-gradient(to bottom, #3B82F6 1px, transparent 1px)',
                backgroundSize: '30px 30px',
              }}
            />

            {/* Zone 1: Inbound Dock 01 */}
            <div
              onClick={() => setSelectedZone('DOCK_BAY_01')}
              className={`absolute border-2 rounded-xl p-3 cursor-pointer transition-all ${
                selectedZone === 'DOCK_BAY_01'
                  ? 'border-amber-400 bg-amber-500/25 shadow-xl shadow-amber-500/20'
                  : 'border-amber-500/40 bg-amber-500/10 hover:border-amber-400'
              }`}
              style={{ left: '10%', top: '50%', width: '32%', height: '40%' }}
            >
              <div className="text-[10px] font-mono font-bold text-amber-300">DOCK_BAY_01</div>
              <div className="text-[9px] text-gray-400">Loading Bay (1.4x Risk)</div>
              {/* Centroid dots */}
              <div className="absolute left-1/3 top-1/2 w-3 h-3 rounded-full bg-blue-400 border border-white shadow-lg animate-pulse" />
              <div className="absolute left-2/3 top-2/3 w-3 h-3 rounded-full bg-red-500 border border-white shadow-lg" />
            </div>

            {/* Zone 2: Inbound Dock 02 (Wet Floor Area) */}
            <div
              onClick={() => setSelectedZone('DOCK_BAY_02_WET')}
              className={`absolute border-2 rounded-xl p-3 cursor-pointer transition-all ${
                selectedZone === 'DOCK_BAY_02_WET'
                  ? 'border-red-400 bg-red-500/25 shadow-xl shadow-red-500/20'
                  : 'border-red-500/40 bg-red-500/10 hover:border-red-400'
              }`}
              style={{ left: '46%', top: '50%', width: '32%', height: '40%' }}
            >
              <div className="text-[10px] font-mono font-bold text-red-300">DOCK_BAY_02_WET</div>
              <div className="text-[9px] text-gray-400">Wet Hazard Area (2.0x Risk)</div>
              <div className="absolute left-1/2 top-1/2 w-3 h-3 rounded-full bg-red-400 border border-white shadow-lg animate-bounce" />
            </div>

            {/* Zone 3: High Rack Storage Aisle A */}
            <div
              onClick={() => setSelectedZone('HIGH_RACK_01')}
              className={`absolute border-2 rounded-xl p-3 cursor-pointer transition-all ${
                selectedZone === 'HIGH_RACK_01'
                  ? 'border-blue-400 bg-blue-500/25 shadow-xl shadow-blue-500/20'
                  : 'border-blue-500/40 bg-blue-500/10 hover:border-blue-400'
              }`}
              style={{ left: '10%', top: '10%', width: '68%', height: '32%' }}
            >
              <div className="text-[10px] font-mono font-bold text-blue-300">HIGH_RACK_AISLE_01</div>
              <div className="text-[9px] text-gray-400">High-Elevation Racks (1.6x Risk)</div>
              <div className="absolute left-1/4 top-1/2 w-3 h-3 rounded-full bg-emerald-400 border border-white" />
              <div className="absolute left-3/4 top-1/3 w-3 h-3 rounded-full bg-blue-400 border border-white" />
            </div>

            {/* Camera Cones */}
            {(topology?.cameras ?? []).map((cam) => (
              <div
                key={cam.camera_id}
                className="absolute flex items-center gap-1 font-mono text-[9px] text-blue-300 bg-black/80 px-2 py-1 rounded-md border border-white/10"
                style={{ left: `${cam.position_xyz[0]}%`, top: `${cam.position_xyz[1]}%` }}
              >
                <Camera className="w-3 h-3 text-blue-400" />
                <span>{cam.camera_code}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right Col: Zone Inspector & Active Camera Specs */}
        <div className="space-y-4">
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400">
              Spatial Zones &amp; Risk Multipliers
            </h3>

            <div className="space-y-3">
              {(topology?.zones ?? []).map((z) => (
                <div
                  key={z.zone_id}
                  onClick={() => setSelectedZone(z.zone_code)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    selectedZone === z.zone_code
                      ? 'bg-blue-600/20 border-blue-500'
                      : 'bg-black/30 border-white/5 hover:border-white/15'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-xs font-mono">{z.zone_code}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                      {z.risk_multiplier}x Multiplier
                    </span>
                  </div>
                  <div className="text-xs text-gray-300 mt-1">{z.zone_name}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
