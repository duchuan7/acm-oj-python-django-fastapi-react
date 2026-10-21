<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api, date, items } from '../api.js';
import { t, session } from '../session.js';
const route = useRoute(),
  router = useRouter(),
  users = ref([]),
  data = ref(null);
onMounted(async () => {
  try {
    data.value = await api('/users/' + route.params.id + '/profile');
    if (session.user) users.value = items(await api('/users'));
  } catch {}
});
</script>
<template>
  <template v-if="data"
    ><div class="page-heading">
      <div>
        <div class="eyebrow">Member profile</div>
        <h1>{{ data.user.username }}</h1>
        <p class="subtitle">
          {{ data.user.school || t('每一天，进一步。', 'A little better every day.') }}
        </p>
      </div>
      <div class="tags">
        <el-tag type="info">{{ data.user.role }}</el-tag
        ><el-tag v-if="data.user.is_online" type="success">{{ t('在线', 'Online') }}</el-tag>
      </div>
    </div>
    <div class="toolbar">
      <el-select
        v-if="users.length"
        :model-value="Number(route.params.id)"
        filterable
        :aria-label="t('选择成员', 'Select member')"
        @update:model-value="(id) => router.push('/users/' + id)"
        ><el-option
          v-for="u in users"
          :key="u.id"
          :value="u.id"
          :label="u.username + ' (' + u.role + ')'"
      /></el-select>
      <el-tag>{{ t('解题', 'Solved') }} {{ data.stats?.solved_count || 0 }}</el-tag
      ><el-tag type="info"
        >{{ t('提交', 'Submissions') }} {{ data.stats?.submission_count || 0 }}</el-tag
      >
    </div>
    <p class="muted">
      {{ t('注册时间', 'Registered') }} · {{ date(data.user.date_joined)
      }}<template v-if="!data.user.is_online">
        · {{ t('最近活跃', 'Last seen') }} · {{ date(data.user.last_seen_at) }}</template
      >
    </p>
    <section class="panel">
      <h2>{{ t('最近提交（公开题目）', 'Recent public submissions') }}</h2>
      <el-table :data="data.submissions || []"
        ><el-table-column prop="id" label="#" width="80" /><el-table-column
          :label="t('题目', 'Problem')"
          ><template #default="{ row }"
            ><router-link class="clickable" :to="'/problems/' + row.problem_id">{{
              row.problem_title
            }}</router-link></template
          ></el-table-column
        ><el-table-column prop="language" label="Lang" width="90" /><el-table-column
          :label="t('结果', 'Verdict')"
          ><template #default="{ row }"
            ><span :class="['verdict', row.verdict]">{{ row.verdict }}</span></template
          ></el-table-column
        ><el-table-column prop="score" :label="t('分数', 'Score')" width="80" /><el-table-column
          :label="t('时间', 'Time')"
          ><template #default="{ row }">{{ date(row.submitted_at) }}</template></el-table-column
        ></el-table
      >
    </section>
    <section class="panel">
      <h2>{{ t('博客', 'Blogs') }}</h2>
      <el-empty v-if="!data.blogs.length" :description="t('暂无博客', 'No posts yet')" />
      <article v-for="b in data.blogs" :key="b.id" class="list-card">
        <div>
          <h3>{{ b.title }}</h3>
          <p class="muted">{{ date(b.created_at) }}</p>
          <div class="statement">{{ b.content }}</div>
        </div>
      </article>
    </section></template
  ><el-empty v-else />
</template>
