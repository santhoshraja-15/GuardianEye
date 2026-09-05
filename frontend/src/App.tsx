import React, { useEffect, useState } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { CopilotChatDrawer } from './components/copilot/CopilotChatDrawer';
import { DashboardPage } from './pages/DashboardPage';
import { LiveStreamsPage } from './pages/LiveStreamsPage';
import { VideoAnalysisPage } from './pages/VideoAnalysisPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { EvidencePage } from './pages/EvidencePage';
import { PreventionStudioPage } from './pages/PreventionStudioPage';
import { DigitalTwinPage } from './pages/DigitalTwinPage';
import { DNAExplorerPage } from './pages/DNAExplorerPage';
import { GuardianAPI } from './services/api';
import { AlertItem } from './types';

export const App: React.FC = () => {
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  useEffect(() => {
    GuardianAPI.getAlerts().then(setAlerts);
  }, []);

  const openAlertsCount = alerts.filter((a) => a.status === 'OPEN').length;

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0B0F17] text-gray-100 flex">
        {/* Left Sidebar */}
        <Sidebar
          alertCount={openAlertsCount}
          onOpenCopilot={() => setIsCopilotOpen(true)}
        />

        {/* Main Content Area */}
        <div className="flex-1 ml-64 flex flex-col min-h-screen">
          {/* Top Header */}
          <Header
            openAlertsCount={openAlertsCount}
            onOpenCopilot={() => setIsCopilotOpen(true)}
            onOpenAlertsModal={() => {}}
          />

          {/* Page Routing Container */}
          <main className="flex-1 mt-16 p-8 overflow-y-auto">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/live" element={<LiveStreamsPage />} />
              <Route path="/analysis" element={<VideoAnalysisPage />} />
              <Route path="/incidents" element={<IncidentsPage />} />
              <Route path="/evidence" element={<EvidencePage />} />
              <Route path="/prevention" element={<PreventionStudioPage />} />
              <Route path="/digital-twin" element={<DigitalTwinPage />} />
              <Route path="/dna" element={<DNAExplorerPage />} />
            </Routes>
          </main>
        </div>

        {/* Grounded AI Copilot Conversational Drawer */}
        <CopilotChatDrawer
          isOpen={isCopilotOpen}
          onClose={() => setIsCopilotOpen(false)}
        />
      </div>
    </BrowserRouter>
  );
};

export default App;
