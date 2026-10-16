<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api, items } from '../api.js';
import { t, session } from '../session.js';
import { ElMessage } from 'element-plus';
const route = useRoute(),
  router = useRouter(),
  problem = ref(null),
  language = ref('CPP'),
  code = ref(''),
  busy = ref(false),
  loading = ref(true),
  editorials = ref([]),
  gutter = ref(null);
const lines = computed(() => Math.max(18, code.value.split('\n').length));
const codeBytes = computed(() => new TextEncoder().encode(code.value).length);
const languageLabel = computed(
  () =>
    ({ C: 'C17', CPP: 'C++17', JAVA: 'Java 21 · public class Main', PYTHON: 'Python 3' })[
      language.value
    ],
);
async function load() {
  loading.value = true;
  try {
    problem.value = await api(
      '/problems/' +
        route.params.id +
        (route.query.contest ? '?contest=' + route.query.contest : ''),
    );
    editorials.value = items(await api('/problem-solutions?problem=' + route.params.id));
  } catch {
  } finally {
    loading.value = false;
  }
}
onMounted(load);
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
function syncGutter(event) {
  if (gutter.value) gutter.value.scrollTop = event.target.scrollTop;
}
async function copySample(text) {
  try {
    await navigator.clipboard.writeText(text || '');
    ElMessage.success(t('已复制', 'Copied'));
  } catch {
    ElMessage.error(
      t('复制失败，请手动选择样例复制。', 'Copy failed. Select the sample to copy it manually.'),
    );
  }
}
</script>
<template>
  <section v-if="loading" class="panel" :aria-label="t('正在加载题目', 'Loading problem')">
    <el-skeleton :rows="10" animated />
  </section>
  <template v-else-if="problem">
    <div class="page-heading problem-heading">
      <div>
        <div class="eyebrow">
          <router-link :to="route.query.contest ? '/contests/' + route.query.contest : '/'">{{
            route.query.contest ? t('返回比赛', 'Back to contest') : t('题目集', 'Problem archive')
          }}</router-link
          ><span>/</span>Problem {{ String(problem.id).padStart(3, '0') }}
        </div>
        <h1>{{ problem.title }}</h1>
        <div v-if="problem.tags?.length" class="tags">
          <el-tag v-for="tag in problem.tags" :key="tag" type="info" size="small">{{ tag }}</el-tag>
        </div>
        <div class="problem-meta">
          <span
            >{{ t('时间限制', 'Time limit') }}<b>{{ problem.time_limit_ms }} ms</b></span
          >
          <span
            >{{ t('内存限制', 'Memory limit') }}<b>{{ problem.memory_limit_mb }} MiB</b></span
          >
          <span
            >{{ t('难度', 'Rating') }}<b>{{ problem.difficulty || '—' }}</b></span
          >
          <span v-if="problem.source"
            >{{ t('来源', 'Source') }}<b>{{ problem.source }}</b></span
          >
        </div>
      </div>
      <router-link class="text-link" :to="'/submissions?problem=' + problem.id"
        >{{ t('查看提交', 'Submissions') }}<span aria-hidden="true">↗</span></router-link
      >
    </div>
    <div class="problem-workbench">
      <div class="reading-column">
        <section class="panel statement-panel">
          <div class="panel-heading">
            <h2>{{ t('题目描述', 'Statement') }}</h2>
            <span class="eyebrow">Read & understand</span>
          </div>
          <div class="statement-body">
            <div class="statement">{{ problem.description }}</div>
            <h3>{{ t('输入', 'Input') }}</h3>
            <div class="statement">{{ problem.input_description }}</div>
            <h3>{{ t('输出', 'Output') }}</h3>
            <div class="statement">{{ problem.output_description }}</div>
            <template v-for="(s, i) in problem.samples" :key="i"
              ><h3>{{ t('样例', 'Sample') }} {{ i + 1 }}</h3>
              <div class="sample-grid">
                <div>
                  <div class="sample-label">
                    <span>{{ t('输入', 'Input') }}</span
                    ><el-button
                      text
                      size="small"
                      :aria-label="t(`复制样例 ${i + 1} 输入`, `Copy sample ${i + 1} input`)"
                      @click="copySample(s.input)"
                      >{{ t('复制', 'Copy') }}</el-button
                    >
                  </div>
                  <pre>{{ s.input }}</pre>
                </div>
                <div>
                  <div class="sample-label">
                    <span>{{ t('输出', 'Output') }}</span
                    ><el-button
                      text
                      size="small"
                      :aria-label="t(`复制样例 ${i + 1} 输出`, `Copy sample ${i + 1} output`)"
                      @click="copySample(s.output)"
                      >{{ t('复制', 'Copy') }}</el-button
                    >
                  </div>
                  <pre>{{ s.output }}</pre>
                </div>
              </div></template
            >
          </div>
        </section>
        <section class="panel editorials-panel">
          <div class="section-heading">
            <h2>
              {{ t('题解', 'Editorials') }}<span class="count-badge">{{ editorials.length }}</span>
            </h2>
          </div>
          <p v-if="!editorials.length" class="subtitle">
            {{
              t(
                '暂无已通过审核的题解。先试着写下你的思路吧。',
                'No approved editorials yet. Try working through your own idea first.',
              )
            }}
          </p>
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
      <section class="panel editor-panel">
        <div class="panel-heading">
          <h2>{{ t('提交代码', 'Submit solution') }}</h2>
          <el-select v-model="language" aria-label="Language"
            ><el-option
              v-for="v in ['C', 'CPP', 'JAVA', 'PYTHON']"
              :key="v"
              :value="v"
              :label="{ C: 'C17', CPP: 'C++17', JAVA: 'Java 21', PYTHON: 'Python 3' }[v]"
          /></el-select>
        </div>
        <div class="editor-meta">
          <span>{{ languageLabel }}</span
          ><span class="mono">{{ (codeBytes / 1024).toFixed(1) }} / 64 KiB</span>
        </div>
        <div class="editor-field">
          <div class="line-numbers" ref="gutter" aria-hidden="true">
            <span v-for="n in lines" :key="n">{{ n }}</span>
          </div>
          <el-input
            v-model="code"
            class="code"
            type="textarea"
            :rows="18"
            wrap="off"
            spellcheck="false"
            autocapitalize="off"
            autocomplete="off"
            :placeholder="t('// 在这里，让思路成为代码。', '// Give your idea a place to begin.')"
            aria-label="Source code"
            @scroll.capture="syncGutter"
          />
        </div>
        <div class="editor-footer">
          <span>{{ t('写好以后，让代码来回答。', 'Ready? Let your code speak.') }}</span
          ><el-button
            type="primary"
            :loading="busy"
            :disabled="!!session.user && (!code.trim() || codeBytes > 65536)"
            @click="submit"
            >{{ session.user ? t('提交评测', 'Submit') : t('登录后提交', 'Sign in to submit')
            }}<span aria-hidden="true">↗</span></el-button
          >
        </div>
      </section>
    </div>
  </template>
  <el-empty v-else :description="t('题目不可用', 'Problem unavailable')"
    ><el-button @click="load">{{ t('重试', 'Retry') }}</el-button></el-empty
  >
</template>
