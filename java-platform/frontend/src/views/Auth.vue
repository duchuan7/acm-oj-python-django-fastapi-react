<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { api } from '../api.js';
import { t,setSession } from '../session.js';
const router=useRouter(),tab=ref('login'),busy=ref(false);
const form=ref({username:'',email:'',password:'',code:'',school:'',real_name:''});
async function code(){await api(tab.value==='reset'?'/auth/password-reset-code':'/auth/registration-code',{method:'POST',body:{email:form.value.email}});ElMessage.success(t('验证码已发送','Code sent'));}
async function submit(){busy.value=true;try{if(tab.value==='reset'){await api('/auth/password-reset',{method:'POST',body:form.value});ElMessage.success(t('密码已更新，请登录','Password updated'));tab.value='login';return;}const data=await api('/auth/'+(tab.value==='login'?'login':'register'),{method:'POST',body:form.value});setSession(data);router.push('/');}finally{busy.value=false;}}
</script>
<template>
  <div class="auth-panel"><div class="page-heading"><div><div class="eyebrow">Your next accepted</div><h1>{{ t('欢迎回来。','Welcome back.') }}</h1><p class="subtitle">{{ t('继续你的下一次突破。','Pick up where you left off.') }}</p></div></div>
    <section class="panel"><el-tabs v-model="tab"><el-tab-pane :label="t('登录','Sign in')" name="login"/><el-tab-pane :label="t('注册','Register')" name="register"/><el-tab-pane :label="t('重置密码','Reset password')" name="reset"/></el-tabs>
    <el-form label-position="top" @submit.prevent="submit">
      <el-form-item v-if="tab!=='reset'" :label="t('用户名','Username')"><el-input v-model="form.username" autocomplete="username" aria-label="Username" maxlength="150"/></el-form-item>
      <el-form-item v-if="tab!=='login'" :label="t('邮箱','Email')"><el-input v-model="form.email" type="email" autocomplete="email" aria-label="Email"/></el-form-item>
      <el-form-item :label="tab==='reset'?t('新密码','New password'):t('密码','Password')"><el-input v-model="form.password" type="password" show-password :autocomplete="tab==='login'?'current-password':'new-password'" aria-label="Password" @keyup.enter="submit"/></el-form-item>
      <el-form-item v-if="tab!=='login'" :label="t('邮箱验证码','Verification code')"><el-input v-model="form.code" maxlength="6" aria-label="Verification code"><template #append><el-button @click="code">{{ t('发送验证码','Send code') }}</el-button></template></el-input></el-form-item>
      <el-form-item v-if="tab==='register'" :label="t('学校（选填）','School (optional)')"><el-input v-model="form.school" maxlength="128"/></el-form-item>
      <el-button type="primary" :loading="busy" style="width:100%;margin-top:10px" @click="submit">{{ tab==='login'?t('登录','Sign in'):tab==='register'?t('创建账号','Create account'):t('更新密码','Update password') }}</el-button>
    </el-form></section>
  </div>
</template>

