import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { vi } from 'vitest';
import { AppLayout } from '../layouts/AppLayout';
import { useSessionStore } from '../stores/session-store';

// AppLayout reads the open-alerts count via useAlerts() (TanStack Query);
// stub it so these shell-level tests don't need a QueryClientProvider or a
// real network call for a concern this file isn't testing.
const { mockUseAlerts } = vi.hoisted(() => ({ mockUseAlerts: vi.fn() }));
vi.mock('../hooks/useAlerts', () => ({
  useAlerts: mockUseAlerts,
}));

describe('application shell', () => {
  beforeEach(() => {
    useSessionStore.setState({
      user: {
        id: 'user-1',
        email: 'admin@guardianeye.ai',
        full_name: 'Admin User',
        is_active: true,
        is_superuser: false,
        role: { id: 'role-1', name: 'Admin', description: null, permissions: null, created_at: '2024-01-01T00:00:00Z' },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      accessToken: 'token',
      refreshToken: 'refresh',
      expiresAt: Date.now() + 3600_000,
      isAuthenticated: true,
      isHydrated: true,
    });
    mockUseAlerts.mockReturnValue({ data: [] });
  });

  it('reflects the real open-alert count on the sidebar and header badges, not a hardcoded zero', () => {
    mockUseAlerts.mockReturnValue({
      data: [
        { id: 'a1', behaviour_event_id: 'e1', alert_level: 'HIGH', message: 'm1', status: 'OPEN', deduplication_key: 'd1', created_at: '2024-01-01T00:00:00Z' },
        { id: 'a2', behaviour_event_id: 'e2', alert_level: 'CRITICAL', message: 'm2', status: 'OPEN', deduplication_key: 'd2', created_at: '2024-01-01T00:00:00Z' },
        { id: 'a3', behaviour_event_id: 'e3', alert_level: 'LOW', message: 'm3', status: 'ACKNOWLEDGED', deduplication_key: 'd3', created_at: '2024-01-01T00:00:00Z' },
      ],
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Workspace Content</div>
        </AppLayout>
      </MemoryRouter>,
    );

    // Only OPEN alerts (2 of the 3) should count towards the badge.
    expect(screen.getAllByText('2')).not.toHaveLength(0);
  });

  it('navigates to the incident board when the alerts bell is clicked', () => {
    function LocationProbe() {
      const location = useLocation();
      return <div>Current path: {location.pathname}</div>;
    }

    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <LocationProbe />
        </AppLayout>
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: /open alerts/i }));

    expect(screen.getByText('Current path: /incidents')).toBeInTheDocument();
  });

  it('supports toggling the sidebar and opening the command palette with Ctrl+K', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Workspace Content</div>
        </AppLayout>
      </MemoryRouter>,
    );

    expect(screen.getByText('Warehouse')).toBeInTheDocument();

    const toggle = screen.getByRole('button', { name: /collapse sidebar/i });
    fireEvent.click(toggle);

    expect(screen.getByRole('button', { name: /expand sidebar/i })).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    expect(screen.getByRole('dialog', { name: /command palette/i })).toBeInTheDocument();
  });

  it('opens the grounded copilot drawer from the app shell', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Workspace Content</div>
        </AppLayout>
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: /ask copilot/i }));

    expect(screen.getByText(/grounded ai copilot/i)).toBeInTheDocument();
    expect(screen.queryByRole('dialog', { name: /command palette/i })).not.toBeInTheDocument();
  });

  it('exposes the human review workspace entry point', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Workspace Content</div>
        </AppLayout>
      </MemoryRouter>,
    );

    expect(screen.getByRole('link', { name: /human review/i })).toBeInTheDocument();
  });

  it('closes the command palette on Escape', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Workspace Content</div>
        </AppLayout>
      </MemoryRouter>,
    );

    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    expect(screen.getByRole('dialog', { name: /command palette/i })).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.queryByRole('dialog', { name: /command palette/i })).not.toBeInTheDocument();
  });

  it('closes the command palette when clicking its backdrop', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Workspace Content</div>
        </AppLayout>
      </MemoryRouter>,
    );

    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    const dialog = screen.getByRole('dialog', { name: /command palette/i });

    // Clicking inside the dialog itself must not close it.
    fireEvent.click(dialog);
    expect(screen.getByRole('dialog', { name: /command palette/i })).toBeInTheDocument();

    // Clicking the backdrop behind it must close it.
    fireEvent.click(dialog.parentElement as HTMLElement);
    expect(screen.queryByRole('dialog', { name: /command palette/i })).not.toBeInTheDocument();
  });

  it('closes the grounded copilot drawer on Escape', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Workspace Content</div>
        </AppLayout>
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: /ask copilot/i }));
    expect(screen.getByText(/grounded ai copilot/i)).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.queryByText(/grounded ai copilot/i)).not.toBeInTheDocument();
  });
});
