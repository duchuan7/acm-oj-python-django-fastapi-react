import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const env = Object.fromEntries(
  fs
    .readFileSync(path.join(root, '.env'), 'utf8')
    .split(/\r?\n/)
    .filter((line) => line && !line.startsWith('#'))
    .map((line) => {
      const index = line.indexOf('=');
      return [line.slice(0, index), line.slice(index + 1)];
    }),
);
let token;
const created = { blogs: [], problems: [], proposals: [] };

test.beforeAll(async ({ request }) => {
  const response = await request.post('/api/auth/login', {
    data: { username: env.ADMIN_USERNAME, password: env.ADMIN_PASSWORD },
  });
  expect(response.ok()).toBeTruthy();
  token = (await response.json()).token;
});

async function authenticate(page) {
  await page.addInitScript((value) => {
    localStorage.setItem('oj_java_token', value);
    localStorage.setItem('oj_java_lang', 'zh');
  }, token);
}

test.afterAll(async ({ request }) => {
  for (const id of created.proposals) {
    const response = await request.delete('/api/problem-proposals/' + id, {
      headers: { Authorization: 'Bearer ' + token },
    });
    expect(response.ok()).toBeTruthy();
  }
  for (const id of created.blogs) {
    const response = await request.delete('/api/blogs/' + id, {
      headers: { Authorization: 'Bearer ' + token },
    });
    expect(response.ok()).toBeTruthy();
  }
  for (const id of created.problems) {
    const response = await request.delete('/api/problems/' + id, {
      headers: { Authorization: 'Bearer ' + token },
    });
    expect(response.ok()).toBeTruthy();
  }
});

test('public problem browsing, filtering, language switch and expired session recovery', async ({
  page,
}) => {
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: '从一道题开始。' })).toBeVisible();
  await page.getByPlaceholder('搜索题目、来源').fill('A + B');
  await page.getByRole('button', { name: '筛选', exact: true }).click();
  await expect(page.getByText('A + B', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'EN', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Start with one problem.' })).toBeVisible();
  await page.evaluate(() => localStorage.setItem('oj_java_token', 'expired.invalid.token'));
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Start with one problem.' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Sign in', exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});

test('login through the page survives a reload', async ({ page }) => {
  await page.goto('/auth');
  await page.getByLabel('Username', { exact: true }).fill(env.ADMIN_USERNAME);
  await page.getByLabel('Password', { exact: true }).fill(env.ADMIN_PASSWORD);
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await expect(page.getByRole('link', { name: '管理', exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('link', { name: '管理', exact: true })).toBeVisible();
  await page.goto('/admin');
  await expect(page.getByRole('heading', { name: '让训练有序进行。' })).toBeVisible();
  await page.getByRole('tab', { name: '用户管理', exact: true }).click();
  await expect(page.getByText(env.ADMIN_USERNAME, { exact: true }).last()).toBeVisible();
});

test('code submission reaches Accepted without manually refreshing', async ({ page }) => {
  await authenticate(page);
  await page.goto('/problems/1');
  await expect(page.getByRole('heading', { name: 'A + B', exact: true })).toBeVisible();
  await page
    .getByLabel('Source code')
    .fill('#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}');
  await page.getByRole('button', { name: '提交评测', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('dialog').locator('.submission-summary .verdict')).toHaveText(
    'ACCEPTED',
    {
      timeout: 75000,
    },
  );
  await expect(page.getByRole('dialog').getByText('100 / 100')).toBeVisible();
});

test('problem manager saves a private problem with testcases', async ({ page }) => {
  await authenticate(page);
  await page.goto('/admin');
  await page.getByRole('button', { name: '新增题目', exact: true }).click();
  const dialog = page.getByRole('dialog');
  const slug = 'browser-' + Date.now();
  await dialog.getByLabel('标题', { exact: true }).fill(slug);
  await dialog.getByLabel('题目标识', { exact: true }).fill(slug);
  await dialog.getByLabel('题目描述', { exact: true }).fill('Return the input.');
  await dialog.getByLabel('输入说明', { exact: true }).fill('A string');
  await dialog.getByLabel('输出说明', { exact: true }).fill('The same string');
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith('/api/problems') && response.request().method() === 'POST',
  );
  await dialog.getByRole('button', { name: '保存题目', exact: true }).click();
  const response = await responsePromise;
  expect(response.ok()).toBeTruthy();
  const problem = await response.json();
  created.problems.push(problem.id);
  await expect(dialog).not.toBeVisible();
  await expect(page.getByText(slug, { exact: true })).toBeVisible();
  await page.goto('/problems/' + problem.id);
  await expect(page.getByRole('heading', { name: slug })).toBeVisible();
});

test('blog publication renders user content as text', async ({ page }) => {
  await authenticate(page);
  await page.goto('/community');
  await page.getByRole('button', { name: '写博客', exact: true }).click();
  const dialog = page.getByRole('dialog');
  const title = 'Browser verification ' + Date.now();
  await dialog.getByLabel('标题', { exact: true }).fill(title);
  await dialog
    .getByLabel('正文', { exact: true })
    .fill('<img src=x onerror=window.__oj_xss=1> Practice notes.');
  const responsePromise = page.waitForResponse(
    (response) => response.url().endsWith('/api/blogs') && response.request().method() === 'POST',
  );
  await dialog.getByRole('button', { name: '保存', exact: true }).click();
  const response = await responsePromise;
  expect(response.ok()).toBeTruthy();
  created.blogs.push((await response.json()).id);
  await expect(dialog).not.toBeVisible();
  await expect(page.getByText(title, { exact: true })).toBeVisible();
  expect(await page.evaluate(() => window.__oj_xss)).toBeUndefined();
});

test('contests, workspace and profile render without JavaScript errors', async ({ page }) => {
  await authenticate(page);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  for (const [url, name] of [
    ['/contests', '把练习，变成比赛。'],
    ['/workspace', '把思路，写成作品。'],
    ['/users/1', env.ADMIN_USERNAME],
  ]) {
    await page.goto(url);
    await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
  }
  expect(errors).toEqual([]);
});

test('an existing proposal can be edited from the workspace', async ({ page, request }) => {
  const slug = 'browser-proposal-' + Date.now();
  const response = await request.post('/api/problem-proposals', {
    headers: { Authorization: 'Bearer ' + token },
    data: {
      problem: {
        title: slug,
        slug,
        description: 'Statement',
        input_description: 'Input',
        output_description: 'Output',
        samples: [],
        time_limit_ms: 1000,
        memory_limit_mb: 256,
        difficulty: 800,
        tags: [],
        source: 'Browser verification',
        is_public: false,
        test_cases: [{ order: 1, input: '1', output: '1', score: 100, is_sample: false }],
      },
      standard_language: 'CPP',
      standard_code: 'int main(){}',
    },
  });
  expect(response.ok()).toBeTruthy();
  const proposal = await response.json();
  created.proposals.push(proposal.id);
  await authenticate(page);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/workspace');
  await page
    .getByRole('row')
    .filter({ hasText: slug })
    .getByRole('button', { name: '编辑', exact: true })
    .click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await expect(dialog.getByLabel('标题', { exact: true })).toHaveValue(slug);
  await dialog.getByLabel('标题', { exact: true }).fill(slug + ' edited');
  await dialog.getByRole('button', { name: '提交审核', exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.getByText(slug + ' edited', { exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});

test('mobile layout fits the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await authenticate(page);
  for (const url of [
    '/',
    '/problems/1',
    '/auth',
    '/contests',
    '/community',
    '/submissions',
    '/workspace',
    '/admin',
    '/users/1',
  ]) {
    await page.goto(url);
    await expect(page.locator('h1')).toBeVisible();
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
      url,
    ).toBeTruthy();
  }
  await page.goto('/');
  await page.screenshot({ path: path.join(root, '.runtime', 'mobile.png'), fullPage: true });
});

test('reading and coding stay side by side on desktop and stack on a phone', async ({ page }) => {
  await page.goto('/problems/1');
  const statement = page.locator('.statement-panel');
  const editor = page.locator('.editor-panel');
  await expect(statement).toBeVisible();
  const left = await statement.boundingBox(),
    right = await editor.boundingBox();
  expect(right.x).toBeGreaterThanOrEqual(left.x + left.width);
  const source = page.getByLabel('Source code');
  await source.fill(Array.from({ length: 80 }, (_, i) => '// line ' + (i + 1)).join('\n'));
  await source.evaluate((el) => {
    el.scrollTop = 400;
    el.dispatchEvent(new Event('scroll'));
  });
  await expect.poll(() => page.locator('.line-numbers').evaluate((el) => el.scrollTop)).toBe(400);
  await page.setViewportSize({ width: 390, height: 844 });
  const top = await statement.boundingBox(),
    bottom = await editor.boundingBox();
  expect(bottom.y).toBeGreaterThan(top.y + top.height);
  expect((await page.locator('.editorials-panel').boundingBox()).y).toBeGreaterThan(
    bottom.y + bottom.height,
  );
  await expect(source).toHaveValue(/\/\/ line 80$/);
});

test('problem archive distinguishes a load failure from an empty search and can retry', async ({
  page,
}) => {
  let fail = true;
  await page.route(/\/api\/problems\?/, (route) =>
    fail
      ? route.fulfill({ status: 503, json: { message: 'Temporarily unavailable' } })
      : route.continue(),
  );
  await page.goto('/');
  await expect(page.getByText('题目加载失败，请稍后重试。')).toBeVisible();
  fail = false;
  await page.getByRole('button', { name: '重试', exact: true }).click();
  await expect(page.getByRole('link', { name: 'A + B', exact: true })).toBeVisible();
  await page.getByPlaceholder('搜索题目、来源').fill('no-such-problem-visual-check');
  await page.getByPlaceholder('搜索题目、来源').press('Enter');
  await expect(page.getByText('没有找到匹配的题目，试试其他筛选条件。')).toBeVisible();
});
