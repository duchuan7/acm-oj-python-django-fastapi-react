import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 90000,
  expect: { timeout: 15000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.OJ_WEB_URL || 'http://127.0.0.1:5175',
    browserName: 'chromium',
    channel: process.env.OJ_BROWSER || (process.platform === 'win32' ? 'msedge' : undefined),
    headless: true,
    viewport: { width: 1440, height: 1000 },
    screenshot: 'only-on-failure',
    trace: 'off',
  },
});
