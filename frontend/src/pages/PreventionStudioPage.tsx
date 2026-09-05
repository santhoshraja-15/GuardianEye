import React, { useState } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  Cpu,
  Layers,
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
import { StatusBadge } from '../components/common/StatusBadge';

export const PreventionStudioPage: React.FC = () => {
  // Counterfactual Simulation Interactive Controls
  const [observedRiskScore] = useState<number>(94.5);
  const [useMechanicalLift, setUseMechanicalLift] = useState<boolean>(true);
  const [twoHandedControl, setTwoHandedControl] = useState<boolean>(true);
  const [installFloorMatting, setInstallFloorMatting] = useState<boolean>(true);
  const [enforceHeightLimit, setEnforceHeightLimit] = useState<boolean>(true);

  // Compute deterministic simulated risk score
  let simScore = observedRiskScore;
  if (useMechanicalLift) simScore *= 0.4;
  if (twoHandedControl) simScore *= 0.6;
  if (installFloorMatting) simScore *= 0.85;
  if (enforceHeightLimit) simScore *= 0.75;
  simScore = Math.max(8.0, Math.round(simScore * 10) / 10);
  const riskDelta = Math.round((observedRiskScore - simScore) * 10) / 10;
  const reductionPct = Math.round((riskDelta / observedRiskScore) * 100);

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
                  Active Case RCA: INC-B01-4921 (Dock 01 Drop)
                </h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold">
                ERGONOMIC & PROCESS
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 space-y-2">
                <div className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">
                  Observed Physical Facts:
                </div>
                <ul className="text-xs text-gray-300 space-y-1.5 list-disc list-inside">
                  <li>Single-handed carton release during elevation transfer.</li>
                  <li>Fall height reached 85px (Safe limit: 30px).</li>
                  <li>Carton velocity prior to impact: 34.8 px/s.</li>
                </ul>
              </div>

              <div className="p-3.5 rounded-lg bg-black/40 border border-white/5 space-y-2">
                <div className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">
                  Inferred Root Factors:
                </div>
                <ul className="text-xs text-gray-300 space-y-1.5 list-disc list-inside">
                  <li>Operator shift hour &gt; 7.5h (Fatigue multiplier 1.15x).</li>
                  <li>Lack of vacuum lift aid for packages &gt; 10kg.</li>
                  <li>High dock throughput pace causing hurried handling.</li>
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
              {[
                {
                  priority: 'P0',
                  title: 'Deploy Vacuum Lift Aid at Dock 01',
                  type: 'EQUIPMENT_CHANGE',
                  reduction: '70% Risk Reduction',
                  desc: 'Provide vacuum suction mechanical assist for bulky electronics cartons.',
                },
                {
                  priority: 'P1',
                  title: 'Enforce Two-Handed Hold Standard Operating Procedure',
                  type: 'TRAINING & SOP',
                  reduction: '65% Risk Reduction',
                  desc: 'Conduct 10-minute shift ergonomic refresher and supervisor spot checks.',
                },
                {
                  priority: 'P1',
                  title: 'Install Anti-Slip Flooring & Drainage Matting',
                  type: 'ENVIRONMENTAL',
                  reduction: '80% Risk Reduction',
                  desc: 'Remediate wet floor areas near bay doors during rainy weather.',
                },
              ].map((rec, i) => (
                <div
                  key={i}
                  className="p-3.5 rounded-lg bg-black/30 border border-white/5 flex items-start justify-between gap-4 hover:border-white/15 transition-all"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/30">
                        {rec.priority}
                      </span>
                      <span className="text-xs font-bold text-white">{rec.title}</span>
                    </div>
                    <div className="text-xs text-gray-400">{rec.desc}</div>
                    <span className="text-[10px] font-mono text-gray-500">{rec.type}</span>
                  </div>

                  <div className="text-right">
                    <span className="px-2 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-bold whitespace-nowrap">
                      {rec.reduction}
                    </span>
                  </div>
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
                  label: 'Install High-Friction Dock Matting',
                  checked: installFloorMatting,
                  setter: setInstallFloorMatting,
                },
                {
                  label: 'Enforce Max Safe Drop Elevation Limit',
                  checked: enforceHeightLimit,
                  setter: setEnforceHeightLimit,
                },
              ].map((item, idx) => (
                <label
                  key={idx}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-black/40 border border-white/5 cursor-pointer hover:border-white/20 transition-all text-xs text-gray-200"
                >
                  <span>{item.label}</span>
                  <input
                    type="checkbox"
                    checked={item.checked}
                    onChange={(e) => item.setter(e.target.checked)}
                    className="w-4 h-4 rounded bg-gray-900 border-gray-700 text-blue-600 focus:ring-0 cursor-pointer"
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
