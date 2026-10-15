<script setup>
import { ref, onMounted } from 'vue';
import { api, items } from '../api.js';
import { t } from '../session.js';
import PracticeArt from '../components/PracticeArt.vue';
const rows = ref([]),
  leaders = ref([]),
  count = ref(0),
  page = ref(1),
  loading = ref(false),
  failed = ref(false);
const search = ref(''),
  tag = ref(''),
  min = ref(null),
  max = ref(null);
async function load() {
  loading.value = true;
  failed.value = false;
  try {
    const q = new URLSearchParams({ page: page.value });
    if (search.value) q.set('search', search.value);
    if (tag.value) q.set('tag', tag.value);
    if (min.value !== null) q.set('difficulty_min', min.value);
    if (max.value !== null) q.set('difficulty_max', max.value);
    const data = await api('/problems?' + q);
    rows.value = items(data);
    count.value = data.count;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}
function filter() {
  page.value = 1;
  load();
}
onMounted(() => {
  load();
  api('/users/leaderboard')
    .then((v) => (leaders.value = items(v)))
    .catch(() => {});
});
</script>
<template>
  <section class="hero">
    <div>
      <div class="eyebrow"><span class="eyebrow-rule"></span>The art of problem solving</div>
      <h1>{{ t('从一道题开始。', 'Start with one problem.') }}</h1>
      <p class="subtitle">
        {{
          t(
            '留一点时间给思考，让每一个想法都有机会成为答案。',
            'Make room for a little thought. Give every idea a chance to become a solution.',
          )
        }}
      </p>
      <div class="hero-actions">
        <a class="hero-button" href="#problem-archive"
          >{{ t('浏览题库', 'Explore problems') }}<span aria-hidden="true">↗</span></a
        >
        <router-link class="text-link" to="/contests"
          >{{ t('参加一场比赛', 'Find a contest') }}<span aria-hidden="true">→</span></router-link
        >
      </div>
    </div>
    <PracticeArt />
  </section>
  <div class="two-col" id="problem-archive">
    <section>
      <div class="section-heading">
        <h2>
          {{ t('题目集', 'Problem archive') }}<span class="count-badge">{{ count }}</span>
        </h2>
        <span class="section-note">EXPLORE · SOLVE · GROW</span>
      </div>
      <div class="panel archive-panel">
        <form class="archive-filters" @submit.prevent="filter">
          <el-input
            class="search-field"
            v-model="search"
            clearable
            :placeholder="t('搜索题目、来源', 'Search title or source')"
            :aria-label="t('搜索题目、来源', 'Search title or source')"
            ><template #prefix
              ><svg class="search-icon" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.4" />
                <path
                  d="m13 13 4 4"
                  stroke="currentColor"
                  stroke-width="1.4"
                  stroke-linecap="round"
                /></svg></template
          ></el-input>
          <el-input
            class="tag-field"
            v-model="tag"
            clearable
            :placeholder="t('精确标签', 'Exact tag')"
            :aria-label="t('精确标签', 'Exact tag')"
          />
          <el-input-number
            v-model="min"
            :placeholder="t('最低难度', 'Min rating')"
            :aria-label="t('最低难度', 'Min rating')"
            :min="0"
            :controls="false"
          />
          <el-input-number
            v-model="max"
            :placeholder="t('最高难度', 'Max rating')"
            :aria-label="t('最高难度', 'Max rating')"
            :min="0"
            :controls="false"
          />
          <el-button class="filter-submit" native-type="submit">{{
            t('筛选', 'Filter')
          }}</el-button>
        </form>
        <el-table :data="rows" v-loading="loading" :aria-label="t('题目列表', 'Problem list')">
          <el-table-column label="#" width="52"
            ><template #default="{ row }"
              ><span class="problem-id">{{ String(row.id).padStart(3, '0') }}</span></template
            ></el-table-column
          >
          <el-table-column :label="t('题目', 'Problem')" min-width="200"
            ><template #default="{ row }"
              ><div class="problem-title-cell">
                <div>
                  <router-link class="problem-link" :to="'/problems/' + row.id">{{
                    row.title
                  }}</router-link>
                  <div class="tags" v-if="row.tags?.length" style="margin-top: 7px">
                    <el-tag v-for="v in row.tags" :key="v" size="small" type="info">{{ v }}</el-tag>
                  </div>
                </div>
                <span class="problem-row-arrow" aria-hidden="true">↗</span>
              </div></template
            ></el-table-column
          >
          <el-table-column :label="t('难度', 'Rating')" width="75"
            ><template #default="{ row }"
              ><span class="mono">{{ row.difficulty || '—' }}</span></template
            ></el-table-column
          >
          <el-table-column :label="t('通过 / 提交', 'AC / All')" width="100" align="right"
            ><template #default="{ row }"
              ><span class="mono"
                >{{ row.accepted_count || 0
                }}<span class="muted"> / {{ row.submission_count || 0 }}</span></span
              ></template
            ></el-table-column
          >
          <template #empty
            ><div class="empty">
              <template v-if="failed"
                >{{ t('题目加载失败，请稍后重试。', 'Could not load problems. Please try again.')
                }}<el-button text type="primary" @click="load">{{
                  t('重试', 'Retry')
                }}</el-button></template
              ><template v-else>{{
                t(
                  '没有找到匹配的题目，试试其他筛选条件。',
                  'No matching problems. Try a different filter.',
                )
              }}</template>
            </div></template
          >
        </el-table>
        <p class="mobile-table-hint">
          {{ t('左右滑动查看完整列表', 'Swipe to see the full table') }} ↔
        </p>
        <div class="archive-footer">
          <span>C17 / C++17 / Java 21 / Python 3</span
          ><el-pagination
            layout="prev,pager,next"
            :page-size="30"
            :total="count"
            v-model:current-page="page"
            @current-change="load"
          />
        </div>
      </div>
    </section>
    <aside class="practice-aside">
      <section class="board-card">
        <div class="eyebrow">The practice board</div>
        <h2>{{ t('解题榜', 'Top solvers') }}</h2>
        <p class="board-caption">
          {{ t('解题榜 · 按通过题目数排序', 'Top solvers · ranked by problems solved') }}
        </p>
        <p v-if="!leaders.length" class="board-caption">
          {{ t('提交你的第一份解答。', 'Submit your first solution.') }}
        </p>
        <router-link
          v-for="(u, i) in leaders"
          :key="u.user_id"
          class="leader-row"
          :to="'/users/' + u.user_id"
          ><span class="leader-rank">{{ String(i + 1).padStart(2, '0') }}</span
          ><span class="leader-avatar" aria-hidden="true">{{
            u.username.slice(0, 1).toUpperCase()
          }}</span
          ><span class="leader-name">{{ u.username }}</span
          ><span class="leader-score">{{ u.solved_count }}</span></router-link
        >
      </section>
      <section class="practice-note">
        <div class="eyebrow">A note for your practice</div>
        <h3>{{ t('不急，想清楚再写。', 'Take your time. Think it through.') }}</h3>
        <p>
          {{
            t(
              '读懂题意，尝试样例，再把思路写成代码。每一次提交，都是下一次进步的起点。',
              'Read the statement, work through a sample, then put your idea into code. Every attempt is a place to begin again.',
            )
          }}
        </p>
        <router-link class="text-link" to="/submissions"
          >{{ t('回看我的提交', 'Review my attempts')
          }}<span aria-hidden="true">→</span></router-link
        >
      </section>
    </aside>
  </div>
</template>
