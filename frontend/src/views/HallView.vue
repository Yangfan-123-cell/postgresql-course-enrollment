<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { api } from "../api";
import { errorMessage } from "../api/client";
import type { Section } from "../api/types";
import { useEnrollment } from "../stores/enrollment";
import { useCart } from "../stores/cart";
import Icon from "./widgets/Icon.vue";
import { useNow } from "./widgets/useNow";
import { CREDIT_RULE, TERM, TERMS, activeRound, countdown } from "./config";
import {
  conflictNames,
  fillLevel,
  meetingText,
  periodTime,
  weekdays,
} from "./format";

const store = useEnrollment(),
  cart = useCart(),
  sections = ref<Section[]>([]),
  total = ref(0),
  loading = ref(false),
  loaded = ref(false),
  error = ref(""),
  message = ref(""),
  view = ref<"card" | "list">(
    (localStorage.getItem("hall-view") as "card" | "list") || "card",
  ),
  hideConflict = ref(false);
const query = reactive({
  term: TERM.code,
  keyword: "",
  dept_id: undefined as number | undefined,
  only_open: false,
  page: 1,
  size: 9,
});
const now = useNow();
const round = computed(() => activeRound(now.value));
const left = computed(() =>
  round.value ? countdown(round.value.target, now.value) : undefined,
);
const pages = computed(() => Math.max(1, Math.ceil(total.value / query.size)));
const termName = computed(
  () => TERMS.find((t) => t.code === query.term)?.name ?? query.term,
);
const enrolledRefs = computed(() =>
  store.items.map((e) => ({
    id: e.section_id,
    name: e.course.name,
    meetings: e.meetings,
  })),
);
function conflictsOf(s: Section) {
  if (selected(s.id)) return [];
  return conflictNames(s.meetings, enrolledRefs.value, s.id);
}
const shown = computed(() =>
  hideConflict.value
    ? sections.value.filter((s) => !conflictsOf(s).length)
    : sections.value,
);
const creditRatio = computed(() =>
  Math.min(100, (store.credits / CREDIT_RULE.max) * 100),
);

let requestId = 0;
async function load(silent = false) {
  const id = ++requestId;
  if (!silent) loading.value = true;
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
    if (id === requestId) {
      loading.value = false;
      loaded.value = true;
    }
  }
}
async function enroll(section: Section) {
  error.value = "";
  message.value = "";
  try {
    const result = await store.enroll(section.id, true);
    message.value =
      result.status === "ENROLLED"
        ? `已选中《${section.course.name}》，可在“我的课程”中查看。`
        : `已加入《${section.course.name}》候补队列，当前第 ${result.waitlist.position} 位`;
    await load(true);
    try {
      await store.refresh();
    } catch {
      error.value = "提交成功，但个人列表刷新失败，请前往我的课程刷新确认";
    }
  } catch (e) {
    error.value = errorMessage(e);
  }
}
function enrolled(id: number) {
  return store.items.some((e) => e.section_id === id);
}
function waiting(id: number) {
  return store.waiting.some((e) => e.section_id === id);
}
function selected(id: number) {
  return enrolled(id) || waiting(id);
}
function actionText(s: Section) {
  if (store.busy.includes(s.id)) return "提交中…";
  if (enrolled(s.id)) return "已选中";
  if (waiting(s.id)) return "候补中";
  return s.remaining > 0 ? "选择课程" : "加入候补";
}
function search() {
  query.page = 1;
  void load();
}
function go(page: number) {
  if (page < 1 || page > pages.value || page === query.page) return;
  query.page = page;
  void load();
}
function setView(v: "card" | "list") {
  view.value = v;
  localStorage.setItem("hall-view", v);
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
    <div class="heading-actions">
      <RouterLink to="/cart" class="btn ghost"
        ><Icon name="bookmark" />我的选课单<span class="count">{{ cart.items.length }}</span></RouterLink
      >
      <span class="term-tag"><Icon name="calendar" :size="15" />{{ termName }}</span>
    </div>
  </div>

  <section class="round-banner">
    <div class="round-main">
      <span class="badge gold"
        ><Icon name="sparkle" :size="14" />{{
          round ? `${round.round.name} · ${round.running ? "进行中" : "即将开始"}` : "本学期选课已结束"
        }}</span
      >
      <h2>下一段学习，从这里开始。</h2>
      <p>选课结果以提交时为准，满员课程可加入候补队列；名额与冲突由服务端实时校验。</p>
    </div>
    <div v-if="round && left" class="countdown" aria-label="轮次倒计时">
      <small>{{ round.running ? "距本轮截止" : "距本轮开始" }}</small>
      <div>
        <span><b>{{ left.days }}</b>天</span>
        <span><b>{{ String(left.hours).padStart(2, "0") }}</b>时</span>
        <span><b>{{ String(left.minutes).padStart(2, "0") }}</b>分</span>
      </div>
    </div>
    <div class="banner-stats">
      <div class="hero-stat">
        <strong>{{ store.items.length }}</strong><span>已选课程</span>
      </div>
      <div class="hero-stat">
        <strong>{{ store.credits }}</strong><span>已选学分</span>
      </div>
      <div class="hero-stat">
        <strong>{{ store.waiting.length }}</strong><span>候补课程</span>
      </div>
      <div class="credit-track" :title="`学分建议 ${CREDIT_RULE.min}–${CREDIT_RULE.max}`">
        <div class="credit-bar">
          <span :style="{ width: `${creditRatio}%` }"></span>
          <i :style="{ left: `${(CREDIT_RULE.min / CREDIT_RULE.max) * 100}%` }"></i>
        </div>
        <small>学分建议 {{ CREDIT_RULE.min }}–{{ CREDIT_RULE.max }}，当前 {{ store.credits }}</small>
      </div>
    </div>
  </section>

  <form class="filter-panel" @submit.prevent="search">
    <div class="filters">
      <div class="input-wrap grow">
        <Icon name="search" />
        <input
          v-model="query.keyword"
          aria-label="搜索课程"
          placeholder="搜索课程名称 / 课程号"
        />
      </div>
      <select v-model="query.term" aria-label="学期" required>
        <option v-for="t in TERMS" :key="t.code" :value="t.code">{{ t.name }}</option>
      </select>
      <input
        v-model.number="query.dept_id"
        type="number"
        min="1"
        aria-label="院系 ID"
        placeholder="院系 ID（可选）"
        class="narrow"
      />
      <button class="primary"><Icon name="search" :size="16" />搜索</button>
    </div>
    <div class="filter-options">
      <label class="switch"
        ><input v-model="query.only_open" type="checkbox" @change="search" /><span></span>仅看有余位</label
      >
      <label class="switch"
        ><input v-model="hideConflict" type="checkbox" /><span></span>隐藏时间冲突课程</label
      >
      <div class="legend">
        <span><i class="lv low"></i>充足</span>
        <span><i class="lv mid"></i>过半</span>
        <span><i class="lv high"></i>紧张</span>
        <span><i class="lv full"></i>已满</span>
      </div>
    </div>
  </form>

  <p v-if="message" role="status" class="notice success">
    <Icon name="check-circle" />{{ message }}
  </p>
  <p v-if="error" role="alert" class="notice error">
    {{ error }} <button type="button" class="sm" @click="load()">重试</button>
  </p>

  <div class="section-heading">
    <h2>
      全部教学班 <span class="muted small">{{ total }} 个结果</span>
    </h2>
    <div class="segmented" role="group" aria-label="显示方式">
      <button type="button" :class="{ active: view === 'card' }" @click="setView('card')">
        <Icon name="grid" :size="15" />卡片
      </button>
      <button type="button" :class="{ active: view === 'list' }" @click="setView('list')">
        <Icon name="list" :size="15" />列表
      </button>
    </div>
  </div>

  <div v-if="loading && !loaded" class="course-grid" aria-busy="true">
    <div v-for="i in 6" :key="i" class="skeleton-card"><i></i><i></i><i></i><i></i></div>
  </div>
  <div v-else-if="loading" class="empty">正在加载课程…</div>
  <div v-else-if="!shown.length && !error" class="empty-state">
    <Icon name="search" :size="34" />
    <p>暂无匹配课程，试试调整搜索条件。</p>
  </div>
  <div v-else-if="view === 'card'" class="course-grid">
    <article
      v-for="section in shown"
      :key="section.id"
      class="course-card"
      :class="{ 'is-selected': selected(section.id), 'is-conflict': conflictsOf(section).length }"
    >
      <div class="card-top">
        <span class="course-code">{{ section.course.code }}</span>
        <span
          class="badge"
          :class="section.remaining > 0 ? (section.remaining <= 5 ? 'red' : 'green') : 'amber'"
          >{{
            section.remaining > 0 ? `余 ${section.remaining} 位` : "已满 · 可候补"
          }}</span
        >
        <button
          type="button"
          class="star-btn"
          :class="{ on: cart.has(section.id) }"
          :aria-pressed="cart.has(section.id)"
          :aria-label="cart.has(section.id) ? '移出选课单' : '加入选课单'"
          :title="cart.has(section.id) ? '移出选课单' : '加入选课单'"
          @click="cart.toggle(section)"
        >
          <Icon name="star" :filled="cart.has(section.id)" />
        </button>
      </div>
      <RouterLink :to="`/sections/${section.id}`" class="course-title">{{
        section.course.name
      }}</RouterLink>
      <div class="tags">
        <span class="tag">{{ section.course.dept }}</span>
        <span class="tag">{{ section.course.credits }} 学分</span>
        <span v-if="enrolled(section.id)" class="tag green">已选中</span>
        <span v-else-if="waiting(section.id)" class="tag amber">候补中</span>
      </div>
      <dl>
        <div>
          <dt><Icon name="user" :size="15" />授课教师</dt>
          <dd>{{ section.teacher }}</dd>
        </div>
        <div>
          <dt><Icon name="clock" :size="15" />上课时间</dt>
          <dd>
            <span v-for="(m, i) in section.meetings" :key="i" class="meeting"
              >周{{ weekdays[m.weekday - 1] }} {{ m.start_period }}–{{ m.end_period }} 节<small>{{
                periodTime(m)
              }}</small></span
            >
            <span v-if="!section.meetings.length">暂未排课</span>
          </dd>
        </div>
      </dl>
      <p v-if="conflictsOf(section).length" class="conflict-hint">
        <Icon name="alert" :size="15" />与《{{ conflictsOf(section).join("》《") }}》时间冲突
      </p>
      <div class="capacity-line">
        <span>已选 {{ section.enrolled_count }} / {{ section.capacity }}</span
        ><span>候补 {{ section.waitlist_count }}</span>
      </div>
      <div class="meter" :class="fillLevel(section.enrolled_count, section.capacity)">
        <span
          :style="{ width: `${Math.min(100, (section.enrolled_count / section.capacity) * 100)}%` }"
        ></span>
      </div>
      <div class="card-actions">
        <RouterLink :to="`/sections/${section.id}`"
          >查看详情<Icon name="arrow-right" :size="14"
        /></RouterLink>
        <button
          :class="section.remaining ? 'primary' : 'secondary'"
          :disabled="selected(section.id) || store.busy.includes(section.id)"
          @click="enroll(section)"
        >
          {{ actionText(section) }}
        </button>
      </div>
    </article>
  </div>
  <div v-else class="panel table-wrap">
    <table class="list-table">
      <thead>
        <tr>
          <th></th>
          <th>课程</th>
          <th>学分</th>
          <th>授课教师</th>
          <th>上课时间</th>
          <th>名额</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="section in shown" :key="section.id" :class="{ 'is-conflict': conflictsOf(section).length }">
          <td class="star-col">
            <button
              type="button"
              class="star-btn"
              :class="{ on: cart.has(section.id) }"
              :aria-pressed="cart.has(section.id)"
              :aria-label="cart.has(section.id) ? '移出选课单' : '加入选课单'"
              @click="cart.toggle(section)"
            >
              <Icon name="star" :filled="cart.has(section.id)" />
            </button>
          </td>
          <td>
            <RouterLink :to="`/sections/${section.id}`" class="strong-link">{{ section.course.name }}</RouterLink>
            <small>{{ section.course.code }} · {{ section.course.dept }}</small>
            <small v-if="conflictsOf(section).length" class="text-red"
              >与《{{ conflictsOf(section).join("》《") }}》冲突</small
            >
          </td>
          <td>{{ section.course.credits }}</td>
          <td>{{ section.teacher }}</td>
          <td>{{ meetingText(section.meetings) }}</td>
          <td class="cap-col">
            <span>{{ section.enrolled_count }} / {{ section.capacity }}</span>
            <div class="meter sm" :class="fillLevel(section.enrolled_count, section.capacity)">
              <span :style="{ width: `${Math.min(100, (section.enrolled_count / section.capacity) * 100)}%` }"></span>
            </div>
          </td>
          <td>
            <button
              class="sm"
              :class="section.remaining ? 'primary' : 'secondary'"
              :disabled="selected(section.id) || store.busy.includes(section.id)"
              @click="enroll(section)"
            >
              {{ actionText(section) }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <nav class="pagination" aria-label="分页">
    <button :disabled="query.page <= 1 || loading" @click="go(query.page - 1)">
      <Icon name="chevron-left" :size="15" />上一页
    </button>
    <button
      v-for="p in pages"
      :key="p"
      class="page-num"
      :class="{ active: p === query.page }"
      :aria-current="p === query.page ? 'page' : undefined"
      :aria-label="`第 ${p} 页`"
      :disabled="loading"
      @click="go(p)"
    >
      {{ p }}
    </button>
    <span class="muted small">第 {{ query.page }} / {{ pages }} 页</span>
    <button :disabled="query.page >= pages || loading" @click="go(query.page + 1)">
      下一页<Icon name="chevron-right" :size="15" />
    </button>
  </nav>
</template>
