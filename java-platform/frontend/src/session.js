import { reactive, ref } from 'vue';
export const session = reactive({ token: localStorage.getItem('oj_java_token') || '', user: null });
export const language = ref(localStorage.getItem('oj_java_lang') || 'zh');
export const t = (zh, en) => (language.value === 'zh' ? zh : en);
export function setSession(data) {
  session.token = data?.token || '';
  session.user = data?.user || null;
  if (session.token) localStorage.setItem('oj_java_token', session.token);
  else localStorage.removeItem('oj_java_token');
}
export const staff = () => ['ADMIN', 'COACH'].includes(session.user?.role);
export const admin = () => session.user?.role === 'ADMIN';
