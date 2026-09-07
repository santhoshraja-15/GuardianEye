import type { Page, Route } from '@playwright/test';

/** Functional (non-layout) specs only need to run once — restrict them to
 * this project and leave full desktop/laptop/tablet/mobile coverage to
 * e2e/responsive.spec.ts, which is deliberately viewport-sensitive. */
export const DESKTOP_PROJECT = 'Desktop Chrome (1920x1080)';

// Realistic mock payloads shaped exactly like the documented backend contract
// (frontend/src/types/*.ts + frontend/src/types/auth.ts) so pages render the
// same code paths they would against the real backend, without depending on
// a live backend/database being available for frontend-only QA.

export const adminUser = {
  id: 'user-admin-1',
  email: 'admin@guardianeye.ai',
  full_name: 'Ava Administrator',
  is_active: true,
  is_superuser: false,
  role: { id: 'role-admin', name: 'Admin', description: null, permissions: null, created_at: '2024-01-01T00:00:00Z' },
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const operatorUser = {
  id: 'user-operator-1',
  email: 'operator@guardianeye.ai',
  full_name: 'Ollie Operator',
  is_active: true,
  is_superuser: false,
  role: { id: 'role-operator', name: 'Operator', description: null, permissions: null, created_at: '2024-01-01T00:00:00Z' },
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockTokens = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
  expires_in: 3600,
};

export const mockDashboardSummary = {
  total_videos_processed: 128,
  total_incidents_detected: 42,
  critical_incidents: 3,
  open_alerts: 5,
  estimated_damage_loss_usd: 18450.5,
  mean_time_to_acknowledge_seconds: 145,
  behaviour_distribution: [
    { behaviour_code: 'DROP', count: 12, percentage: 28.5, avg_risk_score: 74.2 },
    { behaviour_code: 'DRAG', count: 9, percentage: 21.4, avg_risk_score: 61.0 },
  ],
  risk_heatmaps: [
    { x_normalized: 0.3, y_normalized: 0.4, intensity: 0.8, zone_code: 'Z-01', incident_count: 6 },
  ],
  operational_health_status: 'OPTIMAL' as const,
};

export const mockAlerts = [
  {
    id: 'alert-1',
    behaviour_event_id: 'evt-1',
    zone_id: 'zone-1',
    alert_level: 'HIGH' as const,
    message: 'Rough handling detected at Loading Bay 2',
    status: 'OPEN' as const,
    deduplication_key: 'dedup-1',
    created_at: '2026-09-01T10:00:00Z',
  },
  {
    id: 'alert-2',
    behaviour_event_id: 'evt-2',
    zone_id: 'zone-2',
    alert_level: 'CRITICAL' as const,
    message: 'Unstable stacking detected in Storage Zone B',
    status: 'ACKNOWLEDGED' as const,
    deduplication_key: 'dedup-2',
    acknowledged_by: 'Ava Administrator',
    acknowledged_at: '2026-09-01T10:05:00Z',
    created_at: '2026-09-01T09:55:00Z',
  },
];

export const mockIncidents = [
  {
    id: 'incident-1',
    incident_code: 'GE-10428',
    behaviour_event_id: 'evt-1',
    warehouse_id: 'Warehouse 01',
    zone_id: 'zone-1',
    camera_id: 'CAM-04',
    title: 'Rough handling — Loading Bay 2',
    summary: 'Package dropped from approximately 1.0m during unloading.',
    severity: 'HIGH' as const,
    status: 'UNDER_REVIEW' as const,
    created_at: '2026-09-01T10:00:00Z',
    updated_at: '2026-09-01T10:05:00Z',
  },
  {
    id: 'incident-2',
    incident_code: 'GE-10429',
    behaviour_event_id: 'evt-2',
    warehouse_id: 'Warehouse 01',
    zone_id: 'zone-2',
    camera_id: 'CAM-07',
    title: 'Unstable stacking — Storage Zone B',
    summary: 'Pallet stack exceeded safe height threshold.',
    severity: 'CRITICAL' as const,
    status: 'DETECTED' as const,
    created_at: '2026-09-01T09:55:00Z',
    updated_at: '2026-09-01T09:55:00Z',
  },
];

export const mockEvidence = {
  id: 'evidence-1',
  incident_id: 'incident-1',
  snapshot_path: '/media/snapshots/incident-1.jpg',
  clip_path: '/media/clips/incident-1.mp4',
  pre_event_seconds: 5,
  post_event_seconds: 5,
  sha256_checksum: 'abc123',
  overlay_data: '{}',
};

export const mockReplay = {
  incident_id: 'incident-1',
  video_id: 'video-1',
  behaviour_code: 'ROUGH_HANDLING',
  clip_url: '/media/clips/incident-1.mp4',
  snapshot_url: '/media/snapshots/incident-1.jpg',
  sha256_checksum: 'abc123',
  duration_seconds: 12,
  keyframes: [],
};

export const mockVideos = [
  {
    id: 'video-1',
    filename: 'dock-01.mp4',
    storage_path: '/media/videos/dock-01.mp4',
    file_size_bytes: 14800000,
    duration_seconds: 18.4,
    fps: 30,
    width: 1920,
    height: 1080,
    codec: 'h264',
    checksum_sha256: 'def456',
    status: 'PROCESSED' as const,
    created_at: '2026-09-01T08:00:00Z',
    updated_at: '2026-09-01T08:05:00Z',
    processing_jobs: [],
  },
];

export const mockBehaviourEvents = [
  {
    id: 'evt-1',
    video_id: 'video-1',
    behaviour_type: 'ROUGH_HANDLING',
    severity: 'HIGH',
    start_frame: 10,
    end_frame: 40,
    start_time_seconds: 1.2,
    end_time_seconds: 3.4,
    duration_seconds: 2.2,
    confidence: 0.91,
    description: 'Package handled roughly during transfer.',
    keyframe_indices: [12, 20, 35],
  },
];

export const mockDigitalTwinTopology = {
  warehouse_id: 'Warehouse 01',
  warehouse_name: 'Warehouse 01',
  dimensions_meters: [80, 40, 12] as [number, number, number],
  zones: [
    {
      zone_id: 'zone-1',
      zone_code: 'Z-01',
      zone_name: 'Loading Bay 2',
      zone_type: 'loading_bay',
      polygon_points: [[0, 0], [10, 0], [10, 10], [0, 10]] as [number, number][],
      risk_multiplier: 1.4,
    },
  ],
  cameras: [
    { camera_id: 'CAM-04', camera_code: 'CAM-04', camera_name: 'Dock Camera 4', position_xyz: [5, 5, 3] as [number, number, number], coverage_zones: ['zone-1'] },
  ],
  active_entity_count: 3,
};

export const mockAssistantResponse = {
  answer: 'Zone B4 risk increased due to two unstable-stacking events in the last shift.',
  grounded_citations: [
    { source_type: 'incident', source_id: 'incident-2', title: 'GE-10429', confidence: 0.88, snippet: 'Pallet stack exceeded safe height threshold.' },
  ],
  is_grounded: true,
  confidence: 0.88,
  suggested_followups: ['What is the recommended action?'],
};

async function json(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
}

interface ApiMockOptions {
  user?: typeof adminUser | typeof operatorUser;
  loginShouldFail?: boolean;
}

/**
 * Installs mocked handlers for every backend endpoint the frontend actually
 * calls (see BACKEND_INTEGRATION_MAP.md / src/services/api.ts). A broad
 * catch-all is registered first so any endpoint not explicitly listed still
 * returns a benign empty 200 instead of a hard network failure; the specific
 * handlers registered afterwards take priority (Playwright runs the
 * most-recently-registered matching handler first).
 */
export async function installApiMocks(page: Page, options: ApiMockOptions = {}) {
  const user = options.user ?? adminUser;

  // Catch-all fallback for any endpoint not explicitly mocked below.
  await page.route('**/api/v1/**', async (route) => {
    const method = route.request().method();
    await json(route, method === 'GET' ? [] : {});
  });

  await page.route('**/api/v1/auth/login', async (route) => {
    if (options.loginShouldFail) {
      await json(route, { detail: 'Invalid email or password' }, 401);
      return;
    }
    await json(route, mockTokens);
  });

  await page.route('**/api/v1/auth/me', async (route) => {
    await json(route, user);
  });

  await page.route('**/api/v1/auth/refresh', async (route) => {
    await json(route, mockTokens);
  });

  await page.route('**/api/v1/analytics/dashboard', async (route) => {
    await json(route, mockDashboardSummary);
  });

  await page.route('**/api/v1/incidents/status', async (route) => {
    await json(route, mockIncidents[0]);
  });

  await page.route('**/api/v1/incidents', async (route) => {
    await json(route, mockIncidents);
  });

  await page.route('**/api/v1/alerts/acknowledge', async (route) => {
    await json(route, { ...mockAlerts[0], status: 'ACKNOWLEDGED' });
  });

  await page.route('**/api/v1/alerts', async (route) => {
    await json(route, mockAlerts);
  });

  await page.route('**/api/v1/videos', async (route) => {
    await json(route, mockVideos);
  });

  await page.route('**/api/v1/tracks/**', async (route) => {
    await json(route, { video_id: 'video-1', total_tracks: 0, tracks: [] });
  });

  await page.route('**/api/v1/behaviours/video/**', async (route) => {
    await json(route, mockBehaviourEvents);
  });

  await page.route('**/api/v1/evidence/incident/**', async (route) => {
    await json(route, mockEvidence);
  });

  await page.route('**/api/v1/replay/**', async (route) => {
    await json(route, mockReplay);
  });

  await page.route('**/api/v1/digital-twin/topology', async (route) => {
    await json(route, mockDigitalTwinTopology);
  });

  await page.route('**/api/v1/assistant/chat', async (route) => {
    await json(route, mockAssistantResponse);
  });
}

// A minimal valid 1x1 GIF, reused as a stand-in for any evidence image/video
// asset the mock data references, so <img>/<video> requests resolve with a
// real decodable resource instead of a 404 against the preview server.
const TINY_GIF_BASE64 = 'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBTAA7';

/** Mocks the `/media/**` evidence asset paths referenced by the mock evidence
 * data above, so the Evidence Vault's <img>/<video> elements resolve against
 * a real (tiny) file instead of 404ing against the preview server. */
export async function installMediaMocks(page: Page) {
  await page.route('**/media/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'image/gif',
      body: Buffer.from(TINY_GIF_BASE64, 'base64'),
    });
  });
}

/** Mocks the realtime WebSocket endpoint so the app's connection settles into
 * LIVE without needing a real backend, and without triggering the frontend's
 * reconnect loop (which would otherwise fire against a non-existent server). */
export async function installWebSocketMock(page: Page) {
  await page.routeWebSocket(/\/api\/v1\/ws\/events/, () => {
    // Leaving the handler empty keeps the socket open (readyState OPEN) from
    // the page's perspective without forwarding to any real server.
  });
}

/** Seeds an authenticated session directly into localStorage (matching the
 * zustand-persist shape session-store.ts writes) before the app's first
 * script runs, so tests that don't need to exercise the login form itself
 * can start already signed in. */
export async function seedAuthenticatedSession(page: Page, user: typeof adminUser | typeof operatorUser = adminUser) {
  await page.addInitScript(
    ([sessionUser, tokens]) => {
      window.localStorage.setItem(
        'guardianeye-auth',
        JSON.stringify({
          state: {
            user: sessionUser,
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            expiresAt: Date.now() + tokens.expires_in * 1000,
            isAuthenticated: true,
          },
          version: 0,
        }),
      );
    },
    [user, mockTokens] as const,
  );
}
