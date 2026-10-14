<script setup>
import { ref,onMounted } from 'vue';
import { api,items,emptyProblem } from '../api.js';
import { t,admin } from '../session.js';
import ProblemEditor from './ProblemEditor.vue';
const model=defineModel({required:true}),users=ref([]),problems=ref([]);
onMounted(async()=>{try{users.value=items(await api('/users'));problems.value=items(await api('/problems'));}catch{}});
function add(){model.value.contest_problems.push({problem:null,new_problem:null,alias:String.fromCharCode(65+model.value.contest_problems.length),score:100,order:model.value.contest_problems.length+1});}
</script>
<template>
  <el-form label-position="top"><div class="form-grid">
    <el-form-item :label="t('比赛名称','Title')"><el-input v-model="model.title" maxlength="200"/></el-form-item>
    <el-form-item :label="t('赛制','Rule')"><el-select v-model="model.rule"><el-option value="ACM"/><el-option value="IOI"/></el-select></el-form-item>
    <el-form-item :label="t('开始时间','Start')"><el-date-picker v-model="model.start_at" type="datetime" style="width:100%"/></el-form-item>
    <el-form-item :label="t('结束时间','End')"><el-date-picker v-model="model.end_at" type="datetime" style="width:100%"/></el-form-item>
    <el-form-item :label="t('赛前封榜分钟数','Freeze minutes')"><el-input-number v-model="model.freeze_rank_minutes" :min="0"/></el-form-item>
    <el-form-item :label="t('公开比赛（仅管理员）','Public (admin only)')"><el-switch v-model="model.is_public" :disabled="!admin()"/></el-form-item>
    <el-form-item class="wide" :label="t('比赛说明','Description')"><el-input v-model="model.description" type="textarea" :rows="4"/></el-form-item>
    <el-form-item class="wide" :label="t('参赛用户','Participants')"><el-select v-model="model.participants" multiple filterable><el-option v-for="u in users" :key="u.id" :value="u.id" :label="u.username"/></el-select></el-form-item>
  </div>
  <h3>{{ t('比赛题目','Contest problems') }}</h3>
  <div v-for="(p,i) in model.contest_problems" :key="i" class="panel">
    <div class="toolbar"><el-input v-model="p.alias" placeholder="A" style="width:70px"/><el-input-number v-model="p.order" :min="1" style="width:100px"/><el-input-number v-model="p.score" :min="1" :max="100" style="width:100px"/><el-button text type="danger" @click="model.contest_problems.splice(i,1)">{{ t('移除','Remove') }}</el-button></div>
    <el-radio-group :model-value="!!p.new_problem" @update:model-value="v=>{p.new_problem=v?emptyProblem():null;p.problem=null;}"><el-radio :value="false">{{ t('题库选题','Existing problem') }}</el-radio><el-radio :value="true">{{ t('比赛新题','New contest problem') }}</el-radio></el-radio-group>
    <div style="margin-top:20px"><ProblemEditor v-if="p.new_problem" v-model="p.new_problem"/><el-select v-else v-model="p.problem" filterable :placeholder="t('选择题目','Select problem')"><el-option v-for="q in problems" :key="q.id" :label="q.id+'. '+q.title" :value="q.id"/></el-select></div>
  </div><el-button @click="add">+ {{ t('添加题目','Add problem') }}</el-button></el-form>
</template>

