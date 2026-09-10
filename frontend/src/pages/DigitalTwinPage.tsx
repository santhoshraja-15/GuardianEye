import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  Camera as CameraIcon,
  Compass,
  Flame,
  Layers,
  MapPinned,
  Package,
  ShieldAlert,
  Truck,
  User,
  Wrench,
  Zap,
} from 'lucide-react';
import { useDigitalTwinTopology } from '../hooks/useDigitalTwinTopology';
import { useDashboardSummary } from '../hooks/useDashboardSummary';
import { useIncidents } from '../hooks/useIncidents';
import { useAppStore } from '../stores/app-store';
import { EntityTopology } from '../types';

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

// Ground-contact entity icon per tracked class — kept to the handful of
// classes the detector actually emits (ai/perception/yolo_detector.py),
// not a generic fallback set dressed up as full class coverage.
const ENTITY_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  person: User,
  forklift: Truck,
  trolley: Truck,
  equipment: Wrench,
  carton: Package,
  pallet: Package,
  stack: Package,
};

const ENTITY_COLOUR: Record<string, string> = {
  person: '#2F52D6',
  forklift: '#9a3412',
  trolley: '#9a3412',
  equipment: '#9a3412',
  carton: '#15803d',
  pallet: '#15803d',
  stack: '#15803d',
};

type Layer = 'zones' | 'cameras' | 'entities' | 'heatmap';

export const DigitalTwinPage: React.FC = () => {
  const navigate = useNavigate();
  const setPendingFocusVideoId = useAppStore((state) => state.setPendingFocusVideoId);
  const { data: topology, isLoading, isError } = useDigitalTwinTopology();
  // Shared cache — same summary/incident data Dashboard and Analytics use.
  const { data: summary = null } = useDashboardSummary();
  const { data: incidents = [] } = useIncidents();
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<EntityTopology | null>(null);
  const [layers, setLayers] = useState<Record<Layer, boolean>>({
    zones: true,
    cameras: true,
    entities: true,
    heatmap: true,
  });

  const toggleLayer = (layer: Layer) => setLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));

  const effectiveSelectedZone = selectedZone ?? topology?.zones[0]?.zone_code ?? null;

  const selectedZoneData = useMemo(() => {
    if (!topology) return null;
    return (
      topology.zones.find(
        (zone) => zone.zone_code === effectiveSelectedZone || zone.zone_id === effectiveSelectedZone,
      ) ?? topology.zones[0] ?? null
    );
  }, [effectiveSelectedZone, topology]);

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

  const openSourceVideo = (videoId: string) => {
    setPendingFocusVideoId(videoId);
    navigate('/live');
  };

  if (isError) {
    return (
      <div className="space-y-6 pb-12">
        <div className="glass-panel rounded-xl p-8 text-center">
          <MapPinned className="mx-auto h-8 w-8 text-[#9DAFC5]" />
          <h2 className="mt-3 text-sm font-bold text-[#18243A]">No warehouse configured</h2>
          <p className="mt-1 text-xs text-[#6F7F98]">
            The Digital Twin has nothing to render until at least one warehouse exists in the backend.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#18243A] tracking-tight">Digital Twin & Spatial Warehouse Topology</h1>
          <p className="text-xs text-[#6F7F98]">
            Continuous warehouse map — every camera and every processed video's most recent tracked
            entities, not one incident's snapshot.
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs text-[#6F7F98]">
          <span className="px-2.5 py-1 rounded bg-[#5D87FF]/10 border border-[#5D87FF]/20 text-[#2F52D6]">
            {isLoading ? 'Loading…' : `${topology?.warehouse_name ?? 'Warehouse'} · ${topology?.dimensions_meters[0] ?? 0}m x ${topology?.dimensions_meters[1] ?? 0}m`}
          </span>
          <span className="px-2.5 py-1 rounded bg-[rgba(21,128,61,0.1)] border border-[rgba(21,128,61,0.2)] text-[#15803d]">
            {topology?.active_entity_count ?? 0} tracked entities
          </span>
        </div>
      </div>

      {topology && !topology.is_live_entity_count && (
        <div className="rounded-lg border border-[rgba(146,64,14,0.25)] bg-[rgba(146,64,14,0.06)] px-3 py-2 text-[11px] text-[#92400e]">
          Entity positions are each camera's most recently processed video, not a live camera feed — GuardianEye
          processes uploaded footage, it does not ingest RTSP streams yet.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel rounded-xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E9EDF2] pb-3">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-[#2F52D6]" />
              <h3 className="text-sm font-bold text-[#18243A]">Warehouse map</h3>
            </div>
            <div className="flex items-center gap-3 text-[10px] uppercase tracking-[0.12em] text-[#6F7F98]">
              <Layers className="w-3.5 h-3.5 text-[#9DAFC5]" />
              {(['zones', 'cameras', 'entities', 'heatmap'] as Layer[]).map((layer) => (
                <button
                  key={layer}
                  type="button"
                  onClick={() => toggleLayer(layer)}
                  className={`rounded-full border px-2.5 py-1 transition ${
                    layers[layer]
                      ? 'border-[#5D87FF] bg-[#5D87FF]/10 text-[#2F52D6]'
                      : 'border-[#E9EDF2] bg-[#F8FAFC] text-[#9DAFC5]'
                  }`}
                >
                  {layer}
                </button>
              ))}
            </div>
          </div>

          <div className="relative aspect-[16/10] bg-[#05070A] rounded-xl border border-[#E9EDF2] overflow-hidden">
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

              {layers.zones &&
                topology?.zones.map((zone) => {
                  const points = zone.normalized_polygon_points
                    .map(([x, y]) => `${x * 100},${y * 100}`)
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

              {layers.heatmap &&
                summary?.risk_heatmaps.map((point, index) => (
                  <circle
                    key={`${point.zone_code}-${index}`}
                    cx={point.x_normalized * 100}
                    cy={point.y_normalized * 100}
                    r={Math.max(2, point.intensity * 12)}
                    fill={point.intensity > 0.75 ? 'rgba(239,68,68,0.8)' : 'rgba(59,130,246,0.7)'}
                    opacity={0.55}
                  />
                ))}

              {layers.cameras &&
                topology?.cameras.map((camera) => {
                  const x = camera.normalized_position[0] * 100;
                  const y = camera.normalized_position[1] * 100;
                  if (!camera.is_positioned) return null;
                  const hasOrientation = camera.orientation_degrees !== null;
                  return (
                    <g key={camera.camera_id} transform={`translate(${x} ${y})`}>
                      {hasOrientation && (
                        <path
                          d={coverageConePath(camera.orientation_degrees ?? 0, camera.fov_degrees, 14)}
                          fill="rgba(56,189,248,0.12)"
                          stroke="rgba(56,189,248,0.35)"
                          strokeWidth={0.2}
                        />
                      )}
                      <circle
                        r={2.2}
                        fill={camera.is_calibrated ? '#22c55e' : '#38bdf8'}
                        stroke="#e0f2fe"
                        strokeWidth={0.4}
                      />
                      <text x={2.6} y={-1.5} fill="#dbeafe" fontSize={3}>
                        {camera.camera_code}
                      </text>
                    </g>
                  );
                })}

              {layers.entities &&
                topology?.entities.map((entity) => {
                  const x = entity.normalized_position[0] * 100;
                  const y = entity.normalized_position[1] * 100;
                  const colour = ENTITY_COLOUR[entity.class_name] ?? '#9DAFC5';
                  const isSelected = selectedEntity?.track_id === entity.track_id && selectedEntity.video_id === entity.video_id;
                  return (
                    <g
                      key={`${entity.video_id}-${entity.track_id}`}
                      transform={`translate(${x} ${y})`}
                      onClick={() => setSelectedEntity(entity)}
                      style={{ cursor: 'pointer' }}
                    >
                      <circle r={isSelected ? 1.9 : 1.3} fill={colour} opacity={isSelected ? 1 : 0.85} />
                      {isSelected && <circle r={2.8} fill="none" stroke={colour} strokeWidth={0.3} opacity={0.6} />}
                    </g>
                  );
                })}
            </svg>
          </div>
        </div>

        <div className="space-y-4">
          {selectedEntity ? (
            <div className="glass-panel rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
                <span className="flex items-center gap-2">
                  {React.createElement(ENTITY_ICON[selectedEntity.class_name] ?? User, {
                    className: 'w-3.5 h-3.5 text-[#2F52D6]',
                  })}
                  Track #{selectedEntity.track_id}
                </span>
                <button type="button" onClick={() => setSelectedEntity(null)} className="text-[#9DAFC5] hover:text-[#18243A]">
                  ✕
                </button>
              </div>
              <div className="text-lg font-bold text-[#18243A] capitalize">{selectedEntity.class_name}</div>
              <div className="grid grid-cols-2 gap-2 text-[11px] text-[#334155]">
                <div className="rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1.5">
                  <div className="text-[#9DAFC5]">Confidence</div>
                  <div className="font-semibold text-[#18243A]">{(selectedEntity.confidence * 100).toFixed(1)}%</div>
                </div>
                <div className="rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1.5">
                  <div className="text-[#9DAFC5]">Last seen (video time)</div>
                  <div className="font-semibold text-[#18243A]">{selectedEntity.last_seen_timestamp_seconds.toFixed(1)}s</div>
                </div>
                <div className="rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1.5">
                  <div className="text-[#9DAFC5]">World position</div>
                  <div className="font-semibold text-[#18243A]">
                    {selectedEntity.world_position
                      ? `${selectedEntity.world_position[0].toFixed(1)}, ${selectedEntity.world_position[1].toFixed(1)}`
                      : '—'}
                  </div>
                  <div className="text-[9px] text-[#9DAFC5]">{selectedEntity.world_position_quality ?? 'n/a'}</div>
                </div>
                <div className="rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-1.5">
                  <div className="text-[#9DAFC5]">Zone</div>
                  <div className="font-semibold text-[#18243A]">{selectedEntity.zone_id ?? 'unzoned'}</div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => openSourceVideo(selectedEntity.video_id)}
                className="w-full rounded-lg border border-[#5D87FF] bg-[#5D87FF]/10 px-3 py-2 text-[11px] font-semibold text-[#2F52D6] hover:bg-[#5D87FF]/20 transition"
              >
                Open source video in Live Streams
              </button>
            </div>
          ) : (
            <div className="glass-panel rounded-xl p-5 text-xs text-[#6F7F98]">
              Select a tracked entity on the map to inspect it.
            </div>
          )}

          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
              <MapPinned className="w-3.5 h-3.5 text-[#2F52D6]" />
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
                      ? 'border-[#5D87FF] bg-[#5D87FF]/10'
                      : 'border-[#E9EDF2] bg-[#F8FAFC] hover:border-[#CBD5E1]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#18243A]">{zone.zone_code}</span>
                    <span className="rounded border border-[#E9EDF2] bg-[#F1F5F9] px-2 py-0.5 text-[10px] text-[#334155]">
                      {riskTitle(zone.risk_multiplier)}
                    </span>
                  </div>
                  <div className="mt-1 text-[11px] text-[#334155]">{zone.zone_name}</div>
                  <div className="mt-2 text-[10px] text-[#6F7F98]">Risk multiplier: {zone.risk_multiplier.toFixed(1)}x</div>
                </button>
              ))}
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
              <Flame className="w-3.5 h-3.5 text-[#92400e]" />
              Risk heatmap
            </div>

            {(summary?.risk_heatmaps ?? []).length === 0 ? (
              <div className="text-xs text-[#6F7F98]">
                No heatmap data is currently available from the backend.
              </div>
            ) : (
              <div className="space-y-2">
                {summary?.risk_heatmaps.map((point, index) => (
                  <div key={`${point.zone_code}-${index}`} className="rounded border border-[#E9EDF2] bg-[#F8FAFC] p-2">
                    <div className="flex items-center justify-between text-[10px] text-[#334155]">
                      <span>{point.zone_code}</span>
                      <span>{point.intensity.toFixed(2)} intensity</span>
                    </div>
                    <div className="mt-1 text-[10px] text-[#6F7F98]">
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
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
            <MapPinned className="w-3.5 h-3.5 text-[#2F52D6]" />
            Zone
          </div>
          <div className="mt-3 text-lg font-bold text-[#18243A]">{selectedZoneData?.zone_name ?? 'No zone selected'}</div>
          <div className="text-xs text-[#6F7F98]">{selectedZoneData?.zone_code ?? '—'}</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
            <ShieldAlert className="w-3.5 h-3.5 text-[#92400e]" />
            Risk
          </div>
          <div className="mt-3 text-lg font-bold text-[#18243A]">{riskTitle(selectedZoneData?.risk_multiplier ?? 0)}</div>
          <div className="text-xs text-[#6F7F98]">
            multiplier {selectedZoneData?.risk_multiplier.toFixed(1) ?? '0.0'}x · {selectedZoneHeatmap.length} risk points
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
            <Activity className="w-3.5 h-3.5 text-[#15803d]" />
            Incidents
          </div>
          <div className="mt-3 text-lg font-bold text-[#18243A]">{matchingIncidents.length}</div>
          <div className="text-xs text-[#6F7F98]">
            {matchingIncidents.length === 0 ? 'No incidents currently mapped to this zone.' : 'Incidents linked to the selected zone.'}
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
            <Zap className="w-3.5 h-3.5 text-[#2F52D6]" />
            Behaviour
          </div>
          <div className="mt-3 space-y-2">
            {(summary?.behaviour_distribution ?? []).slice(0, 3).map((behaviour) => (
              <div key={behaviour.behaviour_code} className="flex items-center justify-between text-[11px] text-[#334155]">
                <span>{behaviour.behaviour_code}</span>
                <span>{behaviour.count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
            <CameraIcon className="w-3.5 h-3.5 text-[#2F52D6]" />
            Cameras
          </div>
          <div className="mt-3 space-y-2">
            {selectedZoneCameras.length === 0 ? (
              <div className="text-xs text-[#6F7F98]">No camera coverage is exposed for this zone.</div>
            ) : (
              selectedZoneCameras.map((camera) => (
                <div key={camera.camera_id} className="flex items-center justify-between text-[11px] text-[#334155]">
                  <span>{camera.camera_code}</span>
                  <span>{camera.camera_name}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#6F7F98]">
            <CameraIcon className="w-3.5 h-3.5 text-[#2F52D6]" />
            Evidence
          </div>
          <div className="mt-3 space-y-2">
            {matchingIncidents.length === 0 ? (
              <div className="text-xs text-[#6F7F98]">No evidence references are exposed for this zone.</div>
            ) : (
              matchingIncidents.slice(0, 3).map((incident) => (
                <div key={incident.id} className="text-[11px] text-[#334155]">
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

/** SVG path for a camera's field-of-view cone in the 0-100 map viewBox
 * — a simple 2D top-down wedge (see Camera.orientation_degrees/fov_degrees
 * in the backend model), not a full 3D frustum, matching the twin's own
 * 2D floor-plan rendering. */
function coverageConePath(orientationDegrees: number, fovDegrees: number, rangeUnits: number): string {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const half = fovDegrees / 2;
  const a1 = toRad(orientationDegrees - half);
  const a2 = toRad(orientationDegrees + half);
  const x1 = Math.cos(a1) * rangeUnits;
  const y1 = Math.sin(a1) * rangeUnits;
  const x2 = Math.cos(a2) * rangeUnits;
  const y2 = Math.sin(a2) * rangeUnits;
  const largeArc = fovDegrees > 180 ? 1 : 0;
  return `M 0 0 L ${x1} ${y1} A ${rangeUnits} ${rangeUnits} 0 ${largeArc} 1 ${x2} ${y2} Z`;
}
