<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";
import { errorMessage } from "../api/client";
import Icon from "./widgets/Icon.vue";
import Emblem from "./widgets/Emblem.vue";
import { ROUNDS, TERM, roundStatus } from "./config";
import { shortDate } from "./format";

const REMEMBER_KEY = "course-enrollment-remember";
const remembered = localStorage.getItem(REMEMBER_KEY) || "";
const no = ref(remembered),
  password = ref(""),
  remember = ref(Boolean(remembered)),
  reveal = ref(false),
  busy = ref(false),
  error = ref("");
const auth = useAuth(),
  router = useRouter(),
  mock = import.meta.env.VITE_MOCK_API === "true";
const now = Date.now();
const features = [
  { icon: "zap", title: "实时名额", text: "数据库行级锁保证名额不超卖" },
  { icon: "clock", title: "候补晋升", text: "退课释放名额后自动按序晋升" },
  { icon: "alert", title: "冲突检测", text: "提交前后双重校验上课时间" },
  { icon: "calendar", title: "课表规划", text: "选课单预览，冲突一目了然" },
];
function fill(account: string) {
  no.value = account;
  password.value = "Passw0rd!";
}
async function submit() {
  busy.value = true;
  error.value = "";
  try {
    await auth.login(no.value.trim(), password.value);
    if (remember.value) localStorage.setItem(REMEMBER_KEY, no.value.trim());
    else localStorage.removeItem(REMEMBER_KEY);
    await router.replace(auth.user?.role === "admin" ? "/admin" : "/hall");
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <div class="login-layout">
    <section class="login-intro">
      <div class="login-brand">
        <Emblem :size="52" />
        <div>
          <strong>课序 · 研究生选课系统</strong>
          <span>GRADUATE COURSE SELECTION SYSTEM</span>
        </div>
      </div>
      <div class="login-hero">
        <p class="eyebrow">{{ TERM.name }}</p>
        <h1>让每一次选择，<br />都有清晰的方向。</h1>
        <p class="lead">浏览课程、规划课表、实时选课与候补，一站式完成新学期的课程安排。</p>
        <ul class="feature-list">
          <li v-for="f in features" :key="f.title">
            <span class="feature-icon"><Icon :name="f.icon" /></span>
            <div>
              <strong>{{ f.title }}</strong><small>{{ f.text }}</small>
            </div>
          </li>
        </ul>
      </div>
      <ol class="login-rounds" aria-label="选课安排">
        <li
          v-for="r in ROUNDS"
          :key="r.key"
          :class="roundStatus(r, now)"
        >
          <i></i>
          <strong>{{ r.name }}</strong>
          <small>{{ shortDate(r.start) }}{{ r.start.slice(0, 10) === r.end.slice(0, 10) ? "" : ` – ${shortDate(r.end)}` }}</small>
        </li>
      </ol>
    </section>
    <section class="login-form">
      <form @submit.prevent="submit">
        <p class="eyebrow">WELCOME BACK</p>
        <h2>登录选课系统</h2>
        <p class="muted">使用学号或教务工号登录统一身份认证</p>
        <div class="field">
          <label for="login-no">账号</label>
          <div class="input-wrap">
            <Icon name="user" />
            <input
              id="login-no"
              v-model="no"
              autocomplete="username"
              placeholder="请输入学号或管理员账号"
              required
              maxlength="20"
            />
          </div>
        </div>
        <div class="field">
          <label for="login-password">密码</label>
          <div class="input-wrap">
            <Icon name="lock" />
            <input
              id="login-password"
              v-model="password"
              :type="reveal ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="请输入密码"
              required
            />
            <button
              type="button"
              class="input-addon"
              :aria-label="reveal ? '隐藏密码' : '显示密码'"
              @click="reveal = !reveal"
            >
              <Icon :name="reveal ? 'eye-off' : 'eye'" />
            </button>
          </div>
        </div>
        <div class="login-options">
          <label class="inline"><input v-model="remember" type="checkbox" />记住账号</label>
          <span class="muted small">忘记密码请联系研究生院教务办</span>
        </div>
        <p v-if="error" class="notice error" role="alert">{{ error }}</p>
        <button class="primary full lg" :disabled="busy">
          {{ busy ? "登录中…" : "登录" }}
        </button>
        <div v-if="mock" class="demo-box">
          <div><Icon name="info" :size="16" /><strong>Mock 演示模式</strong> · 密码 Passw0rd!</div>
          <div class="demo-actions">
            <button type="button" @click="fill('S0001')">学生演示 S0001</button>
            <button type="button" @click="fill('admin')">教务演示 admin</button>
          </div>
        </div>
        <p class="muted small center">登录即表示同意《选课系统使用规范》，请勿使用脚本批量提交。</p>
      </form>
      <small class="login-copy">© 2026 高级数据库系统课程项目 · 课序选课平台</small>
    </section>
  </div>
</template>
