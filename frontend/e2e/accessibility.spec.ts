import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { DESKTOP_PROJECT, installApiMocks, installMediaMocks, installWebSocketMock, seedAuthenticatedSession } from './mocks';

test.beforeEach(async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== DESKTOP_PROJECT, 'functional test — desktop only, see responsive.spec.ts for viewports');
  await installApiMocks(page);
  await installMediaMocks(page);
  await installWebSocketMock(page);
  await seedAuthenticatedSession(page);
});

const pagesToScan = ['/', '/incidents', '/evidence', '/human-review', '/analytics'];

test.describe('accessibility (axe)', () => {
  for (const path of pagesToScan) {
    test(`${path} has no serious/critical axe violations`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState('networkidle');

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const seriousOrCritical = results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');

      expect(
        seriousOrCritical,
        seriousOrCritical.map((v) => `${v.id}: ${v.help} (${v.nodes.length} node(s))`).join('\n'),
      ).toEqual([]);
    });
  }
});

test.describe('keyboard navigation', () => {
  test('every icon-only header control has an accessible name', async ({ page }) => {
    await page.goto('/');

    for (const name of ['Open alerts', 'Command', 'Ask Copilot', 'Logout']) {
      await expect(page.getByRole('button', { name: new RegExp(name, 'i') }).first()).toBeVisible();
    }
  });

  test('the command palette search input is reachable and usable via keyboard alone', async ({ page }) => {
    await page.goto('/');

    await page.keyboard.press('Control+k');
    await expect(page.getByLabel('Command palette search')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /open overview/i })).toBeFocused();

    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog', { name: /command palette/i })).not.toBeVisible();
  });

  test('sidebar navigation links are reachable and activatable via keyboard', async ({ page }) => {
    await page.goto('/');

    const incidentsLink = page.getByRole('link', { name: 'Incident Board' });
    await incidentsLink.focus();
    await expect(incidentsLink).toBeFocused();

    await page.keyboard.press('Enter');
    await expect(page).toHaveURL('/incidents');
  });
});

test.describe('reduced motion', () => {
  test('continuous animations are effectively disabled when the user prefers reduced motion', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('/');

    const duration = await page.locator('.pulse-live').first().evaluate((el) => getComputedStyle(el).animationDuration);

    // Every value in a shorthand animation-duration list must be clamped by
    // the global reduced-motion override, not just the first one.
    for (const value of duration.split(',')) {
      expect(parseFloat(value)).toBeLessThanOrEqual(0.01);
    }
  });
});
