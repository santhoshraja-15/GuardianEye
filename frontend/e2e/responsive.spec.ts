import { expect, test } from '@playwright/test';
import { installApiMocks, installMediaMocks, installWebSocketMock, seedAuthenticatedSession } from './mocks';

// Runs on every configured project (Desktop / Laptop / Tablet / Mobile) —
// this file is deliberately viewport-sensitive, unlike the other specs.
const routesToCheck = [
  '/',
  '/live',
  '/analysis',
  '/incidents',
  '/evidence',
  '/prevention',
  '/digital-twin',
  '/dna',
  '/human-review',
  '/analytics',
];

test.beforeEach(async ({ page }) => {
  await installApiMocks(page);
  await installMediaMocks(page);
  await installWebSocketMock(page);
  await seedAuthenticatedSession(page);
});

test.describe('responsive layout', () => {
  for (const path of routesToCheck) {
    test(`${path} has no horizontal overflow at this viewport`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState('networkidle');

      const { scrollWidth, clientWidth } = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));

      expect(scrollWidth, `document is wider (${scrollWidth}px) than the viewport (${clientWidth}px) on ${path}`).toBeLessThanOrEqual(clientWidth + 1);
    });
  }

  test('the app shell adapts navigation for the current viewport', async ({ page }, testInfo) => {
    await page.goto('/');

    const viewportWidth = testInfo.project.use.viewport?.width ?? 1920;
    const isMobileLayout = viewportWidth < 768;

    const hamburger = page.getByRole('button', { name: 'Open navigation' });
    const primaryNav = page.getByRole('link', { name: 'Overview' });

    if (isMobileLayout) {
      // On narrow viewports the sidebar starts off-canvas: the hamburger is
      // reachable, and opening it reveals the nav without the app needing a
      // full page reload/crash.
      await expect(hamburger).toBeVisible();
      await expect(primaryNav).not.toBeInViewport();

      await hamburger.click();
      await expect(primaryNav).toBeInViewport();

      // Selecting a destination closes the drawer again. The drawer closes
      // via a CSS transform (off-screen), not display:none, so it stays
      // "visible" per Playwright's toBeVisible() — check viewport position
      // instead, same as the initial off-canvas assertion above.
      await primaryNav.click();
      await expect(page.getByRole('button', { name: 'Close navigation' })).not.toBeInViewport();
    } else {
      // On md+ viewports the sidebar is already docked in place.
      await expect(hamburger).not.toBeVisible();
      await expect(primaryNav).toBeInViewport();
    }
  });
});
