import React, { useState } from 'react';
import {
  CheckCircle2,
  Copy,
  Download,
  Eye,
  FileCheck,
  Hash,
  Layers,
  Lock,
  Shield,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';

const sampleEvidencePackages = [
  {
    incidentId: 'INC-B01-4921',
    title: 'Drop Impact Evidence Manifest',
    timestamp: '2026-09-05 16:42:10 UTC',
    clipPath: '/storage/clips/vid-01_incident_INC-B01-4921.mp4',
    clipSha256: '9f83c1b698e6b36a73c242093d58ef8a90623a84e2a8740f907604b1f481c4e7',
    snapshotPath: '/storage/snapshots/vid-01_keyframe.jpg',
    snapshotSha256: 'b4a8e29d71c8901f4a9b7520e5c9a1d3f6b4e7a89201c345f8e90a1b2c3d4e5f',
    preEventSec: 3.0,
    postEventSec: 3.0,
    verified: true,
    keyframes: [
      {
        frameIndex: 12,
        timeSec: 0.4,
        hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        primaryTrack: 'Carton #14 (Speed: 34.8 px/s)',
      },
      {
        frameIndex: 25,
        timeSec: 0.83,
        hash: 'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb',
        primaryTrack: 'Carton #14 (Impact deceleration on floor)',
      },
    ],
  },
  {
    incidentId: 'INC-B15-8834',
    title: 'Wet Floor Dragging Evidence Manifest',
    timestamp: '2026-09-05 15:30:00 UTC',
    clipPath: '/storage/clips/vid-02_incident_INC-B15-8834.mp4',
    clipSha256: '4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce',
    snapshotPath: '/storage/snapshots/vid-02_keyframe.jpg',
    snapshotSha256: '185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969',
    preEventSec: 3.0,
    postEventSec: 3.0,
    verified: true,
    keyframes: [
      {
        frameIndex: 30,
        timeSec: 1.0,
        hash: '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae',
        primaryTrack: 'Carton #29 (Horizontal Velocity: 18.4 px/s)',
      },
    ],
  },
];

export const EvidencePage: React.FC = () => {
  const [selectedPkg, setSelectedPkg] = useState(sampleEvidencePackages[0]);
  const [copied, setCopied] = useState(false);

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Forensic Evidence Vault & Cryptographic Ledger
          </h1>
          <p className="text-xs text-gray-400">
            Immutable SHA-256 tamper-proof checksums for video clips, keyframes, and bounding box coordinates.
          </p>
        </div>

        <button className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-500 transition-colors">
          <Download className="w-4 h-4" />
          <span>Export Compliance ZIP Package</span>
        </button>
      </div>

      {/* Main Evidence Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Packages List */}
        <div className="space-y-3">
          <div className="text-xs font-mono uppercase tracking-wider text-gray-400">
            Verified Evidence Packages
          </div>
          {sampleEvidencePackages.map((pkg) => (
            <div
              key={pkg.incidentId}
              onClick={() => setSelectedPkg(pkg)}
              className={`glass-panel rounded-xl p-4 cursor-pointer border transition-all ${
                selectedPkg.incidentId === pkg.incidentId
                  ? 'border-blue-500 shadow-lg shadow-blue-500/10'
                  : 'border-white/10 hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-blue-400">
                  {pkg.incidentId}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 font-bold">
                  <CheckCircle2 className="w-3 h-3" />
                  SHA-256 VERIFIED
                </span>
              </div>
              <div className="text-xs font-semibold text-white mt-1.5">{pkg.title}</div>
              <div className="text-[10px] font-mono text-gray-500 mt-2">{pkg.timestamp}</div>
            </div>
          ))}
        </div>

        {/* Center & Right: Selected Evidence Inspector */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-panel rounded-xl p-6 space-y-5">
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div>
                <div className="text-xs font-mono text-gray-400">PACKAGE MANIFEST:</div>
                <h2 className="text-base font-bold text-white mt-0.5">{selectedPkg.title}</h2>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
                <Lock className="w-3.5 h-3.5" />
                <span>TAMPER-PROOF LEDGER SEALED</span>
              </div>
            </div>

            {/* Cryptographic Checksum Cards */}
            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Hash className="w-3.5 h-3.5 text-blue-400" />
                    Video Clip SHA-256:
                  </span>
                  <button
                    onClick={() => handleCopyHash(selectedPkg.clipSha256)}
                    className="text-blue-400 hover:text-blue-300 flex items-center gap-1 text-[11px]"
                  >
                    <Copy className="w-3 h-3" />
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <div className="font-mono text-xs text-emerald-400 break-all select-all">
                  {selectedPkg.clipSha256}
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-gray-400 flex items-center gap-1.5">
                    <Hash className="w-3.5 h-3.5 text-purple-400" />
                    Primary Keyframe Snapshot SHA-256:
                  </span>
                  <button
                    onClick={() => handleCopyHash(selectedPkg.snapshotSha256)}
                    className="text-purple-400 hover:text-purple-300 flex items-center gap-1 text-[11px]"
                  >
                    <Copy className="w-3 h-3" />
                    Copy
                  </button>
                </div>
                <div className="font-mono text-xs text-purple-300 break-all select-all">
                  {selectedPkg.snapshotSha256}
                </div>
              </div>
            </div>

            {/* Keyframe Overlays Inspector */}
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400">
                Keyframe Evidence Overlays ({selectedPkg.keyframes.length} Captured)
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {selectedPkg.keyframes.map((kf, i) => (
                  <div key={i} className="p-3 rounded-lg bg-black/30 border border-white/5 space-y-2">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="text-blue-400 font-bold">FRAME #{kf.frameIndex}</span>
                      <span className="text-gray-400">{kf.timeSec}s</span>
                    </div>
                    <div className="text-xs text-gray-200 font-sans">{kf.primaryTrack}</div>
                    <div className="text-[9px] font-mono text-gray-500 truncate select-all">
                      {kf.hash}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
