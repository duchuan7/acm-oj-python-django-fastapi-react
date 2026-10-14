import { ElMessage } from 'element-plus';
import { session, setSession, t } from './session.js';
export async function api(path, options = {}, retry = true) {
  const response = await fetch('/api' + path, {
    ...options,
    headers: { 'Content-Type':'application/json', ...(session.token ? { Authorization:'Bearer '+session.token } : {}), ...options.headers },
    body: options.body === undefined ? undefined : JSON.stringify(options.body)
  });
  const data = await response.json().catch(() => ({detail:'HTTP '+response.status}));
  if (response.status===401 && session.token) {
    setSession(null);
    if (retry && (!options.method || options.method==='GET')) return api(path,options,false);
  }
  if (!response.ok) {
    const error = new Error(data.detail || t('请求失败','Request failed'));
    error.status=response.status;
    if (!options.quiet) ElMessage.error(error.message);
    throw error;
  }
  return data;
}
export const items = value => Array.isArray(value) ? value : value?.results || [];
export const date = value => value ? new Date(value).toLocaleString() : '—';
export const emptyProblem = () => ({
  title:'',slug:'',description:'',input_description:'',output_description:'',
  samples:[{input:'',output:''}],time_limit_ms:1000,memory_limit_mb:256,difficulty:800,tags:[],
  source:'',is_public:false,test_cases:[{order:1,input:'',output:'',score:100,is_sample:true}]
});
export function editableProblem(p) {
  return { ...p, test_cases:(p.test_cases||[]).map(c=>({order:c.case_order,input:c.input_text,output:c.output_text,score:c.score,is_sample:c.is_sample})) };
}

