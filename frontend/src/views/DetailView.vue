<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../api";
import type { Section } from "../api/types";
import { errorMessage } from "../api/client";
import { useEnrollment } from "../stores/enrollment";
import { meetingText } from "./format";
const route = useRoute(),
  section = ref<Section>(),
  error = ref(""),
  message = ref(""),
  allow = ref(true),
  loading = ref(false),
  store = useEnrollment();
async function load() {
  loading.value = true;
  error.value = "";
  try {
    section.value = await api.section(Number(route.params.id));
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
async function enroll() {
  if (!section.value) return;
  error.value = "";
  message.value = "";
  try {
    const result = await store.enroll(section.value.id, allow.value);
    message.value =
      result.status === "ENROLLED"
        ? "选课成功，请到我的课程查看。"
        : `已加入候补，当前排位 ${result.waitlist.position}。`;
    await load();
  } catch (e) {
    error.value = errorMessage(e);
  }
}
onMounted(load);
</script>
<template>
  <RouterLink to="/hall" class="back-link">返回选课大厅</RouterLink>
  <p v-if="loading" class="empty">加载中…</p>
  <p v-if="error" role="alert" class="notice error">
    {{ error }} <button @click="load">重新加载</button>
  </p>
  <p v-if="message" role="status" class="notice success">{{ message }}</p>
  <section v-if="section" class="panel detail">
    <p class="eyebrow">{{ section.course.code }} / {{ section.term }}</p>
    <h1>{{ section.course.name }}</h1>
    <p class="muted">
      {{ section.course.dept }} · {{ section.course.credits }} 学分
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
      <div>
        <dt>选课批次</dt>
        <dd>{{ section.batch || "待教务公布" }}</dd>
      </div>
      <div>
        <dt>选课人数</dt>
        <dd>
          {{ section.enrolled_count }} / {{ section.capacity }}，候补
          {{ section.waitlist_count }} 人
        </dd>
      </div>
    </dl>
    <h2>课程介绍</h2>
    <p>{{ section.description || "暂无课程简介" }}</p>
    <label class="inline"
      ><input v-model="allow" type="checkbox" />满员时同意加入候补</label
    ><button
      class="primary"
      :disabled="store.busy.includes(section.id)"
      @click="enroll"
    >
      {{ store.busy.includes(section.id) ? "提交中…" : "提交选课" }}
    </button>
  </section>
</template>
