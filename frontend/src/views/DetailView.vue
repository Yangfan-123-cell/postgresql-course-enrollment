<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../api";
import type { Section } from "../api/types";
import { errorMessage } from "../api/client";
import { useEnrollment } from "../stores/enrollment";
import { useCart } from "../stores/cart";
import Icon from "./widgets/Icon.vue";
import { RULES } from "./config";
import {
  conflictNames,
  fillLevel,
  meetingText,
  periodCount,
  periodTime,
  weekdays,
} from "./format";

const route = useRoute(),
  section = ref<Section>(),
  error = ref(""),
  message = ref(""),
  allow = ref(true),
  loading = ref(false),
  store = useEnrollment(),
  cart = useCart();

const isEnrolled = computed(() =>
  section.value ? store.items.some((e) => e.section_id === section.value!.id) : false,
);
const isWaiting = computed(() =>
  section.value ? store.waiting.some((w) => w.section_id === section.value!.id) : false,
);
const conflicts = computed(() => {
  if (!section.value || isEnrolled.value || isWaiting.value) return [];
  const refs = store.items.map((e) => ({
    id: e.section_id,
    name: e.course.name,
    meetings: e.meetings,
  }));
  return conflictNames(section.value.meetings, refs, section.value.id);
});
const fillPct = computed(() =>
  section.value && section.value.capacity
    ? Math.min(100, (section.value.enrolled_count / section.value.capacity) * 100)
    : 0,
);

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
    try {
      await store.refresh();
    } catch {
      // 不覆盖成功提示
    }
  } catch (e) {
    error.value = errorMessage(e);
  }
}
onMounted(async () => {
  void load();
  try {
    await store.refresh();
  } catch {
    // 忽略侧栏统计刷新错误，主详情错误单独提示
  }
});
</script>
<template>
  <RouterLink to="/hall" class="back-link">
    <Icon name="chevron-left" :size="16" />返回选课大厅
  </RouterLink>
  <p v-if="loading" class="empty">加载中…</p>
  <p v-if="error" role="alert" class="notice error">
    {{ error }} <button type="button" class="sm" @click="load">重新加载</button>
  </p>
  <p v-if="message" role="status" class="notice success">
    <Icon name="check-circle" />{{ message }}
  </p>

  <div v-if="section" class="detail-layout">
    <section class="panel detail">
      <div class="detail-header">
        <div>
          <div class="tags">
            <span class="course-code">{{ section.course.code }}</span>
            <span class="tag">{{ section.term }}</span>
            <span class="tag">{{ section.course.dept }}</span>
            <span class="tag">{{ section.course.credits }} 学分</span>
            <span v-if="isEnrolled" class="badge green">已选中</span>
            <span v-else-if="isWaiting" class="badge amber">候补中</span>
          </div>
          <h1>{{ section.course.name }}</h1>
          <p class="muted">
            教学班 #{{ section.id }} · {{ section.batch || "常规选课批次" }}
          </p>
        </div>
        <button
          type="button"
          class="btn ghost"
          @click="cart.toggle(section)"
        >
          <Icon name="star" :filled="cart.has(section.id)" :size="16" />
          {{ cart.has(section.id) ? "已在选课单" : "加入选课单" }}
        </button>
      </div>

      <p v-if="conflicts.length" class="conflict-hint box">
        <Icon name="alert" :size="16" />
        当前时间与已选课程《{{ conflicts.join("》《") }}》冲突，提交将被系统拒绝。
      </p>

      <dl class="detail-grid">
        <div>
          <dt><Icon name="user" :size="15" />授课教师</dt>
          <dd>{{ section.teacher }}</dd>
        </div>
        <div>
          <dt><Icon name="layers" :size="15" />周学时</dt>
          <dd>{{ periodCount(section.meetings) }} 节 / 周</dd>
        </div>
        <div>
          <dt><Icon name="clock" :size="15" />上课时间</dt>
          <dd>
            <div v-for="(m, i) in section.meetings" :key="i" class="meeting-chip">
              周{{ weekdays[m.weekday - 1] }} {{ m.start_period }}–{{ m.end_period }} 节
              <small>{{ periodTime(m) }}</small>
            </div>
            <span v-if="!section.meetings.length">{{ meetingText(section.meetings) }}</span>
          </dd>
        </div>
        <div>
          <dt><Icon name="users" :size="15" />名额状态</dt>
          <dd>
            <div class="capacity-line">
              <span>已选 {{ section.enrolled_count }} / {{ section.capacity }}</span>
              <span>剩余 {{ section.remaining }} · 候补 {{ section.waitlist_count }} 人</span>
            </div>
            <div class="meter" :class="fillLevel(section.enrolled_count, section.capacity)">
              <span :style="{ width: `${fillPct}%` }"></span>
            </div>
          </dd>
        </div>
      </dl>

      <h2>课程介绍</h2>
      <p class="detail-desc">
        {{ section.description || "暂无课程简介，具体教学大纲以授课教师首周课堂发布为准。" }}
      </p>

      <div class="detail-submit">
        <label class="inline"
          ><input v-model="allow" type="checkbox" />满员时同意加入候补</label
        >
        <button
          class="primary lg"
          :disabled="store.busy.includes(section.id)"
          @click="enroll"
        >
          <Icon name="check" :size="16" />
          {{ store.busy.includes(section.id) ? "提交中…" : "提交选课" }}
        </button>
      </div>
    </section>

    <aside class="detail-side">
      <div class="panel side-card">
        <h3>选课注意事项</h3>
        <ul class="rule-list">
          <li v-for="r in RULES" :key="r">
            <Icon name="info" :size="15" /><span>{{ r }}</span>
          </li>
        </ul>
      </div>
      <div class="panel side-card">
        <h3>快捷导航</h3>
        <div class="side-links">
          <RouterLink to="/cart" class="btn ghost">查看选课单 ({{ cart.items.length }})</RouterLink>
          <RouterLink to="/timetable" class="btn ghost">查看每周课表</RouterLink>
          <RouterLink to="/my-courses" class="btn ghost">已选课程 ({{ store.items.length }})</RouterLink>
        </div>
      </div>
    </aside>
  </div>
</template>
