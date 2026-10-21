<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { api, items, date } from '../api.js';
import { session, t } from '../session.js';
const route = useRoute(),
  rows = ref([]),
  detail = ref(null),
  count = ref(0),
  page = ref(1),
  language = ref(''),
  status = ref(''),
  open = ref(false);
let timer,
  refreshing = false;
async function load() {
  if (!session.user || refreshing) return;
  refreshing = true;
  try {
    const q = new URLSearchParams({ page: page.value });
    for (const key of ['problem', 'contest', 'author'])
      if (route.query[key]) q.set(key, route.query[key]);
    if (language.value) q.set('language', language.value);
    if (status.value) q.set('status', status.value);
    const data = await api('/submissions?' + q);
    rows.value = items(data);
    count.value = data.count;
    if (open.value && detail.value && ['PENDING', 'JUDGING'].includes(detail.value.verdict))
      detail.value = await api('/submissions/' + detail.value.id);
  } finally {
    refreshing = false;
  }
}
async function show(id) {
  detail.value = await api('/submissions/' + id);
  open.value = true;
}
onMounted(async () => {
  if (!session.user) return;
  await load().catch(() => {});
  if (route.query.id) await show(route.query.id).catch(() => {});
  timer = setInterval(() => load().catch(() => {}), 3000);
});
onUnmounted(() => clearInterval(timer));
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="eyebrow">Submission log</div>
      <h1>{{ t('每一次尝试，都算数。', 'Every attempt counts.') }}</h1>
      <p class="subtitle">
        {{ t('评测中的提交会自动更新。', 'Pending verdicts update automatically.') }}
      </p>
    </div>
  </div>
  <section v-if="session.user" class="panel">
    <div class="toolbar">
      <el-select v-model="language" clearable :placeholder="t('所有语言', 'All languages')"
        ><el-option v-for="v in ['C', 'CPP', 'JAVA', 'PYTHON']" :key="v" :value="v" /></el-select
      ><el-select v-model="status" clearable :placeholder="t('所有状态', 'All verdicts')"
        ><el-option
          v-for="v in [
            'PENDING',
            'JUDGING',
            'ACCEPTED',
            'WRONG_ANSWER',
            'TIME_LIMIT_EXCEEDED',
            'MEMORY_LIMIT_EXCEEDED',
            'COMPILE_ERROR',
            'RUNTIME_ERROR',
            'OUTPUT_LIMIT_EXCEEDED',
            'SYSTEM_ERROR',
          ]"
          :key="v"
          :value="v" /></el-select
      ><el-button
        @click="
          page = 1;
          load();
        "
        >{{ t('筛选', 'Filter') }}</el-button
      >
    </div>
    <el-table :data="rows"
      ><el-table-column prop="id" label="#" width="80" /><el-table-column
        prop="problem_title"
        :label="t('题目', 'Problem')"
        min-width="150"
      /><el-table-column prop="username" :label="t('用户', 'User')" width="120" /><el-table-column
        prop="language"
        label="Lang"
        width="85"
      /><el-table-column :label="t('结果', 'Verdict')" min-width="200"
        ><template #default="{ row }"
          ><span :class="['verdict', row.verdict]">{{ row.verdict }}</span></template
        ></el-table-column
      ><el-table-column prop="score" :label="t('分数', 'Score')" width="65" /><el-table-column
        label="ms"
        prop="max_time_ms"
        width="65"
      /><el-table-column width="90"
        ><template #default="{ row }"
          ><el-button text @click="show(row.id)">{{ t('详情', 'Detail') }}</el-button></template
        ></el-table-column
      ></el-table
    >
    <el-pagination
      style="margin-top: 20px"
      layout="prev,pager,next"
      :page-size="30"
      :total="count"
      v-model:current-page="page"
      @current-change="load"
    />
  </section>
  <el-empty v-else :description="t('请先登录查看提交', 'Sign in to see submissions')"
    ><router-link to="/auth"
      ><el-button type="primary">{{ t('登录', 'Sign in') }}</el-button></router-link
    ></el-empty
  >
  <el-dialog
    v-model="open"
    :title="t('提交详情', 'Submission detail') + ' #' + detail?.id"
    width="850px"
    ><template v-if="detail"
      ><div class="submission-summary">
        <span :class="['verdict', detail.verdict]">{{ detail.verdict }}</span
        ><span>{{ detail.score }} / 100</span><span>{{ date(detail.submitted_at) }}</span>
      </div>
      <div class="detail-metrics">
        <span
          >{{ t('用时', 'Time') }}<b>{{ detail.max_time_ms ?? '—' }} ms</b></span
        ><span
          >{{ t('内存', 'Memory') }}<b>{{ detail.max_memory_kb ?? '—' }} KiB</b></span
        ><span
          >{{ t('语言', 'Language') }}<b>{{ detail.language }}</b></span
        >
      </div>
      <h3 v-if="detail.compile_message">{{ t('编译信息', 'Compiler output') }}</h3>
      <pre v-if="detail.compile_message">{{ detail.compile_message }}</pre>
      <el-table :data="detail.case_results"
        ><el-table-column prop="status" label="Verdict" min-width="200"
          ><template #default="{ row }"
            ><span :class="['verdict', row.status]">{{ row.status }}</span></template
          ></el-table-column
        ><el-table-column prop="time_used" label="ms" /><el-table-column
          prop="memory_used"
          label="KiB" /><el-table-column prop="score" label="Score"
      /></el-table>
      <h3>{{ t('提交的代码', 'Source code') }}</h3>
      <pre v-if="detail.code">{{ detail.code }}</pre>
      <p v-else class="subtitle">
        {{
          t(
            '源码仅对作者及有权限的成员展示。',
            'Source code is available to its author and authorized members.',
          )
        }}
      </p>
    </template></el-dialog
  >
</template>
