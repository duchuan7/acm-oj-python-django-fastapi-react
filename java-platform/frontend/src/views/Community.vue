<script setup>
import { ref, onMounted } from 'vue';
import { ElMessageBox } from 'element-plus';
import { api, items, date } from '../api.js';
import { t, session, staff } from '../session.js';
const tab = ref('blogs'),
  blogs = ref([]),
  editorials = ref([]),
  detail = ref(null),
  open = ref(false),
  editing = ref(null),
  draft = ref({ title: '', content: '', status: 'PUBLISHED' });
async function load() {
  blogs.value = items(await api('/blogs'));
  editorials.value = items(await api('/problem-solutions'));
}
function edit(post = null) {
  editing.value = post?.id || null;
  draft.value = post
    ? { title: post.title, content: post.content, status: post.status }
    : { title: '', content: '', status: 'PUBLISHED' };
  open.value = true;
}
async function save() {
  await api('/blogs' + (editing.value ? '/' + editing.value : ''), {
    method: editing.value ? 'PUT' : 'POST',
    body: draft.value,
  });
  open.value = false;
  await load();
}
async function remove(post) {
  await ElMessageBox.confirm(t('删除这篇文章？', 'Delete this post?'));
  await api('/blogs/' + post.id, { method: 'DELETE' });
  detail.value = null;
  await load();
}
onMounted(() => load().catch(() => {}));
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="eyebrow">Notes & ideas</div>
      <h1>{{ t('分享解法，也分享思考。', 'Share solutions. Share ideas.') }}</h1>
      <p class="subtitle">
        {{ t('训练笔记、题解与团队动态。', 'Training notes, editorials and team updates.') }}
      </p>
    </div>
    <el-button v-if="session.user" type="primary" @click="edit()">{{
      t('写博客', 'Write a post')
    }}</el-button>
  </div>
  <section class="panel">
    <el-tabs v-model="tab"
      ><el-tab-pane :label="t('博客', 'Blogs')" name="blogs" /><el-tab-pane
        :label="t('题解', 'Editorials')"
        name="editorials"
    /></el-tabs>
    <el-empty
      v-if="!(tab === 'blogs' ? blogs : editorials).length"
      :description="t('还没有内容', 'No posts yet')"
    />
    <div v-for="post in tab === 'blogs' ? blogs : editorials" :key="post.id" class="list-card">
      <div>
        <h3>
          <span class="clickable" @click="detail = post">{{ post.title }}</span>
          <el-tag size="small" type="info">{{ post.status }}</el-tag>
        </h3>
        <p class="muted">
          <router-link :to="'/users/' + post.author_id">{{ post.author_username }}</router-link> ·
          {{ date(post.created_at)
          }}<template v-if="post.problem_title"> · {{ post.problem_title }}</template>
        </p>
        <div class="statement">
          {{ post.content.slice(0, 180) }}{{ post.content.length > 180 ? '…' : '' }}
        </div>
      </div>
    </div>
  </section>
  <el-dialog
    :model-value="!!detail"
    @update:model-value="
      (v) => {
        if (!v) detail = null;
      }
    "
    :title="detail?.title"
    width="800px"
    ><template v-if="detail"
      ><div class="statement">{{ detail.content }}</div>
      <div
        v-if="tab === 'blogs' && session.user && (staff() || session.user.id === detail.author_id)"
        class="action-row"
      >
        <el-button @click="edit(detail)">{{ t('编辑', 'Edit') }}</el-button
        ><el-button type="danger" plain @click="remove(detail)">{{
          t('删除', 'Delete')
        }}</el-button>
      </div></template
    ></el-dialog
  >
  <el-dialog v-model="open" :title="t('编辑博客', 'Edit blog')" width="800px"
    ><el-form label-position="top"
      ><el-form-item :label="t('标题', 'Title')"
        ><el-input v-model="draft.title" maxlength="200" /></el-form-item
      ><el-form-item :label="t('正文', 'Content')"
        ><el-input v-model="draft.content" type="textarea" :rows="16" /></el-form-item
      ><el-form-item :label="t('状态', 'Status')"
        ><el-select v-model="draft.status"
          ><el-option value="PUBLISHED" :label="t('发布', 'Published')" /><el-option
            value="DRAFT"
            :label="t('草稿', 'Draft')" /></el-select></el-form-item></el-form
    ><template #footer
      ><el-button type="primary" @click="save">{{ t('保存', 'Save') }}</el-button></template
    ></el-dialog
  >
</template>
