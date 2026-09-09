import React, { useEffect, useState } from 'react';
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Lightbulb,
  Percent,
  Play,
  RotateCcw,
  ShieldAlert,
  Sliders,
  Sparkles,
  TrendingDown,
  Wrench,
} from 'lucide-react';
import { useIncidents } from '../hooks/useIncidents';
import { GuardianAPI } from '../services/api';
import { PreventionRuleItem, RecommendationItem, RootCauseItem } from '../types';

export const PreventionStudioPage: React.FC = () => {
  const { data: incidents = [] } = useIncidents();
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [rules, setRules] = useState<PreventionRuleItem[]>([]);
  const [rootCauses, setRootCauses] = useState<RootCauseItem[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);

  // Counterfactual Simulation Interactive Controls
  const [observedRiskScore, setObservedRiskScore] = useState<number>(88.0);
  const [useMechanicalLift, setUseMechanicalLift] = useState<boolean>(true);
  const [twoHandedControl, setTwoHandedControl] = useState<boolean>(true);
  const [installFloorMatting, setInstallFloorMatting] = useState<boolean>(true);
  const [enforceHeightLimit, setEnforceHeightLimit] = useState<boolean>(true);

  useEffect(() => {
    GuardianAPI.getRecommendations().then(setRecommendations).catch(() => {});
    GuardianAPI.getPreventionRules().then(setRules).catch(() => {});
    GuardianAPI.getRootCauses().then(setRootCauses).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedIncidentId && incidents.length > 0) {
      setSelectedIncidentId(incidents[0].id);
    }
  }, [incidents, selectedIncidentId]);

  const selectedIncident = incidents.find((inc) => inc.id === selectedIncidentId) ?? incidents[0];
  const activeRootCause = rootCauses.find((rc) => rc.incident_id === selectedIncident?.id) ?? rootCauses[0];
  const activeRecs = recommendations.filter((r) => r.incident_id === selectedIncident?.id);
  const displayRecs = activeRecs.length > 0 ? activeRecs : recommendations;

  // Compute deterministic simulated risk score
  let simScore = observedRiskScore;
  if (useMechanicalLift) simScore *= 0.4;
  if (twoHandedControl) simScore *= 0.6;
  if (installFloorMatting) simScore *= 0.85;
  if (enforceHeightLimit) simScore *= 0.75;
  simScore = Math.max(8.0, Math.round(simScore * 10) / 10);
  const riskDelta = Math.round((observedRiskScore - simScore) * 10) / 10;
  const reductionPct = Math.round((riskDelta / observedRiskScore) * 100);

  let observedFacts: string[] = [];
  let inferredFactors: string[] = [];
  if (activeRootCause) {
    try {
      observedFacts = JSON.parse(activeRootCause.observed_factors);
      inferredFactors = JSON.parse(activeRootCause.inferred_factors);
    } catch {
      observedFacts = [activeRootCause.observed_factors];
      inferredFactors = [activeRootCause.inferred_factors];
    }
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Prevention Studio & Counterfactual Simulator
          </h1>
          <p className="text-xs text-gray-400">
            Factual Root Cause Analysis (RCA), corrective action plans, and what-if risk delta simulations.
          </p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: RCA & Recommendations */}
        <div className="lg:col-span-2 space-y-6">
          {/* Root Cause Analysis Card */}
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-white">
                  Active Case RCA: {selectedIncident ? `${selectedIncident.incident_code} (${selectedIncident.title})` : 'Incident Investigation'}
                </h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold">
                {activeRootCause?.cause_category ?? 'ERGONOMIC & PROCESS'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 space-y-2">
                <div className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">
                  Observed Physical Facts:
                </div>
                <ul className="text-xs text-gray-300 space-y-1.5 list-disc list-inside">
                  {observedFacts.length > 0 ? (
                    observedFacts.map((fact, idx) => <li key={idx}>{fact}</li>)
                  ) : (
                    <>
                      <li>Single-handed carton release during elevation transfer.</li>
                      <li>Fall height reached 85px (Safe limit: 30px).</li>
                      <li>Carton velocity prior to impact: 34.8 px/s.</li>
                    </>
                  )}
                </ul>
              </div>

              <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 space-y-2">
                <div className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">
                  Inferred Root Factors:
                </div>
                <ul className="text-xs text-gray-300 space-y-1.5 list-disc list-inside">
                  {inferredFactors.length > 0 ? (
                    inferredFactors.map((fact, idx) => <li key={idx}>{fact}</li>)
                  ) : (
                    <>
                      <li>Operator shift duration &gt; 7.5h (Fatigue multiplier 1.15x).</li>
                      <li>Lack of vacuum lift assist for packages &gt; 15kg.</li>
                      <li>High dock throughput pace causing hurried manual handling.</li>
                    </>
                  )}
                </ul>
              </div>
            </div>
          </div>

          {/* Corrective Action Recommendations */}
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 border-b border-white/10 pb-3">
              <Lightbulb className="w-4 h-4 text-yellow-400" />
              <h3 className="text-sm font-bold text-white">
                Prioritized Corrective Recommendations
              </h3>
            </div>

            <div className="space-y-3">
              {displayRecs.length > 0 ? (
                displayRecs.map((rec) => (
                  <div
                    key={rec.id}
                    className="p-3.5 rounded-lg bg-black/30 border border-white/5 flex items-start justify-between gap-4 hover:border-white/15 transition-all"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                          {rec.prevention_type}
                        </span>
                        <span className="text-xs font-bold text-white">{rec.action_title}</span>
                      </div>
                      <div className="text-xs text-gray-400">{rec.description}</div>
                      <span className="text-[10px] font-mono text-gray-500">Status: {rec.status}</span>
                    </div>

                    <div className="text-right">
                      <span className="px-2 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-bold whitespace-nowrap">
                        {rec.estimated_risk_reduction_pct}% Risk Reduction
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-4 rounded-lg border border-dashed border-white/10 text-xs text-gray-400">
                  No specific corrective actions logged for this case.
                </div>
              )}
            </div>
          </div>

          {/* Warehouse SOP Rules Matrix */}
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 border-b border-white/10 pb-3">
              <BookOpen className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">
                Active Warehouse Safety Standard Operating Procedures (SOPs)
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {rules.map((rule) => (
                <div
                  key={rule.behaviour_code}
                  className="p-3 rounded-lg bg-black/30 border border-white/5 space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{rule.rule_name}</span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-red-500/20 text-red-300">
                      {rule.severity_default}
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-400">{rule.description}</p>
                  <div className="text-[10px] font-mono text-blue-400/80">{rule.sop_citation}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Interactive What-If Counterfactual Simulator */}
        <div className="space-y-4">
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-bold text-white">What-If Simulator</h3>
              </div>
              <span className="text-[10px] font-mono text-blue-400">PHYSICAL MODEL</span>
            </div>

            {/* Risk Delta Score Comparison */}
            <div className="p-4 rounded-xl bg-black/60 border border-white/10 text-center space-y-2">
              <div className="flex items-center justify-around">
                <div>
                  <div className="text-[10px] font-mono text-gray-400">OBSERVED RISK</div>
                  <div className="text-2xl font-bold font-mono text-red-400">
                    {observedRiskScore}
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-500" />
                <div>
                  <div className="text-[10px] font-mono text-gray-400">SIMULATED RISK</div>
                  <div className="text-2xl font-bold font-mono text-emerald-400">{simScore}</div>
                </div>
              </div>

              <div className="pt-2 border-t border-white/5 flex items-center justify-center gap-2 text-xs font-mono text-emerald-400 font-bold">
                <TrendingDown className="w-4 h-4" />
                <span>
                  -{riskDelta} RISK DELTA ({reductionPct}% REDUCTION)
                </span>
              </div>
            </div>

            {/* Interactive Toggle Controls */}
            <div className="space-y-3 pt-2">
              <div className="text-xs font-mono text-gray-400 uppercase tracking-wider">
                Simulated Safety Interventions:
              </div>

              {[
                {
                  label: 'Use Vacuum Lift / Mechanical Assist',
                  checked: useMechanicalLift,
                  setter: setUseMechanicalLift,
                },
                {
                  label: 'Enforce 2-Handed Controlled Handling',
                  checked: twoHandedControl,
                  setter: setTwoHandedControl,
                },
                {
                  label: 'Install Anti-Slip Dock Matting',
                  checked: installFloorMatting,
                  setter: setInstallFloorMatting,
                },
                {
                  label: 'Enforce Stacking Tier Limit (< 5 layers)',
                  checked: enforceHeightLimit,
                  setter: setEnforceHeightLimit,
                },
              ].map((ctrl, i) => (
                <label
                  key={i}
                  className="flex items-center justify-between p-3 rounded-lg bg-black/30 border border-white/5 cursor-pointer hover:border-white/15 transition-all"
                >
                  <span className="text-xs text-gray-300 font-medium">{ctrl.label}</span>
                  <input
                    type="checkbox"
                    checked={ctrl.checked}
                    onChange={(e) => ctrl.setter(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
                  />
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
