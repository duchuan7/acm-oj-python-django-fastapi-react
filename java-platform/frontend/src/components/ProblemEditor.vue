<script setup>
import { t } from '../session.js';
const model=defineModel({required:true});
function addCase(){model.value.test_cases.push({order:model.value.test_cases.length+1,input:'',output:'',score:0,is_sample:false});}
</script>
<template>
  <el-form label-position="top">
    <div class="form-grid">
      <el-form-item :label="t('标题','Title')"><el-input v-model="model.title" maxlength="200"/></el-form-item>
      <el-form-item :label="t('题目标识','Slug')"><el-input v-model="model.slug" placeholder="a-plus-b"/></el-form-item>
      <el-form-item class="wide" :label="t('题目描述','Statement')"><el-input v-model="model.description" type="textarea" :rows="5"/></el-form-item>
      <el-form-item :label="t('输入说明','Input')"><el-input v-model="model.input_description" type="textarea"/></el-form-item>
      <el-form-item :label="t('输出说明','Output')"><el-input v-model="model.output_description" type="textarea"/></el-form-item>
      <el-form-item :label="t('时间限制 / ms','Time limit / ms')"><el-input-number v-model="model.time_limit_ms" :min="100" :max="10000"/></el-form-item>
      <el-form-item :label="t('内存限制 / MiB','Memory limit / MiB')"><el-input-number v-model="model.memory_limit_mb" :min="32" :max="1024"/></el-form-item>
      <el-form-item :label="t('难度','Difficulty')"><el-input-number v-model="model.difficulty" :min="0" :max="10000"/></el-form-item>
      <el-form-item :label="t('来源','Source')"><el-input v-model="model.source" maxlength="200"/></el-form-item>
      <el-form-item :label="t('标签','Tags')"><el-select v-model="model.tags" multiple filterable allow-create default-first-option/></el-form-item>
      <el-form-item :label="t('公开题目','Public')"><el-switch v-model="model.is_public"/></el-form-item>
    </div>
    <h3>{{ t('样例（公开展示）','Samples (public)') }}</h3>
    <div v-for="(s,i) in model.samples" :key="i" class="form-grid">
      <el-form-item :label="'Input '+(i+1)"><el-input v-model="s.input" type="textarea"/></el-form-item>
      <el-form-item :label="'Output '+(i+1)"><el-input v-model="s.output" type="textarea"/></el-form-item>
    </div>
    <el-button text @click="model.samples.push({input:'',output:''})">+ {{ t('添加样例','Add sample') }}</el-button>
    <h3>{{ t('测试数据（分值合计 100）','Testcases (total score: 100)') }}</h3>
    <div v-for="(c,i) in model.test_cases" :key="i" class="panel">
      <div class="toolbar"><span>#{{ i+1 }}</span><el-input-number v-model="c.order" :min="1" style="width:100px"/><el-input-number v-model="c.score" :min="0" :max="100" style="width:100px"/><el-checkbox v-model="c.is_sample">{{ t('样例','Sample') }}</el-checkbox><el-button text type="danger" @click="model.test_cases.splice(i,1)">{{ t('删除','Remove') }}</el-button></div>
      <div class="form-grid"><el-input v-model="c.input" type="textarea" :rows="3" placeholder="Input"/><el-input v-model="c.output" type="textarea" :rows="3" placeholder="Expected output"/></div>
    </div>
    <el-button @click="addCase">+ {{ t('添加测试','Add testcase') }}</el-button>
  </el-form>
</template>

