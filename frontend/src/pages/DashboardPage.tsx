import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Camera,
  ChevronRight,
  CircleAlert,
  Gauge,
  Layers3,
  MapPinned,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  Workflow,
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { acknowledgeAlert } from '../api/alerts';
import { AlertAcknowledgedModal } from '../components/common/AlertAcknowledgedModal';
import { StatusBadge } from '../components/common/StatusBadge';
import { RiskBadge } from '../components/ui/risk-badge';
import { useAlerts } from '../hooks/useAlerts';
import { useDashboardSummary } from '../hooks/useDashboardSummary';
import { useIncidents } from '../hooks/useIncidents';
import type { AlertItem } from '../types';

// A brand-blue ramp — keeps ordinal chart series distinguishable (a
// functional requirement, not decoration) while staying inside the
// theme's blue-only chromatic rule instead of a neon multi-hue palette.
const chartColors = ['#2F52D6', '#5D87FF', '#49BEFF', '#8AB6FF', '#B9D4FF'];

const formatMoney = (value: number | undefined) =>
  typeof value === 'number' ? `$${value.toLocaleString()}` : 'N/A';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  // Shared TanStack Query hooks — the same cache AppLayout's alert badge
  // reads from, so this data is fetched once per staleness window instead
  // of once per page, and stays in sync with realtime invalidations.
  const { data: summary } = useDashboardSummary();
  const { data: alerts = [] } = useAlerts();
  const { data: incidents = [] } = useIncidents();
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [acknowledgedAlert, setAcknowledgedAlert] = useState<AlertItem | null>(null);
  const [ackModalOpen, setAckModalOpen] = useState(false);

  const behaviourChartData = useMemo(
    () => summary?.behaviour_distribution ?? [],
    [summary],
  );

  const selectedIncident = incidents.find((incident) => incident.id === selectedIncidentId) ?? incidents[0] ?? null;

  const criticalAlertCount = alerts.filter((alert) => alert.alert_level === 'CRITICAL').length;
  const totalBehaviourEvents = behaviourChartData.reduce((sum, item) => sum + item.count, 0);

  const handleAck = async (id: string) => {
    const updated = await acknowledgeAlert(id);
    await queryClient.invalidateQueries({ queryKey: ['alerts'] });
    setAcknowledgedAlert(updated);
    setAckModalOpen(true);
  };

  const riskRiskLabel = summary?.operational_health_status ?? 'UNKNOWN';

  return (
    <div className="space-y-6 pb-12">
      <div className="glass-panel rounded-[24px] p-6 md:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 text-[13px] uppercase tracking-[0.18em] text-[#2F52D6]">
              <span className="h-2 w-2 rounded-full bg-[#2F52D6] pulse-live" />
              Real-time risk surveillance
            </div>
            <h1 className="font-[family-name:var(--font-signifier)] text-[40px] md:text-[44px] leading-[1.15] tracking-[-0.66px] text-[#18243A]">
              Command Center
            </h1>
            <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-[#6F7F98]">
              What is happening, where it is happening, how serious it is, why it happened, what changed, and which next actions require investigation.
            </p>
          </div>
          <div className="rounded-[20px] bg-[#EAF0FF] px-6 py-4 text-right shrink-0">
            <div className="text-[11px] uppercase tracking-[0.18em] text-[#2F52D6]/70">Current risk posture</div>
            <div className="mt-1 font-[family-name:var(--font-signifier)] font-bold text-2xl text-[#2F52D6]">{riskRiskLabel}</div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="glass-panel rounded-[20px] p-4">
          <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">
            <span>Current Risk</span>
            <Gauge className="h-4 w-4 text-[#2F52D6]" />
          </div>
          <div className="text-2xl font-medium text-[#18243A]">{summary?.operational_health_status ?? 'UNKNOWN'}</div>
          <div className="mt-2 text-xs text-[#6F7F98]">Server-reported operational posture</div>
        </div>

        <div className="glass-panel rounded-[20px] p-4">
          <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">
            <span>Active Incidents</span>
            <ShieldAlert className="h-4 w-4 text-[#92400e]" />
          </div>
          <div className="text-2xl font-medium text-[#18243A]">{summary?.total_incidents_detected ?? 0}</div>
          <div className="mt-2 text-xs text-[#6F7F98]">Incident records returned by backend</div>
        </div>

        <div className="glass-panel rounded-[20px] p-4">
          <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">
            <span>Critical Alerts</span>
            <AlertTriangle className="h-4 w-4 text-[#b91c1c]" />
          </div>
          <div className="text-2xl font-medium text-[#18243A]">{criticalAlertCount}</div>
          <div className="mt-2 text-xs text-[#6F7F98]">Alerts at CRITICAL severity</div>
        </div>

        <div className="glass-panel rounded-[20px] p-4">
          <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">
            <span>Potential Damage Exposure</span>
            <TrendingUp className="h-4 w-4 text-[#15803d]" />
          </div>
          <div className="text-2xl font-medium text-[#18243A]">{formatMoney(summary?.potential_damage_exposure_usd)}</div>
          <div className="mt-2 text-xs text-[#6F7F98]">
            AI-estimated (product value × damage probability) for events not yet human-confirmed
            {typeof summary?.confirmed_damage_cost_usd === 'number' && summary.confirmed_damage_cost_usd > 0
              ? ` · ${formatMoney(summary.confirmed_damage_cost_usd)} confirmed`
              : ''}
          </div>
        </div>

        <div className="glass-panel rounded-[20px] p-4">
          <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">
            <span>Cameras Online</span>
            <Camera className="h-4 w-4 text-[#9DAFC5]" />
          </div>
          <div className="text-2xl font-medium text-[#18243A]">Not exposed</div>
          <div className="mt-2 text-xs text-[#6F7F98]">Backend camera telemetry is not currently available</div>
        </div>

        <div className="glass-panel rounded-[20px] p-4">
          <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">
            <span>Cameras Offline</span>
            <Camera className="h-4 w-4 text-[#9DAFC5]" />
          </div>
          <div className="text-2xl font-medium text-[#18243A]">Not exposed</div>
          <div className="mt-2 text-xs text-[#6F7F98]">No offline camera contract is available yet</div>
        </div>

        <div className="glass-panel rounded-[20px] p-4">
          <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">
            <span>Processing Jobs</span>
            <Workflow className="h-4 w-4 text-[#9DAFC5]" />
          </div>
          <div className="text-2xl font-medium text-[#18243A]">Not exposed</div>
          <div className="mt-2 text-xs text-[#6F7F98]">No processing-job endpoint is defined in the backend contract</div>
        </div>

        <div className="glass-panel rounded-[20px] p-4">
          <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">
            <span>Behaviour Events</span>
            <Activity className="h-4 w-4 text-[#2F52D6]" />
          </div>
          <div className="text-2xl font-medium text-[#18243A]">{totalBehaviourEvents}</div>
          <div className="mt-2 text-xs text-[#6F7F98]">Aggregated from behaviour distribution data</div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="space-y-6">
          <div className="rounded-[20px] bg-white shadow-[0_0_0_1px_rgba(4,23,43,0.05),0_20px_25px_-5px_rgba(0,0,0,0.1),0_8px_10px_-6px_rgba(0,0,0,0.1)] p-6">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="font-[family-name:var(--font-signifier)] text-xl text-[#18243A]">Risk Intelligence</h2>
                <p className="text-sm text-[#6F7F98]">Backend-backed hotspot and risk drivers</p>
              </div>
              <RiskBadge level={riskRiskLabel === 'CRITICAL' ? 'CRITICAL' : riskRiskLabel === 'DEGRADED' ? 'HIGH' : 'LOW'} score={summary ? undefined : undefined} />
            </div>

            <div className="grid gap-4 md:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-[20px] border border-[#E9EDF2] bg-[#F8FAFC] p-4">
                <div className="mb-2 text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">Risk Orbit</div>
                <div className="relative mx-auto flex h-48 w-48 items-center justify-center">
                  <div className="absolute h-44 w-44 rounded-full border border-[#E9EDF2]" />
                  <div className="absolute h-32 w-32 rounded-full border border-[rgba(47,82,214,0.15)]" />
                  <div className="absolute h-20 w-20 rounded-full border border-[rgba(146,64,14,0.2)]" />
                  <div className="flex h-20 w-20 items-center justify-center rounded-full border border-[rgba(47,82,214,0.3)] bg-[#EAF0FF] text-center text-xs font-semibold text-[#2F52D6]">
                    {riskRiskLabel}
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2 text-[11px] text-[#334155]">
                  <div className="rounded-2xl border border-[#E9EDF2] bg-white p-2 text-center">
                    <div className="text-[#2F52D6] font-medium">{summary?.risk_heatmaps.length ?? 0}</div>
                    <div className="text-[#6F7F98]">hotspots</div>
                  </div>
                  <div className="rounded-2xl border border-[#E9EDF2] bg-white p-2 text-center">
                    <div className="text-[#2F52D6] font-medium">{behaviourChartData.length}</div>
                    <div className="text-[#6F7F98]">signals</div>
                  </div>
                  <div className="rounded-2xl border border-[#E9EDF2] bg-white p-2 text-center">
                    <div className="text-[#92400e] font-medium">{criticalAlertCount}</div>
                    <div className="text-[#6F7F98]">alerts</div>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">Risk Distribution</div>
                {behaviourChartData.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-[#CBD5E1] p-4 text-xs text-[#9DAFC5]">
                    No behaviour distribution data is exposed by the backend contract.
                  </div>
                ) : (
                  behaviourChartData.map((item, index) => (
                    <div key={item.behaviour_code} className="rounded-2xl border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: chartColors[index % chartColors.length] }} />
                          <span className="text-sm font-medium text-[#18243A]">{item.behaviour_code}</span>
                        </div>
                        <span className="text-xs text-[#6F7F98]">{item.count} events</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-[#E9EDF2]">
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${Math.min(item.percentage, 100)}%`, backgroundColor: chartColors[index % chartColors.length] }}
                        />
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[11px] text-[#9DAFC5]">
                        <span>{item.percentage}% share</span>
                        <span>avg risk {item.avg_risk_score ?? 'N/A'}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-[20px] p-6">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="font-[family-name:var(--font-signifier)] text-xl text-[#18243A]">Live Situation View</h2>
                <p className="text-sm text-[#6F7F98]">Hotspot intensity derived from backend heatmap coordinates</p>
              </div>
              <div className="rounded-full border border-[#E9EDF2] bg-white px-2.5 py-1 text-[10px] uppercase text-[#6F7F98]">Zone intensity</div>
            </div>

            <div className="relative h-60 overflow-hidden rounded-[20px] border border-[#E9EDF2] bg-[#F8FAFC] p-4">
              {(summary?.risk_heatmaps ?? []).length === 0 ? (
                <div className="flex h-full items-center justify-center text-xs text-[#9DAFC5]">
                  No zone heatmap data is currently available from the backend.
                </div>
              ) : (
                <>
                  <div className="absolute inset-0 opacity-40" style={{ backgroundImage: 'linear-gradient(to right, rgba(212,212,214,0.6) 1px, transparent 1px), linear-gradient(to bottom, rgba(212,212,214,0.6) 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
                  {(summary?.risk_heatmaps ?? []).map((zone, index) => (
                    <div
                      key={zone.zone_code}
                      className="absolute flex items-center justify-center rounded-full border border-[rgba(185,28,28,0.4)] text-[10px] text-[#b91c1c] font-medium"
                      style={{
                        left: `${Math.max(8, zone.x_normalized * 100)}%`,
                        top: `${Math.max(8, zone.y_normalized * 100)}%`,
                        width: `${40 + zone.intensity * 80}px`,
                        height: `${40 + zone.intensity * 80}px`,
                        background: `radial-gradient(circle, rgba(185,28,28,${0.1 + zone.intensity * 0.25}), rgba(185,28,28,0.02))`,
                        transform: 'translate(-50%, -50%)',
                        zIndex: 10 + index,
                      }}
                    >
                      {zone.zone_code}
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="glass-panel rounded-[20px] p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-[family-name:var(--font-signifier)] text-lg text-[#18243A]">Behaviour Trends</h2>
                <Activity className="h-4 w-4 text-[#2F52D6]" />
              </div>

              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={behaviourChartData}>
                    <XAxis dataKey="behaviour_code" stroke="#9DAFC5" fontSize={10} />
                    <YAxis stroke="#9DAFC5" fontSize={10} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E9EDF2', borderRadius: '12px', fontSize: 12 }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {behaviourChartData.map((entry, index) => (
                        <Cell key={entry.behaviour_code} fill={chartColors[index % chartColors.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-panel rounded-[20px] p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-[family-name:var(--font-signifier)] text-lg text-[#18243A]">High-Risk Zones</h2>
                <MapPinned className="h-4 w-4 text-[#b91c1c]" />
              </div>

              <div className="ge-scroll-panel space-y-3 max-h-[360px] pr-1">
                {(summary?.risk_heatmaps ?? []).length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-[#CBD5E1] p-4 text-xs text-[#9DAFC5]">
                    No hotspot zones are exposed by the backend.
                  </div>
                ) : (
                  summary?.risk_heatmaps.map((zone) => (
                    <div key={zone.zone_code} className="rounded-2xl border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-[#18243A]">{zone.zone_code}</span>
                        <span className="text-[11px] text-[#b91c1c] font-medium">{Math.round(zone.intensity * 100)}%</span>
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[11px] text-[#6F7F98]">
                        <span>{zone.incident_count} incidents</span>
                        <span>{zone.x_normalized.toFixed(2)}, {zone.y_normalized.toFixed(2)}</span>
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-[#E9EDF2]">
                        <div className="h-full rounded-full bg-[#b91c1c]" style={{ width: `${Math.round(zone.intensity * 100)}%` }} />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-panel rounded-[20px] p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-[family-name:var(--font-signifier)] text-lg text-[#18243A]">Open Incident Queue</h2>
              <button
                type="button"
                onClick={() => navigate('/incidents')}
                className="inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.14em] text-[#2F52D6] hover:underline"
              >
                Investigate <ArrowRight className="h-3 w-3" />
              </button>
            </div>

            <div className="ge-scroll-panel space-y-3 max-h-[420px] pr-1">
              {incidents.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-[#CBD5E1] p-4 text-xs text-[#9DAFC5]">
                  No incident data is currently available from the backend.
                </div>
              ) : (
                incidents.map((incident) => (
                  <button
                    key={incident.id}
                    type="button"
                    onClick={() => setSelectedIncidentId(incident.id)}
                    className={`w-full rounded-2xl border p-3 text-left transition ${selectedIncident?.id === incident.id ? 'border-[#5D87FF] bg-[#5D87FF] text-white' : 'border-[#E9EDF2] bg-[#F8FAFC] hover:border-[#CBD5E1]'}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className={`text-[10px] uppercase tracking-[0.14em] ${selectedIncident?.id === incident.id ? 'text-white/60' : 'text-[#2F52D6]'}`}>{incident.incident_code}</div>
                        <div className={`mt-1 text-sm font-medium ${selectedIncident?.id === incident.id ? 'text-white' : 'text-[#18243A]'}`}>{incident.title}</div>
                      </div>
                      <StatusBadge level={incident.severity} />
                    </div>
                    <div className={`mt-2 flex items-center justify-between text-[11px] ${selectedIncident?.id === incident.id ? 'text-white/50' : 'text-[#6F7F98]'}`}>
                      <span>{incident.zone_id ?? 'Zone unknown'}</span>
                      <span>{new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </button>
                ))
              )}
            </div>

            {selectedIncident && (
              <div className="mt-4 rounded-[20px] border border-[#E9EDF2] bg-[#F8FAFC] p-4">
                <div className="mb-2 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-[#6F7F98]">
                  <span>Selected incident</span>
                  <StatusBadge level={selectedIncident.severity} />
                </div>
                <div className="text-sm font-semibold text-[#18243A]">{selectedIncident.title}</div>
                <p className="mt-2 text-xs text-[#334155]">{selectedIncident.summary}</p>
                <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-[#334155]">
                  <span className="rounded-full border border-[#E9EDF2] bg-white px-2 py-1">{selectedIncident.status}</span>
                  <span className="rounded-full border border-[#E9EDF2] bg-white px-2 py-1">{selectedIncident.camera_id ?? 'Camera unavailable'}</span>
                  <span className="rounded-full border border-[#E9EDF2] bg-white px-2 py-1">{selectedIncident.zone_id ?? 'Zone unavailable'}</span>
                </div>
              </div>
            )}
          </div>

          <div className="glass-panel rounded-[20px] p-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-[family-name:var(--font-signifier)] text-lg text-[#18243A]">Camera Health</h2>
              <ShieldCheck className="h-4 w-4 text-[#15803d]" />
            </div>
            <div className="rounded-2xl border border-dashed border-[#CBD5E1] bg-[#F8FAFC] p-4 text-xs text-[#9DAFC5]">
              Camera health data is not exposed by the current backend contract. No live telemetry is fabricated here.
            </div>
          </div>

          <div className="glass-panel rounded-[20px] p-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-[family-name:var(--font-signifier)] text-lg text-[#18243A]">Live Event Stream</h2>
              <Layers3 className="h-4 w-4 text-[#2F52D6]" />
            </div>

            <div className="ge-scroll-panel space-y-3 max-h-[360px] pr-1">
              {alerts.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-[#CBD5E1] p-4 text-xs text-[#9DAFC5]">
                  No live alerts are currently available.
                </div>
              ) : (
                alerts.map((alert) => (
                  <div key={alert.id} className="rounded-2xl border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                    <div className="flex items-center justify-between gap-3">
                      <StatusBadge level={alert.alert_level} />
                      <span className="text-[11px] text-[#6F7F98]">
                        {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-[#334155]">{alert.message}</p>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-[#6F7F98]">
                      <span>{alert.status}</span>
                      {alert.status === 'OPEN' ? (
                        <button type="button" onClick={() => handleAck(alert.id)} className="inline-flex items-center gap-1 text-[#2F52D6] hover:underline">
                          Acknowledge <ChevronRight className="h-3 w-3" />
                        </button>
                      ) : (
                        <span>acknowledged</span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="glass-panel rounded-[20px] p-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-[family-name:var(--font-signifier)] text-lg text-[#18243A]">Event Timeline</h2>
              <CircleAlert className="h-4 w-4 text-[#92400e]" />
            </div>

            <div className="ge-scroll-panel space-y-3 border-l border-[#E9EDF2] pl-4 max-h-[420px] pr-1">
              {incidents.length === 0 ? (
                <div className="text-xs text-[#9DAFC5]">No timeline events available from the backend.</div>
              ) : (
                incidents.map((incident) => (
                  <div key={incident.id} className="relative">
                    <span className="absolute -left-[1.06rem] top-1 h-2.5 w-2.5 rounded-full border border-[#2F52D6] bg-[#EAF0FF]" />
                    <div className="rounded-2xl border border-[#E9EDF2] bg-[#F8FAFC] p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-[10px] uppercase tracking-[0.14em] text-[#2F52D6]">{incident.incident_code}</span>
                        <StatusBadge level={incident.severity} />
                      </div>
                      <div className="mt-2 text-sm font-medium text-[#18243A]">{incident.title}</div>
                      <div className="mt-2 text-[11px] text-[#6F7F98]">
                        {new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} · {incident.status}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      <AlertAcknowledgedModal
        isOpen={ackModalOpen}
        onClose={() => setAckModalOpen(false)}
        onViewIncidents={() => {
          setAckModalOpen(false);
          navigate('/incidents');
        }}
        alert={acknowledgedAlert}
      />
    </div>
  );
};
