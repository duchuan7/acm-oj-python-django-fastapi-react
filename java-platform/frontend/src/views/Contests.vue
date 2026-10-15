<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { api, items, date } from '../api.js';
import { session, t } from '../session.js';
import ContestEditor from '../components/ContestEditor.vue';
const rows = ref([]),
  visibility = ref(''),
  open = ref(false),
  busy = ref(false),
  router = useRouter();
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
onMounted(() => load().catch(() => {}));
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
    <router-link v-for="c in rows" :key="c.id" :to="'/contests/' + c.id" class="list-card"
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
