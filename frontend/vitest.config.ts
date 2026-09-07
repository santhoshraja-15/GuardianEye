import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    globals: true,
    // Playwright E2E specs live under e2e/ and use @playwright/test's own
    // test runner — keep them out of vitest's (jsdom) unit/integration run.
    exclude: ['**/node_modules/**', '**/dist/**', 'e2e/**'],
  },
});
