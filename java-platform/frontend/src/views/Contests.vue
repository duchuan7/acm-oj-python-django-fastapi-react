<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { api, items, date } from '../api.js';
import { session, t } from '../session.js';
import ContestEditor from '../components/ContestEditor.vue';
const rows = ref([]),
  visibility = ref(''),
  open = ref(false),
  busy = ref(false),
  router = useRouter();
const now = ref(Date.now());
const groups = computed(() => [
  {
    key: 'running',
    title: t('进行中', 'Running'),
    rows: rows.value.filter(
      (c) =>
        new Date(c.start_at).getTime() <= now.value && now.value < new Date(c.end_at).getTime(),
    ),
  },
  {
    key: 'upcoming',
    title: t('即将开始', 'Upcoming'),
    rows: rows.value
      .filter((c) => now.value < new Date(c.start_at).getTime())
      .sort((a, b) => new Date(a.start_at) - new Date(b.start_at)),
  },
  {
    key: 'ended',
    title: t('已结束', 'Ended'),
    rows: rows.value
      .filter((c) => now.value >= new Date(c.end_at).getTime())
      .sort((a, b) => new Date(b.end_at) - new Date(a.end_at)),
  },
]);
let clock;
const draft = ref({
  title: '',
  description: '',
  rule: 'ACM',
  start_at: new Date(),
  end_at: new Date(Date.now() + 7200000),
  is_public: false,
  freeze_rank_minutes: 0,
  participants: [],
  contest_problems: [],
});
async function load() {
  rows.value = items(
    await api('/contests' + (visibility.value ? '?visibility=' + visibility.value : '')),
  );
}
async function save() {
  busy.value = true;
  try {
    const c = await api('/contests', { method: 'POST', body: draft.value });
    open.value = false;
    router.push('/contests/' + c.id);
  } finally {
    busy.value = false;
  }
}
onMounted(() => {
  load().catch(() => {});
  clock = setInterval(() => {
    now.value = Date.now();
  }, 1000);
});
onUnmounted(() => clearInterval(clock));
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="eyebrow">Training ground</div>
      <h1>{{ t('把练习，变成比赛。', 'Make practice a contest.') }}</h1>
      <p class="subtitle">
        {{
          t('ACM 与 IOI，公开赛与邀请训练。', 'ACM and IOI. Public rounds and private training.')
        }}
      </p>
    </div>
    <el-button v-if="session.user" type="primary" @click="open = true">{{
      t('创建比赛', 'Create contest')
    }}</el-button>
  </div>
  <section class="panel">
    <div class="toolbar">
      <el-select v-model="visibility" @change="load" :placeholder="t('全部比赛', 'All contests')"
        ><el-option :label="t('全部', 'All')" value="" /><el-option
          :label="t('公开', 'Public')"
          value="public" /><el-option :label="t('私有', 'Private')" value="private"
      /></el-select>
    </div>
    <el-empty v-if="!rows.length" :description="t('暂无可见比赛', 'No contests available')" />
  </section>
  <section
    v-for="group in groups"
    :key="group.key"
    class="panel"
    :aria-labelledby="'contest-' + group.key"
  >
    <div class="section-heading">
      <h2 :id="'contest-' + group.key">
        {{ group.title }}<span class="count-badge">{{ group.rows.length }}</span>
      </h2>
    </div>
    <el-empty
      v-if="!group.rows.length"
      :description="t('暂无比赛', 'No contests')"
      :image-size="48"
    />
    <router-link v-for="c in group.rows" :key="c.id" :to="'/contests/' + c.id" class="list-card"
      ><div>
        <h3>{{ c.title }}</h3>
        <span class="muted">{{ date(c.start_at) }} → {{ date(c.end_at) }}</span>
      </div>
      <div class="tags">
        <el-tag>{{ c.rule }}</el-tag
        ><el-tag type="info">{{ c.is_public ? t('公开', 'Public') : t('私有', 'Private') }}</el-tag>
      </div></router-link
    >
  </section>
  <el-dialog v-model="open" :title="t('创建比赛', 'Create contest')" width="900px"
    ><ContestEditor v-model="draft" /><template #footer
      ><el-button type="primary" :loading="busy" @click="save">{{
        t('保存比赛', 'Save contest')
      }}</el-button></template
    ></el-dialog
  >
</template>
