import { defineConfig } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

if (!process.env.OJ_ACCEPTANCE_STATE) throw new Error('Run python acceptance/run.py first.');
const state = JSON.parse(fs.readFileSync(process.env.OJ_ACCEPTANCE_STATE, 'utf8'));
if (!/^oj-acceptance-[a-f0-9]{10}$/.test(state.project))
  throw new Error('Isolated test state required.');
export default defineConfig({
  testDir: '.',
  testMatch: 'browser.spec.js',
  workers: 1,
  retries: 0,
  timeout: 90000,
  expect: { timeout: 10000 },
  reporter: [['list'], ['json', { outputFile: path.join(state.work, 'browser-results.json') }]],
  outputDir: path.join(state.work, 'browser-artifacts'),
  use: {
    baseURL: state.web,
    channel: process.platform === 'win32' ? 'msedge' : undefined,
    headless: true,
    viewport: { width: 1366, height: 900 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
});
