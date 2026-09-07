import React, { useEffect, useMemo, useState } from 'react';
import { Activity, Camera, Compass, Flame, MapPinned, ShieldAlert, Zap } from 'lucide-react';
import { getDigitalTwinTopology } from '../api/digital-twin';
import { useDashboardSummary } from '../hooks/useDashboardSummary';
import { useIncidents } from '../hooks/useIncidents';
import { DigitalTwinTopology } from '../types';

const zoneColour = (riskMultiplier: number): string => {
  if (riskMultiplier >= 1.8) return 'rgba(239, 68, 68, 0.35)';
  if (riskMultiplier >= 1.4) return 'rgba(245, 158, 11, 0.35)';
  if (riskMultiplier >= 1.1) return 'rgba(59, 130, 246, 0.35)';
  return 'rgba(16, 185, 129, 0.25)';
};

const riskTitle = (riskMultiplier: number): string => {
  if (riskMultiplier >= 1.8) return 'Critical';
  if (riskMultiplier >= 1.4) return 'Elevated';
  if (riskMultiplier >= 1.1) return 'Moderate';
  return 'Low';
};

export const DigitalTwinPage: React.FC = () => {
  const [topology, setTopology] = useState<DigitalTwinTopology | null>(null);
  // Shared cache — same summary/incident data Dashboard and Analytics use.
  const { data: summary = null } = useDashboardSummary();
  const { data: incidents = [] } = useIncidents();
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  useEffect(() => {
    getDigitalTwinTopology()
      .then((topologyData) => {
        setTopology(topologyData);
        if (topologyData.zones.length > 0) {
          setSelectedZone(topologyData.zones[0].zone_code);
        }
      })
      .catch(() => {
        setTopology(null);
      });
  }, []);

  const selectedZoneData = useMemo(() => {
    if (!topology) return null;
    return (
      topology.zones.find((zone) => zone.zone_code === selectedZone || zone.zone_id === selectedZone) ??
      topology.zones[0] ??
      null
    );
  }, [selectedZone, topology]);

  const matchingIncidents = useMemo(() => {
    if (!selectedZoneData) return [];
    return incidents.filter(
      (incident) =>
        incident.zone_id === selectedZoneData.zone_id || incident.zone_id === selectedZoneData.zone_code,
    );
  }, [incidents, selectedZoneData]);

  const selectedZoneHeatmap = useMemo(() => {
    if (!summary || !selectedZoneData) return [];
    return summary.risk_heatmaps.filter((point) => point.zone_code === selectedZoneData.zone_code);
  }, [selectedZoneData, summary]);

  const selectedZoneCameras = useMemo(() => {
    if (!topology || !selectedZoneData) return [];
    return topology.cameras.filter(
      (camera) =>
        camera.coverage_zones.includes(selectedZoneData.zone_code) ||
        camera.coverage_zones.includes(selectedZoneData.zone_id),
    );
  }, [selectedZoneData, topology]);

  const widthMeters = topology?.dimensions_meters[0] ?? 100;
  const heightMeters = topology?.dimensions_meters[1] ?? 100;

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Digital Twin & Spatial Warehouse Topology</h1>
          <p className="text-xs text-gray-400">
            Operational 2D warehouse map driven by the real backend topology and heatmap data.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs text-gray-400">
          <span className="px-2.5 py-1 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400">
            {topology?.warehouse_name ?? 'Warehouse'} · {topology?.dimensions_meters[0] ?? 0}m x {topology?.dimensions_meters[1] ?? 0}m
          </span>
          <span className="px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            {topology?.active_entity_count ?? 0} live entities
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-bold text-white">Warehouse map</h3>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
              <span className="w-2.5 h-2.5 rounded-sm bg-red-500/40 border border-red-500 inline-block" />
              <span>High risk</span>
              <span className="w-2.5 h-2.5 rounded-sm bg-amber-500/40 border border-amber-500 inline-block ml-2" />
              <span>Elevated</span>
              <span className="w-2.5 h-2.5 rounded-sm bg-blue-500/40 border border-blue-500 inline-block ml-2" />
              <span>Moderate</span>
            </div>
          </div>

          <div className="relative aspect-[16/10] bg-[#05070A] rounded-xl border border-white/10 overflow-hidden">
            <svg viewBox="0 0 100 100" className="h-full w-full">
              <rect x="0" y="0" width="100" height="100" fill="#05070A" />
              <g opacity={0.2} stroke="#3b82f6" strokeWidth={0.2}>
                {Array.from({ length: 12 }).map((_, index) => (
                  <line key={`v-${index}`} x1={index * 10} y1={0} x2={index * 10} y2={100} />
                ))}
                {Array.from({ length: 12 }).map((_, index) => (
                  <line key={`h-${index}`} x1={0} y1={index * 10} x2={100} y2={index * 10} />
                ))}
              </g>

              {topology?.zones.map((zone) => {
                const points = zone.polygon_points
                  .map(([x, y]) => {
                    const xPercent = (x / widthMeters) * 100;
                    const yPercent = (y / heightMeters) * 100;
                    return `${xPercent},${yPercent}`;
                  })
                  .join(' ');

                const isSelected = selectedZoneData?.zone_id === zone.zone_id;

                return (
                  <polygon
                    key={zone.zone_id}
                    points={points}
                    fill={zoneColour(zone.risk_multiplier)}
                    stroke={isSelected ? '#e2e8f0' : '#94a3b8'}
                    strokeWidth={isSelected ? 0.8 : 0.45}
                    onClick={() => setSelectedZone(zone.zone_code)}
                    style={{ cursor: 'pointer' }}
                  />
                );
              })}

              {summary?.risk_heatmaps.map((point, index) => (
                <circle
                  key={`${point.zone_code}-${index}`}
                  cx={point.x_normalized * 100}
                  cy={point.y_normalized * 100}
                  r={Math.max(2, point.intensity * 12)}
                  fill={point.intensity > 0.75 ? 'rgba(239,68,68,0.8)' : 'rgba(59,130,246,0.7)'}
                  opacity={0.75}
                />
              ))}

              {topology?.cameras.map((camera) => {
                const x = (camera.position_xyz[0] / widthMeters) * 100;
                const y = (camera.position_xyz[1] / heightMeters) * 100;
                return (
                  <g key={camera.camera_id} transform={`translate(${x} ${y})`}>
                    <circle r={2.4} fill="#38bdf8" stroke="#e0f2fe" strokeWidth={0.4} />
                    <text x={2.5} y={-1.5} fill="#dbeafe" fontSize={3}>
                      {camera.camera_code}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        <div className="space-y-4">
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.18em] text-gray-400">
              <MapPinned className="w-3.5 h-3.5 text-blue-400" />
              Zones
            </div>

            <div className="space-y-3">
              {topology?.zones.map((zone) => (
                <button
                  key={zone.zone_id}
                  type="button"
                  onClick={() => setSelectedZone(zone.zone_code)}
                  className={`w-full rounded-lg border p-3 text-left transition ${
                    selectedZoneData?.zone_id === zone.zone_id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-white/10 bg-black/20 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-white font-mono">{zone.zone_code}</span>
                    <span className="rounded border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-mono text-gray-300">
                      {riskTitle(zone.risk_multiplier)}
                    </span>
                  </div>
                  <div className="mt-1 text-[11px] text-gray-300">{zone.zone_name}</div>
                  <div className="mt-2 text-[10px] font-mono text-gray-400">Risk multiplier: {zone.risk_multiplier.toFixed(1)}x</div>
                </button>
              ))}
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.18em] text-gray-400">
              <Flame className="w-3.5 h-3.5 text-amber-400" />
              Risk heatmap
            </div>

            {(summary?.risk_heatmaps ?? []).length === 0 ? (
              <div className="text-xs text-gray-400">
                No heatmap data is currently available from the backend.
              </div>
            ) : (
              <div className="space-y-2">
                {summary?.risk_heatmaps.map((point, index) => (
                  <div key={`${point.zone_code}-${index}`} className="rounded border border-white/10 bg-black/20 p-2">
                    <div className="flex items-center justify-between text-[10px] font-mono text-gray-300">
                      <span>{point.zone_code}</span>
                      <span>{point.intensity.toFixed(2)} intensity</span>
                    </div>
                    <div className="mt-1 text-[10px] text-gray-400">
                      incident density: {point.incident_count} · x/y: {point.x_normalized.toFixed(2)} / {point.y_normalized.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.18em] text-gray-400">
            <MapPinned className="w-3.5 h-3.5 text-blue-400" />
            Zone
          </div>
          <div className="mt-3 text-lg font-bold text-white">{selectedZoneData?.zone_name ?? 'No zone selected'}</div>
          <div className="text-xs text-gray-400 font-mono">{selectedZoneData?.zone_code ?? '—'}</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.18em] text-gray-400">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            Risk
          </div>
          <div className="mt-3 text-lg font-bold text-white">{riskTitle(selectedZoneData?.risk_multiplier ?? 0)}</div>
          <div className="text-xs text-gray-400 font-mono">
            multiplier {selectedZoneData?.risk_multiplier.toFixed(1) ?? '0.0'}x · {selectedZoneHeatmap.length} risk points
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.18em] text-gray-400">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            Incidents
          </div>
          <div className="mt-3 text-lg font-bold text-white">{matchingIncidents.length}</div>
          <div className="text-xs text-gray-400 font-mono">
            {matchingIncidents.length === 0 ? 'No incidents currently mapped to this zone.' : 'Incidents linked to the selected zone.'}
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.18em] text-gray-400">
            <Zap className="w-3.5 h-3.5 text-violet-400" />
            Behaviour
          </div>
          <div className="mt-3 space-y-2">
            {(summary?.behaviour_distribution ?? []).slice(0, 3).map((behaviour) => (
              <div key={behaviour.behaviour_code} className="flex items-center justify-between text-[11px] text-gray-300">
                <span className="font-mono">{behaviour.behaviour_code}</span>
                <span>{behaviour.count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.18em] text-gray-400">
            <Camera className="w-3.5 h-3.5 text-blue-400" />
            Cameras
          </div>
          <div className="mt-3 space-y-2">
            {selectedZoneCameras.length === 0 ? (
              <div className="text-xs text-gray-400">No camera coverage is exposed for this zone.</div>
            ) : (
              selectedZoneCameras.map((camera) => (
                <div key={camera.camera_id} className="flex items-center justify-between text-[11px] text-gray-300">
                  <span className="font-mono">{camera.camera_code}</span>
                  <span>{camera.camera_name}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.18em] text-gray-400">
            <Camera className="w-3.5 h-3.5 text-cyan-400" />
            Evidence
          </div>
          <div className="mt-3 space-y-2">
            {matchingIncidents.length === 0 ? (
              <div className="text-xs text-gray-400">No evidence references are exposed for this zone.</div>
            ) : (
              matchingIncidents.slice(0, 3).map((incident) => (
                <div key={incident.id} className="text-[11px] text-gray-300 font-mono">
                  {incident.incident_code} · {incident.status}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
