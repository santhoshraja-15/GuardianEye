import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { AppRoutes } from '../routes';
import { useSessionStore } from '../stores/session-store';

describe('open access flow', () => {
  beforeEach(() => {
    useSessionStore.setState({
      user: {
        id: 'operator-default',
        email: 'operator@guardianeye.ai',
        full_name: 'GuardianEye Operator',
        is_active: true,
        is_superuser: true,
        role: {
          id: 'role-admin',
          name: 'Admin',
          description: 'System Administrator',
          permissions: '*',
          created_at: '2024-01-01T00:00:00Z',
        },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      accessToken: null,
      refreshToken: null,
      expiresAt: null,
      isAuthenticated: true,
      isHydrated: true,
    });
  });

  it('allows unauthenticated users to access routes directly without login', async () => {
    render(
      <MemoryRouter initialEntries={['/workspace']}>
        <Routes>
          <Route
            path="/workspace"
            element={
              <ProtectedRoute>
                <div>Direct Workspace Access</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Direct Workspace Access')).toBeInTheDocument();
  });

  it('does not block access or redirect for any role restrictions', () => {
    render(
      <MemoryRouter initialEntries={['/admin-panel']}>
        <Routes>
          <Route
            path="/admin-panel"
            element={
              <ProtectedRoute allowedRoles={['Admin']}>
                <div>Admin Panel Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText('Admin Panel Content')).toBeInTheDocument();
  });

  it('redirects unknown routes directly to home overview instead of login', () => {
    render(
      <MemoryRouter initialEntries={['/unknown-path']}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(screen.queryByText(/sign in/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/login/i)).not.toBeInTheDocument();
  });
});

