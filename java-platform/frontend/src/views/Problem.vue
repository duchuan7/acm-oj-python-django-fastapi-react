<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api, items } from '../api.js';
import { t, session } from '../session.js';
const route = useRoute(),
  router = useRouter(),
  problem = ref(null),
  language = ref('CPP'),
  code = ref(''),
  busy = ref(false),
  editorials = ref([]);
onMounted(async () => {
  try {
    problem.value = await api(
      '/problems/' +
        route.params.id +
        (route.query.contest ? '?contest=' + route.query.contest : ''),
    );
    editorials.value = items(await api('/problem-solutions?problem=' + route.params.id));
  } catch {}
});
async function submit() {
  if (!session.user) {
    router.push('/auth');
    return;
  }
  busy.value = true;
  try {
    const s = await api('/submissions', {
      method: 'POST',
      body: {
        problem: Number(route.params.id),
        contest: route.query.contest ? Number(route.query.contest) : null,
        language: language.value,
        code: code.value,
      },
    });
    router.push('/submissions?id=' + s.id);
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <template v-if="problem"
    ><div class="page-heading">
      <div>
        <div class="eyebrow">Problem / {{ problem.id }}</div>
        <h1>{{ problem.title }}</h1>
        <div class="tags">
          <el-tag v-for="tag in problem.tags" :key="tag" type="info" size="small">{{ tag }}</el-tag>
        </div>
      </div>
      <router-link :to="'/submissions?problem=' + problem.id"
        >{{ t('查看提交', 'Submissions') }} →</router-link
      >
    </div>
    <div class="two-col">
      <div>
        <section class="panel">
          <h2>{{ t('题目描述', 'Statement') }}</h2>
          <div class="statement">{{ problem.description }}</div>
          <h3>{{ t('输入', 'Input') }}</h3>
          <div class="statement">{{ problem.input_description }}</div>
          <h3>{{ t('输出', 'Output') }}</h3>
          <div class="statement">{{ problem.output_description }}</div>
          <template v-for="(s, i) in problem.samples" :key="i"
            ><h3>{{ t('样例', 'Sample') }} {{ i + 1 }}</h3>
            <div class="form-grid">
              <pre>{{ s.input }}</pre>
              <pre>{{ s.output }}</pre>
            </div></template
          >
        </section>
        <section class="panel">
          <div class="toolbar">
            <h2 style="margin: 0">{{ t('提交代码', 'Submit solution') }}</h2>
            <el-select v-model="language" aria-label="Language"
              ><el-option
                v-for="v in ['C', 'CPP', 'JAVA', 'PYTHON']"
                :key="v"
                :value="v"
                :label="v"
            /></el-select>
          </div>
          <p class="muted">
            {{
              language === 'JAVA'
                ? 'Java 21 · public class Main'
                : language === 'CPP'
                  ? 'C++17'
                  : language === 'C'
                    ? 'C17'
                    : 'Python 3'
            }}
            · 64 KiB
          </p>
          <el-input
            v-model="code"
            class="code"
            type="textarea"
            :rows="18"
            :placeholder="t('在这里编写代码…', 'Write your solution here…')"
            aria-label="Source code"
          />
          <div class="action-row">
            <el-button type="primary" :loading="busy" @click="submit">{{
              session.user ? t('提交评测', 'Submit') : t('登录后提交', 'Sign in to submit')
            }}</el-button>
          </div>
        </section>
        <section class="panel">
          <h2>{{ t('题解', 'Editorials') }}</h2>
          <div v-if="!editorials.length" class="muted">
            {{ t('暂无已通过审核的题解。', 'No approved editorials yet.') }}
          </div>
          <div v-for="e in editorials" :key="e.id" class="list-card">
            <div>
              <h3>
                {{ e.title }} <el-tag size="small" type="info">{{ e.status }}</el-tag>
              </h3>
              <p class="muted">{{ e.author_username }}</p>
              <div class="statement">{{ e.content }}</div>
            </div>
          </div>
        </section>
      </div>
      <aside class="side-card">
        <h2>{{ t('题目信息', 'Details') }}</h2>
        <div class="stat">
          <span>{{ t('时间', 'Time') }}</span
          ><b>{{ problem.time_limit_ms }} ms</b>
        </div>
        <div class="stat">
          <span>{{ t('内存', 'Memory') }}</span
          ><b>{{ problem.memory_limit_mb }} MiB</b>
        </div>
        <div class="stat">
          <span>{{ t('难度', 'Rating') }}</span
          ><b>{{ problem.difficulty || '—' }}</b>
        </div>
        <div class="stat">
          <span>{{ t('来源', 'Source') }}</span
          ><span>{{ problem.source || '—' }}</span>
        </div>
      </aside>
    </div></template
  >
  <el-empty v-else :description="t('题目不可用', 'Problem unavailable')" />
</template>
