import React, { useMemo, useState } from 'react';
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
import { StatusBadge } from '../components/common/StatusBadge';
import { RiskBadge } from '../components/ui/risk-badge';
import { useAlerts } from '../hooks/useAlerts';
import { useDashboardSummary } from '../hooks/useDashboardSummary';
import { useIncidents } from '../hooks/useIncidents';

const chartColors = ['#ef4444', '#f97316', '#f59e0b', '#3b82f6', '#8b5cf6'];

const formatMoney = (value: number | undefined) =>
  typeof value === 'number' ? `$${value.toLocaleString()}` : 'N/A';

export const DashboardPage: React.FC = () => {
  const queryClient = useQueryClient();
  // Shared TanStack Query hooks — the same cache AppLayout's alert badge
  // reads from, so this data is fetched once per staleness window instead
  // of once per page, and stays in sync with realtime invalidations.
  const { data: summary } = useDashboardSummary();
  const { data: alerts = [] } = useAlerts();
  const { data: incidents = [] } = useIncidents();
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);

  const behaviourChartData = useMemo(
    () => summary?.behaviour_distribution ?? [],
    [summary],
  );

  const selectedIncident = incidents.find((incident) => incident.id === selectedIncidentId) ?? incidents[0] ?? null;

  const criticalAlertCount = alerts.filter((alert) => alert.alert_level === 'CRITICAL').length;
  const totalBehaviourEvents = behaviourChartData.reduce((sum, item) => sum + item.count, 0);

  const handleAck = async (id: string) => {
    await acknowledgeAlert(id);
    await queryClient.invalidateQueries({ queryKey: ['alerts'] });
  };

  const riskRiskLabel = summary?.operational_health_status ?? 'UNKNOWN';

  return (
    <div className="space-y-6 pb-12">
      <div className="glass-panel rounded-2xl p-5 md:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-2.5 py-1 text-[10px] font-mono uppercase tracking-[0.2em] text-blue-300">
              <span className="h-2 w-2 rounded-full bg-blue-400 pulse-live" />
              Real-time risk surveillance
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Command Center</h1>
            <p className="mt-1 max-w-2xl text-xs text-gray-400">
              What is happening, where it is happening, how serious it is, why it happened, what changed, and which next actions require investigation.
            </p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-right">
            <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">Current risk posture</div>
            <div className="mt-1 text-xl font-bold text-white">{riskRiskLabel}</div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Current Risk</span>
            <Gauge className="h-4 w-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">{summary?.operational_health_status ?? 'UNKNOWN'}</div>
          <div className="mt-2 text-xs text-gray-400">Server-reported operational posture</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Active Incidents</span>
            <ShieldAlert className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white">{summary?.total_incidents_detected ?? 0}</div>
          <div className="mt-2 text-xs text-gray-400">Incident records returned by backend</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Critical Alerts</span>
            <AlertTriangle className="h-4 w-4 text-red-400" />
          </div>
          <div className="text-2xl font-bold text-white">{criticalAlertCount}</div>
          <div className="mt-2 text-xs text-gray-400">Alerts at CRITICAL severity</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Potential Damage</span>
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">{formatMoney(summary?.estimated_damage_loss_usd)}</div>
          <div className="mt-2 text-xs text-gray-400">Estimated damage loss from analytics summary</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Cameras Online</span>
            <Camera className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">Not exposed</div>
          <div className="mt-2 text-xs text-gray-400">Backend camera telemetry is not currently available</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Cameras Offline</span>
            <Camera className="h-4 w-4 text-red-400" />
          </div>
          <div className="text-2xl font-bold text-white">Not exposed</div>
          <div className="mt-2 text-xs text-gray-400">No offline camera contract is available yet</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Processing Jobs</span>
            <Workflow className="h-4 w-4 text-violet-400" />
          </div>
          <div className="text-2xl font-bold text-white">Not exposed</div>
          <div className="mt-2 text-xs text-gray-400">No processing-job endpoint is defined in the backend contract</div>
        </div>

        <div className="glass-panel rounded-xl p-4">
          <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
            <span>Behaviour Events</span>
            <Activity className="h-4 w-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white">{totalBehaviourEvents}</div>
          <div className="mt-2 text-xs text-gray-400">Aggregated from behaviour distribution data</div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="space-y-6">
          <div className="glass-panel rounded-xl p-5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-white">Risk Intelligence</h2>
                <p className="text-xs text-gray-400">Backend-backed hotspot and risk drivers</p>
              </div>
              <RiskBadge level={riskRiskLabel === 'CRITICAL' ? 'CRITICAL' : riskRiskLabel === 'DEGRADED' ? 'HIGH' : 'LOW'} score={summary ? undefined : undefined} />
            </div>

            <div className="grid gap-4 md:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-xl border border-white/10 bg-black/25 p-4">
                <div className="mb-2 text-[10px] uppercase tracking-[0.18em] text-gray-400">Risk Orbit</div>
                <div className="relative mx-auto flex h-48 w-48 items-center justify-center">
                  <div className="absolute h-44 w-44 rounded-full border border-blue-500/20" />
                  <div className="absolute h-32 w-32 rounded-full border border-violet-500/20" />
                  <div className="absolute h-20 w-20 rounded-full border border-amber-500/20" />
                  <div className="flex h-20 w-20 items-center justify-center rounded-full border border-blue-500/40 bg-blue-500/10 text-center text-xs font-bold text-blue-300">
                    {riskRiskLabel}
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2 text-[10px] text-gray-300">
                  <div className="rounded-lg border border-white/10 bg-white/[0.02] p-2 text-center">
                    <div className="font-mono text-blue-300">{summary?.risk_heatmaps.length ?? 0}</div>
                    <div className="text-gray-400">hotspots</div>
                  </div>
                  <div className="rounded-lg border border-white/10 bg-white/[0.02] p-2 text-center">
                    <div className="font-mono text-violet-300">{behaviourChartData.length}</div>
                    <div className="text-gray-400">signals</div>
                  </div>
                  <div className="rounded-lg border border-white/10 bg-white/[0.02] p-2 text-center">
                    <div className="font-mono text-amber-300">{criticalAlertCount}</div>
                    <div className="text-gray-400">alerts</div>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="text-[10px] uppercase tracking-[0.18em] text-gray-400">Risk Distribution</div>
                {behaviourChartData.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-white/10 p-4 text-xs text-gray-500">
                    No behaviour distribution data is exposed by the backend contract.
                  </div>
                ) : (
                  behaviourChartData.map((item, index) => (
                    <div key={item.behaviour_code} className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: chartColors[index % chartColors.length] }} />
                          <span className="text-sm font-medium text-white">{item.behaviour_code}</span>
                        </div>
                        <span className="text-xs font-mono text-gray-300">{item.count} events</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-white/5">
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${Math.min(item.percentage, 100)}%`, backgroundColor: chartColors[index % chartColors.length] }}
                        />
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[10px] text-gray-400">
                        <span>{item.percentage}% share</span>
                        <span>avg risk {item.avg_risk_score}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-white">Live Situation View</h2>
                <p className="text-xs text-gray-400">Hotspot intensity derived from backend heatmap coordinates</p>
              </div>
              <div className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-1 text-[10px] font-mono uppercase text-gray-400">Zone intensity</div>
            </div>

            <div className="relative h-60 overflow-hidden rounded-xl border border-white/10 bg-[radial-gradient(circle,_rgba(59,130,246,0.12),_rgba(15,23,42,0.9)_58%)] p-4">
              {(summary?.risk_heatmaps ?? []).length === 0 ? (
                <div className="flex h-full items-center justify-center text-xs text-gray-500">
                  No zone heatmap data is currently available from the backend.
                </div>
              ) : (
                <>
                  <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'linear-gradient(to right, rgba(148,163,184,0.3) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.3) 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
                  {(summary?.risk_heatmaps ?? []).map((zone, index) => (
                    <div
                      key={zone.zone_code}
                      className="absolute flex items-center justify-center rounded-full border border-red-400/50 bg-red-500/20 text-[10px] font-mono text-red-200 shadow-lg shadow-red-500/20"
                      style={{
                        left: `${Math.max(8, zone.x_normalized * 100)}%`,
                        top: `${Math.max(8, zone.y_normalized * 100)}%`,
                        width: `${40 + zone.intensity * 80}px`,
                        height: `${40 + zone.intensity * 80}px`,
                        background: `radial-gradient(circle, rgba(239,68,68,${0.18 + zone.intensity * 0.4}), rgba(15,23,42,0.8))`,
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
            <div className="glass-panel rounded-xl p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-bold text-white">Behaviour Trends</h2>
                <Activity className="h-4 w-4 text-blue-400" />
              </div>

              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={behaviourChartData}>
                    <XAxis dataKey="behaviour_code" stroke="#94a3b8" fontSize={10} />
                    <YAxis stroke="#94a3b8" fontSize={10} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
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

            <div className="glass-panel rounded-xl p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-bold text-white">High-Risk Zones</h2>
                <MapPinned className="h-4 w-4 text-red-400" />
              </div>

              <div className="space-y-3">
                {(summary?.risk_heatmaps ?? []).length === 0 ? (
                  <div className="rounded-lg border border-dashed border-white/10 p-4 text-xs text-gray-500">
                    No hotspot zones are exposed by the backend.
                  </div>
                ) : (
                  summary?.risk_heatmaps.map((zone, index) => (
                    <div key={zone.zone_code} className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-white">{zone.zone_code}</span>
                        <span className="text-[10px] font-mono text-red-300">{Math.round(zone.intensity * 100)}%</span>
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[10px] text-gray-400">
                        <span>{zone.incident_count} incidents</span>
                        <span>{zone.x_normalized.toFixed(2)}, {zone.y_normalized.toFixed(2)}</span>
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5">
                        <div className="h-full rounded-full bg-gradient-to-r from-amber-500 to-red-500" style={{ width: `${Math.round(zone.intensity * 100)}%` }} />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-panel rounded-xl p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Open Incident Queue</h2>
              <button type="button" className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-[0.18em] text-blue-400">
                Investigate <ArrowRight className="h-3 w-3" />
              </button>
            </div>

            <div className="space-y-3">
              {incidents.length === 0 ? (
                <div className="rounded-lg border border-dashed border-white/10 p-4 text-xs text-gray-500">
                  No incident data is currently available from the backend.
                </div>
              ) : (
                incidents.map((incident) => (
                  <button
                    key={incident.id}
                    type="button"
                    onClick={() => setSelectedIncidentId(incident.id)}
                    className={`w-full rounded-lg border p-3 text-left transition ${selectedIncident?.id === incident.id ? 'border-blue-500/40 bg-blue-500/10' : 'border-white/10 bg-white/[0.02] hover:border-white/20'}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-blue-400">{incident.incident_code}</div>
                        <div className="mt-1 text-sm font-medium text-white">{incident.title}</div>
                      </div>
                      <StatusBadge level={incident.severity} />
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-gray-400">
                      <span>{incident.zone_id ?? 'Zone unknown'}</span>
                      <span>{new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </button>
                ))
              )}
            </div>

            {selectedIncident && (
              <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-4">
                <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-gray-400">
                  <span>Selected incident</span>
                  <StatusBadge level={selectedIncident.severity} />
                </div>
                <div className="text-sm font-semibold text-white">{selectedIncident.title}</div>
                <p className="mt-2 text-xs text-gray-300">{selectedIncident.summary}</p>
                <div className="mt-3 flex flex-wrap gap-2 text-[10px] font-mono text-gray-300">
                  <span className="rounded border border-white/10 bg-white/[0.02] px-2 py-1">{selectedIncident.status}</span>
                  <span className="rounded border border-white/10 bg-white/[0.02] px-2 py-1">{selectedIncident.camera_id ?? 'Camera unavailable'}</span>
                  <span className="rounded border border-white/10 bg-white/[0.02] px-2 py-1">{selectedIncident.zone_id ?? 'Zone unavailable'}</span>
                </div>
              </div>
            )}
          </div>

          <div className="glass-panel rounded-xl p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Camera Health</h2>
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="rounded-lg border border-dashed border-white/10 bg-white/[0.02] p-4 text-xs text-gray-500">
              Camera health data is not exposed by the current backend contract. No live telemetry is fabricated here.
            </div>
          </div>

          <div className="glass-panel rounded-xl p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Live Event Stream</h2>
              <Layers3 className="h-4 w-4 text-violet-400" />
            </div>

            <div className="space-y-3">
              {alerts.length === 0 ? (
                <div className="rounded-lg border border-dashed border-white/10 p-4 text-xs text-gray-500">
                  No live alerts are currently available.
                </div>
              ) : (
                alerts.map((alert) => (
                  <div key={alert.id} className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                    <div className="flex items-center justify-between gap-3">
                      <StatusBadge level={alert.alert_level} />
                      <span className="text-[10px] font-mono text-gray-400">
                        {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-gray-200">{alert.message}</p>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-gray-400">
                      <span>{alert.status}</span>
                      {alert.status === 'OPEN' ? (
                        <button type="button" onClick={() => handleAck(alert.id)} className="inline-flex items-center gap-1 text-blue-400">
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

          <div className="glass-panel rounded-xl p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Event Timeline</h2>
              <CircleAlert className="h-4 w-4 text-amber-400" />
            </div>

            <div className="space-y-3 border-l border-white/10 pl-4">
              {incidents.length === 0 ? (
                <div className="text-xs text-gray-500">No timeline events available from the backend.</div>
              ) : (
                incidents.map((incident) => (
                  <div key={incident.id} className="relative">
                    <span className="absolute -left-[1.06rem] top-1 h-2.5 w-2.5 rounded-full border border-blue-400 bg-blue-500/20" />
                    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-blue-300">{incident.incident_code}</span>
                        <StatusBadge level={incident.severity} />
                      </div>
                      <div className="mt-2 text-sm font-medium text-white">{incident.title}</div>
                      <div className="mt-2 text-[10px] text-gray-400">
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
    </div>
  );
};
