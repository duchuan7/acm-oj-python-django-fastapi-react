import { test, expect } from '@playwright/test';
import fs from 'node:fs';

const state = JSON.parse(fs.readFileSync(process.env.OJ_ACCEPTANCE_STATE, 'utf8'));

async function login(page, user) {
  await page.goto('/auth');
  await page.getByLabel('Username', { exact: true }).fill(user.username);
  await page.getByLabel('Password', { exact: true }).fill(state.password);
  await page.getByRole('button', { name: '登录', exact: true }).click();
  await expect(page.getByRole('link', { name: user.username, exact: true }).first()).toBeVisible();
}

test('a new student registers using a real local email; incorrect code is refused', async ({
  page,
  request,
}) => {
  const user = state.registration;
  await page.goto('/auth');
  await page.getByRole('tab', { name: '注册', exact: true }).click();
  await page.getByLabel('Username', { exact: true }).fill(user.username);
  await page.getByLabel('Email', { exact: true }).fill(user.email);
  await page.getByLabel('Password', { exact: true }).fill(state.password);
  await page.getByRole('button', { name: '发送验证码', exact: true }).click();
  let code;
  await expect
    .poll(async () => {
      const inbox = await (await request.get(state.mail + '/api/v1/messages')).json();
      const message = inbox.messages.find((m) => m.To.some((p) => p.Address === user.email));
      if (!message) return false;
      const detail = await (await request.get(state.mail + '/api/v1/message/' + message.ID)).json();
      code = detail.Text.match(/code is (\d{6})/)[1];
      return true;
    })
    .toBe(true);
  await page
    .getByLabel('Verification code')
    .fill(String((Number(code) + 1) % 1000000).padStart(6, '0'));
  const rejected = page.waitForResponse((r) => r.url().endsWith('/api/auth/register'));
  await page.getByRole('button', { name: '创建账号', exact: true }).click();
  expect((await rejected).status()).toBe(400);
  await page.getByLabel('Verification code').fill(code);
  await page.getByRole('button', { name: '创建账号', exact: true }).click();
  await expect(page.getByRole('link', { name: user.username, exact: true }).first()).toBeVisible();
  await expect(page.getByRole('link', { name: '管理', exact: true })).toHaveCount(0);
  await page.reload();
  await expect(page.getByRole('link', { name: user.username, exact: true }).first()).toBeVisible();
});

test('student publishes an editorial; coach cannot approve; administrator approves it', async ({
  browser,
}) => {
  const contexts = await Promise.all([
    browser.newContext({ baseURL: state.web }),
    browser.newContext({ baseURL: state.web }),
    browser.newContext({ baseURL: state.web }),
  ]);
  try {
    const [member, coach, admin] = await Promise.all(contexts.map((c) => c.newPage()));
    await Promise.all([
      login(member, state.students[0]),
      login(coach, state.coaches[0]),
      login(admin, state.admin),
    ]);
    await member.goto('/workspace');
    await member.getByRole('tab', { name: '我的题解', exact: true }).click();
    await member.getByRole('button', { name: '新建', exact: true }).click();
    const dialog = member.getByRole('dialog');
    await dialog.getByLabel('题目', { exact: true }).click();
    await member
      .getByRole('option', {
        name: state.problems[0].id + '. ' + state.problems[0].title,
        exact: true,
      })
      .click();
    await dialog.getByLabel('标题', { exact: true }).fill('Acceptance editorial');
    await dialog
      .getByLabel('正文', { exact: true })
      .fill('Compute the sum. <img src=x onerror=window.bad=1>');
    await dialog.getByRole('button', { name: '提交审核', exact: true }).click();
    await expect(dialog).not.toBeVisible();
    await coach.goto('/admin');
    await coach.getByRole('tab', { name: '题解审核', exact: true }).click();
    await expect(coach.getByText('Acceptance editorial', { exact: true })).toBeVisible();
    await expect(coach.getByRole('button', { name: '通过', exact: true })).toHaveCount(0);
    await admin.goto('/admin');
    await admin.getByRole('tab', { name: '题解审核', exact: true }).click();
    await admin
      .getByRole('row')
      .filter({ hasText: 'Acceptance editorial' })
      .getByRole('button', { name: '通过', exact: true })
      .click();
    await admin
      .getByRole('dialog')
      .getByRole('button', { name: /确认|确定|OK/ })
      .click();
    await member.goto('/problems/' + state.problems[0].id);
    await expect(member.getByRole('heading', { name: /Acceptance editorial/ })).toBeVisible();
    expect(await member.evaluate(() => window.bad)).toBeUndefined();
  } finally {
    await Promise.all(contexts.map((c) => c.close()));
  }
});

test('network interruption, expired session, mobile navigation and keyboard problem links recover', async ({
  page,
  context,
}) => {
  await page.addInitScript(
    (token) => localStorage.setItem('oj_java_token', token),
    state.students[1].token,
  );
  await page.goto('/');
  await expect(page.getByRole('link', { name: 'Acceptance 1', exact: true })).toBeVisible();
  await context.setOffline(true);
  await page.reload().catch(() => {});
  await context.setOffline(false);
  await page.goto('/');
  await expect(page.getByRole('link', { name: 'Acceptance 1', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Acceptance 1', exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Acceptance 1', exact: true })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
  ).toBeTruthy();
  await page.evaluate(() => localStorage.setItem('oj_java_token', 'expired.invalid.token'));
  // Clear the original init hook by using the current page's client-side route.
  await page.goto('/auth');
  await page.evaluate(() => localStorage.setItem('oj_java_token', 'expired.invalid.token'));
  const fresh = await context.browser().newContext({ viewport: { width: 390, height: 844 } });
  try {
    await fresh.addInitScript(() => localStorage.setItem('oj_java_token', 'expired.invalid.token'));
    const expired = await fresh.newPage();
    await expired.goto(state.web);
    await expect(expired.getByRole('link', { name: '登录 / 注册', exact: true })).toBeVisible();
    await expect(expired.getByRole('link', { name: 'Acceptance 1', exact: true })).toBeVisible();
  } finally {
    await fresh.close();
  }
});
