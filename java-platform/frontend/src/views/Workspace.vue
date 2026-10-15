<script setup>
import { ref, onMounted } from 'vue';
import { ElMessageBox } from 'element-plus';
import { api, items, emptyProblem } from '../api.js';
import { session, t } from '../session.js';
import ProblemEditor from '../components/ProblemEditor.vue';
const tab = ref('proposals'),
  proposals = ref([]),
  solutions = ref([]),
  problems = ref([]),
  open = ref(false),
  editing = ref(null);
const proposal = ref({ problem: emptyProblem(), standard_language: 'CPP', standard_code: '' });
const editorial = ref({ problem: null, title: '', content: '' });
async function searchProblems(query = '') {
  problems.value = items(await api('/problems?search=' + encodeURIComponent(query)));
}
async function load() {
  if (!session.user) return;
  proposals.value = items(await api('/problem-proposals'));
  solutions.value = items(await api('/problem-solutions')).filter(
    (e) => e.author_id === session.user.id,
  );
  await searchProblems();
}
function edit(item = null) {
  editing.value = item?.id || null;
  if (tab.value === 'proposals')
    proposal.value = item
      ? {
          problem: JSON.parse(JSON.stringify(item.problem)),
          standard_language: item.standard_language,
          standard_code: item.standard_code,
        }
      : { problem: emptyProblem(), standard_language: 'CPP', standard_code: '' };
  else
    editorial.value = item
      ? { problem: item.problem, title: item.title, content: item.content }
      : { problem: null, title: '', content: '' };
  open.value = true;
}
async function save() {
  const path = tab.value === 'proposals' ? '/problem-proposals' : '/problem-solutions';
  await api(path + (editing.value ? '/' + editing.value : ''), {
    method: editing.value ? 'PUT' : 'POST',
    body: tab.value === 'proposals' ? proposal.value : editorial.value,
  });
  open.value = false;
  await load();
}
async function remove(item) {
  await ElMessageBox.confirm(t('删除这份内容？', 'Delete this item?'));
  await api((tab.value === 'proposals' ? '/problem-proposals/' : '/problem-solutions/') + item.id, {
    method: 'DELETE',
  });
  await load();
}
onMounted(() => load().catch(() => {}));
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="eyebrow">Your workspace</div>
      <h1>{{ t('把思路，写成作品。', 'Make something worth sharing.') }}</h1>
      <p class="subtitle">
        {{
          t(
            '投稿题目和题解，查看审核进度。',
            'Propose problems, write editorials and follow reviews.',
          )
        }}
      </p>
    </div>
    <el-button v-if="session.user" type="primary" @click="edit()">{{
      t('新建', 'Create')
    }}</el-button>
  </div>
  <section v-if="session.user" class="panel">
    <el-tabs v-model="tab"
      ><el-tab-pane :label="t('题目投稿', 'Problem proposals')" name="proposals" /><el-tab-pane
        :label="t('我的题解', 'My editorials')"
        name="editorials"
    /></el-tabs>
    <el-table :data="tab === 'proposals' ? proposals : solutions"
      ><el-table-column prop="title" :label="t('标题', 'Title')" min-width="180" /><el-table-column
        prop="status"
        :label="t('审核状态', 'Status')"
        width="130"
      /><el-table-column
        prop="review_message"
        :label="t('审核意见', 'Review')"
        min-width="180"
      /><el-table-column width="140"
        ><template #default="{ row }"
          ><el-button
            v-if="tab !== 'proposals' || row.status === 'PENDING'"
            text
            @click="edit(row)"
            >{{ t('编辑', 'Edit') }}</el-button
          ><el-button text type="danger" @click="remove(row)">{{
            t('删除', 'Delete')
          }}</el-button></template
        ></el-table-column
      ></el-table
    >
  </section>
  <el-empty v-else :description="t('请先登录', 'Please sign in')" />
  <el-dialog
    v-model="open"
    :title="
      tab === 'proposals' ? t('题目投稿', 'Problem proposal') : t('撰写题解', 'Write editorial')
    "
    width="900px"
  >
    <template v-if="tab === 'proposals'"
      ><ProblemEditor v-model="proposal.problem" />
      <h3>{{ t('标准解答', 'Standard solution') }}</h3>
      <div class="toolbar">
        <el-select v-model="proposal.standard_language"
          ><el-option v-for="v in ['C', 'CPP', 'JAVA', 'PYTHON']" :key="v" :value="v"
        /></el-select>
      </div>
      <el-input v-model="proposal.standard_code" type="textarea" class="code" :rows="15"
    /></template>
    <el-form v-else label-position="top"
      ><el-form-item :label="t('题目', 'Problem')"
        ><el-select v-model="editorial.problem" filterable remote :remote-method="searchProblems"
          ><el-option
            v-for="p in problems"
            :key="p.id"
            :value="p.id"
            :label="p.id + '. ' + p.title" /></el-select></el-form-item
      ><el-form-item :label="t('标题', 'Title')"
        ><el-input v-model="editorial.title" /></el-form-item
      ><el-form-item :label="t('正文', 'Content')"
        ><el-input v-model="editorial.content" type="textarea" :rows="16" /></el-form-item
    ></el-form>
    <template #footer
      ><el-button type="primary" @click="save">{{
        t('提交审核', 'Submit for review')
      }}</el-button></template
    >
  </el-dialog>
</template>
