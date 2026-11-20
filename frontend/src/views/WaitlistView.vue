<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api";
import { errorMessage } from "../api/client";
import { useEnrollment } from "../stores/enrollment";
import { dateText } from "./format";
const store = useEnrollment(),
  error = ref(""),
  message = ref(""),
  loading = ref(false),
  pending = ref<number>(),
  busy = ref(false);
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
async function cancel() {
  if (!pending.value) return;
  busy.value = true;
  error.value = "";
  try {
    await api.cancelWaitlist(pending.value);
    pending.value = undefined;
    message.value = "已退出候补队列。";
    await load();
  } catch (e) {
    error.value = errorMessage(e);
    pending.value = undefined;
    try {
      await store.refresh();
    } catch {
      error.value += "；刷新失败，请手动重试";
    }
  } finally {
    busy.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div class="page-heading">
    <div>
      <p class="eyebrow">WAITING LIST</p>
      <h1>候补队列</h1>
      <p class="muted">出现空余名额后系统自动晋升，刷新可查看最新结果。</p>
    </div>
    <button @click="load" :disabled="loading">刷新排位</button>
  </div>
  <p v-if="error" role="alert" class="notice error">{{ error }}</p>
  <p v-if="message" role="status" class="notice success">{{ message }}</p>
  <p v-if="loading" class="empty">正在刷新…</p>
  <div v-else class="course-grid">
    <article v-for="item in store.waiting" :key="item.id" class="course-card">
      <span class="badge amber">候补中</span>
      <h2>{{ item.course_name }}</h2>
      <div class="queue-position">
        <strong>{{ item.position }}</strong
        ><span>当前排位</span>
      </div>
      <p class="muted">
        班级人数 {{ item.section_enrolled }} / {{ item.section_capacity }}
      </p>
      <p class="small muted">加入时间 {{ dateText(item.joined_at) }}</p>
      <div class="card-actions">
        <RouterLink :to="`/sections/${item.section_id}`">查看课程</RouterLink
        ><button class="danger" @click="pending = item.id">放弃候补</button>
      </div>
    </article>
  </div>
  <div v-if="!loading && !store.waiting.length && !error" class="empty">
    暂无候补课程。已晋升的课程可在“我的课程”中查看。
  </div>
  <div v-if="pending" class="modal-backdrop">
    <section
      class="modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cancel-title"
    >
      <h2 id="cancel-title">放弃本次候补？</h2>
      <p>退出后再次加入将重新排队。</p>
      <div class="actions">
        <button :disabled="busy" @click="pending = undefined">取消</button
        ><button class="danger" :disabled="busy" @click="cancel">
          确认放弃
        </button>
      </div>
    </section>
  </div>
</template>
