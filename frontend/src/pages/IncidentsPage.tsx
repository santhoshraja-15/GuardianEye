import React, { useEffect, useState } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  Clock,
  Filter,
  Layers,
  MessageSquare,
  Search,
  Shield,
  User,
  X,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { GuardianAPI } from '../services/api';
import { IncidentItem, SeverityLevel } from '../types';

export const IncidentsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [transitionStatus, setTransitionStatus] = useState<string>('UNDER_REVIEW');
  const [transitionReason, setTransitionReason] = useState('');

  useEffect(() => {
    GuardianAPI.getIncidents().then(setIncidents);
  }, []);

  const filtered = incidents.filter((inc) => {
    const matchSev = filterSeverity === 'ALL' || inc.severity === filterSeverity;
    const matchSearch =
      inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.incident_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.summary.toLowerCase().includes(searchQuery.toLowerCase());
    return matchSev && matchSearch;
  });

  const handleUpdateStatus = () => {
    if (!selectedIncident || !transitionReason.trim()) return;
    setIncidents((prev) =>
      prev.map((i) =>
        i.id === selectedIncident.id
          ? {
              ...i,
              status: transitionStatus as any,
              resolution_notes: transitionReason,
            }
          : i
      )
    );
    setSelectedIncident(null);
    setTransitionReason('');
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Incident Lifecycle & Case Management
          </h1>
          <p className="text-xs text-gray-400">
            Audit-tracked resolution workflow: DETECTED -&gt; ALERTED -&gt; UNDER_REVIEW -&gt; ACTION_TAKEN -&gt; RESOLVED.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 glass-panel rounded-xl p-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by code, description..."
            className="w-full bg-[#111827] border border-white/10 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <span className="text-xs text-gray-400 font-mono">Severity:</span>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                filterSeverity === sev
                  ? 'bg-blue-600/30 text-blue-300 border border-blue-500/50'
                  : 'bg-white/5 text-gray-400 border border-white/5 hover:text-white'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Incident List Table */}
      <div className="glass-panel rounded-xl overflow-hidden border border-white/10">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-black/60 border-b border-white/10 text-gray-400 font-mono uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-6 py-3.5">Incident Code</th>
                <th className="px-6 py-3.5">Severity</th>
                <th className="px-6 py-3.5">Description & Title</th>
                <th className="px-6 py-3.5">Lifecycle Status</th>
                <th className="px-6 py-3.5">Assignee</th>
                <th className="px-6 py-3.5">Timestamp</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono">
              {filtered.map((inc) => (
                <tr key={inc.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 font-bold text-blue-400">{inc.incident_code}</td>
                  <td className="px-6 py-4">
                    <StatusBadge level={inc.severity} />
                  </td>
                  <td className="px-6 py-4 font-sans max-w-sm">
                    <div className="font-semibold text-white">{inc.title}</div>
                    <div className="text-gray-400 text-[11px] truncate mt-0.5">{inc.summary}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold">
                      {inc.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-300 font-sans">
                    {inc.assigned_to || <span className="text-gray-500 italic">Unassigned</span>}
                  </td>
                  <td className="px-6 py-4 text-gray-400 text-[11px]">
                    {new Date(inc.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => setSelectedIncident(inc)}
                      className="px-3 py-1.5 rounded bg-blue-600/20 text-blue-400 border border-blue-500/30 hover:bg-blue-600/40 transition-colors"
                    >
                      Manage Case
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Incident Case Management Modal */}
      {selectedIncident && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-white/10 rounded-2xl w-full max-w-2xl p-6 space-y-5">
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-blue-400 font-bold">
                    {selectedIncident.incident_code}
                  </span>
                  <StatusBadge level={selectedIncident.severity} />
                </div>
                <h3 className="text-base font-bold text-white mt-1">{selectedIncident.title}</h3>
              </div>
              <button
                onClick={() => setSelectedIncident(null)}
                className="p-1 rounded text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 text-xs text-gray-300 space-y-1 font-sans">
              <div className="text-gray-400 font-mono text-[10px] uppercase">Incident Summary:</div>
              <div>{selectedIncident.summary}</div>
            </div>

            {/* Lifecycle Transition Controls */}
            <div className="space-y-3 font-sans">
              <label className="text-xs font-bold text-gray-300">
                Update Case Status (Audit Trail Logging):
              </label>
              <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                {['UNDER_REVIEW', 'ACTION_TAKEN', 'RESOLVED'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setTransitionStatus(st)}
                    className={`py-2 px-3 rounded-lg border font-semibold ${
                      transitionStatus === st
                        ? 'bg-blue-600/30 text-blue-300 border-blue-500'
                        : 'bg-black/30 border-white/5 text-gray-400 hover:text-white'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>

              <div>
                <label className="text-xs text-gray-400">Resolution / Audit Rationale:</label>
                <textarea
                  value={transitionReason}
                  onChange={(e) => setTransitionReason(e.target.value)}
                  placeholder="Enter corrective action taken or justification for state change..."
                  className="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50 mt-1"
                  rows={3}
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
              <button
                onClick={() => setSelectedIncident(null)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-gray-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateStatus}
                disabled={!transitionReason.trim()}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-500 disabled:opacity-40 transition-colors"
              >
                Save &amp; Commit Audit Entry
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
