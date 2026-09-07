import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { DigitalTwinPage } from '../pages/DigitalTwinPage';

const { mockTopology, mockSummary } = vi.hoisted(() => ({
  mockTopology: {
    warehouse_id: 'wh-1',
    warehouse_name: 'North Hub',
    dimensions_meters: [120, 80, 12],
    zones: [
      {
        zone_id: 'zone-1',
        zone_code: 'DOCK_BAY_01',
        zone_name: 'Inbound Loading Bay 01',
        zone_type: 'LOADING_DOCK',
        polygon_points: [[0, 0], [30, 0], [30, 25], [0, 25]],
        risk_multiplier: 1.4,
      },
    ],
    cameras: [
      {
        camera_id: 'cam-1',
        camera_code: 'CAM-DOCK-01',
        camera_name: 'Inbound Dock High-Angle',
        position_xyz: [15, 2, 8.5],
        coverage_zones: ['DOCK_BAY_01'],
      },
    ],
    active_entity_count: 12,
  },
  mockSummary: {
    total_videos_processed: 128,
    total_incidents_detected: 21,
    critical_incidents: 3,
    open_alerts: 5,
    estimated_damage_loss_usd: 18400,
    mean_time_to_acknowledge_seconds: 48,
    behaviour_distribution: [{ behaviour_code: 'DROP', count: 8, percentage: 40, avg_risk_score: 94 }],
    risk_heatmaps: [
      { x_normalized: 0.25, y_normalized: 0.65, intensity: 0.85, zone_code: 'DOCK_BAY_01', incident_count: 7 },
    ],
    operational_health_status: 'DEGRADED',
  },
}));

vi.mock('../api/digital-twin', () => ({
  getDigitalTwinTopology: vi.fn().mockResolvedValue(mockTopology),
}));
vi.mock('../hooks/useDashboardSummary', () => ({
  useDashboardSummary: () => ({ data: mockSummary }),
}));
vi.mock('../hooks/useIncidents', () => ({
  useIncidents: () => ({ data: [] }),
}));

describe('digital twin page', () => {
  it('renders actual warehouse topology and risk heatmap data from the backend', async () => {
    render(<DigitalTwinPage />);

    await waitFor(() => {
      expect(screen.getByText(/North Hub/i)).toBeInTheDocument();
    });

    expect(screen.getAllByText('DOCK_BAY_01').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Inbound Loading Bay 01').length).toBeGreaterThan(0);
    expect(screen.getByText('Risk heatmap')).toBeInTheDocument();
    expect(screen.getAllByText(/incident density/i).length).toBeGreaterThan(0);
  });
});
