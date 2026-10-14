<script setup>
import { api } from './api.js';
import { session,language,t,staff,admin,setSession } from './session.js';
import { router } from './router.js';
function toggle(){language.value=language.value==='zh'?'en':'zh';localStorage.setItem('oj_java_lang',language.value);}
async function logout(){try{await api('/auth/logout',{method:'POST'});}finally{setSession(null);router.push('/');}}
</script>
<template>
  <div class="shell">
    <header class="topbar">
      <router-link to="/" class="brand"><span class="brand-mark">d.</span><span>duilio <b>OJ</b></span></router-link>
      <nav>
        <router-link to="/">{{ t('题库','Problems') }}</router-link>
        <router-link to="/contests">{{ t('比赛','Contests') }}</router-link>
        <router-link to="/submissions">{{ t('提交','Submissions') }}</router-link>
        <router-link to="/community">{{ t('社区','Community') }}</router-link>
        <router-link v-if="session.user" to="/workspace">{{ t('我的创作','Workspace') }}</router-link>
        <router-link v-if="staff()" to="/admin">{{ t('管理','Manage') }}</router-link>
      </nav>
      <div class="account">
        <el-button text @click="toggle">{{ language==='zh'?'EN':'中文' }}</el-button>
        <template v-if="session.user">
          <router-link :to="'/users/'+session.user.id">{{ session.user.username }}</router-link>
          <el-tag size="small" type="info">{{ session.user.role }}</el-tag>
          <el-button text @click="logout">{{ t('退出','Sign out') }}</el-button>
        </template>
        <router-link v-else to="/auth" class="signin">{{ t('登录 / 注册','Sign in') }}</router-link>
      </div>
    </header>
    <main><router-view :key="$route.fullPath" /></main>
    <footer><span>duilio OJ · {{ t('写代码，解问题。','Write code. Solve problems.') }}</span><span>ACM / ICPC</span></footer>
  </div>
</template>

