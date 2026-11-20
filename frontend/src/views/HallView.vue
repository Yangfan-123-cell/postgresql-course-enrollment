<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { api } from "../api";
import { errorMessage } from "../api/client";
import type { Section } from "../api/types";
import { useEnrollment } from "../stores/enrollment";
import { meetingText } from "./format";
const store = useEnrollment(),
  sections = ref<Section[]>([]),
  total = ref(0),
  loading = ref(false),
  error = ref(""),
  message = ref("");
const query = reactive({
  term: "2026-FALL",
  keyword: "",
  dept_id: undefined as number | undefined,
  only_open: false,
  page: 1,
  size: 9,
});
let requestId = 0;
async function load() {
  const id = ++requestId;
  loading.value = true;
  error.value = "";
  try {
    const data = await api.sections({ ...query });
    if (id === requestId) {
      sections.value = data.items;
      total.value = data.total;
    }
  } catch (e) {
    if (id === requestId) error.value = errorMessage(e);
  } finally {
    if (id === requestId) loading.value = false;
  }
}
async function enroll(section: Section) {
  error.value = "";
  message.value = "";
  try {
    const result = await store.enroll(section.id, true);
    message.value =
      result.status === "ENROLLED"
        ? `已选中《${section.course.name}》`
        : `已加入《${section.course.name}》候补队列，当前第 ${result.waitlist.position} 位`;
    await load();
    try {
      await store.refresh();
    } catch {
      error.value = "提交成功，但个人列表刷新失败，请前往我的课程刷新确认";
    }
  } catch (e) {
    error.value = errorMessage(e);
  }
}
function selected(id: number) {
  return (
    store.items.some((e) => e.section_id === id) ||
    store.waiting.some((e) => e.section_id === id)
  );
}
function search() {
  query.page = 1;
  void load();
}
onMounted(async () => {
  void load();
  try {
    await store.refresh();
  } catch (e) {
    error.value = errorMessage(e);
  }
});
</script>
<template>
  <div class="page-heading">
    <div>
      <p class="eyebrow">COURSE EXPLORER</p>
      <h1>选课大厅</h1>
      <p class="muted">探索感兴趣的课程，安排属于你的学习节奏。</p>
    </div>
    <span class="term-tag">{{ query.term }} · 秋季学期</span>
  </div>
  <section class="hero">
    <div>
      <span class="badge">学期选课</span>
      <h2>下一段学习，从这里开始。</h2>
      <p>选课结果以提交时为准，满员课程可加入候补队列。</p>
    </div>
    <div class="hero-stat">
      <strong>{{ store.items.length }}</strong
      ><span>已选课程</span>
    </div>
    <div class="hero-stat">
      <strong>{{ store.credits }}</strong
      ><span>已选学分</span>
    </div>
    <div class="hero-stat">
      <strong>{{ store.waiting.length }}</strong
      ><span>候补课程</span>
    </div>
  </section>
  <form class="filters" @submit.prevent="search">
    <input
      v-model="query.keyword"
      aria-label="搜索课程"
      placeholder="搜索课程名称 / 课程号"
    /><input
      v-model="query.term"
      aria-label="学期"
      required
      placeholder="学期，如 2026-FALL"
    /><input
      v-model.number="query.dept_id"
      type="number"
      min="1"
      aria-label="院系 ID"
      placeholder="院系 ID（可选）"
    /><label class="inline"
      ><input v-model="query.only_open" type="checkbox" />仅看有余位</label
    ><button class="primary" :disabled="loading">搜索</button>
  </form>
  <p v-if="message" role="status" class="notice success">{{ message }}</p>
  <p v-if="error" role="alert" class="notice error">
    {{ error }} <button @click="load">重试</button>
  </p>
  <div class="section-heading">
    <h2>
      全部教学班 <span class="muted small">{{ total }} 个结果</span>
    </h2>
    <span class="muted small">名额由服务端实时校验</span>
  </div>
  <div v-if="loading" class="empty" role="status">正在加载课程…</div>
  <div v-else-if="!sections.length && !error" class="empty">
    暂无匹配课程，试试调整搜索条件。
  </div>
  <div v-else class="course-grid">
    <article v-for="section in sections" :key="section.id" class="course-card">
      <div class="card-top">
        <span class="course-code">{{ section.course.code }}</span
        ><span
          class="badge"
          :class="section.remaining > 0 ? 'green' : 'amber'"
          >{{
            section.remaining > 0
              ? `余 ${section.remaining} 位`
              : "已满 · 可候补"
          }}</span
        >
      </div>
      <RouterLink :to="`/sections/${section.id}`" class="course-title">{{
        section.course.name
      }}</RouterLink>
      <p class="muted">
        {{ section.course.dept }} <span class="dot">·</span>
        {{ section.course.credits }} 学分
      </p>
      <dl>
        <div>
          <dt>授课教师</dt>
          <dd>{{ section.teacher }}</dd>
        </div>
        <div>
          <dt>上课时间</dt>
          <dd>{{ meetingText(section.meetings) }}</dd>
        </div>
      </dl>
      <div class="capacity-line">
        <span>已选 {{ section.enrolled_count }} / {{ section.capacity }}</span
        ><span>候补 {{ section.waitlist_count }}</span>
      </div>
      <progress
        :value="section.enrolled_count"
        :max="section.capacity"
      ></progress>
      <div class="card-actions">
        <RouterLink :to="`/sections/${section.id}`">查看详情</RouterLink
        ><button
          :class="section.remaining ? 'primary' : 'secondary'"
          :disabled="selected(section.id) || store.busy.includes(section.id)"
          @click="enroll(section)"
        >
          {{
            store.busy.includes(section.id)
              ? "提交中…"
              : selected(section.id)
                ? "已选 / 已候补"
                : section.remaining > 0
                  ? "选择课程"
                  : "加入候补"
          }}
        </button>
      </div>
    </article>
  </div>
  <div class="pagination">
    <button
      :disabled="query.page <= 1 || loading"
      @click="
        query.page--;
        load();
      "
    >
      上一页</button
    ><span
      >第 {{ query.page }} /
      {{ Math.max(1, Math.ceil(total / query.size)) }} 页</span
    ><button
      :disabled="query.page * query.size >= total || loading"
      @click="
        query.page++;
        load();
      "
    >
      下一页
    </button>
  </div>
</template>
