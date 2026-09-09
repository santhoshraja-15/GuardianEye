import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

const DashboardPage = lazy(() =>
  import('../pages/DashboardPage').then((module) => ({ default: module.DashboardPage })),
);
const LiveStreamsPage = lazy(() =>
  import('../pages/LiveStreamsPage').then((module) => ({ default: module.LiveStreamsPage })),
);
const VideoAnalysisPage = lazy(() =>
  import('../pages/VideoAnalysisPage').then((module) => ({ default: module.VideoAnalysisPage })),
);
const IncidentsPage = lazy(() =>
  import('../pages/IncidentsPage').then((module) => ({ default: module.IncidentsPage })),
);
const EvidencePage = lazy(() =>
  import('../pages/EvidencePage').then((module) => ({ default: module.EvidencePage })),
);
const PreventionStudioPage = lazy(() =>
  import('../pages/PreventionStudioPage').then((module) => ({ default: module.PreventionStudioPage })),
);
const DigitalTwinPage = lazy(() =>
  import('../pages/DigitalTwinPage').then((module) => ({ default: module.DigitalTwinPage })),
);
const DNAExplorerPage = lazy(() =>
  import('../pages/DNAExplorerPage').then((module) => ({ default: module.DNAExplorerPage })),
);
const AnalyticsPage = lazy(() =>
  import('../pages/AnalyticsPage').then((module) => ({ default: module.AnalyticsPage })),
);
const HumanReviewPage = lazy(() =>
  import('../pages/HumanReviewPage').then((module) => ({ default: module.HumanReviewPage })),
);

export function AppRoutes() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-gray-400">Loading workspace…</div>}>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/live" element={<LiveStreamsPage />} />
        <Route path="/analysis" element={<VideoAnalysisPage />} />
        <Route path="/incidents" element={<IncidentsPage />} />
        <Route path="/evidence" element={<EvidencePage />} />
        <Route path="/prevention" element={<PreventionStudioPage />} />
        <Route path="/digital-twin" element={<DigitalTwinPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/dna" element={<DNAExplorerPage />} />
        <Route path="/human-review" element={<HumanReviewPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

