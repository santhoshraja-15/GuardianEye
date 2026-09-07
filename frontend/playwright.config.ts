import { defineConfig, devices } from '@playwright/test';

const PORT = 4173;
const baseURL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  // Keep this modest: every project shares one `vite preview` instance, and
  // too much concurrency against it just produces goto/click timeouts that
  // look like app bugs but are actually server contention.
  workers: 3,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 1,
  reporter: [['list']],
  timeout: 45_000,
  expect: { timeout: 8_000 },
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    navigationTimeout: 20_000,
  },
  webServer: {
    command: `npm run build && npm run preview -- --port ${PORT} --strictPort`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    {
      name: 'Desktop Chrome (1920x1080)',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1920, height: 1080 } },
      // Runs the full functional suite plus its own responsive checks.
    },
    {
      name: 'Laptop Chrome (1440x900)',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
      // Layout-only: functional specs restrict themselves to the Desktop
      // project internally, so only run the viewport-sensitive spec here.
      testMatch: /responsive\.spec\.ts/,
    },
    {
      name: 'Tablet Chrome (768x1024)',
      use: { ...devices['Desktop Chrome'], viewport: { width: 768, height: 1024 }, hasTouch: true },
      testMatch: /responsive\.spec\.ts/,
    },
    {
      name: 'Mobile Chrome (390x844)',
      use: { ...devices['Pixel 7'], viewport: { width: 390, height: 844 } },
      testMatch: /responsive\.spec\.ts/,
    },
  ],
});
