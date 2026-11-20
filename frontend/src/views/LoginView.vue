<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../stores/auth";
import { errorMessage } from "../api/client";
const no = ref(""),
  password = ref(""),
  busy = ref(false),
  error = ref("");
const auth = useAuth(),
  router = useRouter(),
  mock = import.meta.env.VITE_MOCK_API === "true";
async function submit() {
  busy.value = true;
  error.value = "";
  try {
    await auth.login(no.value.trim(), password.value);
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
      <div class="brand">课序<span>COURSE SELECT</span></div>
      <div>
        <p class="eyebrow">YOUR NEXT CHAPTER</p>
        <h1>让每一次选择，<br />都有清晰的方向。</h1>
        <p>浏览课程，规划课表，开启你的新学期。</p>
        <div class="login-lines">
          <span>课程探索</span><span>自主选课</span><span>候补晋升</span>
        </div>
      </div>
      <small>高级数据库系统 · 课程选修服务平台</small>
    </section>
    <section class="login-form">
      <form @submit.prevent="submit">
        <p class="eyebrow">WELCOME BACK</p>
        <h2>登录选课系统</h2>
        <p class="muted">使用学号或教务账号登录</p>
        <label
          >账号<input
            v-model="no"
            autocomplete="username"
            placeholder="请输入学号或管理员账号"
            required
            maxlength="20" /></label
        ><label
          >密码<input
            v-model="password"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            required
        /></label>
        <p v-if="error" class="notice error" role="alert">{{ error }}</p>
        <button class="primary full" :disabled="busy">
          {{ busy ? "登录中…" : "登录" }}
        </button>
        <p v-if="mock" class="notice">
          当前为 Mock 演示模式<br />学生 S0001 / 管理员 admin<br />演示密码：Passw0rd!
        </p>
        <p class="muted small">登录后可查看所属角色的课程服务。</p>
      </form>
    </section>
  </div>
</template>
