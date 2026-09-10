import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Camera,
  AlertTriangle,
  Gauge,
  FileCheck,
  ShieldCheck,
  ScanEye,
  Activity,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { useAppStore } from '../stores/app-store';
import { useDashboardSummary } from '../hooks/useDashboardSummary';
import './LandingPage.css';

const CONNECTION_LABEL: Record<string, string> = {
  LIVE: 'SYSTEM OPERATIONAL',
  DEGRADED: 'SYSTEM DEGRADED',
  RECONNECTING: 'RECONNECTING',
  OFFLINE: 'SYSTEM OFFLINE',
};

const DEMO_STEPS = [
  { label: 'MOTION DETECTED', detail: 'Frame activity crosses the detection threshold.' },
  { label: 'ENTITIES IDENTIFIED', detail: 'People, pallets, forklifts and cargo are tracked.' },
  { label: 'BEHAVIOUR ANALYZED', detail: 'Movement is matched against unsafe handling patterns.' },
  { label: 'EVENT CLASSIFIED', detail: 'A scored incident and prevention note are recorded.' },
];

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(query.matches);
    const handler = (event: MediaQueryListEvent) => setReduced(event.matches);
    query.addEventListener('change', handler);
    return () => query.removeEventListener('change', handler);
  }, []);
  return reduced;
}

function useLocalClock(): string {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
}

/**
 * GuardianEye marketing landing page.
 *
 * Additive entry surface mounted at /welcome (see src/app/AppShell.tsx) —
 * it does not replace `/`, which continues to serve the existing
 * DashboardPage exactly as before. Every number shown here that looks
 * like live telemetry (open alerts, incidents analyzed, videos processed,
 * connection state) is read from the same real endpoints the dashboard
 * uses (useDashboardSummary / useAppStore) rather than invented — where
 * data isn't loaded yet, fields render "—" instead of a fabricated value.
 */
export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const connectionState = useAppStore((state) => state.connectionState);
  const { data: summary } = useDashboardSummary();
  const clock = useLocalClock();
  const reducedMotion = usePrefersReducedMotion();
  const [showDemo, setShowDemo] = useState(false);
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (!showDemo || reducedMotion) {
      if (reducedMotion) setActiveStep(DEMO_STEPS.length - 1);
      return;
    }
    const timer = setInterval(() => {
      setActiveStep((step) => (step + 1) % DEMO_STEPS.length);
    }, 1500);
    return () => clearInterval(timer);
  }, [showDemo, reducedMotion]);

  const statusLabel = CONNECTION_LABEL[connectionState] ?? 'SYSTEM STATUS UNKNOWN';

  const stat = useMemo(
    () => ({
      videos: summary ? summary.total_videos_processed.toLocaleString() : '—',
      incidents: summary ? summary.total_incidents_detected.toLocaleString() : '—',
      openAlerts: summary ? summary.open_alerts.toLocaleString() : '—',
      health: summary?.operational_health_status ?? '—',
    }),
    [summary],
  );

  const enterPlatform = () => navigate('/');

  return (
    <div className="ge-landing">
      {/* ───────────────────────────── HERO ───────────────────────────── */}
      <section className="ge-hero" aria-label="GuardianEye introduction">
        <div className="ge-hero-image" role="img" aria-label="Warehouse floor monitored by GuardianEye" />
        <div className="ge-hero-wash" aria-hidden="true" />
        <div className="ge-hero-grid" aria-hidden="true" />

        <nav className="ge-hero-nav" aria-label="Landing navigation">
          <div className="ge-brand">
            <img src="/images/logo/logo_ge_icon.png" alt="GuardianEye" className="ge-brand-mark" />
            <div>
              <div className="ge-brand-name">
                Guardian<em>Eye</em>
              </div>
              <div className="ge-brand-tagline">AI RISK &amp; INTELLIGENCE</div>
            </div>
          </div>

          <div className="ge-nav-status" role="status">
            <span className="ge-status-dot" data-state={connectionState} aria-hidden="true" />
            {statusLabel}
          </div>

          <button type="button" className="ge-nav-cta" onClick={enterPlatform}>
            ENTER PLATFORM
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </nav>

        <div className="ge-hero-content">
          <div className="ge-eyebrow">
            <span className="ge-eyebrow-line" aria-hidden="true" />
            AI-POWERED WAREHOUSE INTELLIGENCE
          </div>

          <h1>
            SAFER
            <br />
            <em>OPERATIONS.</em>
            <br />
            BRIGHTER
            <br />
            TOMORROWS.
          </h1>

          <p className="ge-hero-description">
            Warehouse video, turned into detected behaviour, scored risk and prevention
            guidance — so unsafe handling is caught before it becomes a loss.
          </p>

          <div className="ge-hero-actions">
            <button type="button" className="ge-btn-primary" onClick={enterPlatform}>
              EXPLORE GUARDIANEYE
              <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
            <button
              type="button"
              className="ge-btn-secondary"
              aria-expanded={showDemo}
              aria-controls="ge-watch-system-demo"
              onClick={() => setShowDemo((open) => !open)}
            >
              WATCH SYSTEM
              <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>
        </div>

        <div className="ge-camera-card">
          <div className="ge-camera-top">
            <span className="ge-status-dot" data-state={connectionState} aria-hidden="true" />
            {statusLabel}
          </div>
          <div className="ge-camera-title">Warehouse Intelligence</div>
          <div className="ge-camera-data">
            <div>
              <small>VIDEOS ANALYZED</small>
              <strong>{stat.videos}</strong>
            </div>
            <div>
              <small>INCIDENTS FOUND</small>
              <strong>{stat.incidents}</strong>
            </div>
          </div>
        </div>

        <div className="ge-telemetry" aria-hidden="true">
          <div>
            <span>LOCAL TIME</span>
            <strong>{clock}</strong>
          </div>
          <div>
            <span>CONNECTION</span>
            <strong>{connectionState}</strong>
          </div>
          <div>
            <span>OPEN ALERTS</span>
            <strong>{stat.openAlerts}</strong>
          </div>
        </div>

        <div className="ge-intelligence-label" aria-hidden="true">
          <span className="ge-intelligence-line" />
          REAL-TIME WAREHOUSE VIDEO INTELLIGENCE
        </div>

        {showDemo && (
          <div className="ge-demo" id="ge-watch-system-demo" role="status" aria-label="How GuardianEye processes a clip">
            {DEMO_STEPS.map((step, index) => (
              <React.Fragment key={step.label}>
                {index > 0 && <ArrowRight className="w-3.5 h-3.5 ge-demo-arrow" aria-hidden="true" />}
                <span className={`ge-demo-step${index <= activeStep ? ' is-active' : ''}`}>
                  {step.label}
                </span>
              </React.Fragment>
            ))}
          </div>
        )}

        <div className="ge-bottom-strip">
          <div className="ge-strip-item">
            <div className="ge-strip-icon">
              <ScanEye className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <strong>DETECT</strong>
              <span>UNSAFE HANDLING</span>
            </div>
          </div>
          <div className="ge-strip-divider" aria-hidden="true" />
          <div className="ge-strip-item">
            <div className="ge-strip-icon">
              <Activity className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <strong>ANALYZE</strong>
              <span>REAL WAREHOUSE VIDEO</span>
            </div>
          </div>
          <div className="ge-strip-divider" aria-hidden="true" />
          <div className="ge-strip-item">
            <div className="ge-strip-icon">
              <ShieldAlert className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <strong>PREVENT</strong>
              <span>INCIDENT RECURRENCE</span>
            </div>
          </div>
          <div className="ge-strip-divider" aria-hidden="true" />
          <div className="ge-strip-item">
            <div className="ge-strip-icon">
              <ShieldCheck className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <strong>ENABLE</strong>
              <span>SAFER OPERATIONS</span>
            </div>
          </div>
        </div>

        <div className="ge-scroll-indicator" aria-hidden="true">
          <span>SCROLL TO EXPLORE</span>
          <div className="ge-scroll-line">
            <i />
          </div>
        </div>
      </section>

      {/* ───────────────────────── HOW IT SEES ─────────────────────────── */}
      <section className="ge-section" aria-labelledby="ge-how-it-sees-heading">
        <div className="ge-section-head">
          <div className="ge-section-eyebrow">
            <span className="ge-eyebrow-line" aria-hidden="true" />
            HOW IT SEES
          </div>
          <h2 id="ge-how-it-sees-heading">From raw footage to a scored, actionable event</h2>
          <p>
            Every clip GuardianEye processes moves through the same five stages —
            no step is skipped, and nothing is scored until it has actually been detected.
          </p>
        </div>

        <div className="ge-flow">
          {[
            ['01', 'OBSERVE', 'Warehouse video is broken down frame by frame.'],
            ['02', 'DETECT', 'People, pallets, forklifts and cargo are located and tracked.'],
            ['03', 'ANALYZE', 'Movement is matched against known unsafe handling patterns.'],
            ['04', 'UNDERSTAND', 'Each event is scored for severity and potential damage.'],
            ['05', 'RESPOND', 'Incidents, alerts and prevention guidance reach your team.'],
          ].map(([index, title, body]) => (
            <div className="ge-flow-step" key={title}>
              <div className="ge-flow-index">{index}</div>
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ─────────────────────── SAFETY INTELLIGENCE ───────────────────── */}
      <section className="ge-section" aria-labelledby="ge-capability-heading">
        <div className="ge-section-head">
          <div className="ge-section-eyebrow">
            <span className="ge-eyebrow-line" aria-hidden="true" />
            SAFETY INTELLIGENCE
          </div>
          <h2 id="ge-capability-heading">What GuardianEye already watches for</h2>
          <p>
            Built on real detection and risk-scoring models running today — not a roadmap.
          </p>
        </div>

        <div className="ge-capability-grid">
          <div className="ge-capability-card">
            <div className="ge-capability-icon">
              <Camera className="w-4 h-4" aria-hidden="true" />
            </div>
            <h3>Object &amp; People Detection</h3>
            <p>Tracks personnel, pallets, forklifts and cargo across warehouse footage.</p>
          </div>
          <div className="ge-capability-card">
            <div className="ge-capability-icon">
              <AlertTriangle className="w-4 h-4" aria-hidden="true" />
            </div>
            <h3>Behaviour Recognition</h3>
            <p>Flags unsafe handling — drops, rough handling, improper stacking and more.</p>
          </div>
          <div className="ge-capability-card">
            <div className="ge-capability-icon">
              <Gauge className="w-4 h-4" aria-hidden="true" />
            </div>
            <h3>Risk Scoring</h3>
            <p>Every incident is scored and traced back to the exact frame that caused it.</p>
          </div>
          <div className="ge-capability-card">
            <div className="ge-capability-icon">
              <FileCheck className="w-4 h-4" aria-hidden="true" />
            </div>
            <h3>Evidence &amp; Prevention</h3>
            <p>Every alert carries verifiable evidence and a root-cause recommendation.</p>
          </div>
        </div>
      </section>

      {/* ───────────────────────── ENTER PLATFORM ──────────────────────── */}
      <section className="ge-section" aria-labelledby="ge-cta-heading">
        <div className="ge-platform-cta">
          <div>
            <h2 id="ge-cta-heading">See it against your own warehouse footage.</h2>
            <p>Open the live dashboard, incident board and AI copilot — the real product, not a demo shell.</p>
          </div>
          <button type="button" className="ge-btn-primary" onClick={enterPlatform}>
            ENTER THE PLATFORM
            <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>
      </section>

      <footer className="ge-footer">
        <span>
          <strong>GuardianEye</strong> — AI Risk &amp; Intelligence
        </span>
        <span>Operational health: {stat.health}</span>
      </footer>
    </div>
  );
};
