import { chromium, expect } from '@playwright/test';
import path from 'node:path';

const [project, address, mode, work] = process.argv.slice(2);
if (!/^oj-acceptance-[a-f0-9]{10}$/.test(project) || !/^http:\/\/127\.0\.0\.1:\d+$/.test(address))
    throw new Error('An isolated loopback rehearsal project is required.');
if (!['legacy', 'java', 'rollback'].includes(mode)) throw new Error('Unknown rehearsal mode.');
const browser = await chromium.launch({
    channel: process.platform === 'win32' ? 'msedge' : undefined,
});
try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    const problems = page.waitForResponse((r) => /\/api\/problems\/?(?:\?|$)/.test(r.url()));
    await page.goto(address);
    expect((await problems).ok()).toBeTruthy();
    await expect(page.locator(mode === 'java' ? '.shell' : '#root')).toBeVisible();
    await expect(page.getByRole('heading').first()).toBeVisible();
    if (mode === 'java')
        await expect(page.getByRole('heading', { name: '从一道题开始。' })).toBeVisible();
    await page.screenshot({ path: path.join(work, `entrypoint-${mode}.png`), fullPage: true });
    expect(errors).toEqual([]);
    console.log(`${mode} browser entrypoint PASS`);
} finally {
    await browser.close();
}
