import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthStatusPage } from '../components/auth/AuthStatusPage';
import { LoginPage } from '../components/auth/LoginPage';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { SessionExpiredPage } from '../components/auth/SessionExpiredPage';
import { UnauthorizedPage } from '../components/auth/UnauthorizedPage';

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
        <Route path="/login" element={<LoginPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route path="/session-expired" element={<SessionExpiredPage />} />
        <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/live" element={<ProtectedRoute><LiveStreamsPage /></ProtectedRoute>} />
        <Route path="/analysis" element={<ProtectedRoute><VideoAnalysisPage /></ProtectedRoute>} />
        <Route path="/incidents" element={<ProtectedRoute><IncidentsPage /></ProtectedRoute>} />
        <Route path="/evidence" element={<ProtectedRoute><EvidencePage /></ProtectedRoute>} />
        <Route path="/prevention" element={<ProtectedRoute><PreventionStudioPage /></ProtectedRoute>} />
        <Route path="/digital-twin" element={<ProtectedRoute><DigitalTwinPage /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><AnalyticsPage /></ProtectedRoute>} />
        <Route path="/dna" element={<ProtectedRoute><DNAExplorerPage /></ProtectedRoute>} />
        <Route path="/human-review" element={<ProtectedRoute><HumanReviewPage /></ProtectedRoute>} />
        <Route
          path="/session"
          element={
            <ProtectedRoute allowedRoles={['Admin', 'Supervisor']}>
              <AuthStatusPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Suspense>
  );
}
