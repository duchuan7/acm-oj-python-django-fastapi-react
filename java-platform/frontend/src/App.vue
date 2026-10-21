<script setup>
import { api } from './api.js';
import { watch } from 'vue';
import { session, language, t, staff, setSession } from './session.js';
import { router } from './router.js';
watch(language, (value) => (document.documentElement.lang = value === 'zh' ? 'zh-CN' : 'en'), {
  immediate: true,
});
function toggle() {
  language.value = language.value === 'zh' ? 'en' : 'zh';
  localStorage.setItem('oj_java_lang', language.value);
}
async function logout() {
  try {
    await api('/auth/logout', { method: 'POST' });
  } finally {
    setSession(null);
    router.push('/');
  }
}
</script>
<template>
  <div class="shell">
    <a class="skip-link" href="#main-content">{{ t('跳至主要内容', 'Skip to content') }}</a>
    <header class="topbar">
      <div class="header-inner">
        <router-link to="/" class="brand"
          ><span class="brand-mark" aria-hidden="true"
            ><svg viewBox="0 0 36 36" fill="none">
              <path
                d="M12 9 4 18l8 9M24 9l8 9-8 9M21 4l-6 28"
                stroke="currentColor"
                stroke-width="2.3"
                stroke-linecap="round"
                stroke-linejoin="round"
              /></svg></span
          ><span>duilio<b>OJ</b></span></router-link
        >
        <nav class="primary-nav" :aria-label="t('主导航', 'Main navigation')">
          <router-link to="/" :class="{ 'is-current': $route.path.startsWith('/problems/') }">{{
            t('题库', 'Problems')
          }}</router-link>
          <router-link to="/contests">{{ t('比赛', 'Contests') }}</router-link>
          <router-link to="/submissions">{{ t('提交', 'Submissions') }}</router-link>
          <router-link to="/community">{{ t('社区', 'Community') }}</router-link>
          <router-link v-if="session.user" to="/workspace">{{
            t('我的创作', 'Workspace')
          }}</router-link>
          <router-link v-if="staff()" to="/admin">{{ t('管理', 'Manage') }}</router-link>
        </nav>
        <div class="account">
          <el-button text @click="toggle">{{ language === 'zh' ? 'EN' : '中文' }}</el-button>
          <template v-if="session.user">
            <router-link :to="'/users/' + session.user.id">{{ session.user.username }}</router-link>
            <el-tag size="small" type="info">{{ session.user.role }}</el-tag>
            <el-button text @click="logout">{{ t('退出', 'Sign out') }}</el-button>
          </template>
          <router-link v-else to="/auth" class="signin">{{
            t('登录 / 注册', 'Sign in')
          }}</router-link>
        </div>
      </div>
    </header>
    <main id="main-content" tabindex="-1"><router-view :key="$route.fullPath" /></main>
    <footer class="site-footer">
      <div class="footer-inner">
        <span
          ><span class="footer-brand">duilio</span
          >{{ t('给思考一点空间。', 'A little room to think.') }}</span
        ><span class="footer-note">CRAFT YOUR NEXT ACCEPTED &nbsp; / &nbsp; ACM · ICPC</span>
      </div>
    </footer>
  </div>
</template>
