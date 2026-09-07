import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { AnalyticsPage } from '../pages/AnalyticsPage';

const { mockSummary, mockIncidents } = vi.hoisted(() => ({
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
      { behaviour_code: 'STEP', count: 3, percentage: 15, avg_risk_score: 61 },
    ],
    risk_heatmaps: [
      { x_normalized: 0.25, y_normalized: 0.65, intensity: 0.85, zone_code: 'DOCK_BAY_01', incident_count: 7 },
      { x_normalized: 0.62, y_normalized: 0.38, intensity: 0.62, zone_code: 'HIGH_RACK_01', incident_count: 4 },
    ],
    operational_health_status: 'DEGRADED',
  },
  mockIncidents: [
  {
    id: 'inc-1',
    incident_code: 'INC-1001',
    behaviour_event_id: 'evt-1',
    warehouse_id: 'wh-1',
    zone_id: 'DOCK_BAY_01',
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
    {
      id: 'inc-2',
      incident_code: 'INC-1002',
      behaviour_event_id: 'evt-2',
      warehouse_id: 'wh-1',
      zone_id: 'HIGH_RACK_01',
      camera_id: 'cam-2',
      title: 'Drag in aisle',
      summary: 'Equipment drag near rack lane.',
      severity: 'HIGH',
      status: 'ACKNOWLEDGED',
      assigned_to: null,
      resolved_at: null,
      resolution_notes: null,
      created_at: '2024-01-03T15:20:00Z',
      updated_at: '2024-01-03T15:20:00Z',
    },
  ],
}));

vi.mock('../hooks/useDashboardSummary', () => ({
  useDashboardSummary: () => ({ data: mockSummary }),
}));
vi.mock('../hooks/useIncidents', () => ({
  useIncidents: () => ({ data: mockIncidents }),
}));

describe('analytics page', () => {
  it('renders backend-backed analytical storytelling and drill-down data', async () => {
    render(<AnalyticsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Operational analytics narrative/i)).toBeInTheDocument();
    });

    expect(screen.getByText('Behaviour trend')).toBeInTheDocument();
    expect(screen.getByText('Risk hotspot drill-down')).toBeInTheDocument();
    expect(screen.getByText('Operational filters')).toBeInTheDocument();
    expect(screen.getAllByText('DOCK_BAY_01').length).toBeGreaterThan(0);
  });
});
