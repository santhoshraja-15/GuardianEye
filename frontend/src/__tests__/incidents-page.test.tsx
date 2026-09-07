import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { IncidentsPage } from '../pages/IncidentsPage';
import { beforeEach, vi } from 'vitest';

const { mockIncidents } = vi.hoisted(() => ({
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
      severity: 'CRITICAL' as const,
      status: 'DETECTED' as const,
      assigned_to: null,
      resolved_at: null,
      resolution_notes: null,
      created_at: '2024-01-01T10:15:00Z',
      updated_at: '2024-01-01T10:15:00Z',
    },
  ],
}));

const { mockUseIncidents } = vi.hoisted(() => ({ mockUseIncidents: vi.fn() }));
vi.mock('../hooks/useIncidents', () => ({
  useIncidents: mockUseIncidents,
}));
vi.mock('../services/api', () => ({
  GuardianAPI: {
    updateIncidentStatus: vi.fn().mockResolvedValue({
      ...mockIncidents[0],
      status: 'UNDER_REVIEW',
    }),
  },
}));

describe('incidents page', () => {
  beforeEach(() => {
    mockUseIncidents.mockReturnValue({ data: mockIncidents });
  });

  it('shows status transitions supported by the backend contract for the selected incident', async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <IncidentsPage />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText('Incident Board')).toBeInTheDocument();
    });

    screen.getByRole('button', { name: 'Manage Case' }).click();

    await waitFor(() => {
      expect(screen.getByText('Update incident status')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: 'ALERTED' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'ACKNOWLEDGED' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'UNDER_REVIEW' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'REJECTED' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'ACTION_TAKEN' })).not.toBeInTheDocument();
  });

  it('paginates a large incident list instead of rendering every row at once', async () => {
    const manyIncidents = Array.from({ length: 60 }, (_, i) => ({
      ...mockIncidents[0],
      id: `inc-${i}`,
      incident_code: `INC-${1000 + i}`,
      title: `Incident ${i}`,
    }));
    mockUseIncidents.mockReturnValue({ data: manyIncidents });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <IncidentsPage />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText('Incident Board')).toBeInTheDocument();
    });

    // Page 1 shows the first 25 of 60, not all 60 rows.
    expect(screen.getByText('INC-1000')).toBeInTheDocument();
    expect(screen.getByText('INC-1024')).toBeInTheDocument();
    expect(screen.queryByText('INC-1025')).not.toBeInTheDocument();
    expect(screen.getByText('Showing 1–25 of 60 incidents')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Previous page' })).toBeDisabled();

    screen.getByRole('button', { name: 'Next page' }).click();

    await waitFor(() => {
      expect(screen.getByText('INC-1025')).toBeInTheDocument();
    });
    expect(screen.queryByText('INC-1000')).not.toBeInTheDocument();
    expect(screen.getByText('Showing 26–50 of 60 incidents')).toBeInTheDocument();
  });
});
