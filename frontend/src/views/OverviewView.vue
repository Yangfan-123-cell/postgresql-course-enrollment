<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { errorMessage } from "../api/client";
import { useAuth } from "../stores/auth";
import { useEnrollment } from "../stores/enrollment";
import { useCart } from "../stores/cart";
import Icon from "./widgets/Icon.vue";
import ProgressRing from "./widgets/ProgressRing.vue";
import { useNow } from "./widgets/useNow";
import { CREDIT_RULE, NOTICES, ROUNDS, RULES, TERM, roundStatus } from "./config";
import { periodCount, shortDate, weekdays } from "./format";

const auth = useAuth(),
  store = useEnrollment(),
  cart = useCart(),
  now = useNow(),
  loading = ref(false),
  error = ref("");

const totalPeriods = computed(() =>
  store.items.reduce((sum, e) => sum + periodCount(e.meetings), 0),
);

const creditStatus = computed(() => {
  if (store.credits < CREDIT_RULE.min)
    return {
      text: `距离最低建议 ${CREDIT_RULE.min} 学分还差 ${CREDIT_RULE.min - store.credits} 学分`,
      tone: "amber",
    };
  if (store.credits > CREDIT_RULE.max)
    return {
      text: `已超出建议上限 ${CREDIT_RULE.max} 学分`,
      tone: "red",
    };
  return { text: "处于培养方案建议学分范围内", tone: "green" };
});

const dayLoad = computed(() => {
  const counts = Array.from({ length: 7 }, () => 0);
  for (const item of store.items) {
    for (const m of item.meetings) {
      if (m.weekday >= 1 && m.weekday <= 7) {
        counts[m.weekday - 1]! += m.end_period - m.start_period + 1;
      }
    }
  }
  const max = Math.max(4, ...counts);
  return counts.map((count, i) => ({
    label: `周${weekdays[i]}`,
    count,
    pct: Math.round((count / max) * 100),
  }));
});

const deptStats = computed(() => {
  const map = new Map<string, { dept: string; count: number; credits: number }>();
  for (const e of store.items) {
    const cur = map.get(e.course.dept) || {
      dept: e.course.dept,
      count: 0,
      credits: 0,
    };
    cur.count++;
    cur.credits += e.course.credits;
    map.set(e.course.dept, cur);
  }
  return [...map.values()];
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    await store.refresh();
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>
<template>
  <div class="page-heading">
    <div>
      <p class="eyebrow">ACADEMIC OVERVIEW</p>
      <h1>学业概览</h1>
      <p class="muted">
        {{ auth.user?.name }}（{{ auth.user?.student_no }}）·
        {{ auth.user?.major ?? "计算机技术" }} · {{ TERM.name }}
      </p>
    </div>
    <div class="heading-actions">
      <button :disabled="loading" @click="load">
        <Icon name="refresh" :size="15" />刷新数据
      </button>
      <RouterLink to="/hall" class="btn primary">
        <Icon name="grid" :size="15" />前往选课大厅
      </RouterLink>
    </div>
  </div>

  <p v-if="error" role="alert" class="notice error">{{ error }}</p>

  <div class="overview-grid">
    <section class="panel overview-card credit-card">
      <div class="panel-head">
        <h2>学期学分进度</h2>
        <span class="badge" :class="creditStatus.tone">
          {{ store.credits }} / {{ CREDIT_RULE.max }} 学分
        </span>
      </div>
      <div class="ring-layout">
        <ProgressRing
          :value="store.credits"
          :max="CREDIT_RULE.max"
          :size="136"
          :stroke="11"
          color="#255fc6"
        >
          <strong>{{ store.credits }}</strong>
          <small>已选学分</small>
        </ProgressRing>
        <div class="ring-details">
          <p class="status-line">{{ creditStatus.text }}</p>
          <ul>
            <li><span>已选课程</span><b>{{ store.items.length }} 门</b></li>
            <li><span>每周学时</span><b>{{ totalPeriods }} 节</b></li>
            <li><span>候补队列</span><b>{{ store.waiting.length }} 门</b></li>
            <li><span>选课单意向</span><b>{{ cart.items.length }} 门（{{ cart.credits }} 学分）</b></li>
          </ul>
        </div>
      </div>
    </section>

    <section class="panel overview-card">
      <div class="panel-head">
        <h2>每周课时分布</h2>
        <span class="muted small">共 {{ totalPeriods }} 节 / 周</span>
      </div>
      <div class="bar-chart" role="img" aria-label="每周一至周日节次分布">
        <div v-for="d in dayLoad" :key="d.label" class="bar-col">
          <small class="bar-val">{{ d.count || "" }}</small>
          <div class="bar-track">
            <span :style="{ height: `${d.pct}%` }" :class="{ 'is-empty': !d.count }"></span>
          </div>
          <span class="bar-label">{{ d.label }}</span>
        </div>
      </div>
      <div v-if="deptStats.length" class="dept-pills">
        <span v-for="d in deptStats" :key="d.dept" class="tag">
          {{ d.dept }} · {{ d.count }} 门（{{ d.credits }} 学分）
        </span>
      </div>
      <p v-else class="muted small">选课后将在此展示各院系课程学分构成。</p>
    </section>

    <section class="panel overview-card full-span">
      <div class="panel-head">
        <h2>本学期选课日程</h2>
        <span class="muted small">{{ TERM.code }}</span>
      </div>
      <ol class="round-timeline">
        <li
          v-for="r in ROUNDS"
          :key="r.key"
          :class="roundStatus(r, now)"
        >
          <div class="tl-head">
            <span class="tl-dot"></span>
            <strong>{{ r.name }}</strong>
            <span class="badge" :class="roundStatus(r, now) === 'current' ? 'green' : ''">
              {{
                roundStatus(r, now) === "done"
                  ? "已结束"
                  : roundStatus(r, now) === "current"
                    ? "进行中"
                    : "未开始"
              }}
            </span>
          </div>
          <p class="tl-date">
            {{ shortDate(r.start) }} – {{ shortDate(r.end) }}
          </p>
          <p class="muted small">{{ r.desc }}</p>
        </li>
      </ol>
    </section>

    <section class="panel overview-card">
      <div class="panel-head">
        <h2>教务通知公告</h2>
        <span class="muted small">{{ NOTICES.length }} 条</span>
      </div>
      <div class="notice-list">
        <article v-for="n in NOTICES" :key="n.id" class="notice-row">
          <div>
            <span class="tag" :class="{ red: n.important }">{{ n.tag }}</span>
            <strong>{{ n.title }}</strong>
            <time>{{ n.date }}</time>
          </div>
          <p class="muted small">{{ n.body }}</p>
        </article>
      </div>
    </section>

    <section class="panel overview-card">
      <div class="panel-head">
        <h2>选课规则与提示</h2>
        <Icon name="shield" :size="16" />
      </div>
      <ul class="rule-list">
        <li v-for="rule in RULES" :key="rule">
          <Icon name="check" :size="15" /><span>{{ rule }}</span>
        </li>
      </ul>
      <div class="quick-links">
        <RouterLink to="/cart" class="btn ghost">查看选课单</RouterLink>
        <RouterLink to="/timetable" class="btn ghost">查看周课表</RouterLink>
        <RouterLink to="/my-courses" class="btn ghost">管理已选课程</RouterLink>
      </div>
    </section>
  </div>
</template>
