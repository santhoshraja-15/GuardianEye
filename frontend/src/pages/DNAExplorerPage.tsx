import React, { useState } from 'react';
import {
  Activity,
  BarChart2,
  CheckCircle2,
  Dna,
  FileCode,
  Layers,
  Sparkles,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const FEATURE_NAMES = [
  'mean_spd', 'peak_spd', 'accel', 'horiz_bias', 'vert_bias',
  'idle_ratio', 'hold_ratio', 'move_ratio', 'fall_ratio', 'impact_ratio',
  'contact_rat', 'min_dist', 'max_iou', 'multi_ent', 'inter_cnt',
  'zone_risk', 'edge_prox', 'floor_cnt', 'elev_chg', 'tot_disp',
  'num_trans', 'osc_score', 'jerk_met', 'sud_stop', 'lost_rat',
  'drop_met', 'drag_met', 'throw_met', 'step_met', 'rough_met', 'tilt_ang', 'reserved'
];

const sampleDNAs = [
  {
    id: 'DNA-01',
    label: 'Track #14 (Drop Free-fall Signature)',
    signature: 'HOLDING -> FALLING -> IMPACT -> STATIONARY',
    vector: [0.35, 0.92, 0.78, 0.15, 0.88, 0.05, 0.25, 0.10, 0.35, 0.25, 0.30, 0.12, 0.45, 0.0, 0.2, 0.7, 0.4, 0.8, 0.65, 0.45, 0.4, 0.1, 0.7, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0],
    similarityDrop: 0.985,
    similarityDrag: 0.312,
    similarityThrow: 0.420,
    similarityStep: 0.180,
  },
  {
    id: 'DNA-02',
    label: 'Track #29 (Wet Floor Drag Signature)',
    signature: 'HOLDING -> CONTACT -> DRAGGING -> STATIONARY',
    vector: [0.65, 0.55, 0.30, 0.95, 0.08, 0.05, 0.45, 0.45, 0.0, 0.05, 0.85, 0.05, 0.35, 0.0, 0.4, 1.0, 0.8, 0.95, 0.05, 0.85, 0.3, 0.15, 0.2, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    similarityDrop: 0.290,
    similarityDrag: 0.978,
    similarityThrow: 0.340,
    similarityStep: 0.220,
  },
  {
    id: 'DNA-03',
    label: 'Track #08 (Ballistic Throw Signature)',
    signature: 'HOLDING -> RELEASED -> MOVING -> IMPACT',
    vector: [0.85, 0.98, 0.85, 0.88, 0.45, 0.05, 0.15, 0.65, 0.15, 0.0, 0.10, 0.85, 0.0, 0.0, 0.1, 0.5, 0.3, 0.4, 0.55, 0.95, 0.3, 0.1, 0.85, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    similarityDrop: 0.410,
    similarityDrag: 0.330,
    similarityThrow: 0.982,
    similarityStep: 0.140,
  },
];

export const DNAExplorerPage: React.FC = () => {
  const [selectedDNA, setSelectedDNA] = useState(sampleDNAs[0]);

  const chartData = selectedDNA.vector.map((val, idx) => ({
    feature: FEATURE_NAMES[idx] || `F${idx}`,
    value: val,
    index: idx,
  }));

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Behaviour DNA &amp; Kinematic Anomaly Fingerprints
          </h1>
          <p className="text-xs text-gray-400">
            32-dimensional normalized feature vectors capturing velocity, state durations, interactions, and zone risk dynamics.
          </p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Sample DNA Fingerprint Selector */}
        <div className="space-y-3">
          <div className="text-xs font-mono uppercase tracking-wider text-gray-400">
            Observed Incident Fingerprints
          </div>
          {sampleDNAs.map((dna) => (
            <div
              key={dna.id}
              onClick={() => setSelectedDNA(dna)}
              className={`glass-panel rounded-xl p-4 cursor-pointer border transition-all ${
                selectedDNA.id === dna.id
                  ? 'border-blue-500 shadow-xl shadow-blue-500/10'
                  : 'border-white/10 hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-blue-400">{dna.id}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold">
                  32D VECTOR
                </span>
              </div>
              <div className="text-xs font-semibold text-white mt-1.5">{dna.label}</div>
              <div className="text-[10px] font-mono text-gray-400 mt-2 truncate bg-black/40 p-1.5 rounded">
                {dna.signature}
              </div>
            </div>
          ))}
        </div>

        {/* Center & Right: 32D Feature Vector Bar & Similarity Breakdown */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">{selectedDNA.label}</h3>
                <div className="text-xs font-mono text-emerald-400 mt-0.5">
                  SEQUENCE: {selectedDNA.signature}
                </div>
              </div>
              <span className="px-3 py-1 rounded bg-blue-500/20 border border-blue-500/30 text-blue-300 font-mono text-xs font-bold">
                UNIT NORMALIZED
              </span>
            </div>

            {/* 32D Bar Chart */}
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                  <XAxis dataKey="feature" stroke="#4B5563" fontSize={9} interval={0} angle={-45} textAnchor="end" height={60} />
                  <YAxis stroke="#4B5563" fontSize={10} domain={[0, 1]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      borderColor: '#374151',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                  />
                  <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Golden Standard Cosine Similarity Matching */}
          <div className="glass-panel rounded-xl p-5 space-y-3">
            <h4 className="text-xs font-bold font-mono text-gray-300 uppercase tracking-wider">
              Golden Anomaly Template Cosine Match Scores
            </h4>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
              <div className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-1">
                <div className="text-[10px] text-gray-400">B01_DROP</div>
                <div className="text-lg font-bold text-red-400">
                  {(selectedDNA.similarityDrop * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-1">
                <div className="text-[10px] text-gray-400">B02_DRAG</div>
                <div className="text-lg font-bold text-amber-400">
                  {(selectedDNA.similarityDrag * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-1">
                <div className="text-[10px] text-gray-400">B03_THROW</div>
                <div className="text-lg font-bold text-purple-400">
                  {(selectedDNA.similarityThrow * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-1">
                <div className="text-[10px] text-gray-400">B11_STEP</div>
                <div className="text-lg font-bold text-blue-400">
                  {(selectedDNA.similarityStep * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
