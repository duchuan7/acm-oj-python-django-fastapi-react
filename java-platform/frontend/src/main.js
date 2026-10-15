import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import './style.css';
import App from './App.vue';
import { router } from './router.js';
import { api } from './api.js';
import { session, setSession } from './session.js';
if (session.token) {
  try {
    session.user = await api('/auth/me', { quiet: true });
  } catch {
    setSession(null);
  }
}
createApp(App).use(router).use(ElementPlus).mount('#app');
