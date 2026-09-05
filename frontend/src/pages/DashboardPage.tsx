import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  ArrowUpRight,
  Boxes,
  CheckCircle2,
  DollarSign,
  Flame,
  Layers,
  MapPin,
  Play,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { StatCard } from '../components/common/StatCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { GuardianAPI } from '../services/api';
import { AlertItem, DashboardSummary, IncidentItem } from '../types';

const trendData = [
  { time: '00:00', incidents: 1, safety_score: 98 },
  { time: '04:00', incidents: 0, safety_score: 99 },
  { time: '08:00', incidents: 4, safety_score: 92 },
  { time: '12:00', incidents: 7, safety_score: 86 },
  { time: '16:00', incidents: 3, safety_score: 94 },
  { time: '20:00', incidents: 2, safety_score: 96 },
];

const COLORS = ['#EF4444', '#F97316', '#F59E0B', '#3B82F6', '#8B5CF6'];

export const DashboardPage: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);

  useEffect(() => {
    GuardianAPI.getDashboardSummary().then(setSummary);
    GuardianAPI.getAlerts().then(setAlerts);
    GuardianAPI.getIncidents().then(setIncidents);
  }, []);

  const handleAck = async (id: string) => {
    await GuardianAPI.acknowledgeAlert(id);
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: 'ACKNOWLEDGED' } : a))
    );
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner & Safety SLA */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel rounded-2xl p-6 relative overflow-hidden">
        <div className="space-y-1 relative z-10">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-blue-400 pulse-live" />
            REAL-TIME RISK SURVEILLANCE
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Warehouse Operations Command Center
          </h1>
          <p className="text-xs text-gray-400 max-w-xl">
            Autonomous multi-camera tracking, 10-scenario behaviour detection, deterministic risk scoring, and evidence ledger.
          </p>
        </div>

        <div className="flex items-center gap-4 relative z-10">
          <div className="p-4 rounded-xl bg-black/40 border border-white/10 text-right">
            <div className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">
              Safety Score Index
            </div>
            <div className="text-3xl font-bold font-mono text-emerald-400">94.8%</div>
            <div className="text-[10px] text-emerald-400/80 flex items-center justify-end gap-1 mt-0.5">
              <TrendingUp className="w-3 h-3" /> +1.4% vs last week
            </div>
          </div>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Open Alerts"
          value={summary?.open_alerts ?? 3}
          subtitle="Requires supervisor ack"
          icon={AlertTriangle}
          variant="critical"
          trend="-2 from morning shift"
          trendDirection="down"
        />
        <StatCard
          title="Critical Incidents (24h)"
          value={summary?.critical_incidents ?? 6}
          subtitle="Drops & wet floor violations"
          icon={AlertOctagon}
          variant="warning"
          trend="+1 drop on Dock 01"
          trendDirection="up"
        />
        <StatCard
          title="Est. Prevented Loss"
          value={`$${(summary?.estimated_damage_loss_usd ?? 4850).toLocaleString()}`}
          subtitle="Based on product unit values"
          icon={DollarSign}
          variant="success"
          trend="85% claim avoidance"
          trendDirection="down"
        />
        <StatCard
          title="Mean Ack Latency"
          value={`${summary?.mean_time_to_acknowledge_seconds ?? 38.4}s`}
          subtitle="Target SLA < 60s"
          icon={Activity}
          variant="blue"
          trend="Optimal floor response"
          trendDirection="down"
        />
      </div>

      {/* Main Charts & Live Alert Feed Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Incident Trend & Behaviour Distribution */}
        <div className="lg:col-span-2 space-y-6">
          {/* Incident Timeline Area Chart */}
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">
                  Diurnal Risk & Incident Ingestion Trend
                </h3>
                <p className="text-xs text-gray-400">
                  Hourly incident spikes correlated with dock throughput
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
                <span className="w-3 h-3 rounded bg-blue-500/40 inline-block" />
                <span>Incident Count</span>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="colorInc" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#4B5563" fontSize={11} />
                  <YAxis stroke="#4B5563" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      borderColor: '#374151',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="incidents"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorInc)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Behaviour Anomaly Breakdown Pie & Bar */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="glass-panel rounded-xl p-5 space-y-3">
              <h4 className="text-xs font-bold font-mono text-gray-300 uppercase tracking-wider">
                Top Anomaly Scenarios
              </h4>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={summary?.behaviour_distribution ?? []}
                      dataKey="count"
                      nameKey="behaviour_code"
                      cx="50%"
                      cy="50%"
                      outerRadius={70}
                      innerRadius={45}
                      paddingAngle={4}
                    >
                      {(summary?.behaviour_distribution ?? []).map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#111827',
                        borderColor: '#374151',
                        borderRadius: '8px',
                        fontSize: '11px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-panel rounded-xl p-5 space-y-3">
              <h4 className="text-xs font-bold font-mono text-gray-300 uppercase tracking-wider">
                Spatial Risk Heatmap Density
              </h4>
              <div className="space-y-2.5">
                {(summary?.risk_heatmaps ?? []).map((h, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-300 font-mono">{h.zone_code}</span>
                      <span className="text-amber-400 font-mono font-bold">
                        {(h.intensity * 100).toFixed(0)}% Intensity
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-black/40 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-amber-500 to-red-500 rounded-full"
                        style={{ width: `${h.intensity * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Col: Real-time Alert Notification Stream */}
        <div className="space-y-4">
          <div className="glass-panel rounded-xl p-5 flex flex-col h-full">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <Flame className="w-4 h-4 text-red-400" />
                <h3 className="text-sm font-bold text-white">Live Alert Dispatch</h3>
              </div>
              <span className="text-[10px] font-mono text-gray-400">REAL-TIME</span>
            </div>

            <div className="flex-1 space-y-3 mt-4 overflow-y-auto max-h-[500px]">
              {alerts.length === 0 ? (
                <div className="text-center py-8 text-xs text-gray-500">
                  No active unacknowledged alerts.
                </div>
              ) : (
                alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-2 hover:border-white/15 transition-all"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <StatusBadge level={alert.alert_level} />
                      <span className="text-[10px] font-mono text-gray-500">
                        {new Date(alert.created_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>

                    <div className="text-xs text-gray-200 leading-snug">{alert.message}</div>

                    <div className="flex items-center justify-between pt-2 border-t border-white/5">
                      <span className="text-[10px] font-mono text-gray-400">
                        {alert.status === 'ACKNOWLEDGED' ? 'Ack by Lead' : 'Unacknowledged'}
                      </span>
                      {alert.status === 'OPEN' && (
                        <button
                          onClick={() => handleAck(alert.id)}
                          className="px-2 py-1 rounded bg-blue-600/30 text-blue-300 border border-blue-500/40 text-[10px] font-mono font-semibold hover:bg-blue-600/50 transition-colors"
                        >
                          Acknowledge
                        </button>
                      )}
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
