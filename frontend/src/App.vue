<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuth } from "./stores/auth";
import { useEnrollment } from "./stores/enrollment";
const auth = useAuth(),
  enrollment = useEnrollment(),
  router = useRouter();
const mock = import.meta.env.VITE_MOCK_API === "true";
function logout() {
  auth.logout();
  enrollment.reset();
  void router.replace("/login");
}
window.addEventListener("auth-expired", logout);
</script>
<template>
  <div v-if="$route.path === '/login'"><RouterView /></div>
  <div v-else class="app-layout">
    <aside class="sidebar">
      <RouterLink class="brand" to="/"
        >课序<span>COURSE SELECT</span></RouterLink
      >
      <div class="nav-label">
        {{ auth.user?.role === "admin" ? "教务工作台" : "学生工作台" }}
      </div>
      <nav v-if="auth.user?.role === 'student'">
        <RouterLink to="/hall">选课大厅</RouterLink
        ><RouterLink to="/my-courses">我的课程</RouterLink>
        <RouterLink to="/waitlist">候补队列</RouterLink
        ><RouterLink to="/timetable">每周课表</RouterLink>
      </nav>
      <nav v-else><RouterLink to="/admin">课程与教学班管理</RouterLink></nav>
      <div class="sidebar-note">高级数据库系统<br />课程选修服务平台</div>
    </aside>
    <main class="workspace">
      <header class="topbar">
        <span
          >教学服务 /
          {{ auth.user?.role === "admin" ? "教务管理" : "自主选课" }}</span
        >
        <div>
          <span v-if="mock" class="badge amber">Mock 演示</span
          ><span class="avatar">{{ auth.user?.name.slice(0, 1) }}</span
          >{{ auth.user?.name
          }}<button class="text-button" @click="logout">退出</button>
        </div>
      </header>
      <div class="page"><RouterView /></div>
      <footer>
        课序 · PostgreSQL 高并发选课系统 <span>2026 / 高级数据库课程项目</span>
      </footer>
    </main>
  </div>
</template>
