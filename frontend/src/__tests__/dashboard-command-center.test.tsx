import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../pages/DashboardPage';
import { vi } from 'vitest';

const { mockSummary, mockIncidents, mockAlerts, mockRisk } = vi.hoisted(() => ({
  mockSummary: {
    total_videos_processed: 128,
    total_incidents_detected: 21,
    critical_incidents: 3,
    open_alerts: 5,
    estimated_damage_loss_usd: 18400,
    mean_time_to_acknowledge_seconds: 48,
    behaviour_distribution: [
      { behaviour_code: 'DROP', count: 8, percentage: 40, avg_risk_score: 94 },
      { behaviour_code: 'DRAG', count: 5, percentage: 25, avg_risk_score: 82 },
    ],
    risk_heatmaps: [
      { x_normalized: 0.25, y_normalized: 0.65, intensity: 0.85, zone_code: 'BAY-1', incident_count: 7 },
    ],
    operational_health_status: 'DEGRADED',
  },
  mockIncidents: [
    {
      id: 'inc-1',
      incident_code: 'INC-1001',
      behaviour_event_id: 'evt-1',
      warehouse_id: 'wh-1',
      zone_id: 'zone-1',
      camera_id: 'cam-1',
      title: 'Carton drop in loading bay',
      summary: 'Heavy carton dropped from lift.',
      severity: 'CRITICAL',
      status: 'DETECTED',
      assigned_to: null,
      resolved_at: null,
      resolution_notes: null,
      created_at: '2024-01-01T10:15:00Z',
      updated_at: '2024-01-01T10:15:00Z',
    },
  ],
  mockAlerts: [
    {
      id: 'alert-1',
      behaviour_event_id: 'evt-1',
      zone_id: 'zone-1',
      alert_level: 'CRITICAL',
      message: 'Heavy object drop detected near dock',
      status: 'OPEN',
      deduplication_key: 'dedupe-1',
      acknowledged_by: null,
      acknowledged_at: null,
      created_at: '2024-01-01T10:16:00Z',
    },
  ],
  mockRisk: {
    id: 'risk-1',
    behaviour_event_id: 'evt-1',
    risk_score: 92,
    risk_level: 'CRITICAL',
    is_actionable: true,
    recommended_action: 'Stop traffic and inspect bay.',
    factors: ['fall_height', 'loading_speed'],
  },
}));

vi.mock('../hooks/useDashboardSummary', () => ({
  useDashboardSummary: () => ({ data: mockSummary }),
}));
vi.mock('../hooks/useIncidents', () => ({
  useIncidents: () => ({ data: mockIncidents }),
}));
vi.mock('../hooks/useAlerts', () => ({
  useAlerts: () => ({ data: mockAlerts }),
}));
vi.mock('../api/alerts', () => ({
  acknowledgeAlert: vi.fn(),
}));
// Referenced only to keep the mockRisk fixture from being flagged unused —
// this page doesn't fetch a standalone risk assessment today.
void mockRisk;

describe('command center page', () => {
  it('renders the real command-center intelligence panels using backend data', async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <MemoryRouter initialEntries={['/']}>
        <QueryClientProvider client={queryClient}>
          <DashboardPage />
        </QueryClientProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Command Center')).toBeInTheDocument();
    });

    expect(screen.getByText('Risk Intelligence')).toBeInTheDocument();
    expect(screen.getByText('Live Situation View')).toBeInTheDocument();
    expect(screen.getByText('Open Incident Queue')).toBeInTheDocument();
    expect(screen.getByText('Behaviour Trends')).toBeInTheDocument();
    expect(screen.getByText('High-Risk Zones')).toBeInTheDocument();
    expect(screen.getByText('Camera Health')).toBeInTheDocument();
    expect(screen.getByText('Current Risk')).toBeInTheDocument();
  });
});
