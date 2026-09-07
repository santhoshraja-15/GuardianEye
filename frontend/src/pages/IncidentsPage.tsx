import React, { useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Search, X } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { useIncidents } from '../hooks/useIncidents';
import { GuardianAPI } from '../services/api';
import { IncidentItem } from '../types';

const PAGE_SIZE = 25;

const statusTransitionMap: Record<string, string[]> = {
  DETECTED: ['ALERTED', 'ACKNOWLEDGED', 'UNDER_REVIEW', 'REJECTED'],
  ALERTED: ['ACKNOWLEDGED', 'UNDER_REVIEW', 'REJECTED'],
  ACKNOWLEDGED: ['UNDER_REVIEW', 'CONFIRMED', 'REJECTED'],
  UNDER_REVIEW: ['CONFIRMED', 'REJECTED', 'ACTION_TAKEN'],
  CONFIRMED: ['ACTION_TAKEN', 'RESOLVED'],
  REJECTED: ['UNDER_REVIEW'],
  ACTION_TAKEN: ['RESOLVED'],
  RESOLVED: ['UNDER_REVIEW'],
};

export const IncidentsPage: React.FC = () => {
  const queryClient = useQueryClient();
  // Shared cache — the same data AppLayout, the Dashboard, Evidence Vault,
  // etc. all read, instead of each page independently re-fetching the full
  // incident list.
  const { data: incidents = [] } = useIncidents();
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [transitionStatus, setTransitionStatus] = useState<string>('');
  const [transitionReason, setTransitionReason] = useState('');
  const [page, setPage] = useState(1);

  const availableStatuses = useMemo(() => {
    if (!selectedIncident) return [];
    return statusTransitionMap[selectedIncident.status] ?? [];
  }, [selectedIncident]);

  useEffect(() => {
    if (!selectedIncident) {
      setTransitionStatus('');
      setTransitionReason('');
      return;
    }

    setTransitionStatus(availableStatuses[0] ?? selectedIncident.status);
  }, [availableStatuses, selectedIncident]);

  const filtered = incidents.filter((inc) => {
    const matchSev = filterSeverity === 'ALL' || inc.severity === filterSeverity;
    const matchSearch =
      inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.incident_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.summary.toLowerCase().includes(searchQuery.toLowerCase());
    return matchSev && matchSearch;
  });

  // Reset to page 1 whenever the filtered set changes shape, so a search/
  // severity change never strands the user on an out-of-range empty page.
  useEffect(() => {
    setPage(1);
  }, [filterSeverity, searchQuery]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const paged = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  const handleUpdateStatus = async () => {
    if (!selectedIncident || !transitionReason.trim() || !transitionStatus) return;

    const updated = await GuardianAPI.updateIncidentStatus({
      incident_id: selectedIncident.id,
      new_status: transitionStatus,
      change_reason: transitionReason,
      resolution_notes: transitionReason,
    });

    queryClient.setQueryData<IncidentItem[]>(['incidents'], (prev) =>
      (prev ?? []).map((incident) => (incident.id === selectedIncident.id ? { ...incident, ...updated } : incident)),
    );
    setSelectedIncident((prev) => (prev ? { ...prev, ...updated } : prev));
    setTransitionReason('');
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Incident Board</h1>
          <p className="text-xs text-gray-400">
            Using the backend-supported incident lifecycle and audit trail only.
          </p>
        </div>
      </div>

      <div className="flex flex-col md:flex-row items-center justify-between gap-4 glass-panel rounded-xl p-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by code, title or summary"
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

      <div className="glass-panel rounded-xl overflow-hidden border border-white/10">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-black/60 border-b border-white/10 text-gray-400 font-mono uppercase tracking-wider text-[11px]">
              <tr>
                <th className="px-6 py-3.5">Incident Code</th>
                <th className="px-6 py-3.5">Severity</th>
                <th className="px-6 py-3.5">Description</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Assignee</th>
                <th className="px-6 py-3.5">Timestamp</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono">
              {paged.map((inc) => (
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
                    <StatusBadge level={inc.status} />
                  </td>
                  <td className="px-6 py-4 text-gray-300 font-sans">
                    {inc.assigned_to || <span className="text-gray-500 italic">Unassigned</span>}
                  </td>
                  <td className="px-6 py-4 text-gray-400 text-[11px]">
                    {new Date(inc.created_at).toLocaleString([], {
                      month: 'short',
                      day: 'numeric',
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

        {filtered.length > 0 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-white/10 px-6 py-3 text-xs text-gray-400">
            <span>
              Showing {(safePage - 1) * PAGE_SIZE + 1}–{Math.min(safePage * PAGE_SIZE, filtered.length)} of {filtered.length} incidents
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                aria-label="Previous page"
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                disabled={safePage <= 1}
                className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 font-mono text-[11px] text-gray-300 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ChevronLeft className="h-3.5 w-3.5" /> Prev
              </button>
              <span className="font-mono text-[11px] text-gray-500">
                Page {safePage} of {pageCount}
              </span>
              <button
                type="button"
                aria-label="Next page"
                onClick={() => setPage((prev) => Math.min(pageCount, prev + 1))}
                disabled={safePage >= pageCount}
                className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 font-mono text-[11px] text-gray-300 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                Next <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {selectedIncident && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-label={`Manage case ${selectedIncident.incident_code}`}
            className="bg-[#111827] border border-white/10 rounded-2xl w-full max-w-2xl p-6 space-y-5"
          >
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-blue-400 font-bold">{selectedIncident.incident_code}</span>
                  <StatusBadge level={selectedIncident.severity} />
                </div>
                <h3 className="text-base font-bold text-white mt-1">{selectedIncident.title}</h3>
              </div>
              <button onClick={() => setSelectedIncident(null)} className="p-1 rounded text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-[11px] text-gray-300 font-sans">
              <div className="rounded-lg bg-black/30 border border-white/5 p-3">
                <div className="text-gray-400 uppercase tracking-[0.12em] mb-1">Current status</div>
                <StatusBadge level={selectedIncident.status} />
              </div>
              <div className="rounded-lg bg-black/30 border border-white/5 p-3">
                <div className="text-gray-400 uppercase tracking-[0.12em] mb-1">Camera</div>
                <div className="text-white">{selectedIncident.camera_id ?? 'Not specified'}</div>
              </div>
              <div className="rounded-lg bg-black/30 border border-white/5 p-3">
                <div className="text-gray-400 uppercase tracking-[0.12em] mb-1">Zone</div>
                <div className="text-white">{selectedIncident.zone_id ?? 'Not specified'}</div>
              </div>
              <div className="rounded-lg bg-black/30 border border-white/5 p-3">
                <div className="text-gray-400 uppercase tracking-[0.12em] mb-1">Timestamp</div>
                <div className="text-white">{new Date(selectedIncident.created_at).toLocaleString()}</div>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 text-xs text-gray-300 space-y-1 font-sans">
              <div className="text-gray-400 font-mono text-[10px] uppercase">Incident Summary</div>
              <div>{selectedIncident.summary}</div>
            </div>

            <div className="space-y-3 font-sans">
              <label className="text-xs font-bold text-gray-300">Update incident status</label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs font-mono">
                {availableStatuses.map((status) => (
                  <button
                    key={status}
                    type="button"
                    onClick={() => setTransitionStatus(status)}
                    className={`py-2 px-3 rounded-lg border font-semibold ${
                      transitionStatus === status
                        ? 'bg-blue-600/30 text-blue-300 border-blue-500'
                        : 'bg-black/30 border-white/5 text-gray-400 hover:text-white'
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>

              <div>
                <label htmlFor="incident-audit-reason" className="text-xs text-gray-400">Audit reason</label>
                <textarea
                  id="incident-audit-reason"
                  value={transitionReason}
                  onChange={(e) => setTransitionReason(e.target.value)}
                  placeholder="Describe the update reason for the incident record..."
                  className="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50 mt-1"
                  rows={3}
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
              <button onClick={() => setSelectedIncident(null)} className="px-4 py-2 rounded-lg text-xs font-medium text-gray-400 hover:text-white">
                Cancel
              </button>
              <button
                onClick={handleUpdateStatus}
                disabled={!transitionReason.trim() || !transitionStatus}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-500 disabled:opacity-40 transition-colors"
              >
                Save status update
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
