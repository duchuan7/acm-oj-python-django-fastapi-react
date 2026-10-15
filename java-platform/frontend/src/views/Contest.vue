<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api, items, date } from '../api.js';
import { session, staff, t } from '../session.js';
import ContestEditor from '../components/ContestEditor.vue';
const route = useRoute(),
  router = useRouter(),
  contest = ref(null),
  ranks = ref([]),
  frozen = ref(false),
  open = ref(false),
  draft = ref(null);
const canEdit = () => session.user && (staff() || session.user.id === contest.value?.created_by);
async function load() {
  contest.value = await api('/contests/' + route.params.id);
  if (session.user) {
    const r = await api('/contests/' + route.params.id + '/ranklist');
    ranks.value = items(r);
    frozen.value = r.frozen;
  }
}
function edit() {
  draft.value = structuredClone(JSON.parse(JSON.stringify(contest.value)));
  draft.value.contest_problems = draft.value.contest_problems.map((p) => ({
    problem: p.problem,
    new_problem: null,
    alias: p.alias,
    score: p.score,
    order: p.order,
  }));
  open.value = true;
}
async function save() {
  await api('/contests/' + route.params.id, { method: 'PUT', body: draft.value });
  open.value = false;
  await load();
}
async function remove() {
  const { ElMessageBox } = await import('element-plus');
  await ElMessageBox.confirm(t('删除这场比赛？', 'Delete this contest?'));
  await api('/contests/' + route.params.id, { method: 'DELETE' });
  router.push('/contests');
}
onMounted(() => load().catch(() => {}));
</script>
<template>
  <template v-if="contest"
    ><div class="page-heading">
      <div>
        <div class="eyebrow">Contest / {{ contest.rule }}</div>
        <h1>{{ contest.title }}</h1>
        <p class="subtitle">{{ date(contest.start_at) }} → {{ date(contest.end_at) }}</p>
      </div>
      <div v-if="canEdit()" class="toolbar">
        <el-button @click="edit">{{ t('编辑', 'Edit') }}</el-button
        ><el-button type="danger" plain @click="remove">{{ t('删除', 'Delete') }}</el-button>
      </div>
    </div>
    <section class="panel">
      <div class="statement">{{ contest.description }}</div>
    </section>
    <section class="panel">
      <h2>{{ t('比赛题目', 'Problems') }}</h2>
      <el-table :data="contest.contest_problems"
        ><el-table-column prop="alias" label="#" width="70" /><el-table-column
          :label="t('题目', 'Problem')"
          ><template #default="{ row }"
            ><router-link
              class="clickable"
              :to="'/problems/' + row.problem + '?contest=' + contest.id"
              >{{ row.problem_detail?.title }}</router-link
            ></template
          ></el-table-column
        ><el-table-column prop="score" :label="t('分值', 'Score')" width="100"
      /></el-table>
      <p v-if="!contest.contest_problems.length" class="muted">
        {{ t('比赛开始后展示题目。', 'Problems appear after the contest starts.') }}
      </p>
    </section>
    <section class="panel">
      <div class="toolbar">
        <h2 style="margin: 0">{{ t('排行榜', 'Ranklist') }}</h2>
        <el-tag v-if="frozen" type="warning">{{ t('已封榜', 'Frozen') }}</el-tag
        ><el-button text @click="load">{{ t('刷新', 'Refresh') }}</el-button
        ><router-link :to="'/submissions?contest=' + contest.id"
          >{{ t('比赛提交', 'Submissions') }} →</router-link
        >
      </div>
      <el-table v-if="session.user" :data="ranks"
        ><el-table-column prop="rank" label="#" width="70" /><el-table-column
          prop="username"
          :label="t('用户', 'User')" /><el-table-column
          prop="solved"
          :label="t('解题数', 'Solved')" /><el-table-column
          v-if="contest.rule === 'IOI'"
          prop="score"
          :label="t('总分', 'Score')" /><el-table-column
          prop="penalty_minutes"
          :label="t('罚时 / 分钟', 'Penalty / min')"
      /></el-table>
      <p v-else class="muted">{{ t('登录后查看榜单。', 'Sign in to see the ranklist.') }}</p>
    </section></template
  >
  <el-dialog v-model="open" :title="t('编辑比赛', 'Edit contest')" width="900px"
    ><ContestEditor v-if="draft" v-model="draft" /><template #footer
      ><el-button type="primary" @click="save">{{ t('保存', 'Save') }}</el-button></template
    ></el-dialog
  >
</template>
