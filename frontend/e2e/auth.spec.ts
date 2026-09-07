import { expect, test } from '@playwright/test';
import { DESKTOP_PROJECT, adminUser, installApiMocks, installWebSocketMock, seedAuthenticatedSession } from './mocks';

test.beforeEach(async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== DESKTOP_PROJECT, 'functional test — desktop only, see responsive.spec.ts for viewports');
  await installWebSocketMock(page);
});

test.describe('authentication', () => {
  test('unauthenticated users are redirected to /login when visiting a protected route', async ({ page }) => {
    await installApiMocks(page);
    await page.goto('/incidents');
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole('heading', { name: /secure sign in/i })).toBeVisible();
  });

  test('logs in successfully and lands on the protected dashboard', async ({ page }) => {
    await installApiMocks(page);
    await page.goto('/login');

    await page.getByLabel('Email').fill(adminUser.email);
    await page.getByLabel('Password').fill('correct-password');
    await page.getByRole('button', { name: 'Login' }).click();

    await expect(page).toHaveURL('/');
    await expect(page.getByText(adminUser.full_name)).toBeVisible();
  });

  test('shows a readable error on invalid credentials and does not navigate away', async ({ page }) => {
    await installApiMocks(page, { loginShouldFail: true });
    await page.goto('/login');

    await page.getByLabel('Email').fill(adminUser.email);
    await page.getByLabel('Password').fill('wrong-password');
    await page.getByRole('button', { name: 'Login' }).click();

    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
    await expect(page).toHaveURL(/\/login$/);
  });

  test('logout clears the session and returns to the login page', async ({ page }) => {
    await installApiMocks(page);
    // Log in through the real form rather than seedAuthenticatedSession()
    // here: that helper's addInitScript reseeds localStorage on every new
    // navigation in this context, which would silently re-authenticate the
    // page.goto('/incidents') below and mask a real logout regression.
    await page.goto('/login');
    await page.getByLabel('Email').fill(adminUser.email);
    await page.getByLabel('Password').fill('correct-password');
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL('/');

    await page.getByRole('button', { name: 'Logout' }).click();

    await expect(page).toHaveURL(/\/login$/);

    // The cleared session must actually stick — reloading (or trying to go
    // back to a protected route) must not silently restore access.
    await page.goto('/incidents');
    await expect(page).toHaveURL(/\/login$/);
  });

  test('an authenticated user visiting /login is redirected straight to the app', async ({ page }) => {
    await installApiMocks(page);
    await seedAuthenticatedSession(page);
    await page.goto('/login');

    await expect(page).toHaveURL('/');
  });
});
