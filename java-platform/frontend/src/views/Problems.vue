<script setup>
import { ref, onMounted } from 'vue';
import { api, items } from '../api.js';
import { t } from '../session.js';
const rows = ref([]),
  leaders = ref([]),
  count = ref(0),
  page = ref(1),
  loading = ref(false);
const search = ref(''),
  tag = ref(''),
  min = ref(null),
  max = ref(null);
async function load() {
  loading.value = true;
  try {
    const q = new URLSearchParams({ page: page.value });
    if (search.value) q.set('search', search.value);
    if (tag.value) q.set('tag', tag.value);
    if (min.value !== null) q.set('difficulty_min', min.value);
    if (max.value !== null) q.set('difficulty_max', max.value);
    const data = await api('/problems?' + q);
    rows.value = items(data);
    count.value = data.count;
  } finally {
    loading.value = false;
  }
}
onMounted(() => {
  load().catch(() => {});
  api('/users/leaderboard')
    .then((v) => (leaders.value = items(v)))
    .catch(() => {});
});
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="eyebrow">Problem archive</div>
      <h1>{{ t('从一道题开始。', 'Start with one problem.') }}</h1>
      <p class="subtitle">
        {{ t('积累每一次思考，把想法变成通过。', 'Turn your ideas into accepted solutions.') }}
      </p>
    </div>
    <span class="muted">{{ count }} {{ t('道题目', 'problems') }}</span>
  </div>
  <div class="two-col">
    <section class="panel">
      <div class="toolbar">
        <el-input
          v-model="search"
          clearable
          :placeholder="t('搜索题目、来源', 'Search title or source')"
          @keyup.enter="
            page = 1;
            load();
          "
        /><el-input
          v-model="tag"
          clearable
          :placeholder="t('精确标签', 'Exact tag')"
          style="width: 130px"
        /><el-input-number
          v-model="min"
          :placeholder="t('最低难度', 'Min rating')"
          :min="0"
          style="width: 125px"
        /><el-input-number
          v-model="max"
          :placeholder="t('最高难度', 'Max rating')"
          :min="0"
          style="width: 125px"
        /><el-button
          type="primary"
          @click="
            page = 1;
            load();
          "
          >{{ t('筛选', 'Filter') }}</el-button
        >
      </div>
      <el-table
        :data="rows"
        v-loading="loading"
        @row-click="(r) => $router.push('/problems/' + r.id)"
        style="cursor: pointer"
      >
        <el-table-column prop="id" label="#" width="65" />
        <el-table-column :label="t('题目', 'Problem')" min-width="210"
          ><template #default="{ row }"
            ><span class="clickable">{{ row.title }}</span>
            <div class="tags" style="margin-top: 8px">
              <el-tag v-for="v in row.tags" :key="v" size="small" type="info">{{ v }}</el-tag>
            </div></template
          ></el-table-column
        >
        <el-table-column prop="difficulty" :label="t('难度', 'Rating')" width="85" />
        <el-table-column :label="t('通过 / 提交', 'AC / All')" width="110"
          ><template #default="{ row }"
            >{{ row.accepted_count || 0 }} / {{ row.submission_count || 0 }}</template
          ></el-table-column
        >
      </el-table>
      <el-pagination
        style="margin-top: 22px"
        layout="prev,pager,next"
        :page-size="30"
        :total="count"
        v-model:current-page="page"
        @current-change="load"
      />
    </section>
    <aside class="side-card">
      <div class="eyebrow">Practice board</div>
      <h2>{{ t('解题榜', 'Top solvers') }}</h2>
      <div v-if="!leaders.length" class="muted">
        {{ t('提交你的第一份解答。', 'Submit your first solution.') }}
      </div>
      <div v-for="(u, i) in leaders" :key="u.user_id" class="stat">
        <router-link :to="'/users/' + u.user_id">{{ i + 1 }}. {{ u.username }}</router-link
        ><b>{{ u.solved_count }}</b>
      </div>
    </aside>
  </div>
</template>
