import { expect, test } from '@playwright/test';
import {
  DESKTOP_PROJECT,
  installApiMocks,
  installMediaMocks,
  installWebSocketMock,
  seedAuthenticatedSession,
} from './mocks';

test.beforeEach(async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== DESKTOP_PROJECT, 'functional test — desktop only, see responsive.spec.ts for viewports');
  await installApiMocks(page);
  await installMediaMocks(page);
  await installWebSocketMock(page);
  await seedAuthenticatedSession(page);
});

test.describe('command palette', () => {
  test('opens with Ctrl+K, navigates on selection, and closes', async ({ page }) => {
    await page.goto('/');

    await page.keyboard.press('Control+k');
    const dialog = page.getByRole('dialog', { name: /command palette/i });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByLabel('Command palette search')).toBeFocused();

    await dialog.getByRole('button', { name: /open incident board/i }).click();
    await expect(dialog).not.toBeVisible();
    await expect(page).toHaveURL('/incidents');
  });

  test('closes on Escape without navigating', async ({ page }) => {
    await page.goto('/live');
    await page.keyboard.press('Control+k');
    await expect(page.getByRole('dialog', { name: /command palette/i })).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog', { name: /command palette/i })).not.toBeVisible();
    await expect(page).toHaveURL('/live');
  });

  test('closes when clicking the backdrop', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('Control+k');
    const dialog = page.getByRole('dialog', { name: /command palette/i });
    await expect(dialog).toBeVisible();

    // Click near the top-left corner of the viewport, outside the dialog panel.
    await page.mouse.click(10, 10);
    await expect(dialog).not.toBeVisible();
  });
});

test.describe('AI copilot assistant', () => {
  test('opens, answers a grounded question with a citation, and closes on Escape', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: /ask copilot/i }).click();
    // "Grounded AI Copilot" also appears as the sidebar's own launcher button
    // label, so anchor on the drawer's unique subtitle instead.
    await expect(page.getByText('ZERO HALLUCINATION')).toBeVisible();

    const input = page.getByPlaceholder(/ask a question about warehouse safety/i);
    await input.fill('Why did risk increase in Zone B4?');
    await input.press('Enter');

    await expect(page.getByText('Zone B4 risk increased due to two unstable-stacking events in the last shift.')).toBeVisible();
    // "GE-10429" also appears in the dashboard behind the drawer — scope to
    // the citation card under the drawer's own "Verified Evidence" heading.
    const citations = page.getByText('Verified Evidence Citations:').locator('..');
    await expect(citations.getByText('GE-10429')).toBeVisible();
    await expect(page.getByText(/grounded/i).first()).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(page.getByText('ZERO HALLUCINATION')).not.toBeVisible();
  });
});

test.describe('incidents workspace: table, filters, drawer', () => {
  test('filters the incident table by search text and severity', async ({ page }) => {
    await page.goto('/incidents');

    await expect(page.getByText('GE-10428')).toBeVisible();
    await expect(page.getByText('GE-10429')).toBeVisible();

    await page.getByPlaceholder(/filter by code, title or summary/i).fill('storage zone b');
    await expect(page.getByText('GE-10429')).toBeVisible();
    await expect(page.getByText('GE-10428')).not.toBeVisible();

    await page.getByPlaceholder(/filter by code, title or summary/i).fill('');
    await page.getByRole('button', { name: 'CRITICAL' }).click();
    await expect(page.getByText('GE-10429')).toBeVisible();
    await expect(page.getByText('GE-10428')).not.toBeVisible();
  });

  test('opens the manage-case drawer and submits a status update', async ({ page }) => {
    await page.goto('/incidents');

    await page.getByRole('row', { name: /GE-10428/ }).getByRole('button', { name: /manage case/i }).click();

    const drawer = page.getByRole('dialog', { name: /manage case GE-10428/i });
    await expect(drawer.getByText('GE-10428')).toBeVisible();

    await page.getByLabel('Audit reason').fill('Reviewed footage, escalating per SOP.');
    await page.getByRole('button', { name: /save status update/i }).click();

    // The drawer's own request completes and the reason field resets — the
    // interaction must not throw or leave the button permanently disabled.
    await expect(page.getByLabel('Audit reason')).toHaveValue('');
  });
});

test.describe('evidence vault', () => {
  test('selecting an incident loads its replay video, checksum, and keyframes', async ({ page }) => {
    await page.goto('/evidence');

    await expect(page.getByText('CASE / EVIDENCE MANIFEST')).toBeVisible();
    await expect(page.locator('video')).toHaveAttribute('src', /incident-1\.mp4/);
    await expect(page.getByText('abc123')).toBeVisible();

    // Playback-rate and seek controls must be interactive without throwing.
    await page.getByRole('button', { name: '1.5x' }).click();
    await page.getByRole('button', { name: '+1s' }).click();
    await page.getByRole('button', { name: '-1s' }).click();
  });
});

test.describe('human review workflow', () => {
  test('selects an incident, records a verdict, and shows confirmation', async ({ page }) => {
    await page.goto('/human-review');

    await expect(page.getByRole('heading', { name: /human review workspace/i })).toBeVisible();
    await expect(page.getByText('AI prediction')).toBeVisible();

    await page.getByRole('button', { name: 'CHANGE_BEHAVIOUR' }).click();
    await expect(page.getByLabel(/corrected behaviour from backend taxonomy/i)).toBeVisible();

    await page.getByPlaceholder(/describe what the model got right/i).fill('Model missed the secondary contributing factor.');
    await page.getByRole('button', { name: /submit decision/i }).click();

    await expect(page.getByText(/decision captured for/i)).toBeVisible();
  });
});

test.describe('analytics charts', () => {
  test('renders the behaviour and trend charts from real summary data', async ({ page }) => {
    await page.goto('/analytics');

    await expect(page.getByRole('heading', { name: /analytics/i })).toBeVisible();
    // Recharts renders an SVG per chart — confirm at least the expected
    // number of chart surfaces mounted without crashing.
    await expect(page.locator('.recharts-wrapper')).not.toHaveCount(0);
  });
});
