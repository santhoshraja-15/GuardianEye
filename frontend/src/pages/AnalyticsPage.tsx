import React, { useEffect, useMemo, useState } from 'react';
import { Activity, BarChart3, CalendarRange, Filter, Flame, MapPinned, ShieldAlert, Target, TrendingUp } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, LineChart, Line, CartesianGrid } from 'recharts';
import { useDashboardSummary } from '../hooks/useDashboardSummary';
import { useIncidents } from '../hooks/useIncidents';

// A brand-blue ramp — keeps ordinal chart series distinguishable while
// staying inside the theme's blue-only chromatic rule.
const chartColors = ['#2F52D6', '#5D87FF', '#49BEFF', '#8AB6FF', '#B9D4FF'];

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
  const dailyTrend = useMemo(() => summary?.risk_trend_daily ?? [], [summary]);

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
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[rgba(93,135,255,0.3)] bg-[#5D87FF]/10 px-2.5 py-1 text-[10px] uppercase tracking-[0.2em] text-[#2F52D6]">
              <span className="h-2 w-2 rounded-full bg-[#5D87FF] pulse-live" />
              Operational analytics narrative
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[#18243A]">Analytics</h1>
            <p className="mt-1 max-w-2xl text-xs text-[#6F7F98]">
              Supported risk, behaviour, and incident storytelling rooted in the backend summary and real incident records.
            </p>
          </div>
          <div className="rounded-xl border border-[#E9EDF2] bg-[#F1F5F9] px-4 py-3 text-right">
            <div className="text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">Current posture</div>
            <div className="mt-1 text-xl font-bold text-[#18243A]">{summary?.operational_health_status ?? 'UNKNOWN'}</div>
            {summary?.risk_trend_shift && (
              <div className="mt-1 text-[10px] text-[#6F7F98]">
                {summary.risk_trend_shift.data_available && summary.risk_trend_shift.direction ? (
                  <span className={summary.risk_trend_shift.direction === 'DECREASED' ? 'text-[#15803d]' : summary.risk_trend_shift.direction === 'INCREASED' ? 'text-[#b91c1c]' : ''}>
                    {summary.risk_trend_shift.direction === 'DECREASED' ? '↓' : summary.risk_trend_shift.direction === 'INCREASED' ? '↑' : '→'} vs {summary.risk_trend_shift.period_a_label}
                  </span>
                ) : (
                  'Insufficient historical data for shift comparison'
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="glass-panel rounded-xl p-4">
        <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[#6F7F98]">
          <Filter className="h-3.5 w-3.5 text-[#2F52D6]" />
          Operational filters
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {Object.entries(filterOptions).map(([key, values]) => (
            <label key={key} className="block">
              <span className="mb-1 block text-[10px] uppercase tracking-[0.18em] text-[#9DAFC5]">{key}</span>
              <select
                className="w-full rounded-lg border border-[#E9EDF2] bg-[#F1F5F9] px-3 py-2 text-xs text-[#18243A] outline-none focus:border-[#5D87FF]/50"
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
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
            <span>Total incidents</span>
            <ShieldAlert className="h-4 w-4 text-[#92400e]" />
          </div>
          <div className="text-2xl font-bold text-[#18243A]">{summary?.total_incidents_detected ?? 0}</div>
          <div className="mt-2 text-xs text-[#6F7F98]">Backend-supported incident total</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
            <span>High-risk incidents</span>
            <Flame className="h-4 w-4 text-[#b91c1c]" />
          </div>
          <div className="text-2xl font-bold text-[#18243A]">{summary?.risk_heatmaps.reduce((sum, point) => sum + point.incident_count, 0) ?? 0}</div>
          <div className="mt-2 text-xs text-[#6F7F98]">Risk hotspot incident density</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
            <span>Critical incidents</span>
            <Target className="h-4 w-4 text-[#b91c1c]" />
          </div>
          <div className="text-2xl font-bold text-[#18243A]">{summary?.critical_incidents ?? 0}</div>
          <div className="mt-2 text-xs text-[#6F7F98]">Critical items from summary</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-[#6F7F98]">
            <span>Damage probability</span>
            <TrendingUp className="h-4 w-4 text-[#15803d]" />
          </div>
          <div className="text-2xl font-bold text-[#18243A]">{summary ? `${Math.round((summary.critical_incidents / Math.max(summary.total_incidents_detected, 1)) * 100)}%` : '0%'}</div>
          <div className="mt-2 text-xs text-[#6F7F98]">Estimated from backend summary</div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="space-y-6">
          <div className="glass-panel rounded-xl p-5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-[#18243A]">Risk trend</h2>
                <p className="text-xs text-[#6F7F98]">Real daily average risk score — {summary?.provenance?.avg_risk_score_method ?? 'AVG(risk_assessments.risk_score) per day'}</p>
              </div>
              <CalendarRange className="h-4 w-4 text-[#2F52D6]" />
            </div>

            {dailyTrend.every((d) => d.total_incidents === 0) ? (
              <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-[#CBD5E1] text-xs text-[#9DAFC5]">
                No incidents detected in the last 7 days.
              </div>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={dailyTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E9EDF2" />
                    <XAxis dataKey="label" stroke="#9DAFC5" fontSize={11} />
                    <YAxis stroke="#9DAFC5" fontSize={11} domain={[0, 100]} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E9EDF2', borderRadius: '12px', fontSize: 12 }}
                      formatter={(value, name) => [value ?? 'No data', name === 'avg_risk_score' ? 'Avg risk' : name]}
                    />
                    {/* connectNulls defaults to false — a day with zero
                        assessed events shows as a real gap, not an
                        interpolated guess at what risk "must have been". */}
                    <Line type="monotone" dataKey="avg_risk_score" stroke="#2F52D6" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="glass-panel rounded-xl p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-bold text-[#18243A]">Behaviour trend</h2>
                <Activity className="h-4 w-4 text-[#2F52D6]" />
              </div>

              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={behaviourChartData}>
                    <XAxis dataKey="behaviour_code" stroke="#9DAFC5" fontSize={10} />
                    <YAxis stroke="#9DAFC5" fontSize={10} />
                    <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E9EDF2', borderRadius: '8px', fontSize: 12 }} />
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
                <h2 className="text-sm font-bold text-[#18243A]">Pipeline risk watch</h2>
                <BarChart3 className="h-4 w-4 text-[#92400e]" />
              </div>

              <div className="space-y-3">
                {(summary?.risk_heatmaps ?? []).length === 0 ? (
                  <div className="rounded-lg border border-dashed border-[#E9EDF2] p-4 text-xs text-[#9DAFC5]">
                    No hotspot data is exposed by the backend.
                  </div>
                ) : (
                  summary?.risk_heatmaps.map((zone, index) => (
                    <button
                      key={zone.zone_code}
                      type="button"
                      onClick={() => setSelectedHotspot(zone.zone_code)}
                      className={`w-full rounded-lg border p-3 text-left transition ${selectedHotspot === zone.zone_code ? 'border-[#5D87FF] bg-[#5D87FF]/10' : 'border-[#E9EDF2] bg-[#F8FAFC] hover:border-[#CBD5E1]'}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-[#18243A]">{zone.zone_code}</span>
                        <span className="text-[10px] text-[#b91c1c]">{Math.round(zone.intensity * 100)}%</span>
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-[#E9EDF2]">
                        <div className="h-full rounded-full bg-gradient-to-r from-[#92400e] to-[#b91c1c]" style={{ width: `${Math.round(zone.intensity * 100)}%` }} />
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[10px] text-[#6F7F98]">
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
              <h2 className="text-sm font-bold text-[#18243A]">Risk hotspot drill-down</h2>
              <MapPinned className="h-4 w-4 text-[#b91c1c]" />
            </div>

            <div className="space-y-3">
              {hotspotMatches.length === 0 ? (
                <div className="rounded-lg border border-dashed border-[#E9EDF2] p-4 text-xs text-[#9DAFC5]">
                  No hotspot drill-down available for the selected zone.
                </div>
              ) : (
                hotspotMatches.map((point) => (
                  <div key={point.zone_code} className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                    <div className="text-[10px] uppercase tracking-[0.18em] text-[#2F52D6]">{point.zone_code}</div>
                    <div className="mt-2 text-sm font-semibold text-[#18243A]">Intensity {point.intensity.toFixed(2)}</div>
                    <div className="mt-1 text-[11px] text-[#6F7F98]">Incident count: {point.incident_count}</div>
                    <div className="mt-1 text-[11px] text-[#6F7F98]">Normalized x/y: {point.x_normalized.toFixed(2)} / {point.y_normalized.toFixed(2)}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-[#18243A]">Incident drill-down</h2>
              <Target className="h-4 w-4 text-[#2F52D6]" />
            </div>

            <div className="space-y-3">
              {incidentMatches.length === 0 ? (
                <div className="rounded-lg border border-dashed border-[#E9EDF2] p-4 text-xs text-[#9DAFC5]">
                  No backend incidents match this selected risk hotspot.
                </div>
              ) : (
                incidentMatches.map((incident) => (
                  <div key={incident.id} className="rounded-lg border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] uppercase tracking-[0.18em] text-[#2F52D6]">{incident.incident_code}</span>
                      <span className="rounded border border-[#E9EDF2] bg-[#F8FAFC] px-2 py-0.5 text-[10px] text-[#334155]">{incident.severity}</span>
                    </div>
                    <div className="mt-2 text-sm font-medium text-[#18243A]">{incident.title}</div>
                    <div className="mt-1 text-[11px] text-[#6F7F98]">{incident.summary}</div>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-[#9DAFC5]">
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
