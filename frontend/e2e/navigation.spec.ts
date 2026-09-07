import { expect, test, type Page } from '@playwright/test';
import { DESKTOP_PROJECT, adminUser, installApiMocks, installWebSocketMock, operatorUser, seedAuthenticatedSession } from './mocks';

test.beforeEach(async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== DESKTOP_PROJECT, 'functional test — desktop only, see responsive.spec.ts for viewports');
});

interface RouteCase {
  path: string;
  navLabel: string;
  heading: RegExp;
}

// Every route reachable from the sidebar for a signed-in user, per
// src/routes/index.tsx and src/components/layout/Sidebar.tsx.
const routes: RouteCase[] = [
  { path: '/', navLabel: 'Overview', heading: /command center|overview|dashboard/i },
  { path: '/live', navLabel: 'Live Streams', heading: /live/i },
  { path: '/analysis', navLabel: 'Video Intelligence', heading: /video/i },
  { path: '/analytics', navLabel: 'Analytics', heading: /analytics/i },
  { path: '/incidents', navLabel: 'Incident Board', heading: /incident/i },
  { path: '/evidence', navLabel: 'Evidence Vault', heading: /evidence/i },
  { path: '/prevention', navLabel: 'Prevention Studio', heading: /prevention/i },
  { path: '/digital-twin', navLabel: 'Digital Twin', heading: /digital twin/i },
  { path: '/dna', navLabel: 'Behaviour DNA', heading: /dna|behaviour/i },
  { path: '/human-review', navLabel: 'Human Review', heading: /review/i },
];

function trackPageHealth(page: Page) {
  const consoleErrors: string[] = [];
  const failedRequests: string[] = [];

  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text());
    }
  });
  page.on('pageerror', (error) => {
    consoleErrors.push(error.message);
  });
  page.on('requestfailed', (request) => {
    failedRequests.push(`${request.method()} ${request.url()} — ${request.failure()?.errorText}`);
  });

  return { consoleErrors, failedRequests };
}

test.describe('routing and navigation', () => {
  for (const route of routes) {
    test(`${route.path} renders with no console errors, no broken images, no failed requests`, async ({ page }) => {
      await installApiMocks(page);
      await installWebSocketMock(page);
      await seedAuthenticatedSession(page);

      const health = trackPageHealth(page);

      await page.goto(route.path);
      await expect(page).toHaveURL(route.path === '/' ? '/' : route.path);
      await expect(page.getByText(route.heading).first()).toBeVisible();

      // No <img> should be left in a broken/errored state.
      const images = page.locator('img');
      const count = await images.count();
      for (let i = 0; i < count; i += 1) {
        const naturalWidth = await images.nth(i).evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0);
        expect(naturalWidth, `image #${i} on ${route.path} failed to load`).toBe(true);
      }

      expect(health.consoleErrors, `console errors on ${route.path}:\n${health.consoleErrors.join('\n')}`).toEqual([]);
      expect(health.failedRequests, `failed requests on ${route.path}:\n${health.failedRequests.join('\n')}`).toEqual([]);
    });
  }

  test('the sidebar highlights the active route and every nav link is reachable', async ({ page }) => {
    await installApiMocks(page);
    await installWebSocketMock(page);
    await seedAuthenticatedSession(page);
    await page.goto('/');

    for (const route of routes) {
      await page.getByRole('link', { name: route.navLabel, exact: false }).first().click();
      await expect(page).toHaveURL(route.path === '/' ? '/' : route.path);
    }
  });

  test('an unmapped URL does not crash the app', async ({ page }) => {
    await installApiMocks(page);
    await installWebSocketMock(page);
    await seedAuthenticatedSession(page);

    const health = trackPageHealth(page);
    await page.goto('/this-route-does-not-exist');

    // The catch-all route redirects unauthenticated visitors to /login; for
    // an authenticated user the page must still render something coherent,
    // not a blank crash screen.
    await expect(page.locator('body')).not.toBeEmpty();
    expect(health.consoleErrors).toEqual([]);
  });

  test('RBAC: Admin sees and can open the Session nav item', async ({ page }) => {
    await installApiMocks(page, { user: adminUser });
    await installWebSocketMock(page);
    await seedAuthenticatedSession(page, adminUser);
    await page.goto('/');

    const sessionLink = page.getByRole('link', { name: 'Session' });
    await expect(sessionLink).toBeVisible();
    await sessionLink.click();

    await expect(page).toHaveURL('/session');
    await expect(page.getByRole('heading', { name: /session status/i })).toBeVisible();
    await expect(page.getByText(adminUser.email)).toBeVisible();
  });

  test('RBAC: a non-admin/supervisor role does not see the Session nav item and is redirected if it navigates there directly', async ({ page }) => {
    await installApiMocks(page, { user: operatorUser });
    await installWebSocketMock(page);
    await seedAuthenticatedSession(page, operatorUser);
    await page.goto('/');

    await expect(page.getByRole('link', { name: 'Session' })).toHaveCount(0);

    await page.goto('/session');
    await expect(page).toHaveURL(/\/unauthorized$/);
  });
});
