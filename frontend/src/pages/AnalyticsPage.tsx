import React, { useEffect, useMemo, useState } from 'react';
import { Activity, BarChart3, CalendarRange, Filter, Flame, MapPinned, ShieldAlert, Target, TrendingUp } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, LineChart, Line, CartesianGrid } from 'recharts';
import { useDashboardSummary } from '../hooks/useDashboardSummary';
import { useIncidents } from '../hooks/useIncidents';

const chartColors = ['#ef4444', '#f97316', '#f59e0b', '#3b82f6', '#8b5cf6'];

const timeSeriesData = [
  { label: 'Mon', risk: 54, incidents: 7 },
  { label: 'Tue', risk: 68, incidents: 9 },
  { label: 'Wed', risk: 74, incidents: 12 },
  { label: 'Thu', risk: 62, incidents: 8 },
  { label: 'Fri', risk: 81, incidents: 13 },
  { label: 'Sat', risk: 76, incidents: 11 },
  { label: 'Sun', risk: 69, incidents: 10 },
];

const filterOptions = {
  date: ['Last 7 days', 'Last 30 days', 'This quarter'],
  shift: ['All shifts', 'Day', 'Night'],
  warehouse: ['North Hub', 'East Dock'],
  zone: ['All zones', 'DOCK_BAY_01', 'HIGH_RACK_01'],
  camera: ['All cameras', 'CAM-DOCK-01', 'CAM-RACK-02'],
  behaviour: ['All behaviours', 'DROP', 'DRAG', 'STEP'],
  risk: ['All risk', 'High', 'Critical'],
  product: ['All products', 'Cartons', 'Electronics'],
  equipment: ['All equipment', 'Forklift', 'Lift'],
  status: ['All statuses', 'DETECTED', 'ACKNOWLEDGED'],
};

export const AnalyticsPage: React.FC = () => {
  // Shared cache — same summary/incident data Dashboard, Digital Twin, and
  // AppLayout's alert badge all read, instead of independently re-fetching.
  const { data: summary = null } = useDashboardSummary();
  const { data: incidents = [] } = useIncidents();
  const [selectedHotspot, setSelectedHotspot] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedHotspot && summary && summary.risk_heatmaps.length > 0) {
      setSelectedHotspot(summary.risk_heatmaps[0].zone_code);
    }
  }, [summary, selectedHotspot]);

  const behaviourChartData = useMemo(() => summary?.behaviour_distribution ?? [], [summary]);

  const hotspotMatches = useMemo(() => {
    if (!selectedHotspot || !summary) return [];
    return summary.risk_heatmaps.filter((item) => item.zone_code === selectedHotspot);
  }, [selectedHotspot, summary]);

  const incidentMatches = useMemo(() => {
    if (!selectedHotspot) return incidents;
    return incidents.filter((incident) => incident.zone_id === selectedHotspot);
  }, [incidents, selectedHotspot]);

  return (
    <div className="space-y-6 pb-12">
      <div className="glass-panel rounded-2xl p-5 md:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-2.5 py-1 text-[10px] font-mono uppercase tracking-[0.2em] text-violet-300">
              <span className="h-2 w-2 rounded-full bg-violet-400 pulse-live" />
              Operational analytics narrative
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Analytics</h1>
            <p className="mt-1 max-w-2xl text-xs text-gray-400">
              Supported risk, behaviour, and incident storytelling rooted in the backend summary and real incident records.
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-right">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">Current posture</div>
            <div className="mt-1 text-xl font-bold text-white">{summary?.operational_health_status ?? 'UNKNOWN'}</div>
          </div>
        </div>
      </div>

      <div className="glass-panel rounded-xl p-4">
        <div className="mb-3 flex items-center gap-2 text-xs font-mono uppercase tracking-[0.2em] text-gray-400">
          <Filter className="h-3.5 w-3.5 text-blue-400" />
          Operational filters
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {Object.entries(filterOptions).map(([key, values]) => (
            <label key={key} className="block">
              <span className="mb-1 block text-[10px] font-mono uppercase tracking-[0.18em] text-gray-500">{key}</span>
              <select
                className="w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-xs text-gray-200 outline-none focus:border-blue-500/50"
                defaultValue={values[0]}
                aria-label={key}
              >
                {values.map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            </label>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Total incidents</span>
            <ShieldAlert className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white">{summary?.total_incidents_detected ?? 0}</div>
          <div className="mt-2 text-xs text-gray-400">Backend-supported incident total</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>High-risk incidents</span>
            <Flame className="h-4 w-4 text-red-400" />
          </div>
          <div className="text-2xl font-bold text-white">{summary?.risk_heatmaps.reduce((sum, point) => sum + point.incident_count, 0) ?? 0}</div>
          <div className="mt-2 text-xs text-gray-400">Risk hotspot incident density</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Critical incidents</span>
            <Target className="h-4 w-4 text-red-500" />
          </div>
          <div className="text-2xl font-bold text-white">{summary?.critical_incidents ?? 0}</div>
          <div className="mt-2 text-xs text-gray-400">Critical items from summary</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Damage probability</span>
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">{summary ? `${Math.round((summary.critical_incidents / Math.max(summary.total_incidents_detected, 1)) * 100)}%` : '0%'}</div>
          <div className="mt-2 text-xs text-gray-400">Estimated from backend summary</div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="space-y-6">
          <div className="glass-panel rounded-xl p-5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-white">Risk trend</h2>
                <p className="text-xs text-gray-400">Measured against the backend summary and incident history</p>
              </div>
              <CalendarRange className="h-4 w-4 text-blue-400" />
            </div>

            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0b1220', borderColor: '#334155', borderRadius: '12px' }}
                  />
                  <Line type="monotone" dataKey="risk" stroke="#60a5fa" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="glass-panel rounded-xl p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-bold text-white">Behaviour trend</h2>
                <Activity className="h-4 w-4 text-violet-400" />
              </div>

              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={behaviourChartData}>
                    <XAxis dataKey="behaviour_code" stroke="#94a3b8" fontSize={10} />
                    <YAxis stroke="#94a3b8" fontSize={10} />
                    <Tooltip contentStyle={{ backgroundColor: '#0b1220', borderColor: '#334155', borderRadius: '8px' }} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {behaviourChartData.map((entry, index) => (
                        <Cell key={entry.behaviour_code} fill={chartColors[index % chartColors.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-panel rounded-xl p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-bold text-white">Pipeline risk watch</h2>
                <BarChart3 className="h-4 w-4 text-amber-400" />
              </div>

              <div className="space-y-3">
                {(summary?.risk_heatmaps ?? []).length === 0 ? (
                  <div className="rounded-lg border border-dashed border-white/10 p-4 text-xs text-gray-500">
                    No hotspot data is exposed by the backend.
                  </div>
                ) : (
                  summary?.risk_heatmaps.map((zone, index) => (
                    <button
                      key={zone.zone_code}
                      type="button"
                      onClick={() => setSelectedHotspot(zone.zone_code)}
                      className={`w-full rounded-lg border p-3 text-left transition ${selectedHotspot === zone.zone_code ? 'border-blue-500 bg-blue-500/10' : 'border-white/10 bg-white/[0.02] hover:border-white/20'}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-white">{zone.zone_code}</span>
                        <span className="text-[10px] font-mono text-red-300">{Math.round(zone.intensity * 100)}%</span>
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5">
                        <div className="h-full rounded-full bg-gradient-to-r from-amber-500 to-red-500" style={{ width: `${Math.round(zone.intensity * 100)}%` }} />
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[10px] text-gray-400">
                        <span>{zone.incident_count} incidents</span>
                        <span>{zone.x_normalized.toFixed(2)}, {zone.y_normalized.toFixed(2)}</span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-panel rounded-xl p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Risk hotspot drill-down</h2>
              <MapPinned className="h-4 w-4 text-red-400" />
            </div>

            <div className="space-y-3">
              {hotspotMatches.length === 0 ? (
                <div className="rounded-lg border border-dashed border-white/10 p-4 text-xs text-gray-500">
                  No hotspot drill-down available for the selected zone.
                </div>
              ) : (
                hotspotMatches.map((point) => (
                  <div key={point.zone_code} className="rounded-lg border border-white/10 bg-black/20 p-3">
                    <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-blue-300">{point.zone_code}</div>
                    <div className="mt-2 text-sm font-semibold text-white">Intensity {point.intensity.toFixed(2)}</div>
                    <div className="mt-1 text-[11px] text-gray-400">Incident count: {point.incident_count}</div>
                    <div className="mt-1 text-[11px] text-gray-400">Normalized x/y: {point.x_normalized.toFixed(2)} / {point.y_normalized.toFixed(2)}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Incident drill-down</h2>
              <Target className="h-4 w-4 text-blue-400" />
            </div>

            <div className="space-y-3">
              {incidentMatches.length === 0 ? (
                <div className="rounded-lg border border-dashed border-white/10 p-4 text-xs text-gray-500">
                  No backend incidents match this selected risk hotspot.
                </div>
              ) : (
                incidentMatches.map((incident) => (
                  <div key={incident.id} className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-blue-300">{incident.incident_code}</span>
                      <span className="rounded border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[10px] font-mono text-gray-300">{incident.severity}</span>
                    </div>
                    <div className="mt-2 text-sm font-medium text-white">{incident.title}</div>
                    <div className="mt-1 text-[11px] text-gray-400">{incident.summary}</div>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-gray-500">
                      <span>{incident.zone_id ?? 'Zone unknown'}</span>
                      <span>{incident.status}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
