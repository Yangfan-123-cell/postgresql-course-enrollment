<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth } from "./stores/auth";
import { useEnrollment } from "./stores/enrollment";
import { useCart } from "./stores/cart";
import Icon from "./views/widgets/Icon.vue";
import Emblem from "./views/widgets/Emblem.vue";
import { useNow } from "./views/widgets/useNow";
import { NOTICES, TERM, activeRound, countdown } from "./views/config";

const auth = useAuth(),
  enrollment = useEnrollment(),
  cart = useCart(),
  router = useRouter(),
  route = useRoute();
const mock = import.meta.env.VITE_MOCK_API === "true";
const now = useNow();
const noticeOpen = ref(false),
  readNotice = ref(Number(localStorage.getItem("notice-read") || 0));
const unread = computed(() => NOTICES.filter((n) => n.id > readNotice.value).length);
const round = computed(() => activeRound(now.value));
const left = computed(() =>
  round.value ? countdown(round.value.target, now.value) : undefined,
);
const isAdmin = computed(() => auth.user?.role === "admin");

const studentNav = computed(() => [
  {
    group: "选课服务",
    items: [
      { to: "/hall", label: "选课大厅", icon: "grid" },
      { to: "/cart", label: "选课单", icon: "bookmark", badge: cart.items.length },
      { to: "/waitlist", label: "候补队列", icon: "clock", badge: enrollment.waiting.length },
    ],
  },
  {
    group: "我的学业",
    items: [
      { to: "/my-courses", label: "我的课程", icon: "book", badge: enrollment.items.length },
      { to: "/timetable", label: "每周课表", icon: "calendar" },
      { to: "/overview", label: "学业概览", icon: "chart" },
    ],
  },
]);
const adminNav = [
  {
    group: "教务管理",
    items: [{ to: "/admin", label: "课程与教学班管理", icon: "sliders", badge: 0 }],
  },
];

function toggleNotice() {
  noticeOpen.value = !noticeOpen.value;
  if (noticeOpen.value) {
    readNotice.value = Math.max(...NOTICES.map((n) => n.id));
    localStorage.setItem("notice-read", String(readNotice.value));
  }
}
function closePopups(e: MouseEvent) {
  if (!(e.target as HTMLElement).closest(".notice-center")) noticeOpen.value = false;
}
function onKey(e: KeyboardEvent) {
  if (e.key === "Escape") noticeOpen.value = false;
}
function logout() {
  auth.logout();
  enrollment.reset();
  void router.replace("/login");
}
window.addEventListener("auth-expired", logout);
onMounted(() => {
  document.addEventListener("click", closePopups);
  document.addEventListener("keydown", onKey);
});
onBeforeUnmount(() => {
  document.removeEventListener("click", closePopups);
  document.removeEventListener("keydown", onKey);
});
</script>
<template>
  <div v-if="route.path === '/login'"><RouterView /></div>
  <div v-else class="app-layout">
    <aside class="sidebar">
      <RouterLink class="brand" :to="isAdmin ? '/admin' : '/hall'">
        <Emblem :size="40" />
        <span class="brand-text"
          >课序<small>COURSE SELECT</small></span
        >
      </RouterLink>
      <div class="term-card">
        <span class="term-dot" :class="{ live: round?.running }"></span>
        <div>
          <strong>{{ TERM.short }}</strong>
          <small>{{
            round ? `${round.round.name}${round.running ? "进行中" : "即将开始"}` : "本学期选课已结束"
          }}</small>
        </div>
      </div>
      <nav aria-label="主导航">
        <template v-for="g in isAdmin ? adminNav : studentNav" :key="g.group">
          <div class="nav-label">{{ g.group }}</div>
          <RouterLink v-for="item in g.items" :key="item.to" :to="item.to"
            ><Icon :name="item.icon" />{{ item.label
            }}<span v-if="item.badge" class="nav-badge" aria-hidden="true">{{
              item.badge
            }}</span></RouterLink
          >
        </template>
      </nav>
      <div class="sidebar-note">
        <Icon name="shield" :size="16" />
        <span>高级数据库系统<br />PostgreSQL 高并发选课平台</span>
      </div>
    </aside>
    <main class="workspace">
      <header class="topbar">
        <nav class="crumbs" aria-label="当前位置">
          <span>{{ isAdmin ? "教务管理" : "研究生教育" }}</span>
          <Icon name="chevron-right" :size="14" />
          <span>{{ route.meta.section }}</span>
          <Icon name="chevron-right" :size="14" />
          <strong>{{ route.meta.title }}</strong>
        </nav>
        <div class="topbar-right">
          <span v-if="round && left" class="round-pill" :class="{ live: round.running }">
            <Icon name="clock" :size="15" />
            {{ round.round.name }}{{ round.running ? "截止" : "开始" }}还有
            <b>{{ left.days }}</b>天<b>{{ left.hours }}</b>时<b>{{ left.minutes }}</b>分
          </span>
          <span v-if="mock" class="badge amber">Mock 演示</span>
          <div class="notice-center">
            <button
              class="icon-btn"
              aria-label="通知公告"
              :aria-expanded="noticeOpen"
              @click.stop="toggleNotice"
            >
              <Icon name="bell" />
              <i v-if="unread" class="dot-badge" aria-hidden="true">{{ unread }}</i>
            </button>
            <div v-if="noticeOpen" class="dropdown notice-dropdown">
              <div class="dropdown-head">
                <strong>通知公告</strong><small>{{ NOTICES.length }} 条</small>
              </div>
              <details v-for="n in NOTICES" :key="n.id" class="notice-item">
                <summary>
                  <span class="tag" :class="{ red: n.important }">{{ n.tag }}</span>
                  <span class="notice-title">{{ n.title }}</span>
                  <time>{{ n.date.slice(5) }}</time>
                </summary>
                <p>{{ n.body }}</p>
              </details>
            </div>
          </div>
          <div class="user-chip">
            <span class="avatar">{{ auth.user?.name.slice(0, 1) }}</span>
            <span class="user-meta">
              <strong>{{ auth.user?.name }}</strong>
              <small>{{
                isAdmin ? "教务管理员" : `${auth.user?.student_no} · ${auth.user?.major ?? "研究生"}`
              }}</small>
            </span>
          </div>
          <button class="text-button" @click="logout">
            <Icon name="logout" :size="16" />退出
          </button>
        </div>
      </header>
      <div class="page"><RouterView /></div>
      <footer>
        <span>课序 · PostgreSQL 高并发选课系统</span>
        <span>2026 / 高级数据库课程项目 · 建议使用 Edge / Chrome 最新版</span>
      </footer>
    </main>
  </div>
</template>
